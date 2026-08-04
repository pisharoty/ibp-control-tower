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

# =====================================================================
# MODULE ROUTING & NAVIGATION CONTROLLER
# =====================================================================
# Check active selected module from sidebar radio
if 'selected_module' in locals() or 'selected_module' in globals():
    active_nav = selected_module
else:
    active_nav = st.session_state.get('selected_module', "D/S Match & Net Margin Solver")

# Render CTRM Desk on D/S Solver and Procurement & Trading Desk modules
if active_nav in ["D/S Match & Net Margin Solver", "Procurement & Trading Desk"]:
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

    if st.button("⚡ Approve & Execute CTRM Option Trade", type="primary"):
        approved_ticket = ctrm_bridge.approve_hedge_order(staged_ticket)
        results = ctrm_bridge.execute_and_close_loop(ds_run, approved_ticket, market_price_at_expiry=shock_data["spot_price"] * 1.1)
        
        if 'ledger_data' in st.session_state:
            st.session_state['ledger_data']['trades'].append(results)
            st.session_state['ledger_data']['trade_count'] += 1
            st.session_state['ledger_data']['total_hedging_revenue'] += results['financial_waterfall']['hedge_payout_received_usd']
            st.session_state['ledger_data']['total_cogs_savings'] += (
                results['financial_waterfall']['hedge_payout_received_usd'] - results['financial_waterfall']['hedge_premium_paid_usd']
            )
        
        st.balloons()
        st.success(f"Trade **{approved_ticket.order_id}** EXECUTED on Exchange for **{shock_data['commodity']}**!")
        st.subheader("📊 Closed-Loop Financial Waterfall")
        st.json(results["financial_waterfall"])
