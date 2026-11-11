import csv, json
from dataclasses import asdict
from pathlib import Path
from .models import PromoCandidate, Episode

def write_outputs(out: str | Path, candidates: list[PromoCandidate], episodes: list[Episode], summary: dict, suppressed: list[dict], warnings: list[str], all_candidates: list[PromoCandidate] | None = None) -> None:
    out = Path(out); out.mkdir(parents=True, exist_ok=True); payload = [asdict(c) for c in candidates]
    raw_candidates = all_candidates or candidates
    (out / "promos.json").write_text(json.dumps([asdict(c) for c in raw_candidates], indent=2), encoding="utf-8")
    fields = ["rank","promo_id","episode_numbers","segments","duration","hook","cliffhanger","hook_score","cliffhanger_score","intensity_score","standalone_score","length_score","heuristic_score","gemini_score","final_score","evaluation_status","validation_status"]
    with (out / "promos.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for c in raw_candidates:
            writer.writerow({"rank":c.rank or "", "promo_id":c.promo_id, "episode_numbers":",".join(str(s.episode_number) for s in c.segments), "segments":json.dumps([asdict(s) for s in c.segments]), "duration":round(c.total_duration,2), "hook":c.hook, "cliffhanger":c.cliffhanger, "hook_score":c.feature_scores.get("hook"), "cliffhanger_score":c.feature_scores.get("cliffhanger"), "intensity_score":c.feature_scores.get("intensity"), "standalone_score":c.feature_scores.get("standalone"), "length_score":c.feature_scores.get("length"), "heuristic_score":c.heuristic_score, "gemini_score":c.gemini_score, "final_score":c.final_score, "evaluation_status":c.evaluation_status, "validation_status":c.validation_status})
    (out / "top_picks.md").write_text("# Top Picks\n\n" + "\n".join(f"## Rank {c.rank}: {c.promo_id}\nEpisodes: {', '.join(str(s.episode_number) for s in c.segments)}\nDuration: {c.total_duration:.2f}s\n\n{c.transcript}\n\nHook: {c.hook}\nCliffhanger: {c.cliffhanger}\nWhy it works: {c.editorial_reasoning or 'Strong deterministic hook, tension, and unresolved ending.'}\nScores: {c.final_score:.3f}\n" for c in candidates[:20]), encoding="utf-8")
    (out / "report.md").write_text("# Promo Finder Report\n\nThe pipeline parses timestamped screenplay events, generates bounded event-window candidates, applies deterministic hard validation, scores editorial features, optionally judges top candidates with Gemini, and ranks with duplicate suppression.\n\nOriginal screenplay files remain private and are excluded by `.gitignore`.\n", encoding="utf-8")
    (out / "quality_report.md").write_text(f"# Quality Report\n\nEpisodes: {len(episodes)}\nScenes: {sum(len(e.scenes) for e in episodes)}\nEvents: {sum(len(e.events) for e in episodes)}\nCandidates: {summary.get('candidate_count', 0)}\nValid candidates: {summary.get('valid_count', 0)}\nSelected: {len(candidates)}\n\nGold and human review data were not supplied, so precision and recall are unavailable.\n", encoding="utf-8")
    (out / "suppressed.json").write_text(json.dumps(suppressed, indent=2), encoding="utf-8"); (out / "warnings.json").write_text(json.dumps(warnings, indent=2), encoding="utf-8"); (out / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "walkthrough.md").write_text("# Three-minute walkthrough\n\n1. Show the private input folder and parser output.\n2. Run heuristic mode and inspect candidate scores.\n3. Show optional Gemini evaluation and cached responses.\n4. Open top_picks.md, promos.csv, and quality_report.md.\n", encoding="utf-8")
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen.canvas import Canvas
        pdf = Canvas(str(out / "solution_summary.pdf"), pagesize=letter); width, height = letter
        pages = [
            ["KUKU AI Problem 1: Find the Promos", "Measured solution summary", "", "Approach", "A reusable Python pipeline parses all timestamped screenplay events, generates bounded event windows, scores hook, cliffhanger, intensity, standalone clarity, and length, then applies hard validation before ranking.", "", "Measured run", f"{summary.get('processed_episode_count', 0)} episodes | {summary.get('candidate_count', 0)} candidates | {summary.get('valid_count', 0)} valid | {summary.get('runtime_seconds', 0)} seconds", "The source pack remains private and is excluded from version control."],
            ["Validation and ranking", "Independent duration, bounds, ordering, gap, boundary, hook, cliffhanger, and diversity checks prevent AI scores from authorizing invalid promos.", "", "Results and limitations", f"The run produced {summary.get('selected_count', 0)} ranked selections. No gold or human review data was supplied, so precision and recall are unavailable. The weakest selections can still be coherent but overly resolved; human review is recommended before publication.", "", "AI disclosure", "Tools used: GitHub Copilot and optional Google Gemini API. Example mistake: the initial heuristic treated a resolved statement containing 'leave' as a cliffhanger; closure detection was added after inspecting the actual top picks."]]
        for page in pages:
            y = height - 55
            for paragraph in page:
                pdf.setFont("Helvetica-Bold" if y == height-55 else "Helvetica", 12 if y == height-55 else 10)
                for line in [paragraph[i:i+100] for i in range(0, len(paragraph), 100)] or [""]:
                    pdf.drawString(45, y, line); y -= 16
                y -= 8
            pdf.showPage()
        pdf.save()
    except Exception as exc:
        warnings.append(f"PDF generation failed: {exc}")
