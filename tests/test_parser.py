from pathlib import Path
from promo_finder.parser import parse_folder, parse_timestamp

ROOT = Path(__file__).parents[1]

def test_timestamp_variants():
    assert parse_timestamp("00:33.80") == 33.8
    assert parse_timestamp("01:02:13.80") == 3733.8

def test_real_corpus_parse():
    episodes, warnings = parse_folder(ROOT / "input_pack")
    assert len(episodes) == 50
    assert sum(len(e.scenes) for e in episodes) == 100
    assert sum(len(e.events) for e in episodes) > 500
    assert any(e.event_type == "dialogue" for e in episodes[0].events)
    assert any(e.event_type == "camera" for e in episodes[0].events)
    assert any(e.event_type == "action" for e in episodes[0].events)
