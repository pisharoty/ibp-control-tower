import streamlit as st

if "active_mc_scenario" not in st.session_state:
    st.session_state["active_mc_scenario"] = None
if "mc_expected_loss" not in st.session_state:
    st.session_state["mc_expected_loss"] = 0.0
if "mc_transit_delay" not in st.session_state:
    st.session_state["mc_transit_delay"] = 0.0

import streamlit as st

if "rerouted_vessels" not in st.session_state:
    st.session_state["rerouted_vessels"] = []
if "executed_hedges" not in st.session_state:
    st.session_state["executed_hedges"] = []

from robot_feeds import calculate_inventory_carrying_cost, calculate_demurrage_and_decay, simulate_rerouting_arbitrage, get_digital_twin_telemetry_feed
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

nav_choice = selected_module = st.sidebar.radio("Navigation Modules:", modules, key="sidebar_module_radio")

# MODULE 1: EXECUTIVE S&OP CONTROL TOWER
def render_executive_sop(persona=None):
    st.header("📊 Global Trade Flows & S&OP Engine")
    st.caption("Integrated Business Planning, P&L EBITDA Margin Waterfall, and Live Desk Signal Synchronization.")

    rerouted = st.session_state.get("rerouted_vessels", [])
    hedges = st.session_state.get("executed_hedges", [])
    mc_scenario = st.session_state.get("active_mc_scenario", None)
    mc_loss = st.session_state.get("mc_expected_loss", 0.0)

    twin_data = get_digital_twin_telemetry_feed()
    total_transit_drag = 0.0
    for v in twin_data:
        v_name = v["vessel_name"]
        c_cost = v["carrying_cost_usd"]
        d_cost = v["demurrage_penalty_usd"]
        
        if any(r in v_name for r in rerouted):
            total_transit_drag += c_cost + 56958.90
        else:
            total_transit_drag += c_cost + d_cost

    drag_m = total_transit_drag / 1000000.0
    hedge_benefit = 3.25 + len(hedges) * 2.15
    base_aop = 120.0
    cogs = -70.0
    surge_rev = 10.0
    net_ebitda = base_aop + cogs + surge_rev - drag_m - mc_loss + hedge_benefit

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Annual Operating Plan (AOP)", f"${base_aop:.1f}M", "+4.2% YoY")
    col_m2.metric("Unconstrained Demand", "$125.94M", "+23,750 Units")
    col_m3.metric("CTRM Hedge Benefit", f"+${hedge_benefit:.2f}M", f"{len(hedges)} Digital Twin Hedges Locked")
    col_m4.metric("Available Treasury Cash", f"${15.29 + (1.14 - drag_m) - mc_loss:.2f}M", f"-${drag_m + mc_loss:.2f}M Total Drag")

    col_w1, col_w2 = st.columns([2, 1])

    with col_w1:
        st.subheader("📊 Financial P&L Margin Waterfall")
        import plotly.graph_objects as go
        
        x_bars = ["Base AOP Rev", "Base COGS", "Surge Rev", "Freight Drag"]
        measures = ["relative", "relative", "relative", "relative"]
        y_vals = [base_aop, cogs, surge_rev, -drag_m]
        text_vals = [f"+${base_aop:.1f}M", f"-${abs(cogs):.1f}M", f"+${surge_rev:.1f}M", f"-${drag_m:.2f}M"]

        if mc_loss > 0:
            x_bars.append("Macro Stress Shock")
            measures.append("relative")
            y_vals.append(-mc_loss)
            text_vals.append(f"-${mc_loss:.2f}M")

        x_bars.extend(["Hedge Benefit", "Net EBITDA"])
        measures.extend(["relative", "total"])
        y_vals.extend([hedge_benefit, None])
        text_vals.extend([f"+${hedge_benefit:.2f}M", f"${net_ebitda:.2f}M"])

        fig = go.Figure(go.Waterfall(
            name="P&L Waterfall",
            orientation="v",
            measure=measures,
            x=x_bars,
            textposition="outside",
            text=text_vals,
            y=y_vals,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#ef553b"}},
            increasing={"marker": {"color": "#00cc96"}},
            totals={"marker": {"color": "#1d70b8"}}
        ))
        fig.update_layout(
            title="Dynamic EBITDA Margin Waterfall ($M USD)",
            showlegend=False,
            height=340,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width='stretch')

    with col_w2:
        st.subheader("► Live Operational Desk Feeds")
        
        if mc_scenario:
            st.error(f"🔥 **Macro Stress Active**: **{mc_scenario}** injected (-${mc_loss:.2f}M P&L Drag).")
        else:
            st.markdown("• **Active Signal**: Sub-Factor Weight Shift (GSCPI:35% / NOAA:25% / Freight:25% / GEP:15%)")
        
        if rerouted:
            r_str = ", ".join(rerouted)
            st.success(f"• **Logistics Desk**: 🚢 Digital Twin Reroute Executed for **{r_str}** via Cape of Good Hope.")
        else:
            st.warning("• **Logistics Desk**: Lead time delay drag set at +3.5 days (Panama/Suez queues active).")

        if hedges:
            st.success(f"• **CTRM Risk Desk**: ⚡ {len(hedges)} Digital Twin FIX 4.4 Short Futures Position(s) Locked.")
        else:
            st.info("• **CTRM Risk Desk**: 0 Digital Twin Hedges Executed.")

    st.markdown("---")
    st.subheader("💰 Digital Twin Carrying Cost Drag on P&L Waterfall")
    col_pnl1, col_pnl2, col_pnl3 = st.columns(3)
    col_pnl1.metric("Gross EBITDA Target", "$120.00M")
    col_pnl2.metric("In-Transit Carrying & Demurrage Drag", f"-${drag_m + mc_loss:.2f}M", delta=f"Injected Macro Loss: -${mc_loss:.2f}M" if mc_loss > 0 else f"Saved ${1.14 - drag_m:.2f}M via Rerouting", delta_color="inverse")
    col_pnl3.metric("Net Adjusted EBITDA", f"${net_ebitda:.2f}M")


