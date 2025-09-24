from __future__ import annotations
import os, io, json, re, sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlmodel import SQLModel, create_engine, Session, select
from passlib.context import CryptContext

# robust imports
try:
    from .models import User, Dataset, Result
    from .analyze import run_analysis
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from models import User, Dataset, Result  # type: ignore
    from analyze import run_analysis  # type: ignore

# Weibull helpers
def weibull_probability_points(values: np.ndarray):
    x = np.sort(values[~np.isnan(values)])
    n = x.size
    if n == 0:
        return np.array([]), np.array([])
    ranks = (np.arange(1, n+1) - 0.3) / (n + 0.4)
    X = np.log(x)
    Y = np.log(-np.log(1 - ranks))
    return X, Y

def make_weibull_plot(values, beta: float, eta: float):
    vals = np.asarray(values, dtype=float)
    if vals.size == 0:
        return go.Figure()
    Xp, Yp = weibull_probability_points(vals)
    xs = np.linspace(max(vals.min()*0.5, 1e-6), max(vals.max()*1.5, 1.0), 200)
    F = 1 - np.exp(-(xs/float(eta))**float(beta))
    y = np.log(-np.log(1-F))
    x = np.log(xs)
    fig = go.Figure()
    if Xp.size > 0:
        fig.add_scatter(x=Xp, y=Yp, mode="markers", name="Data")
    fig.add_scatter(x=x, y=y, mode="lines", name="Weibull Fit")
    fig.update_layout(xaxis_title="ln(Time)", yaxis_title="ln(-ln(1-F))")
    return fig

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = (st.secrets.get("DATABASE_URL") if hasattr(st, "secrets") else None) or os.getenv("DATABASE_URL") or "sqlite:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "app.db"))
engine = create_engine(DATABASE_URL, echo=False)
SQLModel.metadata.create_all(engine)

@st.cache_resource
def get_session():
    return Session(engine)

def get_user_by_email(db: Session, email: str):
    return db.exec(select(User).where(User.email == email)).first()

def create_user(db: Session, email: str, pw: str) -> User:
    u = User(email=email, hashed_password=pwd_ctx.hash(pw))
    db.add(u); db.commit(); db.refresh(u)
    return u

st.set_page_config(page_title="Reliability SaaS – Streamlit", layout="wide")
st.title("Reliability SaaS – Streamlit MVP")

with st.sidebar:
    st.header("Konto")
    if "user_id" not in st.session_state:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("E-Mail")
            pw = st.text_input("Passwort", type="password")
            new = st.checkbox("Neu registrieren")
            submitted = st.form_submit_button("Weiter")
        if submitted:
            db = get_session()
            user = get_user_by_email(db, email)
            if new:
                if user: st.error("E-Mail bereits vergeben")
                else:
                    user = create_user(db, email, pw)
                    st.session_state.user_id = user.id
                    st.rerun()
            else:
                if not user or not pwd_ctx.verify(pw, user.hashed_password):
                    st.error("Ungültige Zugangsdaten")
                else:
                    st.session_state.user_id = user.id
                    st.rerun()
    else:
        db = get_session()
        user = db.get(User, st.session_state.user_id)
        st.success(f"Eingeloggt als {user.email}")
        if st.button("Logout"):
            st.session_state.clear(); st.rerun()

if "user_id" not in st.session_state:
    st.info("Bitte einloggen oder registrieren.")
    st.stop()

db = get_session()
user = db.get(User, st.session_state.user_id)
tab1, tab2 = st.tabs(["Upload & Analyse", "Deine Datensätze"])

