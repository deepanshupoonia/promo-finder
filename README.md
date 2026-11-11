# Promo Finder

This private Python prototype finds 20-60 second promotional moments from timestamped screenplay episodes. It parses event boundaries, generates bounded candidates, applies independent hard validation, scores hooks and cliffhangers deterministically, optionally asks Gemini for editorial judgment, then ranks and suppresses duplicates.

## Setup

Create a virtual environment and install `requirements.txt`. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` only when using Gemini. `GEMINI_MODEL` is configurable; the default is `gemini-3.5-flash-lite`, which is listed as a current stable model. Confirm current pricing and free-tier eligibility in Google's model documentation before use.

## Commands

`python -m promo_finder run --input input_pack --out outputs_private --judge none`

`python -m promo_finder run --input input_pack --out outputs_private --judge gemini`

`python -m promo_finder validate outputs_private/promos.json`

`python -m promo_finder eval --gold gold.json --out outputs_private`

The original `input_pack` is confidential and must not be published. Generated outputs are private too. Heuristic mode makes zero API calls.

The API key is not used in `--judge none`. It is loaded from `.env` only when `--judge gemini` is explicitly selected. Never print or commit `.env`; rotate any credential that has been exposed.

## Outputs

`promos.json` and `promos.csv` contain ranked machine output. `top_picks.md`, `report.md`, `quality_report.md`, `suppressed.json`, `warnings.json`, `run_summary.json`, and `walkthrough.md` provide presentation, audit, and run metadata. No gold or human review data was supplied, so precision and recall are not claimed.

## Tests

Run `pytest -q`. The parser uses seconds internally and preserves warnings for missing or malformed timestamps. Gemini never chooses or changes timestamps; hard validation remains authoritative.
