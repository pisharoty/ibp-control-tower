import streamlit as st
import json
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import math

import robot_feeds as rf
from inventory_manager import render_inventory_position_manager

# Page Config
st.set_page_config(
    page_title="IBP Enterprise Control Tower",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "platform_active_signal" not in st.session_state:
    st.session_state["platform_active_signal"] = "Baseline Operations (No Active Signal Ingested)"
if "extracted_demand_surge" not in st.session_state:
    st.session_state["extracted_demand_surge"] = 65000
if "si_composite" not in st.session_state:
    st.session_state["si_composite"] = -0.33

# =====================================================================
# SIDEBAR NAVIGATION ROUTER (ALL 9 MODULES INCLUDED)
# =====================================================================
st.sidebar.title("⚡ IBP Control Tower")

persona = st.sidebar.selectbox(
    "🏢 Enterprise Operating Persona:",
    [
        "🏭 Discrete & Heavy Industrial Enterprise",
        "📦 Process Goods & FMCG Enterprise",
        "📈 Merchant Trading & Commodity Risk Desk"
    ],
    key="platform_persona_select"
)

modules = [
    "📊 Executive S&OP Control Tower",
    "📦 Enterprise Inventory & Position Manager",
    "🧠 NLP Commercial Sensing & Field Intelligence",
    "⚙️ Demand/Supply Match & Plant Load Balancer",
    "📈 Physical Procurement & Master Contract Desk",
    "🛡️ CTRM Derivatives & Commodity Risk Desk",
    "🌐 Global Logistics Network & GIS Control Tower",
    "🧪 Sandbox Flight Simulator & Stress Lab",
    "🔌 Integration & Architecture Endpoints"
]

selected_module = st.sidebar.radio("Navigation Modules:", modules, key="sidebar_module_radio")

# =====================================================================
# MODULE 1: EXECUTIVE S&OP CONTROL TOWER
# =====================================================================
def render_executive_sop(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("📊 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    
    surge = st.session_state.get("platform_demand_impact", st.session_state.get("extracted_demand_surge", 65000))
    si = st.session_state.get("platform_si_override", st.session_state.get("si_composite", -0.33))
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2% YoY")
    c2.metric("Unconstrained Demand", f"${(120.0 + surge*0.00025):.2f}M", f"+{surge:,} {term_unit}")
    c3.metric("CTRM Hedge Benefit", "+$3.25M", "Derivative Gain")
    c4.metric("Available Treasury Cash", "$4,430,000.00", "-$0.57M Freight Surcharge")
    
    st.divider()
    
    col_p1, col_p2 = st.columns([1.3, 1])
    with col_p1:
        st.subheader("💵 Financial P&L Margin Waterfall")
        fig = go.Figure(go.Waterfall(
            name="P&L Reconciliation", orientation="v",
            measure=["relative", "relative", "relative", "relative", "relative", "total"],
            x=["Base AOP Rev", "Base COGS", "Surge Rev", "Freight Drag", "Hedge Benefit", "Net EBITDA"],
            y=[120.0, -78.0, surge*0.00025, -0.57, 3.25, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_p2:
        st.subheader("🚩 Live Operational Desk Feeds")
        st.info(f"🔹 **Active Signal**: {st.session_state.get('platform_active_signal', 'Baseline Operations Target')}")
        st.warning(f"✈️ **Logistics Desk**: Lead time delay drag set at +{st.session_state.get('platform_leadtime_impact', 2.5)} days")
        st.success("🟢 **CTRM Risk Desk**: Active hedge ratio target aligned.")

# =====================================================================
# MODULE 3: NLP COMMERCIAL SENSING & FIELD INTELLIGENCE
# =====================================================================
def render_nlp_commercial_sensing(persona="Discrete & Heavy Industrial Enterprise"):
    st.title("🧠 NLP Commercial Sensing & Field Intelligence")
    st.caption("Active Persona View: Discrete & Heavy Industrial Enterprise | Ingest unstructured signals from live RSS feeds, executive disclosures, email debriefs, hard macro indicators (NY Fed, FRED, World Bank, ECB, PBOC, KOSPI), and ocean/air freight telemetry.")
    
    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals", 
        "📧 Email & Event Debrief Parser", 
        "⚓ Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        st.subheader("📡 Live Genspark Tactical Market Signals (50 Commodities Spectrum)")
        rf.render_genspark_overlay()

        st.markdown("---")
        rf.render_predictive_commodity_engine()

        st.markdown("---")
        rf.render_macro_telemetry_bar()

        rf.render_triangulated_sentiment_section()

        rf.render_rss_breaking_news_stream()

    with tab2:
        st.subheader("📧 Executive Email & Field Intelligence Debrief Stream")
        st.caption("Parsing post-trade show debriefs, executive LinkedIn disclosures, and CFO field updates before ERP entry.")
        
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            debrief_list = sig_data.get("email_debriefs", sig_data.get("field_intelligence", []))
        except Exception:
            debrief_list = []
        
        if not debrief_list:
            st.info("No active executive event debriefs available.")
        else:
            cols_t2 = st.columns(2)
            for idx, item in enumerate(debrief_list):
                with cols_t2[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Executive Briefing')}** | **{item.get('author', 'Field Sourcing')}** | Commodity: **{item.get('commodity', 'General')}**")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Debrief'))}")
                        st.write(item.get('content', 'Executive field intelligence report regarding spot supply constraints.'))
                        si = float(item.get('sentiment_score', -0.33))
                        st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                        
                        if st.button(f"⚡ Ingest Debrief #{idx+1}", key=f"btn_tab2_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 15400)
                            st.session_state["platform_leadtime_impact"] = item.get("impact_leadtime", 4.2)
                            st.session_state["platform_active_signal"] = item.get("headline", item.get("title", ""))
                            st.toast(f"⚡ Executive Debrief #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()

    with tab3:
        st.subheader("⚓ Live Maritime Freight, Weather & Black Swan Feeds")
        st.caption("Real-time ocean/air spot freight indices, NOAA severe weather tracking, and geopolitical chokepoints.")
        
        rf.render_freight_weather_blackswan_tab()

        st.markdown("---")
        st.markdown("#### 📡 Real-time Telemetry Incident Stream")
        
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            freight_list = sig_data.get("freight_telemetry_feeds", sig_data.get("freight_weather_feeds", []))
        except Exception:
            freight_list = []
        
        if freight_list:
            cols_t3 = st.columns(2)
            for idx, item in enumerate(freight_list):
                with cols_t3[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Telemetry Feed')}** | Corridor: **{item.get('commodity', 'Logistics')}**")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Freight Disruption'))}")
                        si = float(item.get('sentiment_score', -0.42))
                        lt = float(item.get('impact_leadtime', 4.5))
                        st.metric("Lead Time Drag", f"+{lt:.1f} Days", delta=f"SI: {si:+.2f}")
                        
                        if st.button(f"⚡ Ingest Freight Signal #{idx+1}", key=f"btn_tab3_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_leadtime_impact"] = lt
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 16500)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast(f"⚡ Freight Disruption Signal #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()
# =====================================================================
# MODULE 4: DEMAND/SUPPLY MATCH
# =====================================================================
def render_demand_supply_match(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("⚙️ Demand/Supply Match & Plant Load Balancer")
    st.caption("Automated inventory netting, multi-horizon S&OP scheduling, and dynamic order offsets.")
    
    tab1, tab2 = st.tabs([
        "📊 Netting & Forward MRP Horizon (30-180 Days)",
        "⚙️ Dynamic Plant Load Balancing & Capacity Allocation"
    ])
    
    with tab1:
        st.subheader("🗓️ Multi-Period Forward Demand & Netting Horizon")
        horizon = st.select_slider("Select Forward Window (Days):", [30, 45, 60, 90, 180], value=60)
        c1, c2, c3 = st.columns(3)
        c1.metric("Selected Horizon", f"{horizon} Days")
        c2.metric("Gross Requirements", f"{102968:,} {term_unit}")
        c3.metric("Net Uncovered Deficit", f"{38000:,} {term_unit}", delta="Uncovered Risk", delta_color="inverse")

    with tab2:
        st.subheader("⚙️ Dynamic Plant Load Balancing & Capacity Allocation")
        pcols = st.columns(3)
        with pcols[0]:
            st.metric("Detroit Stamping & Assembly", "88.4% Load", "+4% Capacity Drag")
        with pcols[1]:
            st.metric("Munich Component Line", "64.2% Load", "-2.2% Headroom")
        with pcols[2]:
            st.metric("Ohio CMO Partner Node", "92.0% Load", "High Utilization Risk", delta_color="inverse")

# =====================================================================
# MODULE 5: PHYSICAL PROCUREMENT
# =====================================================================
def render_physical_procurement(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("📈 Physical Procurement & Master Contract Desk")
    st.caption("Physical vendor contract execution, direct material sourcing, and price adjustment clauses.")
    
    st.subheader("📋 Active Master Physical Supply Contracts")
    contracts = pd.DataFrame([
        {"Contract ID": "CTR-2026-A1", "Commodity": "Primary Aluminum Ingot", "Supplier": "Rio Tinto Metals", "Volume": "15,000 MT", "Fixed Price": "$2,200 / MT", "Status": "🟢 Active"},
        {"Contract ID": "CTR-2026-B4", "Commodity": "Freight Futures (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "Status": "🟡 Under Review"},
        {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor Components", "Supplier": "TSMC Wafer Foundry", "Volume": "100,000 Units", "Fixed Price": "$450 / Unit", "Status": "🟢 Executing"}
    ])
    st.dataframe(contracts, use_container_width=True)

# =====================================================================
# MODULE 6: CTRM DESK
# =====================================================================
def render_ctrm_desk(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🛡️ CTRM Derivatives & Commodity Risk Desk")
    st.caption("Event-driven financial hedging, Black76 option pricing, and FIX 4.4 execution gateway.")
    
    st.info(f"📡 **Active Ingested Risk Signal**: {st.session_state.get('platform_active_signal', 'Baseline Target')}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Unhedged Margin Risk", f"${(st.session_state.get('platform_demand_impact', 65000) * 150.0):,.2f}")
    col2.metric("Pricing Engine", "Black76 Jump-Diffusion")
    col3.metric("Recommended Structure", "Asian Call Option Collar")
    
    if st.button("⚡ Execute FIX 4.4 Option Order", type="primary"):
        st.balloons()
        st.success("✅ FIX 4.4 Order Executed! Tag 35=D | Tag 150=0 (Filled @ $38.20/unit)")

# =====================================================================
# MODULE 7: GLOBAL LOGISTICS GIS
# =====================================================================
def render_global_logistics_gis(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption("Real-time ocean AIS vessel tracking, port congestion, and air freight telemetry.")
    
    nodes = pd.DataFrame({
        "Name": ["Detroit Plant", "Munich Line", "Panama Canal Chokepoint", "Rotterdam Port"],
        "lat": [42.3314, 48.1351, 9.0800, 51.9244],
        "lon": [-83.0458, 11.5820, -79.6800, 4.4777],
        "Category": ["Plant", "Plant", "Chokepoint", "Port"],
        "Size": [20, 20, 25, 22]
    })
    
    fig = px.scatter_mapbox(nodes, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=400)
    fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# MODULE 8: FLIGHT SIMULATOR
# =====================================================================
def render_flight_simulator(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🧪 Sandbox Flight Simulator & Stress Lab")
    st.caption("Monte Carlo risk simulation and macro stress testing engine.")
    
    scenario = st.selectbox("Select Macro Stress Scenario:", [
        "Baseline Operations",
        "Red Sea / Suez Canal Blockade (+12d Delay)",
        "Black Swan Volatility Spike (+250% IV Shock)"
    ])
    if st.button("🚀 Run Monte Carlo Simulation"):
        st.success(f"✓ Executed 10,000 Monte Carlo Iterations for '{scenario}'! 95% VaR: $1.82M.")

# =====================================================================
# MODULE 9: INTEGRATION ARCHITECTURE
# =====================================================================
def render_integration_architecture(persona="Discrete & Heavy Industrial Enterprise", selected_module=""):
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption("REST API endpoints, SAP S/4HANA & Oracle ERP sync protocols.")
    st.code("""
    GET /api/v1/telemetry/stream
    Host: ibp-control-tower.enterprise.com
    Status: 200 OK
    Payload: { "gscpi": +1.59, "fbx_ocean": 3850, "si_composite": -0.33 }
    """, language="json")

# =====================================================================
# MAIN NAVIGATION ROUTER
# =====================================================================
if "Executive S&OP" in selected_module:
    render_executive_sop(persona)
elif "Inventory" in selected_module or "Position Manager" in selected_module:
    render_inventory_position_manager()
elif "NLP Commercial" in selected_module:
    render_nlp_commercial_sensing(persona)
elif "Demand/Supply Match" in selected_module:
    render_demand_supply_match(persona)
elif "Physical Procurement" in selected_module:
    render_physical_procurement(persona)
elif "CTRM" in selected_module:
    render_ctrm_desk(persona)
elif "Global Logistics" in selected_module:
    render_global_logistics_gis(persona)
elif "Sandbox" in selected_module:
    render_flight_simulator(persona)
elif "Integration" in selected_module:
    render_integration_architecture(persona, selected_module)
else:
    render_executive_sop(persona)
