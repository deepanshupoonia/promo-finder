# Promo Finder Project Documentation

## Purpose

Promo Finder identifies compelling 20-60 second promotional clips from timestamped screenplay episodes. It is designed to process a complete local episode folder, produce auditable candidate clips, rank the strongest selections, and optionally use Gemini for editorial judgment.

The original screenplay pack is confidential. It is intentionally excluded from version control and must not be published.

## High-level workflow

```text
Screenplay files
      |
      v
Parser and timestamp normalizer
      |
      v
Structured episodes, scenes, and events
      |
      v
Bounded candidate generation
      |
      v
Feature extraction and heuristic score
      |
      v
Independent hard validation
      |
      +---- judge none ------> heuristic ranking
      |
      +---- judge gemini ----> Gemini evaluation -> combined ranking
                                      |
                                      v
                         duplicate suppression and diversity rules
                                      |
                                      v
                         JSON, CSV, Markdown, PDF, and summaries
```

## Input processing

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

Timestamp formats such as `00:33.80` and `01:02:13.80` are supported. Missing or malformed timestamps produce warnings instead of fabricated values.

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

The event type is one of `dialogue`, `action`, `camera`, `sound`, or another preserved category.

## Candidate generation

The system ranks meaningful moments such as questions, warnings, accusations, confrontations, reversals, emotional statements, and strong action events. It does not simply select the beginning of every scene.

Candidate generation is bounded so that the 50-episode pack remains practical:

- Maximum hook moments per episode: 25.
- Maximum cliffhanger moments per episode: 25.
- Maximum configured segments: 3.
- Hard maximum segments: 4.
- Maximum episode span: 5 episodes.
- Beam-style limits prevent exhaustive combinations.

Single-segment candidates are built around complete event boundaries. Controlled multi-segment candidates are considered only when separated moments have a shared speaker or a meaningful relationship.

## Heuristic scoring

Each candidate receives normalized feature scores from 0 to 1:

- Hook strength: questions, warnings, direct address, threats, commands, names, and strong emotional language.
- Cliffhanger strength: unanswered questions, reveals, ellipses, reversals, threats, and unresolved emotional changes.
- Intensity: conflict language, urgency, action, sound, and dialogue density.
- Standalone clarity: whether a new viewer can understand the situation without knowing the show.
- Length: preference for approximately 40 seconds.

The heuristic score is calculated as:

```text
0.30 * hook
+ 0.30 * cliffhanger
+ 0.15 * intensity
+ 0.20 * standalone
+ 0.05 * length
- 0.03 * (segment_count - 1)
- 0.02 * episode_span
```

The original heuristic score is retained even when Gemini is used.

## Hard validation

Scoring cannot override hard validation. The validator checks duration, episode bounds, chronological playback order, same-episode gaps, minimum segment length, multi-segment maximum length, hook strength, cliffhanger strength, episode span, overlap, and ranking-level duplicate rules.

Invalid candidates remain in raw output for auditability but cannot become final selections.

## Gemini mode

Gemini is optional. In `--judge none` mode, the API key is not read and no API call is made.

In `--judge gemini` mode:

1. `.env` is loaded.
2. `GEMINI_API_KEY` and `GEMINI_MODEL` are read.
3. Only the highest heuristic candidates are sent.
4. The prompt contains the assembled transcript and editorial context.
5. Gemini returns hook, cliffhanger, standalone, intensity, reasoning, weaknesses, and coherence.
6. Scores are validated and normalized.
7. A SHA-1 prompt/model cache avoids duplicate calls.
8. Failures are recorded and the candidate falls back to heuristic scoring.
9. The total configured evaluation allowance is capped at 40 candidates.

Gemini never generates timestamps and never overrides hard validation.

## Ranking

Ranking uses rounded final scores and deterministic tie-breakers. It then suppresses:

- Duplicate normalized hooks.
- Overlapping moments from the same episode.
- More than three selections from one episode.
- More than two selections from the same episode in the top 20.
- Multi-segment candidates that fail to beat the related single-segment candidate by 0.04.

## Output files

- `promos.json`: complete raw candidate data.
- `promos.csv`: spreadsheet-friendly candidate data.
- `top_picks.md`: selected ranked promos with transcripts and reasons.
- `report.md`: method and architecture summary.
- `quality_report.md`: measured counts and known limitations.
- `suppressed.json`: duplicate, overlap, and diversity suppression reasons.
- `warnings.json`: parser and Gemini warnings.
- `run_summary.json`: runtime, counts, API calls, cache hits, and configuration.
- `solution_summary.pdf`: concise two-page submission summary.
- `walkthrough.md`: three-minute demonstration outline.

## Reproducibility and privacy

The heuristic pipeline is deterministic for the same input, configuration, and candidate boundaries. API responses are cached separately. The input folder, `.env`, generated private outputs, and cache are excluded in `.gitignore`.

## Current measured run

The current heuristic run processed 50 episodes, 100 scenes, and 3,727 events. It generated 7,026 candidates, found 1,781 hard-valid candidates, and selected 86 final promos in approximately 2 seconds. It made zero Gemini API calls.

No gold dataset or human review file was supplied, so precision and recall are not claimed.
