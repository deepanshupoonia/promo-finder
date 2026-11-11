import csv, json
from pathlib import Path
from typing import Any

def _records(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    return json.loads(path.read_text(encoding="utf-8"))

def evaluate_outputs(gold_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    gold = _records(gold_path); outputs = _records(output_path)
    def key(item: dict[str, Any]) -> tuple[str, float]:
        episode = str(item.get("episode_id", item.get("episode_number", "")))
        start = float(item.get("start_time", item.get("start", 0)))
        return episode, start
    gold_keys = {key(item) for item in gold}
    output_keys = {key(item) for item in outputs}
    hits = len(gold_keys & output_keys)
    top10 = outputs[:10]
    top10_hits = sum(1 for item in top10 if key(item) in gold_keys)
    return {
        "gold_records": len(gold),
        "output_records": len(outputs),
        "recall": hits / len(gold_keys) if gold_keys else None,
        "hit_rate": 1 if hits else 0,
        "precision_at_10": top10_hits / len(top10) if top10 else None,
        "note": "Matching uses episode identifier and start timestamp; adapt gold fields if your review schema differs.",
    }