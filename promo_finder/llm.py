import hashlib, json, os
from pathlib import Path
from .models import PromoCandidate
from .config import Config

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

def evaluate(candidates: list[PromoCandidate], config: Config, judge: str, cache_dir: str | Path) -> tuple[int, int, int, list[str]]:
    if judge == "none": return 0, 0, 0, []
    if load_dotenv:
        load_dotenv()
    key = os.getenv("GEMINI_API_KEY"); model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if not key: return 0, 0, 0, ["GEMINI_API_KEY is missing; configure .env for --judge gemini"]
    try:
        from google import genai
        client = genai.Client(api_key=key)
    except Exception as exc: return 0, 0, 0, [f"Gemini client unavailable: {exc}"]
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True); calls = hits = fallbacks = 0; warnings = []
    for candidate in candidates[:config.max_gemini_candidates]:
        prompt = "Evaluate this promo as JSON with hook, cliffhanger, standalone, intensity scores 0-10, reasoning, weaknesses, coherent. Do not change timestamps.\n" + candidate.transcript
        digest = hashlib.sha1((model + prompt).encode()).hexdigest(); cached = cache / f"{digest}.json"
        try:
            data = json.loads(cached.read_text()) if cached.exists() else None
            if data is not None: hits += 1
            else:
                if calls >= config.max_gemini_candidates: break
                response = client.models.generate_content(model=model, contents=prompt); calls += 1
                text = response.text.strip().replace("```json", "").replace("```", ""); data = json.loads(text); cached.write_text(json.dumps(data), encoding="utf-8")
            scores = {name: max(0, min(10, float(data[name]))) / 10 for name in ("hook", "cliffhanger", "standalone", "intensity")}
            candidate.gemini_score = .3*scores["hook"] + .3*scores["cliffhanger"] + .2*scores["standalone"] + .2*scores["intensity"]
            candidate.final_score = (1-config.llm_weight)*candidate.heuristic_score + config.llm_weight*candidate.gemini_score; candidate.evaluation_status = "gemini_evaluated"; candidate.editorial_reasoning = str(data.get("reasoning", "")); candidate.weaknesses = list(data.get("weaknesses", []))
        except Exception as exc:
            fallbacks += 1
            candidate.evaluation_status = "heuristic_fallback"; candidate.warnings.append(f"Gemini evaluation failed for {candidate.promo_id}: {exc}"); warnings.append(f"{candidate.promo_id}: {exc}")
    return calls, hits, fallbacks, warnings
