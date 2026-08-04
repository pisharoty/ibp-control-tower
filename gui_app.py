import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Initialize Session State Variables
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "custom_scenarios" not in st.session_state:
    st.session_state["custom_scenarios"] = {}
if "ledger_data" not in st.session_state:
    st.session_state["ledger_data"] = {
        "trades": [],
        "trade_count": 0,
        "total_hedging_revenue": 0.0,
        "total_cogs_savings": 0.0
    }

st.set_page_config(page_title="IBP Control Tower", layout="wide")

# Sidebar Navigation
st.sidebar.title("⚡ IBP Control Tower")
selected_module = st.sidebar.radio(
    "Select Module",
    [
        "📊 Executive S&OP Dashboard",
        "🧠 NLP Commercial Sensing",
        "⚖️ D/S Match & Net Margin Solver",
        "📈 Procurement & Trading Desk",
        "🌐 Global Network & Logistics Map"
    ],
    key="nav_module_selection_v5"
)

# Store active module in session state
st.session_state["selected_module"] = selected_module

# Imports for CTRM Extension
try:
    from ctrm_engine import CTRMExtensionEngine, DSSolverOutput, RiskEventType
    CTRM_AVAILABLE = True
except ImportError:
    CTRM_AVAILABLE = False

# =====================================================================
# MODULE 1: EXECUTIVE S&OP DASHBOARD
# =====================================================================
if "Executive S&OP" in selected_module:
    st.title("📊 Executive S&OP Control Tower")
    st.markdown("Real-time financial alignment, demand-supply balance, and operational KPIs.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2%")
    col2.metric("Unconstrained Demand", "$135.5M", "+12.8%")
    col3.metric("Constrained Supply Plan", "$118.2M", "-1.5%")
    col4.metric("Net Margin Gap", "$17.3M", "-2.1%", delta_color="inverse")
    
    st.subheader("📈 S&OP Financial Alignment Gap")
    df_sop = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "AOP Target": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        "Unconstrained Demand": [10.5, 11, 11.2, 11.8, 12, 12.5, 11.9, 11.5, 11.2, 11, 10.8, 10.1],
        "Constrained Supply": [9.8, 9.9, 10.0, 10.1, 9.7, 9.8, 9.9, 10.0, 9.8, 9.9, 9.7, 9.6]
    })
    fig_sop = px.line(df_sop, x="Month", y=["AOP Target", "Unconstrained Demand", "Constrained Supply"],
                      title="12-Month S&OP Demand vs. Supply vs. AOP ($M)")
    st.plotly_chart(fig_sop, use_container_width=True)

# =====================================================================
# MODULE 2: NLP COMMERCIAL SENSING
# =====================================================================
elif "NLP Commercial" in selected_module:
    st.title("🧠 NLP Commercial Sensing & Demand Signals")
    st.markdown("Unstructured market intelligence, social sentiment, and news feed ingestion.")
    
    st.subheader("📡 Live Signals & Sentiment Ingestion")
    signals = pd.DataFrame({
        "Source": ["Twitter / X", "Bloomberg News", "Custom Tariff Regulatory Feed", "Supplier Portal"],
        "Signal Detected": ["Port Congestion Warning", "Red Sea Shipping Surcharge", "Rare Earth Export Restriction", "Semiconductor Lead Time Spike"],
        "Sentiment Score": [-0.85, -0.62, -0.91, -0.45],
        "Confidence": ["94%", "88%", "97%", "82%"]
    })
    st.dataframe(signals, use_container_width=True)
    
    st.subheader("🎯 Real-Time Demand Shock Extractor")
    demand_surge = st.slider("Extracted Surge Volume (Units)", 10000, 200000, 50000, step=5000, key="nlp_demand_surge_slider")
    st.session_state["extracted_demand_surge"] = demand_surge
    st.success(f"Extracted Demand Surge of {demand_surge:,} units propagated to D/S Matcher!")

# =====================================================================
# MODULE 3: D/S MATCH & NET MARGIN SOLVER
# =====================================================================
elif "D/S Match" in selected_module:
    st.title("⚖️ Demand/Supply Match & Net Margin Solver")
    st.markdown("Linear programming optimization for global allocation and profit maximization.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Solver Inputs")
        st.number_input("Base Selling Price ($/unit)", value=250.0, key="ds_base_price")
        st.number_input("Flex Capacity Cost ($/unit)", value=45.0, key="ds_flex_cost")
        st.number_input("Unmet Penalty Cost ($/unit)", value=80.0, key="ds_penalty_cost")
        
    with col2:
        st.subheader("📊 Optimal Allocation Summary")
        st.write("**Primary Network Capacity**: 450,000 units")
        st.write("**Flex Network Allocation**: 50,000 units")
        st.write("**Maximized Gross Profit**: $18.45M")

