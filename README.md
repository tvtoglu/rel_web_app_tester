# Reliability SaaS – Streamlit MVP

This repository contains a Streamlit app for reliability/lifetime analysis with:
- User login/registration (simple, in-app with hashed passwords)
- CSV/Excel upload **or** manual paste entry (values + censored flags)
- Weibull (2-parameter) fitting demo out of the box
- SQLModel database (SQLite locally, Postgres on Cloud)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Optionally create a `.env` with `DATABASE_URL` and `SECRET_KEY` (local only). By default it uses `sqlite:///./app.db` in the repo.

## Deploy on Streamlit Cloud
1. Push this repo to GitHub.
2. In Streamlit Cloud: New app → select repo/branch → main file: `app/streamlit_app.py`.
3. Set **Secrets** (gear icon):
```toml
DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"
SECRET_KEY = "change-me"
```
4. Deploy.

> Tip: Use a managed Postgres (Neon/Supabase/ElephantSQL). SQLite is ephemeral in the Cloud.

## Data format (manual paste)
- Two columns: `value` and `censored` (0/1), either in two textareas or one textarea with comma/tab/semicolon delimiter.

## License
MIT
