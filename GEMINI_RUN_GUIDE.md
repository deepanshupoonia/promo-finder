## Run this in terminal step by step
```powershell

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

python -m promo_finder run --input input_pack --out outputs_private --judge none

python -m promo_finder validate outputs_private\promos.json

python -m pytest -q

python -m streamlit run app.py

# Open http://localhost:8501 in a browser
```
