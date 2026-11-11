import csv
import json
from datetime import datetime
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Promo Finder", page_icon="PF", layout="wide", initial_sidebar_state="expanded")

st.markdown(
	"""
	<style>
	:root { --ink: #17212b; --muted: #64727f; --line: #dce4e8; --accent: #d95f3f; --soft: #f5f7f6; }
	.block-container { max-width: 1440px; padding-top: 2rem; }
	h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
	.eyebrow { color: var(--accent); font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
	.hero { border-bottom: 1px solid var(--line); padding-bottom: 1.2rem; margin-bottom: 1.3rem; }
	.muted { color: var(--muted); }
	.score { font-size: 2rem; font-weight: 700; color: var(--accent); }
	.transcript { background: var(--soft); border-left: 4px solid var(--accent); padding: 1rem 1.2rem; white-space: pre-wrap; line-height: 1.55; }
	.tag { background: #e8f0ed; border-radius: 999px; color: #295348; display: inline-block; font-size: .8rem; margin: .15rem; padding: .25rem .55rem; }
	</style>
	""",
	unsafe_allow_html=True,
)


def load_promos(path: Path) -> list[dict]:
	if not path.exists():
		return []
	try:
		return parse_promos(path.read_bytes(), str(path))
	except (OSError, json.JSONDecodeError) as exc:
		st.error(f"Could not read {path}: {exc}")
		return []


def parse_promos(raw: bytes, source: str) -> list[dict]:
	try:
		data = json.loads(raw.decode("utf-8"))
		if not isinstance(data, list):
			st.error(f"{source} must contain a JSON array of promo candidates.")
			return []
		return data
	except (UnicodeDecodeError, json.JSONDecodeError) as exc:
		st.error(f"Could not read {source}: {exc}")
		return []


def format_time(seconds: float) -> str:
	minutes, remainder = divmod(float(seconds), 60)
	return f"{int(minutes):02d}:{remainder:05.2f}"


def save_review(path: Path, promo: dict, decision: str, notes: str) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	exists = path.exists()
	with path.open("a", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=["timestamp", "promo_id", "decision", "notes"])
		if not exists:
			writer.writeheader()
		writer.writerow({"timestamp": datetime.now().isoformat(timespec="seconds"), "promo_id": promo.get("promo_id", ""), "decision": decision, "notes": notes})


