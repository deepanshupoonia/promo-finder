from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Any
import yaml

@dataclass
class Config:
    min_duration: float = 20
    max_duration: float = 60
    min_segment_duration: float = 4
    max_segments: int = 3
    hard_max_segments: int = 4
    min_same_episode_gap: float = 0.5
    spoken_unit_gap: float = 2.0
    hook_window: float = 3
    cliffhanger_window: float = 4
    max_episode_span: int = 5
    beam_width: int = 200
    max_hook_moments_per_episode: int = 25
    max_cliff_moments_per_episode: int = 25
    max_gemini_candidates: int = 40
    llm_weight: float = 0.5
    minimum_final_score: float = 0.40
    default_judge: str = "none"

def load_config(path: str | Path = "config.yaml") -> Config:
    data: dict[str, Any] = {}
    if Path(path).exists():
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    allowed = {f.name for f in fields(Config)}
    config = Config(**{k: v for k, v in data.items() if k in allowed})
    if not 0 <= config.llm_weight <= 1 or config.min_duration > config.max_duration:
        raise ValueError("Invalid duration or llm_weight configuration")
    if config.max_segments > config.hard_max_segments:
        raise ValueError("max_segments cannot exceed hard_max_segments")
    return config
