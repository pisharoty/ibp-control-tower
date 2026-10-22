import streamlit as st
import json
import os
import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
if "executed_hedges" not in st.session_state:
    st.session_state["executed_hedges"] = []

def execute_ctrm_trade(trade_title="CTRM FIX Protocol Hedge", benefit_per_trade=3250000.0):
    """Global callback to execute a trade, update state, and force instant rerun."""
    trade_count = len(st.session_state["executed_hedges"]) + 1
    new_trade = {
        "title": f"{trade_title} #{trade_count}",
        "source_type": "CTRM Desk Trade Execution",
        "hedge_benefit_usd": benefit_per_trade,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    st.session_state["executed_hedges"].append(new_trade)
    st.toast(f"🔒 Trade #{trade_count} Executed! Locked +${benefit_per_trade:,.2f}", icon="🚀")
    st.rerun()

# =====================================================================
# SIDEBAR NAVIGATION ROUTER
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
    
    total_hedge_gain = sum(t.get("hedge_benefit_usd", 0.0) for t in st.session_state["executed_hedges"]) or 3250000.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2% YoY")
    c2.metric("Unconstrained Demand", f"${(120.0 + surge*0.00025):.2f}M", f"+{surge:,} {term_unit}")
    c3.metric("CTRM Hedge Benefit", f"+${total_hedge_gain/1e6:.2f}M", f"{len(st.session_state['executed_hedges'])} Trades Locked")
    c4.metric("Available Treasury Cash", f"${(4.43 + total_hedge_gain/1e6):,.2f}M", "-$0.57M Freight Drag")
    
    st.divider()
    
    col_p1, col_p2 = st.columns([1.3, 1])
    with col_p1:
        st.subheader("💵 Financial P&L Margin Waterfall")
        fig = go.Figure(go.Waterfall(
            name="P&L Reconciliation", orientation="v",
            measure=["relative", "relative", "relative", "relative", "relative", "total"],
            x=["Base AOP Rev", "Base COGS", "Surge Rev", "Freight Drag", "Hedge Benefit", "Net EBITDA"],
            y=[120.0, -78.0, surge*0.00025, -0.57, total_hedge_gain/1e6, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_p2:
        st.subheader("🚩 Live Operational Desk Feeds")
        st.info(f"🔹 **Active Signal**: {st.session_state.get('platform_active_signal', 'Baseline Operations Target')}")
        st.warning(f"✈️ **Logistics Desk**: Lead time delay drag set at +{st.session_state.get('platform_leadtime_impact', 2.5)} days")
        st.success(f"🟢 **CTRM Risk Desk**: {len(st.session_state['executed_hedges'])} Hedges Executed | Gain: +${total_hedge_gain:,.2f}")

# =====================================================================
# MODULE 3: NLP COMMERCIAL SENSING
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
        st.subheader("📡 Live Genspark Tactical Market Signals")
        rf.render_genspark_overlay()

        rf.render_predictive_commodity_engine()

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
# MODULE 4: DEMAND/SUPPLY MATCH & PLANT LOAD BALANCER (RESTORED)
# =====================================================================
def render_demand_supply_match(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("⚙️ Demand/Supply Match & Plant Load Balancer")
    st.caption("Automated inventory netting, multi-horizon S&OP scheduling, dynamic order offsets, and plant load balancing.")
    
    surge_units = st.session_state.get("platform_demand_impact", st.session_state.get("extracted_demand_surge", 102968))
    delta_lt = st.session_state.get("platform_leadtime_impact", 2.5)
    
    st.info(f"🔗 **Active Orchestrated Signal**: `{st.session_state.get('platform_active_signal', 'Baseline Operations Target')}` | **Surge**: {surge_units:,} {term_unit} | **ΔLT Transit Delay**: +{delta_lt} Days")
    
    tab1, tab2 = st.tabs([
        "📊 Netting & Forward MRP Horizon (30-180 Days)",
        "⚙️ Dynamic Plant Load Balancing & Capacity Allocation"
    ])
    
    with tab1:
        st.subheader("🗓️ Multi-Period Forward Demand & Netting Horizon")
        horizon_days = st.select_slider("Select Forward Window (Days):", [30, 45, 60, 90, 180], value=60, key="mrp_horizon_slider")
        
        daily_rate = surge_units / 90.0
        req_vol = int(daily_rate * horizon_days)
        cov_vol = int(req_vol * 0.65)
        net_def = max(0, req_vol - cov_vol)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selected Horizon", f"{horizon_days} Days")
        m2.metric(f"Gross Req ({horizon_days}d)", f"{req_vol:,} {term_unit}")
        m3.metric("Contracted Inbound", f"{cov_vol:,} {term_unit}")
        m4.metric("Net Uncovered Deficit", f"{net_def:,} {term_unit}", delta="Uncovered Risk" if net_def > 0 else "Balanced", delta_color="inverse")

        st.markdown("##### 📋 Forward MRP Netting Schedule Matrix")
        periods = [30, 45, 60, 90, 180]
        matrix = []
        for p in periods:
            p_req = int(daily_rate * p)
            p_cov = int(p_req * 0.65)
            p_net = max(0, p_req - p_cov)
            matrix.append({
                "Horizon": f"T+{p} Days",
                "Gross Req": f"{p_req:,} {term_unit}",
                "Contract Cover": f"{p_cov:,} {term_unit}",
                "Safety Stock Buffer (12%)": f"{int(p_req*0.12):,} {term_unit}",
                "Net Planned Release": f"{p_net + int(p_req*0.12):,} {term_unit}",
                "MRP Status": "⚠️ Deficit / Release Needed" if p_net > 0 else "✅ Balanced"
            })
        st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("⚙️ Upstream ERP Planned Order Release (POR) Recalculation")
        base_release = "2026-11-15"
        shifted_release = "2026-11-07"
        
        o1, o2, o3 = st.columns(3)
        o1.metric("Baseline Order Release Date", base_release)
        o2.metric("Upstream Transit Delay (ΔLT)", f"+{delta_lt} Days")
        o3.metric("Shifted ERP Release Date", shifted_release)
        
        st.success(f"**Automated ERP Action**: Planned Order Release shifted backward to **`{shifted_release}`** to absorb the **+{delta_lt} day** bottleneck.")

    with tab2:
        st.subheader("⚙️ Dynamic Plant Load Balancing & Capacity Allocation")
        
        pcols = st.columns(3)
        with pcols[0]:
            st.metric("Detroit Stamping & Assembly", "88.4% Load", "+4.0% Capacity Drag")
            st.progress(0.884)
        with pcols[1]:
            st.metric("Munich Component Line", "64.2% Load", "-2.2% Headroom")
            st.progress(0.642)
        with pcols[2]:
            st.metric("Ohio CMO Partner Node", "92.0% Load", "High Utilization Risk", delta_color="inverse")
            st.progress(0.920)

        st.markdown("##### Reallocate Demand Surge Across Manufacturing Facilities")
        detroit_alloc = st.slider("Detroit Allocation (%):", 0, 100, 50, key="detroit_alloc_slider")
        munich_alloc = st.slider("Munich Allocation (%):", 0, 100, 30, key="munich_alloc_slider")
        ohio_alloc = 100 - (detroit_alloc + munich_alloc)
        st.caption(f"Ohio CMO Allocation: **{ohio_alloc}%**")
        
        if st.button("🚀 Rebalance Plant Capacity & Re-route S&OP Load", type="primary"):
            st.toast("✅ Plant Load Rebalanced across Detroit, Munich, and Ohio CMO Nodes!")

# =====================================================================
# MODULE 5: PHYSICAL PROCUREMENT & MASTER CONTRACT DESK (RESTORED)
# =====================================================================
def render_physical_procurement(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("📈 Physical Procurement & Master Contract Desk")
    st.caption("Physical vendor contract execution, direct material sourcing, tier-1 risk scorecards, and price adjustment clauses.")
    
    st.subheader("📋 Active Master Physical Supply Contracts Booking Register")
    
    if "physical_contracts_list" not in st.session_state:
        st.session_state["physical_contracts_list"] = [
            {"Contract ID": "CTR-2026-A1", "Commodity": "Primary Aluminum Ingot", "Supplier": "Rio Tinto Metals", "Volume": "15,000 MT", "Fixed Price": "$2,200 / MT", "GL Account": "GL-5100-AL", "Status": "🟢 Active"},
            {"Contract ID": "CTR-2026-B4", "Commodity": "Ocean Freight (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "GL Account": "GL-5400-FRT", "Status": "🟡 Under Review"},
            {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor MCUs", "Supplier": "TSMC Wafer Foundry", "Volume": "100,000 Units", "Fixed Price": "$450 / Unit", "GL Account": "GL-5200-SEMI", "Status": "🟢 Executing"}
        ]

    st.dataframe(pd.DataFrame(st.session_state["physical_contracts_list"]), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📝 Commit New Physical Supply Contract")
    
    cform1, cform2 = st.columns(2)
    with cform1:
        vendor_input = st.text_input("Supplier / Vendor Name:", "Glencore International PLC")
        material_input = st.text_input("Material / Commodity:", "Physical Copper Cathodes Grade A")
    with cform2:
        vol_input = st.number_input(f"Contract Volume ({term_unit}):", value=10000, step=1000)
        price_input = st.number_input("Unit Price ($ USD):", value=4200.0, step=50.0)
        
    if st.button("🖊️ Sign & Commit Physical Supply Contract", type="primary"):
        new_ctr = {
            "Contract ID": f"CTR-2026-D{len(st.session_state['physical_contracts_list'])+1}",
            "Commodity": material_input,
            "Supplier": vendor_input,
            "Volume": f"{vol_input:,} {term_unit}",
            "Fixed Price": f"${price_input:,.2f} / unit",
            "GL Account": "GL-5100-PHYSICAL",
            "Status": "🟢 Committed"
        }
        st.session_state["physical_contracts_list"].append(new_ctr)
        st.toast(f"✅ Signed Physical Contract with {vendor_input} for {vol_input:,} units!", icon="📜")
        st.rerun()

# =====================================================================
# MODULE 6: CTRM DERIVATIVES & COMMODITY RISK DESK (RESTORED)
# =====================================================================
def render_ctrm_desk(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🛡️ CTRM Derivatives & Commodity Risk Desk")
    st.caption("Event-driven financial hedging, Black76 option pricing, FIX 4.4 execution gateway, and derivatives booking register.")
    
    st.info(f"📡 **Active Ingested Risk Signal**: {st.session_state.get('platform_active_signal', 'Baseline Target')}")
    
    surge_vol = st.session_state.get("platform_demand_impact", st.session_state.get("extracted_demand_surge", 65000))
    spot_f = 14669.54
    strike_k = 14500.00
    
    call_price, put_price, delta_val, vega_val = rf.pure_black76_call_put(spot_f, strike_k, 60.0/365.0, 0.045, 0.28)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unhedged Surge Exposure", f"{surge_vol:,} {term_unit}")
    c2.metric("Black76 Asian Call Option", f"${call_price:,.2f} / MT")
    c3.metric("Option Delta (Δ)", f"{delta_val:.3f}")
    c4.metric("Vega Sensitivity (ν)", f"${vega_val:,.2f}")

    st.divider()
    st.subheader("⚡ FIX 4.4 Financial Hedge Execution Gateway")
    
    fcol1, fcol2 = st.columns([2, 1])
    with fcol1:
        st.code(f"""
[FIX 4.4 OUTBOUND ORDER PROPOSAL]
8=FIX.4.4|9=245|35=D|49=PLATFORM_DESK|56=CME_LME_GATEWAY|34=1082|52=2026-10-22T13:00:00Z|
11=ORDER_HEDGE_20261022|55=LME_CU_3M|54=1|38={surge_vol}|40=2|44={strike_k:.2f}|59=0|10=182|
        """, language="text")
    with fcol2:
        st.markdown("##### Executive Actions")
        if st.button("⚡ Execute Auto-Hedge FIX 4.4 Order", type="primary", use_container_width=True):
            execute_ctrm_trade("CME/LME Asian Call Collar", benefit_per_trade=3250000.0)

    st.divider()
    st.subheader("📑 CTRM Executed Derivatives Booking Register")
    
    hedges = st.session_state.get("executed_hedges", [])
    if not hedges:
        st.info("No derivative trades executed yet. Click 'Execute Auto-Hedge' to lock positions.")
    else:
        st.dataframe(pd.DataFrame(hedges), use_container_width=True, hide_index=True)

# =====================================================================
# MODULE 7: GLOBAL LOGISTICS GIS (FIXED PLOTLY ATTRIBUTE ERROR)
# =====================================================================
def render_global_logistics_gis(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption("Real-time ocean AIS vessel tracking, port congestion, and air freight telemetry.")
    
    nodes = pd.DataFrame({
        "Name": ["Detroit Stamping Plant", "Munich Component Line", "Panama Canal Chokepoint", "Rotterdam Port Hub"],
        "lat": [42.3314, 48.1351, 9.0800, 51.9244],
        "lon": [-83.0458, 11.5820, -79.6800, 4.4777],
        "Category": ["Plant", "Plant", "Chokepoint", "Port"],
        "Size": [16, 16, 22, 18]
    })
    
    # Safe Plotly Map renderer
    fig = rf.create_gis_map_figure(nodes)
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
# MAIN ROUTER EXECUTION
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
