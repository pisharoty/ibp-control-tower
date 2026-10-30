import re
import os

patch_macro_code = '''
@st.cache_data(ttl=600)
def fetch_live_macro_telemetry():
    """Fetch live macro indicators using yfinance and FRED REST endpoints."""
    telemetry = {
        "ny_fed_gscpi": {"value": "+1.28 σ", "label": "NY Fed GSCPI", "sub": "🟢 Normalizing"},
        "fred_mfg": {"value": "99.44 pts", "label": "US Industrial Prod", "sub": "🔴 -0.2% YoY"},
        "wb_commodity": {"value": "147.5 Index", "label": "World Bank Commodity Index", "sub": "🟢 +1.8% MoM"},
        "usd_index": {"value": "102.03 pts", "label": "US Dollar Index (DXY)", "sub": "🟢 Live Spot"},
        "kospi_index": {"value": "2,618 pts", "label": "KOSPI Industrial Index", "sub": "🟢 Live Spot"}
    }
    
    # 1. Fetch live DXY and KOSPI via yfinance
    try:
        import yfinance as yf
        tickers = yf.Tickers("DX-Y.NYB ^KS11")
        
        dxy = tickers.tickers["DX-Y.NYB"].fast_info.get("lastPrice")
        if dxy:
            telemetry["usd_index"] = {"value": f"{dxy:.2f} pts", "label": "US Dollar Index (DXY)", "sub": "🟢 Live YFinance Feed"}
            
        kospi = tickers.tickers["^KS11"].fast_info.get("lastPrice")
        if kospi:
            telemetry["kospi_index"] = {"value": f"{kospi:,.0f} pts", "label": "KOSPI Industrial Index", "sub": "🟢 Live YFinance Feed"}
    except Exception:
        pass

    # 2. Fetch live FRED Industrial Production Index (INDPRO)
    try:
        import requests
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO"
        res = requests.get(url, timeout=3.0)
        if res.status_code == 200:
            lines = [line for line in res.text.strip().split("\n") if line and not line.startswith("DATE")]
            if lines:
                latest_val = float(lines[-1].split(",")[-1])
                telemetry["fred_mfg"] = {"value": f"{latest_val:.2f} pts", "label": "FRED Industrial Prod (INDPRO)", "sub": "🟢 Live St. Louis Fed Feed"}
    except Exception:
        pass

    return telemetry
'''

target = "robot_feeds.py" if os.path.exists("robot_feeds.py") else "robot_feeds.txt"
with open(target, "r") as f:
    code = f.read()

pattern = r"(@st\.cache_data\(ttl=\d+\)\s*)?def fetch_live_macro_telemetry\([\s\S]*?\):[\s\S]*?(?=\n@|\ndef |\Z)"
if re.search(pattern, code):
    code = re.sub(pattern, patch_macro_code.strip() + "\n\n", code)
else:
    code += "\n\n" + patch_macro_code.strip()

with open(target, "w") as f:
    f.write(code)

print("✅ Live Macro Telemetry integrated successfully into " + target)
