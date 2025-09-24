# Reliability SaaS – Streamlit MVP (Hotfix)

**Main file:** `app/streamlit_app.py`

## Notes
- Fixed `attempted relative import` by using robust import logic.
- Fixed `trapped) error reading bcrypt version` by pinning `bcrypt==3.2.2` and `passlib==1.7.4`.
- Removed stray `from app.models import Result` inside the upload flow (now uses the already-imported class).

## Local run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