# =====================================================================
# MODULE 4: PROCUREMENT & TRADING DESK
# =====================================================================
elif "Procurement" in selected_module:
    st.title("📈 Procurement & Physical Commodity Trading Desk")
    st.markdown("Physical contract management, supplier allocation, and exchange exposure.")
    
    st.subheader("💼 Active Procurement Contracts")
    contracts = pd.DataFrame({
        "Contract ID": ["CTR-2026-A1", "CTR-2026-B4", "CTR-2026-C9"],
        "Commodity": ["Primary Aluminum", "Freight Futures (FBX)", "Semiconductor Wafers"],
        "Supplier": ["Rio Tinto", "Maersk Line", "TSMC"],
        "Volume": ["15,000 MT", "2,500 FEU", "100,000 Wafers"],
        "Fixed Price": ["$2,200 / MT", "$1,450 / FEU", "$450 / Wafer"],
        "Status": ["Active", "Under Review", "Executing"]
    })
    st.dataframe(contracts, use_container_width=True)

# =====================================================================
# MODULE 5: GLOBAL NETWORK & LOGISTICS MAP
# =====================================================================
elif "Global Network" in selected_module:
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.markdown("Real-time geospatial tracking of maritime routes, distribution nodes, and disruption zones.")
    
    # Map Visualization
    nodes = pd.DataFrame({
        "Name": ["Port of Shanghai", "Port of Rotterdam", "Port of LA", "Suez Canal Bottleneck", "Panama Canal Node"],
        "lat": [31.2304, 51.9244, 33.7405, 30.5852, 9.0800],
        "lon": [121.4737, 4.4777, -118.2713, 32.3132, -79.6800],
        "Status": ["Operational", "Congested", "Operational", "High Risk", "Moderate Risk"],
        "Throughput (%)": [98, 62, 91, 35, 55]
    })
    
    fig_map = px.scatter_mapbox(
        nodes,
        lat="lat",
        lon="lon",
        hover_name="Name",
        hover_data=["Status", "Throughput (%)"],
        color="Status",
        size="Throughput (%)",
        color_discrete_map={"Operational": "green", "Congested": "orange", "High Risk": "red", "Moderate Risk": "yellow"},
        zoom=1,
        height=500
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.title("IBP Control Tower")
    st.info("Select a module from the sidebar navigation to view dashboard details.")

# =====================================================================
# CTRM RISK SCENARIO INJECTOR & HEDGING ENGINE (SIDEBAR + MAIN)
# =====================================================================
if CTRM_AVAILABLE:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌋 Risk Scenario Injector")
    st.sidebar.caption("⚡ Auto-Ingest Telemetry Alerts:")

    col_nlp1, col_nlp2 = st.sidebar.columns(2)
    if col_nlp1.button("🌋 Iceland Ash", use_container_width=True, key="ctrm_ash_v5"):
        st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
        st.toast("⚡ Ingested: Eyjafjallajökull Volcanic Ash Cloud Alert!", icon="🌋")

    if col_nlp2.button("🌊 El Niño AIS", use_container_width=True, key="ctrm_elnino_v5"):
        st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
        st.toast("⚡ Ingested: Sea surface anomaly confirmed in Pacific!", icon="🌊")

    if st.sidebar.button("💥 Seismic Earthquake Feed", use_container_width=True, key="ctrm_seismic_v5"):
        st.session_state["active_disruption"] = "Seismic Earthquake Shock (Port Facilities Damage)"
        st.toast("⚡ Ingested: Port Infrastructure Impaired!", icon="💥")

    with st.sidebar.expander("🎨 Custom Disruption Model Builder (CME/ICE)"):
        with st.form("custom_disruption_form_v5"):
            c_name = st.text_input("Disruption Title", "Panama Canal Drought Bottleneck", key="ctrm_title_v5")
            c_comm = st.selectbox("Target Commodity (CME/ICE)", [
                "CME Freight Futures (FBX)",
                "ICE Arabica Coffee (KC)",
                "NYMEX WTI Crude Oil (CL)",
                "CBOT Corn Futures (ZC)",
                "LME Primary Copper (HG)",
                "Custom Ticker / Asset"
            ], key="ctrm_comm_v5")
            if c_comm == "Custom Ticker / Asset":
                c_comm = st.text_input("Custom Asset Ticker", "CME Random Length Lumber", key="ctrm_cust_v5")
                
            c_type_str = st.selectbox("Pricing Engine Routing", [
                "Volcanic / Air Corridor Shock (Hawkes Jump)",
                "Climate / Weather Anomaly (Hawkes Jump)",
                "Seismic / Facility Loss (Parametric CAT)",
                "Standard / Geopolitical Volatility (Black-76)"
            ], key="ctrm_routing_v5")
            
            col_p1, col_p2 = st.columns(2)
            c_base = col_p1.number_input("Base Price ($)", value=120.0, key="ctrm_pbase_v5")
            c_spot = col_p2.number_input("Spot Price ($)", value=195.0, key="ctrm_pspot_v5")
            c_vol = st.slider("Implied Volatility (σ)", 0.05, 1.50, 0.45, 0.05, key="ctrm_pvol_v5")
            c_thru = st.slider("Throughput Ratio (θ)", 0.05, 1.00, 0.30, 0.05, key="ctrm_pthru_v5")
            
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
        key="ctrm_shock_select_v5"
    )

    if st.sidebar.button("🚨 Inject Selected Shock to CTRM Desk", type="primary", use_container_width=True, key="ctrm_inject_v5"):
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

    # CTRM Desk is displayed on active trading & margin modules
    if any(m in selected_module for m in ["D/S Match", "Procurement"]):
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

        if st.button("⚡ Approve & Execute CTRM Option Trade", type="primary", key="ctrm_exec_trade_v5"):
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