with tab1:
    st.subheader("Datensatz hochladen")
    up = st.file_uploader("CSV oder Excel hochladen", type=["csv","xls","xlsx"])
    if up is not None:
        content = up.read()
        ds = Dataset(user_id=user.id, filename=f"{user.id}_{up.name}", original_name=up.name)
        db.add(ds); db.commit(); db.refresh(ds)
        result = run_analysis(content, up.name)
        if result.get("status") != "ok":
            st.error(result.get("message"))
        else:
            # use already imported Result class (no inside import)
            res = Result(dataset_id=ds.id, summary_json=json.dumps(result["summary"]))
            db.add(res); db.commit()
            st.success("Analyse abgeschlossen und gespeichert.")
            try:
                if up.name.lower().endswith((".xls",".xlsx")):
                    df_local = pd.read_excel(io.BytesIO(content))
                else:
                    df_local = pd.read_csv(io.BytesIO(content))
                values = pd.to_numeric(df_local.get("value", df_local.iloc[:,0]), errors="coerce").dropna().to_numpy()
                beta, eta = result["summary"].get("shape"), result["summary"].get("scale")
                if beta and eta and values.size>0:
                    st.subheader("Weibull Probability Plot")
                    fig = make_weibull_plot(values, beta, eta)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Plot konnte nicht erzeugt werden: {e}")

    st.markdown("---")
    st.subheader("Manuelle Eingabe")
    with st.form("manual_input", clear_on_submit=False):
        c1,c2 = st.columns(2)
        with c1: values_txt = st.text_area("Werte", height=200)
        with c2: cens_txt = st.text_area("Zensiert? (0/1)", height=200)
        manual_name = st.text_input("Datensatz-Name", value="manual_input.csv")
        submit_manual = st.form_submit_button("Analysieren")
    if submit_manual:
        vals = [v.strip() for v in values_txt.splitlines() if v.strip()]
        cens = [c.strip() for c in cens_txt.splitlines() if c.strip()]
        if len(vals)==0: st.error("Bitte Werte eingeben.")
        elif len(vals)!=len(cens): st.error("Zeilenzahl passt nicht.")
        else:
            vnums=[]; cbool=[]
            for i,(v,c) in enumerate(zip(vals,cens),1):
                vnums.append(float(v.replace(',','.')))
                cbool.append(int(c))
            df_manual=pd.DataFrame({"value":vnums,"censored":cbool})
            csv_bytes=df_manual.to_csv(index=False).encode("utf-8")
            ds=Dataset(user_id=user.id, filename=f"{user.id}_{manual_name}", original_name=manual_name)
            db.add(ds); db.commit(); db.refresh(ds)
            result=run_analysis(csv_bytes, manual_name)
            if result.get("status")!="ok": st.error(result.get("message"))
            else:
                res=Result(dataset_id=ds.id, summary_json=json.dumps(result["summary"]))
                db.add(res); db.commit()
                st.success("Manueller Datensatz analysiert und gespeichert.")
                try:
                    values=np.asarray(vnums,float)
                    beta, eta = result["summary"].get("shape"), result["summary"].get("scale")
                    if beta and eta and values.size>0:
                        st.subheader("Weibull Probability Plot")
                        fig=make_weibull_plot(values,beta,eta)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Plot konnte nicht erzeugt werden: {e}")

with tab2:
    items=db.exec(select(Dataset).where(Dataset.user_id==user.id).order_by(Dataset.uploaded_at.desc())).all()
    if not items: st.info("Noch keine Datensätze.")
    else:
        for it in items:
            with st.expander(f"#{it.id} – {it.original_name}"):
                res=db.exec(select(Result).where(Result.dataset_id==it.id)).first()
                if not res: st.warning("Kein Ergebnis."); continue
                summary=json.loads(res.summary_json); st.json(summary)
                try:
                    beta,eta=summary.get("shape"),summary.get("scale")
                    if beta and eta:
                        xs=np.linspace(0.01, float(eta)*3,200)
                        F=1-np.exp(-(xs/float(eta))**float(beta))
                        y=np.log(-np.log(1-F)); x=np.log(xs)
                        fig=go.Figure(); fig.add_scatter(x=x,y=y,mode="lines",name="Weibull Fit")
                        fig.update_layout(xaxis_title="ln(Time)", yaxis_title="ln(-ln(1-F))")
                        st.plotly_chart(fig,use_container_width=True)
                except Exception: pass
