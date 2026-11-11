from promo_finder.models import PromoCandidate, PromoSegment, Episode
from promo_finder.config import Config
from promo_finder.validate import validate_candidate

def test_short_candidate_rejected():
    segment = PromoSegment("1", 1, 0, 5, "a", "b")
    candidate = PromoCandidate("x", [segment], 5, "x", "x", "x", [], {"hook":.5,"cliffhanger":.5}, {}, 0)
    errors = validate_candidate(candidate, {"1": Episode("1",1,"","",[],[],10)}, Config())
    assert "V1 duration" in errors
