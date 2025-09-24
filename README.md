# Reliability SaaS – Streamlit MVP

**Main file:** `app/streamlit_app.py` (set this in Streamlit Cloud).

## Local run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
SQLite is default locally. On Cloud, add Secrets if you use Postgres (and install a driver yourself).
