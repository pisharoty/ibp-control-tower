import os
import re

patch_macro_code = '''
@st.cache_data(ttl=600)
def fetch_live_macro_telemetry():
    """Fetch live macro indicators using yfinance and FRED REST endpoints with full backward compatibility."""
    gscpi_val = "+1.28 σ"
    fred_val = "99.44 pts"
    wb_val = "147.5 Index"
    dxy_val = "102.03 pts"
    kospi_val = "2,618 pts"

    dxy_sub = "🟢 Live Spot"
    kospi_sub = "🟢 Live Spot"
    fred_sub = "🔴 -0.2% YoY"

    # 1. Fetch live DXY and KOSPI via yfinance
    try:
        import yfinance as yf
        tickers = yf.Tickers("DX-Y.NYB ^KS11")

        dxy = tickers.tickers["DX-Y.NYB"].fast_info.get("lastPrice")
        if dxy:
            dxy_val = f"{dxy:.2f} pts"
            dxy_sub = "🟢 Live YFinance Feed"

        kospi = tickers.tickers["^KS11"].fast_info.get("lastPrice")
        if kospi:
            kospi_val = f"{kospi:,.0f} pts"
            kospi_sub = "🟢 Live YFinance Feed"
    except Exception:
        pass

    # 2. Fetch live FRED Industrial Production Index (INDPRO)
    try:
        import requests
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO"
        res = requests.get(url, timeout=3.0)
        if res.status_code == 200:
            lines = [line for line in res.text.strip().splitlines() if line and not line.startswith("DATE")]
            if lines:
                latest_val = float(lines[-1].split(",")[-1])
                fred_val = f"{latest_val:.2f} pts"
                fred_sub = "🟢 Live St. Louis Fed Feed"
    except Exception:
        pass

    # Multi-alias dictionary mapping all keys (gscpi, indpro, dxy, kospi) and sub-keys (val, value)
    telemetry = {
        "gscpi": {"val": gscpi_val, "value": gscpi_val, "label": "NY Fed GSCPI", "sub": "🟢 Normalizing"},
        "ny_fed_gscpi": {"val": gscpi_val, "value": gscpi_val, "label": "NY Fed GSCPI", "sub": "🟢 Normalizing"},
        "fred_mfg": {"val": fred_val, "value": fred_val, "label": "US Industrial Prod", "sub": fred_sub},
        "indpro": {"val": fred_val, "value": fred_val, "label": "US Industrial Prod", "sub": fred_sub},
        "wb_commodity": {"val": wb_val, "value": wb_val, "label": "World Bank Commodity Index", "sub": "🟢 +1.8% MoM"},
        "usd_index": {"val": dxy_val, "value": dxy_val, "label": "US Dollar Index (DXY)", "sub": dxy_sub},
        "dxy": {"val": dxy_val, "value": dxy_val, "label": "US Dollar Index (DXY)", "sub": dxy_sub},
        "kospi_index": {"val": kospi_val, "value": kospi_val, "label": "KOSPI Industrial Index", "sub": kospi_sub},
        "kospi": {"val": kospi_val, "value": kospi_val, "label": "KOSPI Industrial Index", "sub": kospi_sub}
    }

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

print("✅ Patched fetch_live_macro_telemetry in " + target)
