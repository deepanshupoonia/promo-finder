from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Event:
    event_id: str
    episode_id: str
    scene_id: str
    event_type: str
    text: str
    start_time: float | None
    end_time: float | None
    source_order: int
    speaker: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Scene:
    scene_id: str
    heading: str
    start_time: float | None
    end_time: float | None
    events: list[Event] = field(default_factory=list)

@dataclass
class Episode:
    episode_id: str
    episode_number: int
    logline: str
    continuity_notes: str
    scenes: list[Scene]
    events: list[Event]
    duration: float
    parsing_warnings: list[str] = field(default_factory=list)

@dataclass
class PromoSegment:
    episode_id: str
    episode_number: int
    start_time: float
    end_time: float
    start_event_id: str
    end_event_id: str
    original_start_time: float | None = None
    original_end_time: float | None = None
    adjustment_reason: str = ""

@dataclass
class PromoCandidate:
    promo_id: str
    segments: list[PromoSegment]
    total_duration: float
    transcript: str
    hook: str
    cliffhanger: str
    speakers: list[str]
    feature_scores: dict[str, float]
    feature_evidence: dict[str, list[str]]
    heuristic_score: float
    gemini_score: float | None = None
    final_score: float = 0.0
    evaluation_status: str = "not_requested"
    editorial_reasoning: str = ""
    weaknesses: list[str] = field(default_factory=list)
    validation_status: str = "pending"
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rank: int | None = None
