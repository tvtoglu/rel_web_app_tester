import io
from typing import Dict
import pandas as pd
from scipy.stats import weibull_min

def fit_weibull(df: pd.DataFrame) -> Dict[str, float]:
    if "value" not in df.columns:
        if df.shape[1] == 1:
            df = df.rename(columns={df.columns[0]: "value"})
        else:
            raise ValueError("Column 'value' not found in input data")
    data = pd.to_numeric(df["value"], errors="coerce").dropna().to_numpy()
    if data.size < 2:
        raise ValueError("Not enough data points for Weibull fit (need >= 2)")
    c, loc, scale = weibull_min.fit(data, floc=0)
    mttf = weibull_min.mean(c, loc=loc, scale=scale)
    return {"shape": float(c), "scale": float(scale), "MTTF": float(mttf), "n": int(data.size)}

def run_analysis(file_bytes: bytes, filename: str) -> dict:
    try:
        if filename.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {"status": "error", "message": f"Datei konnte nicht gelesen werden: {e}"}
    try:
        results = fit_weibull(df)
        return {"status": "ok", "summary": results}
    except Exception as e:
        return {"status": "error", "message": f"Analyse fehlgeschlagen: {e}"}
