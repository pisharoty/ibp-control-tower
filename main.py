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
    trade_count = len(st.session_state["executed_hedges"]) + 1
    new_trade = {
        "Trade ID": f"TRD-2026-X{trade_count:03d}",
        "Strategy": trade_title,
        "Volume": "10,000 Units",
        "Strikes": "K1: $15,000 / K2: $14,000",
        "Net Premium": f"${benefit_per_trade*0.05:,.2f}",
        "Hedge Benefit ($)": benefit_per_trade,
        "Timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    }
    st.session_state["executed_hedges"].append(new_trade)
    st.toast(f"🔒 Trade #{trade_count} Executed! Locked +${benefit_per_trade:,.2f}", icon="🚀")
    st.rerun()

# SIDEBAR NAVIGATION ROUTER
st.sidebar.title("⚡ Predictive Commodity Intelligence Platform")

persona = st.sidebar.selectbox(
    "🏢 Enterprise Operating Persona:",
    [
        "🏭 Commercial Commodities & Trading Enterprise",
        "📦 Process Goods & FMCG Enterprise",
        "📈 Merchant Trading & Commodity Risk Desk"
    ],
    key="platform_persona_select"
)

modules = [
    "📊 Global Trade Flows & S&OP Engine",
    "📦 Commodity Inventory & Position Analytics",
    "🧠 Alternative Data & Sentiment Vector Matrix",
    "⚙️ Machine Learning Supply/Demand Projections",
    "📈 Physical Cargo & Contract Intelligence",
    "🛡️ Backtested Portfolio & CTRM Risk Desk",
    "🌐 Real-Time AIS Cargo & GIS Telemetry",
    "🧪 Monte Carlo Risk & Scenario Simulator",
    "🔌 Integration & Architecture Endpoints"
]

nav_choice = st.sidebar.radio("Navigation Modules:", modules, key="sidebar_module_radio")

# MODULE 1: EXECUTIVE S&OP CONTROL TOWER
def render_executive_sop(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("📊 Global Trade Flows & S&OP Engine")
    st.caption(f"Active Persona View: **{persona}**")
    
    surge = st.session_state.get("platform_demand_impact", st.session_state.get("extracted_demand_surge", 65000))
    si = st.session_state.get("platform_si_override", st.session_state.get("si_composite", -0.33))
    
    total_hedge_gain = sum(t.get("Hedge Benefit ($)", 3250000.0) for t in st.session_state["executed_hedges"]) or 3250000.0
    
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

# MODULE 3: NLP COMMERCIAL SENSING
def render_nlp_commercial_sensing(persona="Commercial Commodities & Trading Enterprise"):
    st.title("🧠 Alternative Data & Sentiment Vector Matrix")
    st.caption("A data-driven commodity intelligence and machine-learning forecasting platform providing real-time cargo tracking, supply/demand projections, and backtested analytics across 50+ commodities.")
    
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

# MODULE 4: DEMAND/SUPPLY MATCH
def render_demand_supply_match(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("⚙️ Machine Learning Supply/Demand Projections")
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

# MODULE 5: PHYSICAL PROCUREMENT
def render_physical_procurement(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("📈 Physical Cargo & Contract Intelligence")
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

# MODULE 6: CTRM DERIVATIVES & COMMODITY RISK DESK (ENHANCED WITH SYNTHETIC & MULTI-OPTION STRATEGIES)
def render_ctrm_desk(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("🛡️ Backtested Portfolio & CTRM Risk Desk")
    st.caption("Event-driven financial hedging, Black76 multi-option pricing, strategy payoff modeling, FIX 4.4 gateway, and derivatives register.")
    
    st.info(f"📡 **Active Ingested Risk Signal**: {st.session_state.get('platform_active_signal', 'Baseline Operations Target')}")
    
    surge_vol = st.session_state.get("platform_demand_impact", st.session_state.get("extracted_demand_surge", 65000))
    spot_f = 14669.54
    
    st.subheader("⚙️ Multi-Option Derivatives Strategy Builder")
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        strategy_type = st.selectbox(
            "Select Hedging Strategy Structure:",
            [
                "Asian Call Option Collar (Bought Call / Sold Put)",
                "Zero-Cost Collar (Net Zero Outlay)",
                "Synthetic Long Forward / Futures (Bought Call + Sold Put)",
                "Bear Put Spread (Bought Put $K_1$ / Sold Put $K_2$)",
                "Delta-Neutral Straddle (Volatility Hedge)",
                "Synthetic Floating-to-Fixed Commodity Swap"
            ],
            key="ctrm_strat_select"
        )
        vol_input = st.number_input(f"Hedging Contract Volume ({term_unit}):", value=int(surge_vol), step=1000, key="ctrm_vol_in")

    with col_s2:
        k1_strike = st.number_input("Primary Strike ($K_1$ Call/Forward USD):", value=15000.0, step=100.0, key="ctrm_k1_in")
        k2_strike = st.number_input("Secondary Strike ($K_2$ Floor/Put USD):", value=14000.0, step=100.0, key="ctrm_k2_in")
        expiry_days = st.slider("Time to Expiration (Days):", 15, 180, 60, key="ctrm_expiry_in")
        implied_vol = st.slider("Implied Volatility (σ %):", 10, 100, 28, key="ctrm_iv_in") / 100.0

    greeks = rf.compute_strategy_greeks(
        spot_f, k1_strike, k2_strike, expiry_days/365.0, 0.045, implied_vol, strategy_type, volume=vol_input
    )
    
    st.markdown("##### 📊 Strategy Pricing & Black76 Risk Greeks")
    gcols = st.columns(5)
    gcols[0].metric("Net Unit Premium", f"${greeks['price_per_unit']:,.2f} / unit")
    gcols[1].metric("Total Outlay", f"${greeks['total_premium']:,.2f}")
    gcols[2].metric("Delta (Δ)", f"{greeks['delta']:.3f}")
    gcols[3].metric("Gamma (Γ)", f"{greeks['gamma']:.5f}")
    gcols[4].metric("Vega (ν)", f"${greeks['vega']:,.2f}")

    st.plotly_chart(rf.plot_strategy_payoff(spot_f, k1_strike, k2_strike, strategy_type, volume=vol_input), use_container_width=True)

    st.divider()
    st.subheader("⚡ FIX 4.4 Financial Hedge Execution Gateway")
    
    fcol1, fcol2 = st.columns([2, 1])
    with fcol1:
        st.code(f"""
[FIX 4.4 OUTBOUND DERIVATIVE ORDER PROPOSAL]
8=FIX.4.4|9=288|35=D|49=IBP_DESK|56=CME_LME_GATEWAY|34=1099|52={datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}|
11=ORDER_HEDGE_{datetime.datetime.utcnow().strftime("%Y%m%d_%H%M")}|55=LME_COMMODITY_HEDGE|54=1|38={vol_input}|
40=2|44={k1_strike:.2f}|207=CME_LME|1000={strategy_type[:20]}|10=204|
        """, language="text")
    with fcol2:
        st.markdown("##### Executive Trade Execution")
        if st.button("⚡ Execute Derivative Order via FIX 4.4", type="primary", use_container_width=True, key="btn_exec_ctrm_fix"):
            trade_count = len(st.session_state.get("executed_hedges", [])) + 1
            benefit = abs(greeks['total_premium']) if greeks['total_premium'] != 0 else 3250000.0
            new_trade = {
                "Trade ID": f"TRD-2026-X{trade_count:03d}",
                "Strategy": strategy_type,
                "Volume": f"{vol_input:,} {term_unit}",
                "Strikes": f"K1: ${k1_strike:,.2f} / K2: ${k2_strike:,.2f}",
                "Net Premium": f"${greeks['total_premium']:,.2f}",
                "Hedge Benefit ($)": benefit,
                "Status": "🟢 Executed & Matched"
            }
            if "executed_hedges" not in st.session_state:
                st.session_state["executed_hedges"] = []
            st.session_state["executed_hedges"].append(new_trade)
            st.toast(f"🔒 Executed FIX 4.4 Order for {strategy_type}! Benefit: +${benefit:,.2f}", icon="🚀")
            st.rerun()

    st.divider()
    st.subheader("📑 CTRM Executed Derivatives Booking Register")
    hedges = st.session_state.get("executed_hedges", [])
    if not hedges:
        st.info("No derivative trades executed yet. Configure parameters above and click 'Execute Derivative Order'.")
    else:
        st.dataframe(pd.DataFrame(hedges), use_container_width=True, hide_index=True)

# MODULE 7: GLOBAL LOGISTICS GIS (EXPANDED WITH RICH MAP & TELEMETRY REGISTERS)
def render_global_logistics_gis(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("🌐 Real-Time AIS Cargo & GIS Telemetry")
    st.caption("Real-time ocean AIS vessel tracking, port congestion, maritime chokepoints, and freight lane telemetry.")
    
    nodes = pd.DataFrame({
        "Name": [
            "Detroit Stamping Plant", "Munich Component Line", "Nagoya Metals Hub", "São Paulo Logistics Node",
            "Rotterdam Port Hub", "Shanghai Container Port", "Singapore Terminal", "Los Angeles / Long Beach Port",
            "Panama Canal Chokepoint", "Suez Canal Corridor", "Bab-el-Mandeb Strait", "Strait of Malacca", "Strait of Hormuz"
        ],
        "lat": [42.3314, 48.1351, 35.1815, -23.5505, 51.9244, 31.2304, 1.3521, 33.7405, 9.0800, 29.9753, 12.5833, 2.5000, 26.5667],
        "lon": [-83.0458, 11.5820, 136.9066, -46.6333, 4.4777, 121.4737, 103.8198, -118.2786, -79.6800, 32.5599, 43.3333, 101.5000, 56.2500],
        "Category": [
            "Plant Node", "Plant Node", "Plant Node", "Plant Node",
            "Global Port", "Global Port", "Global Port", "Global Port",
            "Maritime Chokepoint", "Maritime Chokepoint", "Maritime Chokepoint", "Maritime Chokepoint", "Maritime Chokepoint"
        ],
        "Size": [16, 16, 16, 16, 22, 24, 22, 22, 26, 26, 26, 24, 26]
    })
    
    fig = rf.create_gis_map_figure(nodes)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📡 Global Maritime Shipping Lanes Telemetry Register")
    
    lanes_data = [
        {"Shipping Lane Corridor": "Asia East Coast to US West Coast (Transpacific)", "FBX Rate ($/FEU)": "$4,250", "YoY Change": "+18.5%", "Avg Transit (Days)": "14.2 Days", "Congestion Delay": "+3.5 Days", "Status": "🔴 High Bottleneck"},
        {"Shipping Lane Corridor": "Asia to North Europe (Suez / Red Sea)", "FBX Rate ($/FEU)": "$5,820", "YoY Change": "+42.0%", "Avg Transit (Days)": "34.0 Days", "Congestion Delay": "+12.5 Days", "Status": "🔴 Cape Rerouting Active"},
        {"Shipping Lane Corridor": "Transatlantic North Europe to US East Coast", "FBX Rate ($/FEU)": "$2,100", "YoY Change": "-2.1%", "Avg Transit (Days)": "10.5 Days", "Congestion Delay": "+0.5 Days", "Status": "🟢 Smooth Flow"},
        {"Shipping Lane Corridor": "US Gulf to East Asia (Panama Canal)", "FBX Rate ($/FEU)": "$3,950", "YoY Change": "+12.4%", "Avg Transit (Days)": "22.8 Days", "Congestion Delay": "+6.0 Days", "Status": "🟡 Draft Restrictions"}
    ]
    st.dataframe(pd.DataFrame(lanes_data), use_container_width=True, hide_index=True)

# MODULE 8: SANDBOX FLIGHT SIMULATOR (ENHANCED WITH MONTE CARLO & PROPAGATION)
def render_flight_simulator(persona="Commercial Commodities & Trading Enterprise", term_unit="Units"):
    st.title("🧪 Monte Carlo Risk & Scenario Simulator")
    st.caption("Monte Carlo risk simulation, fat-tailed volatility stress testing, and direct scenario propagation into platform state.")
    
    st.subheader("⚙️ Macro Stress Scenario & Monte Carlo Parameters")
    
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        scenario_select = st.selectbox(
            "Select Macro Stress Scenario:",
            [
                "Red Sea / Suez Canal Naval Blockade (+12.5d Delay)",
                "Strait of Hormuz Oil & Energy Shock (Brent +45%)",
                "Black Swan Implied Volatility Surge (IV +250%)",
                "Panama Canal Severe Drought (Draft Limits -30%)",
                "Global Macro Demand Contraction / Stagflation",
                "Baseline Operations"
            ],
            key="sandbox_scen_select"
        )
        sim_iterations = st.slider("Monte Carlo Iterations:", 1000, 50000, 10000, step=1000, key="mc_iter_sld")

    with col_sc2:
        sim_horizon = st.slider("Simulation Horizon (Days):", 30, 180, 60, key="mc_horiz_sld")
        conf_level = st.selectbox("Value at Risk (VaR) Confidence Level:", [0.90, 0.95, 0.99], index=1, key="mc_conf_sel")

    mc_res = rf.run_monte_carlo_simulation(
        iterations=sim_iterations,
        horizon_days=sim_horizon,
        confidence_level=conf_level,
        base_value_usd=120000000.0,
        scenario_type=scenario_select
    )

    st.markdown("##### 📊 Monte Carlo Risk Metrics & Value at Risk (VaR)")
    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
    mcol1.metric("Expected Mean P&L", f"${mc_res['mean_pnl']/1e6:+.2f}M")
    mcol2.metric(f"{conf_level*100:.0f}% VaR Loss", f"-${mc_res['var_usd']/1e6:.2f}M", delta_color="inverse")
    mcol3.metric("Expected Shortfall (CVaR)", f"-${mc_res['cvar_usd']/1e6:.2f}M", delta_color="inverse")
    mcol4.metric("Max Drawdown", f"-${mc_res['max_drawdown']/1e6:.2f}M")
    mcol5.metric("Loss Probability", f"{mc_res['prob_loss']:.1f}%")

    st.plotly_chart(mc_res["fig"], use_container_width=True)

    st.divider()
    if st.button("⚡ Propagate Monte Carlo Scenario to Exec S&OP & CTRM", type="primary", use_container_width=True, key="btn_propagate_mc_sop"):
        calc_si = -0.45 if "Blockade" in scenario_select or "Shock" in scenario_select else (-0.65 if "Vol" in scenario_select else -0.15)
        st.session_state["platform_si_override"] = calc_si
        st.session_state["platform_demand_impact"] = 100000 + mc_res["add_surge"]
        st.session_state["platform_leadtime_impact"] = 2.5 + mc_res["add_lt"]
        st.session_state["platform_active_signal"] = f"Monte Carlo Stress Ingest: {scenario_select} (VaR: -${mc_res['var_usd']/1e6:.2f}M)"
        st.toast(f"⚡ Propagated Monte Carlo Scenario '{scenario_select}' to S&OP & CTRM! Lead time updated: +{2.5 + mc_res['add_lt']:.1f} days.", icon="🚀")
        st.rerun()

# MODULE 9: INTEGRATION & ARCHITECTURE ENDPOINTS (EXPANDED CATALOG & ARCHITECTURE BLUEPRINT)
def render_integration_architecture(persona="Commercial Commodities & Trading Enterprise", selected_module=""):
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption("REST API endpoints, Webhook listeners, FIX 4.4 protocol specifications, and SAP S/4HANA / Oracle ERP connectors.")
    
    st.subheader("📑 Enterprise API Catalog & Swagger Specs")
    
    ep_tabs = st.tabs([
        "🌐 Macro & Telemetry API",
        "📰 RSS & Sentiment Stream API",
        "🛡️ CTRM FIX 4.4 / REST Order Gateway",
        "🔄 S&OP Cascade Propagation Webhook",
        "⚓ GIS Vessel & Port Telemetry API"
    ])
    
    with ep_tabs[0]:
        st.code("""
GET /api/v1/telemetry/macro
Host: ibp-control-tower.enterprise.com
Authorization: Bearer <JWT_TOKEN>

[RESPONSE 200 OK]
{
  "timestamp": "2026-10-22T13:30:00Z",
  "ny_fed_gscpi": 1.59,
  "fred_mfg_index": 103.8,
  "wb_commodity_index": 152.2,
  "ecb_refi_rate": 2.65,
  "kospi_index": 2618.0
}
        """, language="json")

    with ep_tabs[1]:
        st.code("""
GET /api/v1/telemetry/rss?sector=Metals%20%26%20Mining
Host: ibp-control-tower.enterprise.com

[RESPONSE 200 OK]
{
  "total_items": 4,
  "articles": [
    {
      "title": "Global Raw Materials Update: Spot Market Tightening Across Metals",
      "source": "Reuters Telemetry",
      "sentiment_score": -0.40,
      "inferred_demand_surge": 18500
    }
  ]
}
        """, language="json")

    with ep_tabs[2]:
        st.code("""
POST /api/v1/ctrm/orders/submit
Host: ibp-control-tower.enterprise.com
Content-Type: application/json

{
  "fix_msg_type": "D",
  "symbol": "LME_CU_3M",
  "strategy": "Asian Call Option Collar",
  "volume_units": 65000,
  "strike_k1": 15000.00,
  "strike_k2": 14000.00,
  "time_in_force": 0
}
        """, language="json")

    with ep_tabs[3]:
        st.code("""
POST /api/v1/sop/cascade/propagate
Host: ibp-control-tower.enterprise.com

{
  "active_signal": "Red Sea Carrier Surcharges & Cape Route Rerouting",
  "si_override": -0.450,
  "demand_impact_units": 102968,
  "leadtime_impact_days": 4.5
}
        """, language="json")

    with ep_tabs[4]:
        st.code("""
GET /api/v1/gis/vessel-telemetry?corridor=Transpacific
Host: ibp-control-tower.enterprise.com

[RESPONSE 200 OK]
{
  "corridor": "Transpacific Eastbound",
  "fbx_spot_rate": 4250.00,
  "active_ais_vessels": 142,
  "avg_delay_days": 3.5,
  "chokepoint_status": "ELEVATED"
}
        """, language="json")

    st.divider()
    st.subheader("🏗️ Enterprise Event Architecture Feed Blueprint")
    st.info("🔹 **Telemetry Ingestion Engine**: Apache Kafka / Redis PubSub stream ingestion running at 100 Hz.")
    st.info("🔹 **ERP Master Data Connectors**: Direct SAP S/4HANA IDoc / OData API & Oracle Cloud SCM synchronization.")
    st.info("🔹 **Risk Execution Gateway**: Low-latency FIX 4.4 binary protocol integration with CME, LME, and ICE brokers.")

# MAIN ROUTER EXECUTION
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
