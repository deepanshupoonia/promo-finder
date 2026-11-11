import re
from decimal import Decimal, ROUND_HALF_UP
from .models import PromoCandidate
from .config import Config

def _rounded(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

def rank_candidates(candidates: list[PromoCandidate], config: Config) -> tuple[list[PromoCandidate], list[dict]]:
    valid = [c for c in candidates if c.validation_status == "valid" and c.final_score >= config.minimum_final_score]
    valid.sort(key=lambda c: (-_rounded(c.final_score), -c.feature_scores.get("hook", 0), -c.feature_scores.get("cliffhanger", 0), -c.feature_scores.get("standalone", 0), len(c.segments), abs(c.total_duration-40), max(s.episode_number for s in c.segments)-min(s.episode_number for s in c.segments), c.segments[0].episode_number, c.segments[0].start_time, c.promo_id))
    selected: list[PromoCandidate] = []; suppressed: list[dict] = []; hooks: set[str] = set(); episode_counts: dict[int, int] = {}
    for candidate in valid:
        normalized = re.sub(r"[^a-z0-9 ]", "", candidate.hook.lower()).strip()
        if normalized in hooks: suppressed.append({"promo_id": candidate.promo_id, "reason": "duplicate hook"}); continue
        overlaps = False
        for existing in selected:
            for left in candidate.segments:
                for right in existing.segments:
                    if left.episode_id == right.episode_id and max(left.start_time, right.start_time) < min(left.end_time, right.end_time) - 0.5:
                        overlaps = True
        if overlaps:
            suppressed.append({"promo_id": candidate.promo_id, "reason": "overlapping moment"}); continue
        if len(candidate.segments) > 1:
            related = [single for single in valid if len(single.segments) == 1 and (single.hook == candidate.hook or single.cliffhanger == candidate.cliffhanger)]
            if related and candidate.final_score < max(single.final_score for single in related) + 0.04:
                suppressed.append({"promo_id": candidate.promo_id, "reason": "multi-segment did not beat related single by 0.04"}); continue
        if len(selected) < 20 and sum(1 for item in selected if item.segments[0].episode_number == candidate.segments[0].episode_number) >= 2:
            suppressed.append({"promo_id": candidate.promo_id, "reason": "top-20 episode diversity"}); continue
        if any(episode_counts.get(s.episode_number, 0) >= 3 for s in candidate.segments): suppressed.append({"promo_id": candidate.promo_id, "reason": "episode diversity"}); continue
        selected.append(candidate); hooks.add(normalized)
        for segment in candidate.segments: episode_counts[segment.episode_number] = episode_counts.get(segment.episode_number, 0) + 1
    for rank, candidate in enumerate(selected, 1): candidate.rank = rank
    return selected, suppressed
