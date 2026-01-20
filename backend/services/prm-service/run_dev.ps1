$env:DATABASE_URL="postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech"
..\..\venv\Scripts\python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
