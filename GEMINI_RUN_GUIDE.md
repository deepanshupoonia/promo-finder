# Promo Finder Run Guide

This guide explains how to run every project mode from a clean Windows PowerShell session.

## 1. Open the project

```powershell
cd C:\Users\deepanshu\Desktop\promo-finder
```

The confidential screenplay files must remain inside `input_pack/`. Do not upload or publish that folder.

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the project with `.venv\Scripts\python.exe` directly instead.

## 3. Configure Gemini only when needed

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

```env
GEMINI_API_KEY=replace_with_a_new_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

The API key is not used by heuristic mode. It is loaded only when `--judge gemini` is selected. Never commit `.env` or print its contents. Rotate a key if it has been exposed.

## 4. Heuristic mode: no API, recommended first run

This mode is deterministic and works offline after dependencies are installed.

```powershell
python -m promo_finder run --input input_pack --out outputs_private --judge none
```

Expected behavior:

- Reads all episode files.
- Makes zero Gemini API calls.
- Writes the full candidate and ranking outputs into `outputs_private/`.
- Reports runtime and candidate counts.

## 5. Gemini smoke test

Run one Gemini candidate first. This checks the API configuration without evaluating the full 40-candidate allowance.

```powershell
python -m promo_finder run --input input_pack --out outputs_private_gemini_smoke --judge gemini --max-gemini-candidates 1
```

Check `run_summary.json`:

- `gemini_calls > 0` means a live API request was made.
- `cache_hits > 0` means a previous result was reused.
- `gemini_fallbacks > 0` means the candidate fell back to heuristic scoring.
- `gemini_warnings` contains the exact error if evaluation failed.

A successful cached smoke test can show `gemini_calls: 0` and `cache_hits: 1`; that is expected and means no new API request was needed.

## 6. Full Gemini mode

After the smoke test succeeds:

```powershell
python -m promo_finder run --input input_pack --out outputs_private_gemini --judge gemini
```

The configured maximum is 40 candidates. Cache files are stored under `.cache/gemini/`. The parser and hard validation rules remain authoritative; Gemini cannot change timestamps or approve invalid candidates.

If the command exits with status 2, inspect:

```powershell
Get-Content outputs_private_gemini\warnings.json
Get-Content outputs_private_gemini\run_summary.json
```

Common causes are an invalid key, unavailable model name, quota exhaustion, network failure, or missing `google-genai` installation.

## 7. Validate generated output

```powershell
python -m promo_finder validate outputs_private\promos.json
```

The raw JSON contains every generated candidate. Invalid candidates are retained for auditability and are not selected in the final ranked list.

## 8. Evaluate against human-reviewed data

When a compatible `gold.json` exists:

```powershell
python -m promo_finder eval --gold gold.json --out outputs_private
```

This writes `evaluation.json`. Without gold or review data, precision and recall must not be claimed.

No gold file is included because the supplied task did not provide human-reviewed reference data. Use `gold.example.json` as a schema example, replace its example record with real reviewed moments, save it as `gold.json`, and then run the command above.

## 9. Run automated tests

```powershell
python -m pytest -q
```

## 10. Launch the Streamlit UI

The UI reads `outputs_private/promos.json` and does not require PostgreSQL.

```powershell
python -m streamlit run app.py
```

Open the displayed address, usually:

```text
http://localhost:8501
```

The dashboard lets you:

- Filter by episode, score, search text, and evaluation status.
- Include or hide invalid candidates.
- Inspect transcripts, timestamps, hooks, cliffhangers, and score evidence.
- View Gemini reasoning when Gemini results are available.
- Download an individual candidate as JSON.
- Record `Approved`, `Rejected`, or `Needs edit` decisions with notes.

Human review decisions are saved locally to `outputs_private/reviews.csv`. The API key is never displayed by the UI.

If the UI says that no promo data exists, run the heuristic pipeline first and click `Reload data` in the sidebar:

```powershell
python -m promo_finder run --input input_pack --out outputs_private --judge none
```

To stop the UI, return to its terminal and press `Ctrl+C`.

## 11. Inspect the results

Open these files after a run:

- `outputs_private\top_picks.md`: selected promos and transcripts.
- `outputs_private\promos.csv`: spreadsheet view.
- `outputs_private\promos.json`: complete raw candidate data.
- `outputs_private\quality_report.md`: measured counts and limitations.
- `outputs_private\run_summary.json`: runtime, API calls, cache hits, and configuration.
- `outputs_private\solution_summary.pdf`: two-page assignment summary.

## End-to-end command sequence

```powershell
cd C:\Users\deepanshu\Desktop\promo-finder
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m promo_finder run --input input_pack --out outputs_private --judge none
python -m promo_finder validate outputs_private\promos.json
python -m streamlit run app.py
# Open http://localhost:8501 in a browser
python -m promo_finder run --input input_pack --out outputs_private_gemini_smoke --judge gemini --max-gemini-candidates 1
python -m promo_finder run --input input_pack --out outputs_private_gemini --judge gemini
```
