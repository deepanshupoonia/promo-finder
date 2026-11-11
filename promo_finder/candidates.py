import hashlib
from .models import Episode, PromoCandidate, PromoSegment, Event
from .config import Config
from .scoring import score_candidate

def _id(segments: list[PromoSegment]) -> str:
    raw = "|".join(f"{s.episode_id}:{s.start_time:.2f}-{s.end_time:.2f}" for s in segments)
    return hashlib.sha1(raw.encode()).hexdigest()[:10]

def _segment(episode: Episode, start_event: Event, end_event: Event) -> PromoSegment:
    start = max(0, (start_event.start_time or 0) - .3); end = min(episode.duration, (end_event.end_time or 0) + .4)
    return PromoSegment(episode.episode_id, episode.episode_number, start, end, start_event.event_id, end_event.event_id, start_event.start_time, end_event.end_time, "boundary padded around complete events")

def generate_candidates(episodes: list[Episode], config: Config) -> list[PromoCandidate]:
    candidates: list[PromoCandidate] = []
    for episode in episodes:
        meaningful = [e for e in episode.events if e.start_time is not None and e.end_time is not None and (e.event_type == "dialogue" or len(e.text) > 20)]
        hooks = sorted(meaningful, key=lambda e: (e.event_type != "dialogue", -(len(e.text) + (20 if "?" in e.text or "!" in e.text else 0))))[:config.max_hook_moments_per_episode]
        for start in hooks:
            following = [e for e in meaningful if e.start_time is not None and e.start_time >= start.start_time and e.end_time - start.start_time <= config.max_duration - .4]
            for end in following[-8:]:
                segment = _segment(episode, start, end)
                if not config.min_duration <= segment.end_time - segment.start_time <= config.max_duration: continue
                events = [e for e in episode.events if e.start_time is not None and e.end_time is not None and e.start_time >= segment.start_time and e.end_time <= segment.end_time]
                transcript = "\n".join(f"{e.speaker or e.event_type.upper()}: {e.text}" for e in events)
                candidate = PromoCandidate(_id([segment]), [segment], segment.end_time-segment.start_time, transcript, "", "", sorted({e.speaker for e in events if e.speaker}), {}, {}, 0)
                candidates.append(score_candidate(candidate, events, episode.logline))
        # Pair separated moments only when a speaker carries the narrative across the cut.
        for first in hooks[: min(8, len(hooks))]:
            for second in meaningful:
                if second.start_time is None or first.end_time is None or second.start_time <= first.end_time + .5:
                    continue
                if first.speaker and second.speaker != first.speaker:
                    continue
                left = _segment(episode, first, first)
                right = _segment(episode, second, second)
                duration = (left.end_time-left.start_time) + (right.end_time-right.start_time)
                if not config.min_duration <= duration <= config.max_duration or right.start_time-left.end_time < .5:
                    continue
                selected = [e for e in episode.events if (left.start_time <= (e.start_time or -1) <= left.end_time) or (right.start_time <= (e.start_time or -1) <= right.end_time)]
                transcript = "\n".join(f"{e.speaker or e.event_type.upper()}: {e.text}" for e in selected)
                candidate = PromoCandidate(_id([left, right]), [left, right], duration, transcript, "", "", sorted({e.speaker for e in selected if e.speaker}), {}, {}, 0)
                candidates.append(score_candidate(candidate, selected, episode.logline))
    return list({c.promo_id: c for c in candidates}.values())