def main() -> None:
	st.markdown('<div class="hero"><div class="eyebrow">Editorial review workspace</div><h1>Promo Finder</h1><p class="muted">Explore candidate clips, compare their story beats, and record human review decisions.</p></div>', unsafe_allow_html=True)

	with st.sidebar:
		st.header("Library")
		output_dir = Path(st.text_input("Output folder", "outputs_private"))
		json_path = output_dir / "promos.json"
		uploaded_promos = st.file_uploader("Upload promos.json", type=["json"], help="Use this on Streamlit Cloud, where your local outputs_private folder is unavailable.")
		if st.button("Reload data", use_container_width=True):
			st.cache_data.clear()
			st.rerun()
		st.caption(f"Reading: `{json_path}`" if uploaded_promos is None else f"Using uploaded file: `{uploaded_promos.name}`")
		show_invalid = st.checkbox("Include invalid candidates", value=False)

	promos = parse_promos(uploaded_promos.getvalue(), uploaded_promos.name) if uploaded_promos is not None else load_promos(json_path)
	if not promos:
		st.warning("No promo data found. Run the pipeline locally, then upload outputs_private/promos.json here.")
		st.code("python -m promo_finder run --input input_pack --out outputs_private --judge none", language="powershell")
		st.info("On Streamlit Cloud, input_pack and outputs_private are not available unless you explicitly deploy them. Keep confidential screenplay files private and upload only the generated promos.json.")
		return

	valid_promos = [promo for promo in promos if promo.get("validation_status") == "valid"]
	visible = promos if show_invalid else valid_promos
	episodes = sorted({segment.get("episode_number") for promo in visible for segment in promo.get("segments", []) if segment.get("episode_number") is not None})
	max_score = max((float(promo.get("final_score") or 0) for promo in visible), default=1.0)
	with st.sidebar:
		st.header("Filters")
		selected_episodes = st.multiselect("Episodes", episodes)
		minimum_score = st.slider("Minimum final score", 0.0, 1.0, 0.4, 0.01)
		status_options = sorted({promo.get("evaluation_status", "unknown") for promo in visible})
		selected_status = st.multiselect("Evaluation status", status_options, default=status_options)
		search = st.text_input("Search transcript or promo ID")

	def matches(promo: dict) -> bool:
		promo_episodes = {segment.get("episode_number") for segment in promo.get("segments", [])}
		haystack = f"{promo.get('promo_id', '')} {promo.get('transcript', '')}".lower()
		return (
			(not selected_episodes or promo_episodes.intersection(selected_episodes))
			and float(promo.get("final_score") or 0) >= minimum_score
			and promo.get("evaluation_status", "unknown") in selected_status
			and (not search or search.lower() in haystack)
		)

	filtered = [promo for promo in visible if matches(promo)]
	filtered.sort(key=lambda promo: (promo.get("rank") is None, promo.get("rank") or 999999, -(promo.get("final_score") or 0)))
	metric_a, metric_b, metric_c, metric_d = st.columns(4)
	metric_a.metric("Visible promos", len(filtered))
	metric_b.metric("Valid candidates", len(valid_promos))
	metric_c.metric("Episodes", len(episodes))
	metric_d.metric("Top score", f"{max_score:.3f}")

	if not filtered:
		st.info("No candidates match the current filters.")
		return

	left, right = st.columns([1.1, 2.2], gap="large")
	with left:
		st.subheader("Ranked candidates")
		labels = [f"#{promo.get('rank') or '-'}  {promo.get('promo_id', '')}  ·  {(promo.get('final_score') or 0):.3f}" for promo in filtered]
		selected_label = st.radio("Choose a promo", labels, label_visibility="collapsed")
		selected_index = labels.index(selected_label)
		promo = filtered[selected_index]
		st.download_button("Download candidate JSON", json.dumps(promo, indent=2), file_name=f"{promo.get('promo_id', 'promo')}.json", mime="application/json", use_container_width=True)

	with right:
		segments = promo.get("segments", [])
		episode_text = ", ".join(str(segment.get("episode_number")) for segment in segments)
		st.markdown(f"<div class='eyebrow'>Promo {promo.get('promo_id', '')}</div><h2>Episode {episode_text}</h2>", unsafe_allow_html=True)
		st.markdown(f"<span class='tag'>{promo.get('validation_status', 'unknown')}</span><span class='tag'>{promo.get('evaluation_status', 'unknown')}</span><span class='score'>{float(promo.get('final_score') or 0):.3f}</span>", unsafe_allow_html=True)
		st.write(" · ".join(f"Episode {segment.get('episode_number')}: {format_time(segment.get('start_time', 0))} - {format_time(segment.get('end_time', 0))}" for segment in segments))
		st.markdown("**Hook**")
		st.write(promo.get("hook") or "Not available")
		st.markdown("**Cliffhanger**")
		st.write(promo.get("cliffhanger") or "Not available")
		st.markdown("**Transcript**")
		transcript = promo.get("transcript") or "Transcript not available for this candidate."
		st.text_area("Transcript text", value=transcript, height=420, disabled=True, label_visibility="collapsed")

		st.subheader("Score breakdown")
		feature_rows = [{"Feature": key.title(), "Score": round(float(value), 3), "Evidence": "; ".join(promo.get("feature_evidence", {}).get(key, []))} for key, value in promo.get("feature_scores", {}).items()]
		st.dataframe(feature_rows, use_container_width=True, hide_index=True)
		if promo.get("editorial_reasoning"):
			st.subheader("Gemini reasoning")
			st.write(promo["editorial_reasoning"])
		if promo.get("weaknesses"):
			st.warning("Weaknesses: " + "; ".join(promo["weaknesses"]))
		if promo.get("validation_errors"):
			st.error("Validation: " + "; ".join(promo["validation_errors"]))

		with st.expander("Human review"):
			decision = st.selectbox("Decision", ["Unreviewed", "Approved", "Rejected", "Needs edit"], key=f"decision-{promo.get('promo_id')}")
			notes = st.text_area("Notes", key=f"notes-{promo.get('promo_id')}")
			if st.button("Save review", type="primary"):
				save_review(output_dir / "reviews.csv", promo, decision, notes)
				st.success("Review saved to reviews.csv")


if __name__ == "__main__":
	main()
