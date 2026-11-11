import re
from .models import Event

HOOK_WORDS = re.compile(r"\b(turn around|run|stop|wait|warning|danger|betray|never|how could|what happened|you should|swore|truth|dead|marry|leave|don't|cannot|must)\b", re.I)
CONTEXT_WORDS = re.compile(r"\b(family|wedding|husband|wife|sister|brother|love|money|revenge|betray|marry|father|mother|secret|power|enemy)\b", re.I)
QUESTION = re.compile(r"\?|\b(why|how|what|who|where|when)\b", re.I)

def hook_score(event: Event) -> tuple[float, list[str]]:
    text = event.text or ""; score = 0.15; evidence = []
    if QUESTION.search(text): score += .22; evidence.append("question or interrogative")
    if HOOK_WORDS.search(text): score += .28; evidence.append("warning, threat, reversal, or imperative")
    if re.search(r"\b(you|your)\b", text, re.I) and event.speaker: score += .15; evidence.append("direct address")
    if "!" in text: score += .08; evidence.append("exclamation")
    if re.search(r"\b[A-Z][a-z]+\b", text): score += .06; evidence.append("named person")
    if len(text.split()) < 2: score *= .5; evidence.append("contextless short line")
    return min(score, 1.0), evidence

def cliffhanger_score(event: Event) -> tuple[float, list[str]]:
    text = event.text or ""; score = .18; evidence = []
    if QUESTION.search(text): score += .25; evidence.append("unanswered question")
    if "..." in text: score += .2; evidence.append("ellipsis")
    if HOOK_WORDS.search(text): score += .18; evidence.append("threat or reversal")
    if event.event_type in {"action", "sound"}: score += .12; evidence.append("visual or sound escalation")
    if re.search(r"\b(yes|no|never|leave|changed|truth|secret|dead)\b", text, re.I): score += .12; evidence.append("high-consequence final beat")
    if re.search(r"\b(i (will|am|found|know)|you have shown|i may .* but i will)\b", text, re.I): score -= .35; evidence.append("complete emotional resolution")
    return max(0.0, min(score, 1.0)), evidence

def intensity_score(events: list[Event]) -> tuple[float, list[str]]:
    text = " ".join(e.text for e in events); hits = len(HOOK_WORDS.findall(text)) + text.count("!")
    return min(.25 + hits * .08 + len([e for e in events if e.event_type in {"action", "sound"}]) * .04, 1), [f"{hits} high-tension language hits", f"{len(events)} selected events"]

def standalone_score(events: list[Event], logline: str) -> tuple[float, list[str]]:
    text = " ".join(e.text for e in events); score = .35; evidence = []
    if len(text.split()) >= 5: score += .2; evidence.append("opening has enough words")
    if CONTEXT_WORDS.search(text + " " + logline): score += .2; evidence.append("story context present")
    if len({e.speaker for e in events if e.speaker}) >= 2: score += .15; evidence.append("multiple voices")
    if re.match(r"\s*(because|and|but|so|yes|no|he|she|it)\b", text, re.I): score -= .2; evidence.append("contextless connector opening")
    return max(0, min(score, 1)), evidence

def length_score(duration: float) -> float:
    return max(0.0, 1.0 - abs(duration - 40) / 20)
