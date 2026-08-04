import streamlit as st
import pandas as pd
import numpy as np
import math
import re
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="IBP Control Tower", layout="wide", page_icon="⚡")

# --- Session State Initialization ---
if 'extracted_demand_surge' not in st.session_state:
    st.session_state['extracted_demand_surge'] = 50000
if 'unconstrained_demand' not in st.session_state:
    st.session_state['unconstrained_demand'] = 150000
if 'active_signal_name' not in st.session_state:
    st.session_state['active_signal_name'] = "Costco Demand Signal (+50,000 units)"
if 'ledger_data' not in st.session_state:
    st.session_state['ledger_data'] = {
        "trades": [],
        "total_hedging_revenue": 0.0,
        "total_cogs_savings": 0.0,
        "trade_count": 0
    }

# Sidebar Navigation
st.sidebar.title("⚡ IBP Control Tower")
module = st.sidebar.radio(
    "Select Module",
    [
        "📊 Executive S&OP Dashboard",
        "💬 NLP Commercial Sensing",
        "⚖️ D/S Match & Net Margin Solver",
        "🏭 Procurement & Trading Desk",
        "🌐 Global Network & Logistics Map"
    ]
)

# Helper function to check if overflow was outsourced
def get_outsourced_info():
    trades = st.session_state['ledger_data'].get('trades', [])
    outsourced_vol = 0
    outsourced_cost_weighted = 0.0
    for t in trades:
        if t.get('category') == 'Physical Make/Buy':
            vol = t.get('volume', 0)
            outsourced_vol += vol
            outsourced_cost_weighted += t.get('strike', 12.01) * vol
    if outsourced_vol > 0:
        avg_cost = outsourced_cost_weighted / outsourced_vol
        return outsourced_vol, avg_cost
    return 0, 0.0


# >>> UNIQUE_CTRM_RISK_ENGINE_DESK_DEPLOYED <<<
from ctrm_engine import CTRMExtensionEngine, DSSolverOutput, RiskEventType

# Initialize Session State
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "custom_scenarios" not in st.session_state:
    st.session_state["custom_scenarios"] = {}

# Sidebar Risk Scenario Injector
st.sidebar.markdown("---")
st.sidebar.subheader("🌋 Risk Scenario Injector")
st.sidebar.caption("⚡ Auto-Ingest Telemetry Alerts:")

col_nlp1, col_nlp2 = st.sidebar.columns(2)
if col_nlp1.button("🌋 Iceland Ash", use_container_width=True, key="ctrm_ash_btn"):
    st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
    st.toast("⚡ Ingested: Eyjafjallajökull Volcanic Ash Cloud Alert!", icon="🌋")

if col_nlp2.button("🌊 El Niño AIS", use_container_width=True, key="ctrm_elnino_btn"):
    st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
    st.toast("⚡ Ingested: Sea surface anomaly confirmed in Pacific!", icon="🌊")

if st.sidebar.button("💥 Seismic Earthquake Feed", use_container_width=True, key="ctrm_seismic_btn"):
    st.session_state["active_disruption"] = "Seismic Earthquake Shock (Port Facilities Damage)"
    st.toast("⚡ Ingested: Port Infrastructure Impaired!", icon="💥")

with st.sidebar.expander("🎨 Custom Disruption Model Builder (CME/ICE)"):
    with st.form("custom_disruption_form_prod"):
        c_name = st.text_input("Disruption Title", "Panama Canal Drought Bottleneck", key="ctrm_title")
        c_comm = st.selectbox("Target Commodity (CME/ICE)", [
            "CME Freight Futures (FBX)",
            "ICE Arabica Coffee (KC)",
            "NYMEX WTI Crude Oil (CL)",
            "CBOT Corn Futures (ZC)",
            "LME Primary Copper (HG)",
            "Custom Ticker / Asset"
        ], key="ctrm_target_comm")
        if c_comm == "Custom Ticker / Asset":
            c_comm = st.text_input("Custom Asset Ticker", "CME Random Length Lumber", key="ctrm_cust_ticker")
            
        c_type_str = st.selectbox("Pricing Engine Routing", [
            "Volcanic / Air Corridor Shock (Hawkes Jump)",
            "Climate / Weather Anomaly (Hawkes Jump)",
            "Seismic / Facility Loss (Parametric CAT)",
            "Standard / Geopolitical Volatility (Black-76)"
        ], key="ctrm_routing")
        
        col_p1, col_p2 = st.columns(2)
        c_base = col_p1.number_input("Base Price ($)", value=120.0, key="ctrm_pbase")
        c_spot = col_p2.number_input("Spot Price ($)", value=195.0, key="ctrm_pspot")
        c_vol = st.slider("Implied Volatility (σ)", 0.05, 1.50, 0.45, 0.05, key="ctrm_pvol")
        c_thru = st.slider("Throughput Ratio (θ)", 0.05, 1.00, 0.30, 0.05, key="ctrm_pthru")
        
        submit_custom = st.form_submit_button("🚀 Inject Custom Scenario", type="primary")
        if submit_custom:
            type_map = {
                "Volcanic / Air Corridor Shock (Hawkes Jump)": RiskEventType.VOLCANIC_ASH_DISRUPTION,
                "Climate / Weather Anomaly (Hawkes Jump)": RiskEventType.CLIMATE_SHOCK_EL_NINO,
                "Seismic / Facility Loss (Parametric CAT)": RiskEventType.SEISMIC_EARTHQUAKE_SHOCK,
                "Standard / Geopolitical Volatility (Black-76)": RiskEventType.STANDARD_VOLATILITY
            }
            st.session_state["custom_scenarios"][c_name] = {
                "commodity": c_comm,
                "event_type": type_map[c_type_str],
                "baseline_price": float(c_base),
                "spot_price": float(c_spot),
                "volatility": float(c_vol),
                "throughput": float(c_thru)
            }
            st.session_state["active_disruption"] = c_name
            st.toast(f"Custom Scenario Injected: {c_name}!", icon="🎯")

