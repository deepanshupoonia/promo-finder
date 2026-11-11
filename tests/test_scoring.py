from promo_finder.features import hook_score
from promo_finder.models import Event

def test_warning_named_person_is_hook():
    event = Event("1", "1", "1", "dialogue", "You should turn around, Juliana.", 0, 3, 0, "MATRIARCH")
    assert hook_score(event)[0] >= .5