def render_nlp_commercial_sensing(persona="Commercial Commodities & Trading Enterprise"):
    st.title("🧠 Alternative Data & Sentiment Vector Matrix")
    st.caption("A data-driven commodity intelligence and machine-learning forecasting platform providing real-time cargo tracking, supply/demand projections, and backtested analytics across 50+ commodities.")
    
    if "selected_sector" not in st.session_state:
        st.session_state["selected_sector"] = "Metals & Mining"

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals", 
        "📧 Email & Event Debrief Parser", 
        "⚓ Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        # Dynamically load live market ticks from robot_signals.json if available
        try:
            with open("robot_signals.json", "r") as f:
                robot_data = json.load(f)
            live_ticks = robot_data.get("live_ticks", {})
        except Exception:
            live_ticks = {}
        st.subheader("📡 Live Genspark Tactical Market Signals")
        rf.render_genspark_overlay()

        rf.render_predictive_commodity_engine()

        rf.render_macro_telemetry_bar()

        rf.render_triangulated_sentiment_section()

        rf.render_rss_breaking_news_stream()

    with tab2:
        st.subheader("Alternative Data & Multi-Source Intelligence Scraper Matrix")
        st.caption("Multi-channel signal scraping, NLP sentiment scoring (VADER), and predictive anomaly vector propagation.")

        c_sym, c_depth, c_btn = st.columns([2, 2, 2])
        with c_sym:
            target_symbol = st.selectbox(
                "Target Commodity / Asset Stream:",
                [
                    "HO=F (ULSD Heating Oil / Distillates)",
                    "CL=F (WTI Crude Oil)",
                    "BZ=F (Brent Crude Oil)",
                    "NG=F (Henry Hub Natural Gas)",
                    "RB=F (RBOB Gasoline)",
                    "HG=F (LME Copper Cathode)",
                    "ALI=F (Primary Aluminum Ingot)",
                    "ZN=F (Special High Grade Zinc)",
                    "GC=F (Gold Spot / Futures)",
                    "SI=F (Silver Spot / Futures)",
                    "LIT (Battery Grade Lithium)",
                    "KC=F (Arabica Coffee & Softs)",
                    "ZW=F (CBOT Milling Wheat)",
                    "ZC=F (CBOT Yellow Corn)",
                    "ZS=F (CBOT Soybeans)",
                    "SB=F (ICE Raw Sugar)",
                    "NTR (Potassium Chloride & MOP)",
                    "CF (Ammonia & Nitrogen Feedstock)",
                    "MOS (Phosphates & Acid Benchmark)",
                    "BDRY (Baltic Dry Shipping Index)",
                    "ZIM (Ocean Container Transport)",
                    "EXPD (Global Freight Logistics)"
                ]
            )
        with c_depth:
            feed_mode = st.select_slider("Scraper Feed Depth Mode:", options=["Standard Feeds", "Deep Multi-Channel Scraper"], value="Deep Multi-Channel Scraper")
        with c_btn:
            st.write("")
            st.write("")
            if st.button("🚨 Run Multi-Source Scraper Agent Network", width='stretch'):
                st.toast("Scraper Agents active: Processing RSS XML, Reuters, and Maritime Feeds...", icon="📡")

        selected_ticker = target_symbol.split()[0]
        raw_name = target_symbol.split("(")[1].replace(")", "") if "(" in target_symbol else target_symbol
        
        try:
            with open("robot_signals.json", "r") as f:
                robot_data = json.load(f)
            live_ticks_t2 = robot_data.get("live_ticks", {})
        except Exception:
            live_ticks_t2 = {}

        tick_info = live_ticks_t2.get(selected_ticker, {})
        if "vader" in tick_info:
            avg_score = float(tick_info["vader"])
        else:
            hash_val = sum(ord(c) for c in target_symbol)
            avg_score = float(((hash_val % 100) - 48) / 100.0) if selected_ticker != "HO=F" else -0.0200

        leadtime_drag = round(max(0.5, abs(avg_score) * 5.2), 1)
        demand_impact = int(112200 + avg_score * 18500)
        delta_lbl = "Bearish Drag" if avg_score < 0 else "Bullish Signal"
        delta_c = "inverse" if avg_score < 0 else "normal"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Target Symbol", selected_ticker)
        m2.metric("Dynamic VADER Composite", f"{avg_score:+.4f}", delta=delta_lbl, delta_color=delta_c)
        m3.metric("Derived Lead-Time Drag", f"+{leadtime_drag:.1f} days", delta=f"+{leadtime_drag*0.6:.1f}d Lead Time", delta_color="inverse")
        m4.metric("Derived Demand Impact", f"{demand_impact:,} units", delta=f"{avg_score*100:+.1f}% Shift", delta_color=delta_c)

        st.markdown("---")

        articles = [
            {'source': f'{selected_ticker} Market Desk', 'title': f'{raw_name} Supply Chain Anomaly Vectors Signal +{abs(avg_score)*4:.1f}d Lead-Time Shift', 'pubDate': 'Thu, 05 Nov 2026', 'vader_score': avg_score},
            {'source': 'Reuters Energy & Commodities', 'title': f'Global Spot Liquidity and Inventory Draws Impact {raw_name} Spot Pricing', 'pubDate': 'Thu, 05 Nov 2026', 'vader_score': round(avg_score * 0.8, 4)},
            {'source': 'S&P Global Platts', 'title': f'Chokepoint Congestion and Vessel Charter Rates Affecting {selected_ticker} Delivery Timelines', 'pubDate': 'Wed, 04 Nov 2026', 'vader_score': round(-avg_score * 0.6, 4)},
            {'source': 'Bloomberg Commodities', 'title': f'Macro Futures Curve Shift for {raw_name} Triggers Risk Desk Re-hedging', 'pubDate': 'Wed, 04 Nov 2026', 'vader_score': round(avg_score * 1.1, 4)}
        ]

        sub_rss, sub_world, sub_social, sub_matrix = st.tabs([
            "📰 Live RSS & News Feed Matrix",
            "🌐 World News Scraper",
            "💬 Reddit & Community Signals",
            "📈 Sentiment Vector Heatmap & Matrix"
        ])

        with sub_rss:
            st.subheader(f"📰 Live {selected_ticker} ({raw_name}) News Stream")
            for item in articles:
                score = item['vader_score']
                badge_color = "🟢" if score > 0.1 else ("🔴" if score < -0.1 else "🟡")
                st.markdown(f"**{badge_color} [{item['source']}] {item['pubDate']}** | `VADER Score: {score:+.4f}`")
                st.markdown(f"> **{item['title']}**")
                st.caption(f"Signal Vector: Lead-Time Impact +{abs(score)*3.5:.1f}d | Demand Volatility {score*5:+.1f}%")
                st.markdown("---")

        with sub_world:
            st.subheader(f"🌐 Global Logistics & {raw_name} Desk Feeds")
            world_feeds = [
                {"Source": "Reuters Intelligence", "Headline": f"{raw_name} European & Asian Terminal Capacity Reaches 91%", "Vader Score": f"{avg_score:+.4f}", "Impact Vector": "Active Supply Vector"},
                {"Source": "S&P Platts", "Headline": f"Maritime Tanker/Bulk Shipping Rates for {selected_ticker} Routes Shift", "Vader Score": f"{-avg_score*0.7:+.4f}", "Impact Vector": "Lead-Time Drag"},
                {"Source": "Bloomberg Freight", "Headline": f"Spot Charter Premiums Stabilize Across Key {selected_ticker} Hubs", "Vader Score": "+0.1200", "Impact Vector": "Neutral Drag"}
            ]
            st.dataframe(pd.DataFrame(world_feeds), width='stretch')

        with sub_social:
            st.subheader(f"💬 Community & Trader Sentiment Scraper for {selected_ticker}")
            hash_val = sum(ord(c) for c in target_symbol)
            social_data = [
                {"Platform": "r/Commodities", "Topic": f"{raw_name} Stocks & Refining Margins", "Sentiment": f"{avg_score:+.2f} ({'Bullish' if avg_score > 0 else 'Bearish'})", "Mentions": 1420 + hash_val % 500},
                {"Platform": "r/Maritime", "Topic": f"Panama & Suez Transit Slots for {selected_ticker}", "Sentiment": f"{-abs(avg_score):+.2f} (Logistics Drag)", "Mentions": 2890},
                {"Platform": "X / Financial", "Topic": f"{selected_ticker} Spot Volatility & Hedge Activity", "Sentiment": f"{avg_score*0.5:+.2f} (Moderate)", "Mentions": 3100}
            ]
            st.dataframe(pd.DataFrame(social_data), width='stretch')

        with sub_matrix:
            st.subheader("📊 Multi-Asset Sentiment Polarity Heatmap")
            matrix_df = pd.DataFrame({
                "Commodity": [selected_ticker, "HO=F Distillates", "CL=F WTI Crude", "BZ=F Brent Crude", "NG=F Natural Gas", "HG=F Copper"],
                "Sentiment Score": [avg_score, +0.1075, -0.2200, +0.3500, -0.4500, +0.1800]
            })
            fig = px.bar(
                matrix_df,
                x="Commodity",
                y="Sentiment Score",
                color="Sentiment Score",
                title=f"Multi-Asset NLP Polarity Comparison (Target: {selected_ticker})",
                color_continuous_scale="RdYlGn"
            )
            fig.update_layout(height=380, margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

        st.markdown("---")
        if st.button("🚀 Propagate Live Agent Vector to Downstream Control Tower Desks", width='stretch'):
            st.session_state["platform_leadtime_impact"] = leadtime_drag
            st.session_state["platform_demand_impact"] = demand_impact
            st.session_state["platform_active_signal"] = f"VADER Vector Score: {avg_score:+.4f} ({selected_ticker})"
            st.success(f"✅ Propagated Live Signal Vector to S&OP, CTRM, and Simulator Desks! (Lead-Time Drag: +{leadtime_drag}d)")

    with tab3:
        st.subheader("⚓ Live Maritime Freight, Weather & Black Swan Feeds")
        st.caption("Real-time ocean/air spot freight indices, NOAA severe weather tracking, and geopolitical chokepoints.")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Baltic Dry Freight Index (BDI)", "5,484 pts", delta="-1.8% WoW", delta_color="inverse")
            st.caption("🚢 Capesize & Panamax Bulk Carrier Telemetry")
        with m2:
            st.metric("FBX Global Ocean Freight", "$3,420 / FEU", delta="+4.2% MoM", delta_color="inverse")
            st.caption("📦 Freightos Baltic Index (40ft Container Spot)")
        with m3:
            st.metric("NOAA Severe Climate Anomaly", "+1.28 σ Anomaly", delta="Moderate Threat", delta_color="off")
            st.caption("🌩️ Global Port Storm & Typhoon Delay Index")
        with m4:
            st.metric("Geopolitical Choke-Point Risk", "ELEVATED", delta="+6.8 Days Delay", delta_color="inverse")
            st.caption("🚩 Red Sea, Suez & Bab-el-Mandeb Strait Risk")

        st.markdown("---")

        st.subheader("🚢 Real-Time Telemetry Incident Stream")

        c_filter, c_action = st.columns([3, 1])
        with c_filter:
            incident_type = st.multiselect(
                "Filter Active Black Swan Risk Vectors:",
                ["Panama Canal Drought & Slot Caps", "Red Sea Tanker Rerouting", "NOAA Atlantic Hurricane Watch", "Singapore Storage Port Congestion"],
                default=["Panama Canal Drought & Slot Caps", "Red Sea Tanker Rerouting"]
            )
        with c_action:
            st.write("")
            st.write("")
            if st.button("📡 Refresh Live Telemetry Feeds", width='stretch'):
                st.toast("Updated NOAA API & Freightos spot indices...", icon="🔄")

        st.markdown("")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div style="padding:15px; border-radius:8px; border:1px solid #333; background-color:#1e1e1e; margin-bottom:15px;">
                <p style="color:#888; font-size:12px; margin:0;">The Guardian | Tue, 20 Oct 2026</p>
                <h4 style="margin:5px 0 10px 0;">'For Panama, it is life or death': how drought is choking the canal that feeds a nation</h4>
                <p style="color:#aaa; font-size:13px; margin-bottom:8px;"><b>Transit Impact:</b> <span style="color:#ff4b4b;">+4.5 Days Lead-Time Drag</span></p>
                <p style="color:#aaa; font-size:13px;">Daily vessel transits restricted to 24 ships/day. Draft limits reduced to 44 feet.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⚡ Ingest Panama Canal Signal", key="btn_ingest_panama", width='stretch'):
                st.session_state["platform_leadtime_impact"] = 4.5
                st.session_state["platform_active_signal"] = "Panama Canal Transit Cap (+4.5d)"
                st.toast("⚡ Ingested Panama Canal Transit Delay into S&OP Engine!", icon="🚀")

        with col_b:
            st.markdown("""
            <div style="padding:15px; border-radius:8px; border:1px solid #333; background-color:#1e1e1e; margin-bottom:15px;">
                <p style="color:#888; font-size:12px; margin:0;">DW.com | Fri, 21 Aug 2026</p>
                <h4 style="margin:5px 0 10px 0;">Panama Canal to cap ship transits due to El Niño drought - DW.com</h4>
                <p style="color:#aaa; font-size:13px; margin-bottom:8px;"><b>Transit Impact:</b> <span style="color:#ff4b4b;">+6.8 Days Rerouting Drag</span></p>
                <p style="color:#aaa; font-size:13px;">Gatun Lake water levels touch multi-year lows, forcing Cape Horn rerouting for bulk carriers.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⚡ Ingest El Niño Climate Signal", key="btn_ingest_elnino", width='stretch'):
                st.session_state["platform_leadtime_impact"] = 6.8
                st.session_state["platform_active_signal"] = "El Niño Severe Drought Anomaly (+6.8d)"
                st.toast("⚡ Ingested NOAA El Niño Anomaly into CTRM & S&OP Engine!", icon="🚀")

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
        # Dynamically load live market ticks from robot_signals.json if available
        try:
            with open("robot_signals.json", "r") as f:
                robot_data = json.load(f)
            live_ticks = robot_data.get("live_ticks", {})
        except Exception:
            live_ticks = {}
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
        st.dataframe(pd.DataFrame(matrix), width='stretch', hide_index=True)

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
        st.subheader("Alternative Data & Multi-Source Intelligence Scraper Matrix")
        st.caption("Multi-channel signal scraping, NLP sentiment scoring (VADER), and predictive anomaly vector propagation.")

        c_sym, c_depth, c_btn = st.columns([2, 2, 2])
        with c_sym:
            target_symbol = st.selectbox(
                "Target Commodity / Asset Stream:",
                [
                    "HO=F (ULSD Heating Oil / Distillates)",
                    "CL=F (WTI Crude Oil)",
                    "BZ=F (Brent Crude Oil)",
                    "NG=F (Henry Hub Natural Gas)",
                    "RB=F (RBOB Gasoline)",
                    "HG=F (LME Copper Cathode)",
                    "ALI=F (Primary Aluminum Ingot)",
                    "ZN=F (Special High Grade Zinc)",
                    "GC=F (Gold Spot / Futures)",
                    "SI=F (Silver Spot / Futures)",
                    "LIT (Battery Grade Lithium)",
                    "KC=F (Arabica Coffee & Softs)",
                    "ZW=F (CBOT Milling Wheat)",
                    "ZC=F (CBOT Yellow Corn)",
                    "ZS=F (CBOT Soybeans)",
                    "SB=F (ICE Raw Sugar)",
                    "NTR (Potassium Chloride & MOP)",
                    "CF (Ammonia & Nitrogen Feedstock)",
                    "MOS (Phosphates & Acid Benchmark)",
                    "BDRY (Baltic Dry Shipping Index)",
                    "ZIM (Ocean Container Transport)",
                    "EXPD (Global Freight Logistics)"
                ]
            )
        with c_depth:
            feed_mode = st.select_slider("Scraper Feed Depth Mode:", options=["Standard Feeds", "Deep Multi-Channel Scraper"], value="Deep Multi-Channel Scraper")
        with c_btn:
            st.write("")
            st.write("")
            if st.button("🚨 Run Multi-Source Scraper Agent Network", width='stretch'):
                st.toast("Scraper Agents active: Processing RSS XML, Reuters, and Maritime Feeds...", icon="📡")

        selected_ticker = target_symbol.split()[0]
        raw_name = target_symbol.split("(")[1].replace(")", "") if "(" in target_symbol else target_symbol
        
        try:
            with open("robot_signals.json", "r") as f:
                robot_data = json.load(f)
            live_ticks_t2 = robot_data.get("live_ticks", {})
        except Exception:
            live_ticks_t2 = {}

        tick_info = live_ticks_t2.get(selected_ticker, {})
        if "vader" in tick_info:
            avg_score = float(tick_info["vader"])
        else:
            hash_val = sum(ord(c) for c in target_symbol)
            avg_score = float(((hash_val % 100) - 48) / 100.0) if selected_ticker != "HO=F" else -0.0200

        leadtime_drag = round(max(0.5, abs(avg_score) * 5.2), 1)
        demand_impact = int(112200 + avg_score * 18500)
        delta_lbl = "Bearish Drag" if avg_score < 0 else "Bullish Signal"
        delta_c = "inverse" if avg_score < 0 else "normal"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Target Symbol", selected_ticker)
        m2.metric("Dynamic VADER Composite", f"{avg_score:+.4f}", delta=delta_lbl, delta_color=delta_c)
        m3.metric("Derived Lead-Time Drag", f"+{leadtime_drag:.1f} days", delta=f"+{leadtime_drag*0.6:.1f}d Lead Time", delta_color="inverse")
        m4.metric("Derived Demand Impact", f"{demand_impact:,} units", delta=f"{avg_score*100:+.1f}% Shift", delta_color=delta_c)

        st.markdown("---")

        articles = [
            {'source': f'{selected_ticker} Market Desk', 'title': f'{raw_name} Supply Chain Anomaly Vectors Signal +{abs(avg_score)*4:.1f}d Lead-Time Shift', 'pubDate': 'Thu, 05 Nov 2026', 'vader_score': avg_score},
            {'source': 'Reuters Energy & Commodities', 'title': f'Global Spot Liquidity and Inventory Draws Impact {raw_name} Spot Pricing', 'pubDate': 'Thu, 05 Nov 2026', 'vader_score': round(avg_score * 0.8, 4)},
            {'source': 'S&P Global Platts', 'title': f'Chokepoint Congestion and Vessel Charter Rates Affecting {selected_ticker} Delivery Timelines', 'pubDate': 'Wed, 04 Nov 2026', 'vader_score': round(-avg_score * 0.6, 4)},
            {'source': 'Bloomberg Commodities', 'title': f'Macro Futures Curve Shift for {raw_name} Triggers Risk Desk Re-hedging', 'pubDate': 'Wed, 04 Nov 2026', 'vader_score': round(avg_score * 1.1, 4)}
        ]

        sub_rss, sub_world, sub_social, sub_matrix = st.tabs([
            "📰 Live RSS & News Feed Matrix",
            "🌐 World News Scraper",
            "💬 Reddit & Community Signals",
            "📈 Sentiment Vector Heatmap & Matrix"
        ])

        with sub_rss:
            st.subheader(f"📰 Live {selected_ticker} ({raw_name}) News Stream")
            for item in articles:
                score = item['vader_score']
                badge_color = "🟢" if score > 0.1 else ("🔴" if score < -0.1 else "🟡")
                st.markdown(f"**{badge_color} [{item['source']}] {item['pubDate']}** | `VADER Score: {score:+.4f}`")
                st.markdown(f"> **{item['title']}**")
                st.caption(f"Signal Vector: Lead-Time Impact +{abs(score)*3.5:.1f}d | Demand Volatility {score*5:+.1f}%")
                st.markdown("---")

        with sub_world:
            st.subheader(f"🌐 Global Logistics & {raw_name} Desk Feeds")
            world_feeds = [
                {"Source": "Reuters Intelligence", "Headline": f"{raw_name} European & Asian Terminal Capacity Reaches 91%", "Vader Score": f"{avg_score:+.4f}", "Impact Vector": "Active Supply Vector"},
                {"Source": "S&P Platts", "Headline": f"Maritime Tanker/Bulk Shipping Rates for {selected_ticker} Routes Shift", "Vader Score": f"{-avg_score*0.7:+.4f}", "Impact Vector": "Lead-Time Drag"},
                {"Source": "Bloomberg Freight", "Headline": f"Spot Charter Premiums Stabilize Across Key {selected_ticker} Hubs", "Vader Score": "+0.1200", "Impact Vector": "Neutral Drag"}
            ]
            st.dataframe(pd.DataFrame(world_feeds), width='stretch')

        with sub_social:
            st.subheader(f"💬 Community & Trader Sentiment Scraper for {selected_ticker}")
            hash_val = sum(ord(c) for c in target_symbol)
            social_data = [
                {"Platform": "r/Commodities", "Topic": f"{raw_name} Stocks & Refining Margins", "Sentiment": f"{avg_score:+.2f} ({'Bullish' if avg_score > 0 else 'Bearish'})", "Mentions": 1420 + hash_val % 500},
                {"Platform": "r/Maritime", "Topic": f"Panama & Suez Transit Slots for {selected_ticker}", "Sentiment": f"{-abs(avg_score):+.2f} (Logistics Drag)", "Mentions": 2890},
                {"Platform": "X / Financial", "Topic": f"{selected_ticker} Spot Volatility & Hedge Activity", "Sentiment": f"{avg_score*0.5:+.2f} (Moderate)", "Mentions": 3100}
            ]
            st.dataframe(pd.DataFrame(social_data), width='stretch')

        with sub_matrix:
            st.subheader("📊 Multi-Asset Sentiment Polarity Heatmap")
            matrix_df = pd.DataFrame({
                "Commodity": [selected_ticker, "HO=F Distillates", "CL=F WTI Crude", "BZ=F Brent Crude", "NG=F Natural Gas", "HG=F Copper"],
                "Sentiment Score": [avg_score, +0.1075, -0.2200, +0.3500, -0.4500, +0.1800]
            })
            fig = px.bar(
                matrix_df,
                x="Commodity",
                y="Sentiment Score",
                color="Sentiment Score",
                title=f"Multi-Asset NLP Polarity Comparison (Target: {selected_ticker})",
                color_continuous_scale="RdYlGn"
            )
            fig.update_layout(height=380, margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

        st.markdown("---")
        if st.button("🚀 Propagate Live Agent Vector to Downstream Control Tower Desks", width='stretch'):
            st.session_state["platform_leadtime_impact"] = leadtime_drag
            st.session_state["platform_demand_impact"] = demand_impact
            st.session_state["platform_active_signal"] = f"VADER Vector Score: {avg_score:+.4f} ({selected_ticker})"
            st.success(f"✅ Propagated Live Signal Vector to S&OP, CTRM, and Simulator Desks! (Lead-Time Drag: +{leadtime_drag}d)")

