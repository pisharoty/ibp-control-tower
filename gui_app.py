# global_init_marker_v1
ledger_data = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}


# =======================================================
# CTRM GLOBAL STATE & HYBRID SOLVER ENGINE
# =======================================================
import math
import streamlit as st
import requests

def local_norm_cdf(x: float) -> float:
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def local_norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

def run_black76_local(F, K, T, r, sigma, volume, opt_type, comm_sym):
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return {"premium_per_unit": 0.0, "total_premium_income": 0.0, "greeks": {"delta": 0.0, "vega_1pct_vol": 0.0}, "strategy": "N/A", "trading_desk_recommendation": "Invalid parameters"}

    d1 = (math.log(F / K) + (0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    discount = math.exp(-r * T)

    if opt_type.lower() == "call":
        price = discount * (F * local_norm_cdf(d1) - K * local_norm_cdf(d2))
        delta = discount * local_norm_cdf(d1)
        strategy = "Upside Price Protection / Call Overlay"
        rec = f"Call Option on {comm_sym}: Locks maximum purchasing price ceiling at ${K:,.2f}."
    else:
        price = discount * (K * local_norm_cdf(-d2) - F * local_norm_cdf(-d1))
        delta = -discount * local_norm_cdf(-d1)
        strategy = "Inventory Floor Protection / Put Hedge"
        rec = f"Put Option on {comm_sym}: Provides downside price floor at ${K:,.2f} for physical volume."

    vega = discount * F * local_norm_pdf(d1) * math.sqrt(T) * 0.01

    return {
        "status": "SUCCESS",
        "premium_per_unit": round(price, 4),
        "total_premium_income": round(price * volume, 2),
        "greeks": {
            "delta": round(delta, 4),
            "vega_1pct_vol": round(vega * volume, 2)
        },
        "strategy": strategy,
        "trading_desk_recommendation": rec
    }

if 'ledger_data' not in st.session_state:
    st.session_state['ledger_data'] = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}

ledger_data = st.session_state['ledger_data']

try:
    ledger_res = requests.get(f"{BACKEND_URL}/api/v1/ibp/trading/ledger", timeout=3)
    if ledger_res.status_code == 200:
        fetched = ledger_res.json()
        if isinstance(fetched, dict):
            st.session_state['ledger_data'] = fetched
            ledger_data = fetched
except Exception:
    pass

st.markdown("---")
st.subheader("⚡ CTRM Commodity & Derivatives Trading Engine (Black-76)")
st.caption("Monetize physical inventory, hedge agricultural/energy inputs, and price supply flexibility as real options.")

trade_cnt = ledger_data.get("trade_count", 0)
if trade_cnt > 0:
    hedging_rev = ledger_data.get("total_hedging_revenue", 0.0)
    cogs_sav = ledger_data.get("total_cogs_savings", 0.0)
    st.success(f"📈 **Corporate P&L Ledger Active**: **${hedging_rev:,.2f}** in option yield + **${cogs_sav:,.2f}** in COGS risk protection across **{trade_cnt}** persistent trade(s).")

col_cat, col_sym = st.columns(2)
with col_cat:
    comm_cat = st.selectbox("Commodity Sector", [
        "Agriculture & Livestock", 
        "Energy", 
        "Rare Earths & Battery Metals", 
        "Industrial Metals"
    ], key="ctrm_cat")
with col_sym:
    if comm_cat == "Agriculture & Livestock":
        comm_sym = st.selectbox("Asset", ["CME Lean Hogs (lbs)", "CME Corn (Bushels)", "CME Live Cattle (lbs)", "Soybean Meal (Tons)"], key="ctrm_asset_a")
        default_f, default_vol = 88.50, 0.28
    elif comm_cat == "Energy":
        comm_sym = st.selectbox("Asset", ["WTI Crude Oil (bbl)", "Henry Hub Natural Gas (MMBtu)", "Electricity (MWh)"], key="ctrm_asset_e")
        default_f, default_vol = 78.50, 0.38
    elif comm_cat == "Rare Earths & Battery Metals":
        comm_sym = st.selectbox("Asset", ["Neodymium NdFeB (kg)", "Lithium Carbonate (MT)", "Dysprosium Oxide (kg)"], key="ctrm_asset_r")
        default_f, default_vol = 145.00, 0.45
    else:
        comm_sym = st.selectbox("Asset", ["LME Copper (MT)", "LME Aluminum (MT)", "Nickel (MT)"], key="ctrm_asset_m")
        default_f, default_vol = 9200.00, 0.22

col_inputs1, col_inputs2 = st.columns(2)
with col_inputs1:
    f_price = st.slider("Forward / Futures Price ($/unit)", min_value=1.0, max_value=15000.0, value=float(default_f), step=1.0, key="ctrm_f")
    k_price = st.slider("Strike Price ($/unit)", min_value=1.0, max_value=15000.0, value=float(default_f * 1.05), step=1.0, key="ctrm_k")
    opt_type = st.radio("Option Type", ["call", "put"], horizontal=True, key="ctrm_type")

with col_inputs2:
    exp_months = st.slider("Contract Expiration (Months)", min_value=1, max_value=24, value=6, key="ctrm_exp")
    imp_vol = st.slider("Implied Volatility (σ)", min_value=0.05, max_value=1.00, value=float(default_vol), step=0.01, key="ctrm_vol")
    contract_qty = st.number_input("Contract Volume (Units)", value=10000, step=1000, key="ctrm_qty")

if st.button("Run Black-76 Option Valuation & Arbitrage Solver", key="ctrm_btn"):
    payload = {
        "commodity_category": comm_cat,
        "commodity_symbol": comm_sym,
        "forward_price": f_price,
        "strike_price": k_price,
        "time_to_expiration": exp_months / 12.0,
        "risk_free_rate": 0.045,
        "implied_volatility": imp_vol,
        "contract_volume": int(contract_qty),
        "option_type": opt_type
    }
    
    # Try Backend API first; fallback to embedded local calculation if 404 or network issue
    calculated = False
    try:
        res = requests.post(f"{BACKEND_URL}/api/v1/ibp/trading/black-scholes", json=payload, timeout=5)
        if res.status_code == 200:
            st.session_state['last_ctrm_res'] = res.json()
            calculated = True
    except Exception:
        pass

    if not calculated:
        # Client-side instantaneous fallback calculation
        st.session_state['last_ctrm_res'] = run_black76_local(
            F=f_price,
            K=k_price,
            T=exp_months / 12.0,
            r=0.045,
            sigma=imp_vol,
            volume=int(contract_qty),
            opt_type=opt_type,
            comm_sym=comm_sym
        )

if 'last_ctrm_res' in st.session_state and st.session_state['last_ctrm_res']:
    data = st.session_state['last_ctrm_res']
    st.success(f"Strategy: {data.get('strategy', 'N/A')}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Option Premium / Unit", f"${data.get('premium_per_unit', 0.0)}")
    m2.metric("Total Premium Revenue", f"${data.get('total_premium_income', 0.0):,.2f}")
    m3.metric("Delta (Δ)", data.get('greeks', {}).get('delta', 0.0))
    m4.metric("1% Vol Vega Impact", f"${data.get('greeks', {}).get('vega_1pct_vol', 0.0):,.2f}")
    
    st.info(f"**Trading Desk Action Plan:** {data.get('trading_desk_recommendation', 'N/A')}")

    st.markdown("##### 💼 Corporate Financial Ledger Sync")
    if st.button("💰 Commit Trade Yield to Corporate P&L Ledger", key="commit_pnl_btn"):
        commit_payload = {
            "commodity_symbol": comm_sym,
            "commodity_category": comm_cat,
            "option_type": opt_type,
            "contract_volume": int(contract_qty),
            "premium_per_unit": float(data.get('premium_per_unit', 0.0)),
            "total_premium_income": float(data.get('total_premium_income', 0.0)),
            "strike_price": float(k_price),
            "forward_price": float(f_price),
            "strategy": data.get('strategy', 'N/A')
        }
        try:
            commit_res = requests.post(f"{BACKEND_URL}/api/v1/ibp/trading/commit", json=commit_payload, timeout=5)
            if commit_res.status_code == 200:
                st.balloons()
                st.success("✅ Trade committed to persistent backend ledger!")
                st.rerun()
            else:
                # Local state update fallback if backend commit endpoint is unreachable
                cogs_sav = (f_price - k_price) * contract_qty if opt_type == "call" and f_price > k_price else 0.0
                new_trade = {
                    "id": f"TRD-{len(ledger_data['trades']) + 1001}",
                    "symbol": comm_sym,
                    "category": comm_cat,
                    "option_type": opt_type.upper(),
                    "volume": int(contract_qty),
                    "premium_income": float(data.get('total_premium_income', 0.0)),
                    "cogs_savings": round(cogs_sav, 2),
                    "strike": k_price,
                    "forward": f_price,
                    "strategy": data.get('strategy', 'N/A')
                }
                st.session_state['ledger_data']['trades'].append(new_trade)
                st.session_state['ledger_data']['total_hedging_revenue'] += float(data.get('total_premium_income', 0.0))
                st.session_state['ledger_data']['total_cogs_savings'] += cogs_sav
                st.session_state['ledger_data']['trade_count'] += 1
                st.balloons()
                st.success("✅ Trade committed to session P&L ledger!")
                st.rerun()
        except Exception:
            pass

trades_list = ledger_data.get('trades', [])
if isinstance(trades_list, list) and len(trades_list) > 0:
    st.markdown("---")
    st.subheader("📋 Active Corporate Trade & Derivatives Book")
    st.dataframe(trades_list, use_container_width=True)
