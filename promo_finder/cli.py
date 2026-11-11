import argparse, json, time
from dataclasses import asdict
from .config import load_config
from .parser import parse_folder
from .candidates import generate_candidates
from .validate import validate_candidate
from .llm import evaluate
from .ranking import rank_candidates
from .report import write_outputs
from .evaluation import evaluate_outputs

def run(args: argparse.Namespace) -> int:
    started = time.perf_counter(); config = load_config(args.config); episodes, warnings = parse_folder(args.input); episode_map = {e.episode_id:e for e in episodes}
    candidates = generate_candidates(episodes, config)
    for candidate in candidates: validate_candidate(candidate, episode_map, config)
    if args.max_gemini_candidates is not None:
        config.max_gemini_candidates = args.max_gemini_candidates
    calls, hits, fallbacks, llm_warnings = evaluate(sorted(candidates, key=lambda c: c.heuristic_score, reverse=True), config, args.judge, ".cache/gemini")
    for candidate in candidates: validate_candidate(candidate, episode_map, config)
    selected, suppressed = rank_candidates(candidates, config)
    summary = {"input_episode_count":len(episodes), "processed_episode_count":len(episodes), "candidate_count":len(candidates), "valid_count":sum(c.validation_status == 'valid' for c in candidates), "selected_count":len(selected), "gemini_calls":calls, "gemini_fallbacks":fallbacks, "cache_hits":hits, "gemini_warnings":llm_warnings, "runtime_seconds":round(time.perf_counter()-started, 3), "configuration":asdict(config), "software_version":"1.0.0"}
    write_outputs(args.out, selected, episodes, summary, suppressed, warnings + llm_warnings, all_candidates=candidates); print(json.dumps(summary, indent=2))
    if args.judge == "gemini" and calls == 0 and hits == 0:
        print("Gemini mode did not evaluate any candidate. See warnings.json and configure GEMINI_API_KEY/GEMINI_MODEL.")
        return 2
    return 0

def validate_command(args: argparse.Namespace) -> int:
    payload = json.loads(open(args.path, encoding="utf-8").read())
    invalid = [item for item in payload if item.get("validation_status") != "valid"]
    print(json.dumps({"promos": len(payload), "invalid": len(invalid)}, indent=2)); return 1 if invalid else 0

def eval_command(args: argparse.Namespace) -> int:
    from pathlib import Path
    gold_path = Path(args.gold)
    output_path = Path(args.out) / "promos.json"
    if not gold_path.exists():
        gold_path.write_text("[]\n", encoding="utf-8")
        message = {"status": "template_created", "file": str(gold_path), "reason": "A gold file must contain human-reviewed references and cannot be generated from model output.", "next_step": "Edit this file with approved episode_id/start_time/end_time records, then rerun the command."}
        print(json.dumps(message, indent=2))
        return 2
    if not output_path.exists():
        message = {"status": "unavailable", "reason": f"Generated output not found: {output_path}", "next_step": "Run the pipeline first with --judge none or --judge gemini."}
        print(json.dumps(message, indent=2))
        return 2
    metrics = evaluate_outputs(gold_path, output_path)
    print(json.dumps(metrics, indent=2))
    with open(f"{args.out}/evaluation.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(prog="promo_finder"); sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run"); run_parser.add_argument("--input", required=True); run_parser.add_argument("--out", required=True); run_parser.add_argument("--judge", choices=["none", "gemini"], default="none"); run_parser.add_argument("--max-gemini-candidates", type=int, default=None); run_parser.add_argument("--config", default="config.yaml"); run_parser.set_defaults(func=run)
    validate_parser = sub.add_parser("validate"); validate_parser.add_argument("path"); validate_parser.set_defaults(func=validate_command)
    eval_parser = sub.add_parser("eval"); eval_parser.add_argument("--gold", required=True); eval_parser.add_argument("--out", required=True); eval_parser.set_defaults(func=eval_command)
    args = parser.parse_args(); return args.func(args)
