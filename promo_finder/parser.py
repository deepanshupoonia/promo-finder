from pathlib import Path
import re
from .models import Episode, Scene, Event

TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})(?:\.(\d+))?$")
BLOCK_TIME_RE = re.compile(r"Start:\s*\(?([^)|\s]+)\)?\s*\|\s*End:\s*\(?([^)|\s]+)\)?", re.I)
LABEL_RE = re.compile(r"^\*\*(.+?):\*{0,2}\s*$")

def parse_timestamp(value: str) -> float:
    raw = value.strip().strip("()")
    match = TIME_RE.match(raw)
    if not match:
        raise ValueError(f"Malformed timestamp: {value}")
    hours, minutes, seconds, fraction = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + float(f"0.{fraction or '0'}")

def _header(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.upper().startswith(prefix.upper()):
            return line.split(":", 1)[1].strip()
    return ""

def parse_episode(path: str | Path) -> Episode:
    path = Path(path)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    number_match = re.search(r"EPISODE NUMBER:\s*Episode\s*(\d+)", "\n".join(lines), re.I)
    file_match = re.search(r"episode-(\d+)-Episode\s*(\d+)", path.name, re.I)
    number = int(number_match.group(1) if number_match else (file_match.group(1) if file_match else 0))
    episode_id = file_match.group(2) if file_match else str(number)
    warnings: list[str] = []
    scenes: list[Scene] = []
    events: list[Event] = []
    current: Scene | None = None
    current_label: str | None = None
    current_speaker: str | None = None
    current_text: list[str] = []
    current_times: tuple[float, float] | None = None
    order = 0

    def flush() -> None:
        nonlocal current_label, current_speaker, current_text, current_times, order
        if current is None or not current_label:
            current_label = current_speaker = None; current_text = []; current_times = None; return
        text = " ".join(x.strip().strip('"') for x in current_text if x.strip()).strip()
        if not text and current_label not in {"camera", "action", "sound"}:
            current_label = current_speaker = None; current_text = []; current_times = None; return
        start, end = current_times if current_times else (None, None)
        if start is None or end is None:
            warnings.append(f"Missing timestamp in {path.name}, scene {current.scene_id}, event {order}")
        event = Event(f"{episode_id}-{order:04d}", episode_id, current.scene_id, current_label, text, start, end, order, current_speaker)
        current.events.append(event); events.append(event); order += 1
        current_label = current_speaker = None; current_text = []; current_times = None

    for line in lines:
        line = line.strip()
        scene_match = re.match(r"SCENE\s+(?:HEADING\s*:|)(\d+)?\s*$", line, re.I)
        if scene_match:
            flush()
            if current: scenes.append(current)
            scene_num = scene_match.group(1) or str(len(scenes) + 1)
            current = Scene(f"{episode_id}-scene-{int(scene_num):02d}", "", None, None)
        elif current and re.match(r"Scene heading:", line, re.I):
            current.heading = line.split(":", 1)[1].strip()
        elif current and re.match(r"Scene start:", line, re.I):
            try: current.start_time = parse_timestamp(line.split(":", 1)[1].strip())
            except ValueError as exc: warnings.append(str(exc))
        elif current and re.match(r"Scene end:", line, re.I):
            try: current.end_time = parse_timestamp(line.split(":", 1)[1].strip())
            except ValueError as exc: warnings.append(str(exc))
        elif current:
            label_match = LABEL_RE.match(line)
            if label_match:
                flush()
                raw_label = label_match.group(1).strip().rstrip("*").strip(); upper = raw_label.upper()
                if upper in {"CAMERA", "ACTION", "SOUND FX"}:
                    current_label = {"CAMERA":"camera", "ACTION":"action", "SOUND FX":"sound"}[upper]
                else:
                    current_label = "dialogue"
                    current_speaker = re.sub(r"\s*\([^)]*\)", "", raw_label).strip()
            else:
                time_match = BLOCK_TIME_RE.search(line)
                if time_match and current_label:
                    try: current_times = (parse_timestamp(time_match.group(1)), parse_timestamp(time_match.group(2)))
                    except ValueError as exc: warnings.append(str(exc)); current_times = None
                elif current_label and not line.startswith("Start:") and not line.startswith("End:"):
                    current_text.append(line)
    flush()
    if current: scenes.append(current)
    duration = max((s.end_time or 0 for s in scenes), default=0.0)
    return Episode(episode_id, number, _header(lines, "EPISODE LOGLINE"), _header(lines, "CONTINUITY NOTES"), scenes, events, duration, warnings)

def parse_folder(folder: str | Path) -> tuple[list[Episode], list[str]]:
    paths = sorted(Path(folder).glob("*.txt"))
    if not paths: raise FileNotFoundError(f"No .txt episodes found in {folder}")
    episodes = [parse_episode(path) for path in paths]
    warnings = [warning for episode in episodes for warning in episode.parsing_warnings]
    return sorted(episodes, key=lambda x: x.episode_number), warnings
