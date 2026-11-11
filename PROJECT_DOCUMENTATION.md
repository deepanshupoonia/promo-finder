# Promo Finder Project Documentation

## Purpose

Promo Finder identifies compelling 20-60 second promotional clips from timestamped screenplay episodes. The current deployed product uses deterministic heuristic scoring only. Gemini is not required for the deployed workflow and no API key is used by the Streamlit UI.

The deployed application is available at:

[Promo Finder Streamlit UI](https://deepanshupoonia-promo-finder-app-fn2dih.streamlit.app/)

The original screenplay pack is confidential. It is not stored in the public repository or bundled into the deployed application.

## Current user workflow

```text
User opens Streamlit UI
          |
          v
Uploads one or more episode .txt files
          |
          v
Clicks Run heuristic pipeline
          |
          v
Streamlit backend creates a temporary workspace
          |
          v
Parser -> candidates -> scores -> validation -> ranking
          |
          v
Ranked promos appear in the UI
          |
          v
User filters, inspects, downloads, and reviews candidates
```

The uploaded files are processed in the Streamlit runtime and are not written into the GitHub repository. The current runtime is temporary; long-term storage would require private object storage or a database.

### Using the deployed UI

1. Open the [deployed Promo Finder UI](https://deepanshupoonia-promo-finder-app-fn2dih.streamlit.app/).
2. In the sidebar, upload one or more screenplay episode `.txt` files.
3. Click **Run heuristic pipeline**.
4. Wait while the backend parses the episodes, generates candidates, scores them, validates them, and ranks them.
5. Review the resulting ranked promos, transcripts, timestamps, hooks, cliffhangers, and score breakdowns in the UI.

The UI does not require the user to run a terminal command. The uploaded episodes are processed by the Streamlit backend for that session.

## Local workflow

Install dependencies and run the deterministic CLI:

```powershell
python -m pip install -r requirements.txt
python -m promo_finder run --input input_pack --out outputs_private --judge none
```

Launch the local UI:

```powershell
python -m streamlit run app.py
```

Open `http://localhost:8501`, upload episode files, and click **Run heuristic pipeline**. The UI can also read an existing local `outputs_private/promos.json` when no in-session run is active.

## Input parsing

Each episode is read without modifying the source file. The parser extracts:

- Episode number and stable episode identifier.
- Logline and continuity notes.
- Scene headings and scene timestamps.
- Dialogue with speaker names.
- Camera descriptions.
- Actions.
- Sound effects.
- Original event order.
- Start and end timestamps converted to seconds.

Timestamp formats such as `00:33.80` and `01:02:13.80` are supported. Missing or malformed timestamps produce warnings instead of fabricated values. Label matching is case-insensitive to support the observed screenplay variants.

## Event model

Every normalized event contains:

- `event_id`
- `episode_id`
- `scene_id`
- `event_type`
- `speaker`
- `text`
- `start_time`
- `end_time`
- `source_order`

Event types include `dialogue`, `action`, `camera`, `sound`, and other preserved categories.

## Candidate generation

The system looks for meaningful moments such as questions, warnings, accusations, confrontations, reversals, emotional statements, and strong action events. It does not simply select the beginning of every scene.

Generation is bounded for practical processing:

- Maximum hook moments per episode: 25.
- Maximum cliffhanger moments per episode: 25.
- Maximum configured segments: 3.
- Hard maximum segments: 4.
- Maximum episode span: 5 episodes.
- Beam-style limits prevent exhaustive combinations.

Single-segment candidates are built around complete event boundaries. Controlled multi-segment candidates are considered only when separated moments have a shared speaker or meaningful relationship.

## Heuristic scoring criteria

Each feature is normalized from 0 to 1:

- **Hook, 30%:** questions, warnings, direct address, threats, commands, names, and strong emotional language. Short contextless lines receive lower scores.
- **Cliffhanger, 30%:** unanswered questions, reveals, ellipses, reversals, threats, ominous actions, and unresolved emotional changes. Complete resolutions are penalized.
- **Intensity, 15%:** conflict language, urgency, action, sound, emotional language, and dialogue density.
- **Standalone clarity, 20%:** whether a new viewer can understand the situation without knowing the show, using logline context, named characters, relationships, and distinct speakers.
- **Length, 5%:** legal clips remain eligible from 20 to 60 seconds, with the strongest preference near 40 seconds.

The score is calculated as:

```text
0.30 * hook
+ 0.30 * cliffhanger
+ 0.15 * intensity
+ 0.20 * standalone
+ 0.05 * length
- 0.03 * (segment_count - 1)
- 0.02 * episode_span
```

The heuristic score remains available in every output record.

## Hard validation criteria

Scoring cannot override validation. Candidates are rejected when they violate applicable rules including:

- Total duration between 20 and 60 seconds.
- Segment boundaries inside the actual episode duration.
- Chronological playback order.
- At least 0.5 seconds between same-episode segments.
- Minimum segment duration of 4 seconds.
- Multi-segment individual duration no longer than 35 seconds.
- Meaningful hook strength of at least 0.30.
- Unresolved cliffhanger strength of at least 0.30.
- Maximum episode span of 5.
- Overlap, duplicate-hook, episode-diversity, and weak multi-segment suppression during ranking.

Invalid candidates remain in raw output for auditability but cannot become final selections.

## Ranking and suppression

Ranking uses deterministic rounded scores and tie-breakers. It suppresses:

- Duplicate normalized hooks.
- Overlapping moments from the same episode.
- More than three selections from one episode.
- More than two selections from the same episode in the top 20.
- Multi-segment candidates that fail to beat a related single-segment candidate by 0.04.

## Streamlit UI features

The UI provides:

- Multiple episode `.txt` upload.
- Backend heuristic processing in a temporary workspace.
- Run progress and summary feedback.
- Episode, score, status, and transcript filters.
- Ranked candidate selection.
- Timestamp and segment display.
- Transcript display in a scrollable read-only text area.
- Hook, cliffhanger, and score evidence.
- Validation warnings.
- Candidate JSON download.
- Human review decisions: `Approved`, `Rejected`, or `Needs edit`.
- Review notes saved to `reviews.csv` during the current runtime.
- **Clear uploaded data** control to reset the current session.

The UI does not require PostgreSQL, Gemini, or an API key.

## Output files

The CLI writes these files into `outputs_private/`:

- `promos.json`: complete raw candidate data.
- `promos.csv`: spreadsheet-friendly candidate data.
- `top_picks.md`: selected ranked promos with transcripts and reasons.
- `report.md`: method and architecture summary.
- `quality_report.md`: measured counts and known limitations.
- `suppressed.json`: duplicate, overlap, and diversity suppression reasons.
- `warnings.json`: parser and runtime warnings.
- `run_summary.json`: runtime, counts, API calls, cache hits, and configuration.
- `solution_summary.pdf`: concise two-page assignment summary.
- `walkthrough.md`: three-minute demonstration outline.

## Privacy and deployment

The repository excludes `input_pack/`, `outputs_private/`, `.env`, caches, and Python artifacts through `.gitignore`. Do not commit confidential episode files or generated transcripts to a public repository.

Streamlit Cloud cannot access files on the developer's local machine. The deployed workflow therefore accepts episode uploads through the UI. Uploaded files are processed by the app runtime and are not automatically permanent storage. Production persistence would require a private storage service and access controls.

## Evaluation data

The optional `gold.json` file must contain human-reviewed approved moments. It must not be generated from the system's own predictions. Without human-reviewed gold data, precision, recall, hit rate, and related quality metrics are not meaningful.

## Testing and measured results

Run the tests with:

```powershell
python -m pytest -q
```

The current automated tests cover timestamp parsing, corpus parsing, hook scoring, and short-duration rejection. The current suite passes 4 tests.

The latest full heuristic run processed 50 episodes, 100 scenes, and 3,727 events. It generated 7,026 candidates, found 1,781 hard-valid candidates, and selected 86 final promos in approximately 2 seconds. It made zero Gemini API calls.

Known limitations include small automated-test coverage, approximate handling of some advanced validation rules, temporary deployment storage, and no human-reviewed gold dataset.