COMMODITY_SHOCK_MATRIX = {
    "El Niño Climate Shock (Pacific Ocean Warm Current)": {
        "commodity": "ICE Arabica Coffee & Softs",
        "event_type": RiskEventType.CLIMATE_SHOCK_EL_NINO,
        "baseline_price": 22.50,
        "spot_price": 28.40,
        "volatility": 0.32,
        "throughput": 0.70
    },
    "Icelandic Volcanic Ash (North Atlantic Freight Corridor)": {
        "commodity": "CME Freight Futures (FBX Air/Sea)",
        "event_type": RiskEventType.VOLCANIC_ASH_DISRUPTION,
        "baseline_price": 85.00,
        "spot_price": 135.00,
        "volatility": 0.55,
        "throughput": 0.40
    },
    "Seismic Earthquake Shock (Port Facilities Damage)": {
        "commodity": "Semiconductor Wafers & Rare Metals",
        "event_type": RiskEventType.SEISMIC_EARTHQUAKE_SHOCK,
        "baseline_price": 450.00,
        "spot_price": 720.00,
        "volatility": 0.65,
        "throughput": 0.20
    },
    "Standard Market Price Volatility": {
        "commodity": "LME Primary Aluminum",
        "event_type": RiskEventType.STANDARD_VOLATILITY,
        "baseline_price": 2200.00,
        "spot_price": 2350.00,
        "volatility": 0.18,
        "throughput": 1.00
    }
}
COMMODITY_SHOCK_MATRIX.update(st.session_state["custom_scenarios"])

disruption_options = list(COMMODITY_SHOCK_MATRIX.keys())
current_selection = st.session_state.get("active_disruption", "Standard Market Price Volatility")
default_idx = disruption_options.index(current_selection) if current_selection in disruption_options else 0

selected_event_label = st.sidebar.selectbox(
    "Select Physical Supply Chain Shock:",
    options=disruption_options,
    index=default_idx,
    key="ctrm_shock_select"
)

if st.sidebar.button("🚨 Inject Selected Shock to CTRM Desk", type="primary", use_container_width=True, key="ctrm_inject_btn"):
    st.session_state["active_disruption"] = selected_event_label
    st.sidebar.success(f"Injected: {selected_event_label}")

active_label = st.session_state["active_disruption"]
st.sidebar.info(f"📡 **Active Signal Ingested:** {active_label}")

shock_data = COMMODITY_SHOCK_MATRIX.get(active_label, COMMODITY_SHOCK_MATRIX["Standard Market Price Volatility"])

ds_run = DSSolverOutput(
    scenario_name=active_label,
    commodity_name=shock_data["commodity"],
    incremental_gross_profit=7137631.0,
    flex_capacity_cost=930194.0,
    volume_shortfall_units=float(st.session_state.get("extracted_demand_surge", 50000)),
    baseline_price=shock_data["baseline_price"],
    spot_price=shock_data["spot_price"],
    implied_volatility=shock_data["volatility"],
    risk_event_type=shock_data["event_type"],
    network_throughput_ratio=shock_data["throughput"]
)

# Detect current navigation module
nav_mod = locals().get("selected_module", globals().get("selected_module", st.session_state.get("selected_module", None)))

# Render CTRM Desk ONLY on active trading/margin modules
if nav_mod in ["D/S Match & Net Margin Solver", "Procurement & Trading Desk"]:
    st.markdown("---")
    st.header("🛡️ CTRM Event-Driven Hedging & Arbitrage Desk")
    st.caption(f"Active Commodity Exposure: **{shock_data['commodity']}**")

    ctrm_bridge = CTRMExtensionEngine()
    arbitrage_info = ctrm_bridge.detect_arbitrage_risk(ds_run)
    staged_ticket = ctrm_bridge.select_model_and_structure_hedge(ds_run)

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Unhedged Margin Risk", f"${arbitrage_info['unhedged_margin_risk_usd']:,.2f}")
    col_b.metric("Pricing Model", staged_ticket.selected_model.value.replace("_", " "))
    col_c.metric("Notional Volume", f"{staged_ticket.notional_volume:,.0f} units")
    col_d.metric("Option Premium", f"${staged_ticket.estimated_premium:,.2f}")

    st.info(f"💡 **Recommendation**: Activate **{staged_ticket.selected_model.value}** to cap price volatility at **${staged_ticket.strike_price:.2f}/unit**.")

    if st.button("⚡ Approve & Execute CTRM Option Trade", type="primary", key="ctrm_exec_trade"):
        approved_ticket = ctrm_bridge.approve_hedge_order(staged_ticket)
        results = ctrm_bridge.execute_and_close_loop(ds_run, approved_ticket, market_price_at_expiry=shock_data["spot_price"] * 1.1)
        
        if "ledger_data" in st.session_state:
            st.session_state["ledger_data"]["trades"].append(results)
            st.session_state["ledger_data"]["trade_count"] += 1
            st.session_state["ledger_data"]["total_hedging_revenue"] += results["financial_waterfall"]["hedge_payout_received_usd"]
            st.session_state["ledger_data"]["total_cogs_savings"] += (
                results["financial_waterfall"]["hedge_payout_received_usd"] - results["financial_waterfall"]["hedge_premium_paid_usd"]
            )
        
        st.balloons()
        st.success(f"Trade **{approved_ticket.order_id}** EXECUTED on Exchange for **{shock_data['commodity']}**!")
        st.subheader("📊 Closed-Loop Financial Waterfall")
        st.json(results["financial_waterfall"])
