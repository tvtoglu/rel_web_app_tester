# Reliability SaaS – Streamlit MVP

**Main file:** `app/streamlit_app.py`

## Local run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

SQLite works out of the box. On Streamlit Cloud you can set DATABASE_URL + SECRET_KEY in Secrets for Postgres.
