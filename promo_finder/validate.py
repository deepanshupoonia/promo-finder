from .models import PromoCandidate, Episode
from .config import Config

def validate_candidate(candidate: PromoCandidate, episodes: dict[str, Episode], config: Config) -> list[str]:
    errors: list[str] = []
    if not config.min_duration <= candidate.total_duration <= config.max_duration: errors.append("V1 duration")
    if len(candidate.segments) > config.hard_max_segments: errors.append("V7 hard segment count")
    previous = None
    for segment in candidate.segments:
        episode = episodes.get(segment.episode_id)
        if not episode or segment.start_time < 0 or segment.end_time > episode.duration + .001: errors.append("V2 bounds")
        if segment.end_time - segment.start_time < config.min_segment_duration: errors.append("V6 segment duration")
        if len(candidate.segments) > 1 and segment.end_time - segment.start_time > 35: errors.append("V7 segment duration")
        key = (segment.episode_number, segment.start_time)
        if previous and key < previous: errors.append("V3 playback order")
        previous = key
    for left, right in zip(candidate.segments, candidate.segments[1:]):
        if left.episode_id == right.episode_id and right.start_time - left.end_time < config.min_same_episode_gap: errors.append("V4 overlap or gap")
    if candidate.feature_scores.get("hook", 0) < .30: errors.append("V8 weak hook")
    if candidate.feature_scores.get("cliffhanger", 0) < .30: errors.append("V9 weak cliffhanger")
    candidate.validation_errors = sorted(set(errors)); candidate.validation_status = "valid" if not errors else "invalid"
    return candidate.validation_errors
