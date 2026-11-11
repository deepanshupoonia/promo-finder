from .features import hook_score, cliffhanger_score, intensity_score, standalone_score, length_score
from .models import PromoCandidate, Event

def score_candidate(candidate: PromoCandidate, events: list[Event], logline: str) -> PromoCandidate:
    spoken = [e for e in events if e.event_type == "dialogue"]
    first = spoken[0] if spoken else (events[0] if events else Event("", "", "", "other", "", 0, 0, 0))
    last = events[-1] if events else first
    hook, he = hook_score(first); cliff, ce = cliffhanger_score(last); intensity, ie = intensity_score(events); standalone, se = standalone_score(events, logline); length = length_score(candidate.total_duration)
    candidate.feature_scores = {"hook": hook, "cliffhanger": cliff, "intensity": intensity, "standalone": standalone, "length": length}
    candidate.feature_evidence = {"hook": he, "cliffhanger": ce, "intensity": ie, "standalone": se, "length": ["preferred duration is 40 seconds"]}
    candidate.hook = first.text; candidate.cliffhanger = last.text
    candidate.heuristic_score = .30 * hook + .30 * cliff + .15 * intensity + .20 * standalone + .05 * length - .03 * (len(candidate.segments)-1) - .02 * (max(s.episode_number for s in candidate.segments) - min(s.episode_number for s in candidate.segments))
    candidate.final_score = candidate.heuristic_score
    return candidate
