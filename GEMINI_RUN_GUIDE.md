# Promo Finder Run Guide

This guide explains how to run every project mode from a clean Windows PowerShell session.

## 1. Open the project

```powershell

cd ...........

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


## 3. Heuristic mode:

This mode is deterministic and works offline after dependencies are installed.

```powershell


python -m promo_finder run --input input_pack --out outputs_private --judge none


```

Expected behavior:

- Reads all episode files.
- Makes zero Gemini API calls.
- Writes the full candidate and ranking outputs into `outputs_private/`.
- Reports runtime and candidate counts.


## 4. Validate generated output

```powershell


python -m promo_finder validate outputs_private\promos.json


```

The raw JSON contains every generated candidate. Invalid candidates are retained for auditability and are not selected in the final ranked list.


## 5. Run automated tests

```powershell


python -m pytest -q


```

## 6. Launch the Streamlit UI

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





## Overall Process in simple words
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
