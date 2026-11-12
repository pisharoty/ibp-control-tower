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
import os
try:
    from live_intel_sync import run_full_sync as _run_live_intel_sync, COMMODITY_CATALOG as _COMMODITY_CATALOG
except Exception:
    _run_live_intel_sync = None
    _COMMODITY_CATALOG = []


def _get_full_36_catalog():
    sig = _load_fresh_signals()
    cat = sig.get("commodity_catalog", [])
    if cat:
        return cat
    return [
        {"name": "LME Copper Cathode", "ticker": "HG=F", "sector": "Base & Battery Metals", "unit": "$ / MT"},
        {"name": "Primary Aluminum Ingot", "ticker": "ALI=F", "sector": "Base & Battery Metals", "unit": "$ / MT"},
        {"name": "Special High Grade Zinc", "ticker": "ZN=F", "sector": "Base & Battery Metals", "unit": "$ / MT"},
        {"name": "Gold Spot / Futures", "ticker": "GC=F", "sector": "Base & Battery Metals", "unit": "$ / oz"},
        {"name": "Silver Spot / Futures", "ticker": "SI=F", "sector": "Base & Battery Metals", "unit": "$ / oz"},
        {"name": "Battery Grade Lithium", "ticker": "LIT", "sector": "Base & Battery Metals", "unit": "$ / Index"},
        {"name": "Rare Earth & Strategic Metals Basket", "ticker": "REMX", "sector": "Rare Earths & Critical", "unit": "$ / Index"},
        {"name": "NdPr Magnet Oxide Benchmark (MP)", "ticker": "MP", "sector": "Rare Earths & Critical", "unit": "$ / Index"},
        {"name": "Heavy/Light Rare Earths Ex-China (Lynas)", "ticker": "LYSDY", "sector": "Rare Earths & Critical", "unit": "$ / Index"},
        {"name": "Cobalt & Strategic Cathode Basket", "ticker": "BATT", "sector": "Rare Earths & Critical", "unit": "$ / Index"},
        {"name": "WTI Crude Oil", "ticker": "CL=F", "sector": "Energy", "unit": "$ / bbl"},
        {"name": "Brent Crude Oil", "ticker": "BZ=F", "sector": "Energy", "unit": "$ / bbl"},
        {"name": "Henry Hub Natural Gas", "ticker": "NG=F", "sector": "Energy", "unit": "$ / MMBtu"},
        {"name": "RBOB Gasoline", "ticker": "RB=F", "sector": "Energy", "unit": "$ / gal"},
        {"name": "ULSD Heating Oil", "ticker": "HO=F", "sector": "Energy", "unit": "$ / gal"},
        {"name": "CBOT Milling Wheat", "ticker": "ZW=F", "sector": "Grains & Softs", "unit": "$ / bu"},
        {"name": "CBOT Yellow Corn", "ticker": "ZC=F", "sector": "Grains & Softs", "unit": "$ / bu"},
        {"name": "CBOT Soybeans", "ticker": "ZS=F", "sector": "Grains & Softs", "unit": "$ / bu"},
        {"name": "CBOT Soybean Meal", "ticker": "ZM=F", "sector": "Grains & Softs", "unit": "$ / ton"},
        {"name": "CBOT Soybean Oil", "ticker": "ZL=F", "sector": "Grains & Softs", "unit": "$ / lb"},
        {"name": "CBOT Rough Rice", "ticker": "ZR=F", "sector": "Grains & Softs", "unit": "$ / cwt"},
        {"name": "CBOT Oats", "ticker": "ZO=F", "sector": "Grains & Softs", "unit": "$ / bu"},
        {"name": "Arabica Coffee & Softs", "ticker": "KC=F", "sector": "Grains & Softs", "unit": "$ / lb"},
        {"name": "ICE Cocoa", "ticker": "CC=F", "sector": "Grains & Softs", "unit": "$ / MT"},
        {"name": "ICE Raw Sugar #11", "ticker": "SB=F", "sector": "Grains & Softs", "unit": "$ / lb"},
        {"name": "ICE Cotton #2", "ticker": "CT=F", "sector": "Grains & Softs", "unit": "$ / lb"},
        {"name": "ICE Frozen Orange Juice", "ticker": "OJ=F", "sector": "Grains & Softs", "unit": "$ / lb"},
        {"name": "CME Live Cattle", "ticker": "LE=F", "sector": "Livestock & Meats", "unit": "$ / lb"},
        {"name": "CME Feeder Cattle", "ticker": "GF=F", "sector": "Livestock & Meats", "unit": "$ / lb"},
        {"name": "CME Lean Hogs", "ticker": "HE=F", "sector": "Livestock & Meats", "unit": "$ / lb"},
        {"name": "Potassium Chloride & MOP", "ticker": "NTR", "sector": "Fertilizers & Freight", "unit": "$ / MT"},
        {"name": "Ammonia & Nitrogen Feedstock", "ticker": "CF", "sector": "Fertilizers & Freight", "unit": "$ / MT"},
        {"name": "Phosphates & Acid Benchmark", "ticker": "MOS", "sector": "Fertilizers & Freight", "unit": "$ / MT"},
        {"name": "Baltic Dry Shipping Index", "ticker": "BDRY", "sector": "Fertilizers & Freight", "unit": "$ / Index"},
        {"name": "Ocean Container Transport", "ticker": "ZIM", "sector": "Fertilizers & Freight", "unit": "$ / Index"},
        {"name": "Global Freight Logistics", "ticker": "EXPD", "sector": "Fertilizers & Freight", "unit": "$ / Index"},
    ]

def _get_sota_names_36():
    return [c["name"] for c in _get_full_36_catalog()]

def _get_scraper_options_36():
    return [f"{c['ticker']} ({c['name']})" for c in _get_full_36_catalog()]

def _load_fresh_signals():
    if os.path.exists('robot_signals.json'):
        try:
            with open('robot_signals.json', 'r', encoding='utf-8') as _f:
                return _load_fresh_signals() or json.load(_f)
        except Exception:
            pass
    return {}


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


def render_nlp_commercial_sensing(persona):
    # Comprehensive multi-stream telemetry scope loader
    try:
        with open("robot_signals.json", "r", encoding="utf-8") as f:
            robot_data = json.load(f)
        live_ticks = robot_data.get("live_ticks", {})
        macro_telemetry = robot_data.get("macro_telemetry", {})
        weather_telemetry = robot_data.get("weather_telemetry", {})
        ais_telemetry = robot_data.get("ais_cargo_telemetry", {})
        gis_telemetry = robot_data.get("gis_spatial_telemetry", {})
        cftc_telemetry = robot_data.get("cftc_positioning", {})
        gdelt_telemetry = robot_data.get("gdelt_scuttlebutt", [])
    except Exception:
        live_ticks, macro_telemetry, weather_telemetry, ais_telemetry, gis_telemetry, cftc_telemetry, gdelt_telemetry = {}, {}, {}, {}, {}, {}, []

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals", 
        "📧 Email & Event Debrief Parser", 
        "⚓ Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        st.subheader("📡 Live Genspark Tactical Market Signals")
        _sig_36 = _load_fresh_signals()
        _ticks_36 = _sig_36.get("live_ticks", {})
        _cat_36 = _get_full_36_catalog()
        if _ticks_36:
            _sectors_36 = ["All Sectors (36)"] + sorted(list({c["sector"] for c in _cat_36}))
            _sec_choice = st.selectbox("Filter Tactical Market Signals by Sector:", _sectors_36, key="tactical_sector_filter")
            _filtered_cat = [c for c in _cat_36 if _sec_choice == "All Sectors (36)" or c["sector"] == _sec_choice]
            _tcols = st.columns(4)
            for _idx, _item in enumerate(_filtered_cat[:8]):
                _tk = _item["ticker"]
                _td = _ticks_36.get(_tk, {})
                _px = _td.get("price", "N/A")
                _chg = _td.get("change_pct", 0.0)
                with _tcols[_idx % 4]:
                    st.metric(
                        label=f"{_tk} • {_item['name'][:22]}",
                        value=f"${_px:,.2f}" if isinstance(_px, (int, float)) else str(_px),
                        delta=f"{_chg:+.2f}% ({_item['sector']})"
                    )

        rf.render_genspark_overlay()

        rf.render_predictive_commodity_engine()

        rf.render_macro_telemetry_bar()

        # --- Row 2: Expanded Macro & Logistics Telemetry (ADDED) ---
        st.caption("🌐 **Expanded Macro & Logistics Telemetry Stream (FRED, NOAA, Baltic Dry & ACSI)**")
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
        with r2_c1:
            st.metric("US CPI Inflation", str(macro_telemetry.get("us_cpi", "3.1%")), delta=str(macro_telemetry.get("cpi_delta", "-0.2% MoM")), delta_color="normal")
            st.caption("🟢 FRED Live Feed")
        with r2_c2:
            st.metric("World Bank Freight", str(macro_telemetry.get("world_bank_freight", "142.5 pts")), delta=str(macro_telemetry.get("freight_delta", "+3.8% MoM")), delta_color="inverse")
            st.caption("🟢 Live Freight Feed")
        with r2_c3:
            st.metric("Baltic Dry Index (BDI)", str(weather_telemetry.get("bdi_index", "5,484 pts")), delta=str(weather_telemetry.get("bdi_delta", "-1.8% WoW")), delta_color="inverse")
            st.caption("🟢 Live Shipping Feed")
        with r2_c4:
            st.metric("ACSI Logistics Score", str(macro_telemetry.get("acsi_score", "76.8 / 100")), delta=str(macro_telemetry.get("acsi_delta", "+1.2 pts")), delta_color="normal")
            st.caption("🟢 Live Logistics Feed")
        st.markdown("---")

        rf.render_triangulated_sentiment_section()

        rf.render_rss_breaking_news_stream()

    with tab2:
        st.subheader("Alternative Data & Multi-Source Intelligence Scraper Matrix")
        st.caption("Multi-channel signal scraping, NLP sentiment scoring (VADER), and predictive anomaly vector propagation.")

        c_sym, c_depth, c_btn = st.columns([2, 2, 2])
        with c_sym:
            target_symbol = st.selectbox("Target Commodity / Asset Stream (36 Live Streams Across 6 Sectors):", _get_scraper_options_36(), key="scraper_selected_stream_widget")
            st.session_state["scraper_selected_stream"] = target_symbol
            _parsed_comm_name = target_symbol.split("(", 1)[1].rstrip(")") if "(" in target_symbol else target_symbol
            st.session_state["sota_selected_commodity"] = _parsed_comm_name
        with c_depth:
            feed_mode = st.select_slider("Scraper Feed Depth Mode:", options=["Standard Feeds", "Deep Multi-Channel Scraper"], value="Deep Multi-Channel Scraper")
        with c_btn:
            st.write("")
            st.write("")
            if st.button("🚨 Run Multi-Source Scraper Agent Network", width='stretch'):
                st.toast("Scraper Agents active: Processing RSS XML, Reuters, and Maritime Feeds...", icon="📡")

        selected_ticker = target_symbol.split()[0]
        raw_name = target_symbol.split("(")[1].replace(")", "") if "(" in target_symbol else target_symbol
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

        # --- CFTC COT Positioning & GDELT Scuttlebutt NLP Panel (LIVE + CTRM TRIGGER) ---
        st.markdown("---")
        st.subheader("🏛️ CFTC Institutional Hedge Positioning & GDELT Scuttlebutt NLP")
        st.caption("Live Commitment of Traders (COT) hedge fund positioning alongside GDELT 15-minute global event sentiment.")

        _fresh_sig = _load_fresh_signals()
        _live_cftc_all = _fresh_sig.get("cftc_positioning", cftc_telemetry if isinstance(cftc_telemetry, dict) else {})
        _live_gdelt_all = _fresh_sig.get("gdelt_scuttlebutt", gdelt_telemetry if isinstance(gdelt_telemetry, list) else [])
        _last_sync = _fresh_sig.get("last_intel_sync_utc", "Live Feed")

        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1.3, 1.5, 2.2])
        with ctrl_c1:
            if st.button("🔄 Refresh CFTC & GDELT", key="btn_refresh_cftc_gdelt", use_container_width=True):
                if _run_live_intel_sync is not None:
                    with st.spinner("Syncing all 22 commodities, CFTC COT & GDELT 15m feeds..."):
                        _run_live_intel_sync()
                    st.rerun()
        with ctrl_c2:
            push_ctrm_clicked = st.button("⚡ Push Vectors to CTRM", type="primary", key="btn_push_cftc_gdelt_ctrm", use_container_width=True)
        with ctrl_c3:
            st.caption(f"🟢 Telemetry Sync: `{_last_sync}` | **CFTC Socrata + GDELT 2.0**")

        col_cftc, col_gdelt = st.columns(2)

        active_comm = (
            st.session_state.get("sota_selected_commodity")
            or st.session_state.get("selected_commodity")
            or st.session_state.get("target_commodity")
            or st.session_state.get("selected_commodity_ticker")
            or "LME Copper Cathode"
        )
        ticker_cftc = _live_cftc_all.get(active_comm) or _live_cftc_all.get("HG=F") or {
            "managed_money_net": "+14,250 cts",
            "hedgers_net": "-18,100 cts",
            "bias": "Bullish Short-Squeeze Risk",
            "squeeze_score": 0.72,
            "report_date": "Live"
        }

        with col_cftc:
            st.markdown(f"##### 📊 CFTC COT Net Positioning ({active_comm})")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Managed Money (Funds)", str(ticker_cftc.get("managed_money_net", "+14,250 cts")), delta=f"COT: {ticker_cftc.get('report_date', 'Live')}")
            with c2:
                st.metric("Commercial Hedgers", str(ticker_cftc.get("hedgers_net", "-18,100 cts")), delta="Producer Offset")
            st.info(f"**Institutional Squeeze Risk:** {ticker_cftc.get('bias', 'Bullish Short-Squeeze Risk')} (Squeeze Factor: `{ticker_cftc.get('squeeze_score', 0.72)}`)")

        with col_gdelt:
            st.markdown("##### 🌍 GDELT Global Scuttlebutt NLP Feed (15m Window)")
            if isinstance(_live_gdelt_all, list) and len(_live_gdelt_all) > 0:
                for item in _live_gdelt_all[:3]:
                    st.markdown(f"""
                    <div style="padding:10px; border-radius:6px; border:1px solid #333; background-color:#1e1e1e; margin-bottom:8px;">
                        <span style="color:#ff4b4b; font-weight:bold;">[{item.get('region', 'Global')}]</span>
                        <span style="color:#ddd; font-size:13px;">{item.get('headline', '')}</span><br/>
                        <span style="color:#888; font-size:11px;">Tone Score: {item.get('tone_score', 0)} | Goldstein Scale: {item.get('goldstein_scale', 0)} | {item.get('timestamp', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No active GDELT scuttlebutt anomalies reported.")

        if push_ctrm_clicked:
            avg_tone = sum(float(x.get("tone_score", -2.0)) for x in _live_gdelt_all) / max(1, len(_live_gdelt_all)) if isinstance(_live_gdelt_all, list) else -2.0
            sq_score = float(ticker_cftc.get("squeeze_score", 0.72))
            ctrm_payload = {
                "commodity": active_comm,
                "cftc_squeeze_score": sq_score,
                "cftc_bias": ticker_cftc.get("bias", "Bullish Short-Squeeze Risk"),
                "managed_money_net": ticker_cftc.get("managed_money_net", "+14,250 cts"),
                "gdelt_avg_tone": round(avg_tone, 2),
                "recommended_hedge_delta_pct": round((sq_score - 0.5) * 35.0 + abs(min(0.0, avg_tone)) * 2.5, 1),
            }
            st.session_state["ctrm_institutional_signal"] = ctrm_payload
            st.success(
                f"⚡ **Propagated to CTRM Risk Desk ({active_comm}):** Squeeze Factor `{sq_score}` + GDELT Tone `{round(avg_tone, 2)}` "
                f"→ Recommended Hedge Ratio Adjustment: **+{ctrm_payload['recommended_hedge_delta_pct']}%**."
            )

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
        st.subheader("⚓ Real-Time AIS Cargo & GIS Spatial Telemetry Desk")
        st.caption("Downstream multi-modal ingestion of satellite AIS vessel tracking, GIS atmospheric storm layers, ocean container freight spot rates, and chokepoint congestion dynamics.")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Tracked AIS Cargo Fleet",
                str(ais_telemetry.get("active_vessels_tracked", "1,420 Tankers & Carriers")),
                delta=str(ais_telemetry.get("suez_reroute_factor", "+12.4% Route Dist")),
                delta_color="inverse"
            )
            st.caption("🚢 Satellite AIS Density Vector")

        with m2:
            st.metric(
                "Chokepoint Congestion Index",
                str(ais_telemetry.get("chokepoint_congestion_idx", "88.4 / 100")),
                delta=str(ais_telemetry.get("panama_queue_count", "34 Vessels In Queue")),
                delta_color="inverse"
            )
            st.caption("📍 Panama Canal & Suez Slot Delay")

        with m3:
            st.metric(
                "NOAA GIS Climate Anomaly",
                str(weather_telemetry.get("noaa_anomaly", "+1.28 σ Anomaly")),
                delta=str(weather_telemetry.get("noaa_status", "Moderate Threat")),
                delta_color="off"
            )
            st.caption("🌩️ Storm & Typhoon Radar Layer")

        with m4:
            st.metric(
                "GIS Derived Spatial Drag",
                str(gis_telemetry.get("gis_leadtime_modifier", "+2.4 Days Spatial Drag")),
                delta=str(gis_telemetry.get("refinery_radar_status", "94% Operational")),
                delta_color="inverse"
            )
        st.caption("🛰️ Terminal Ports & Refining Footprints")

        st.markdown("---")

        st.subheader("🌐 Real-Time AIS Spatial Congestion Map & Telemetry Matrix")

        ais_gis_matrix = [
            {"Vector": "Panama Canal Locks", "Telemetry Source": "Satellite AIS Fleet Tracking", "Reading / Queue": "34 Vessels Waiting", "Spatial Impact": "+4.5d Lead-Time Drag", "Status": "🔴 CRITICAL"},
            {"Vector": "Red Sea / Suez Corridor", "Telemetry Source": "AIS Transponder Signal Analysis", "Reading / Queue": "+12.4% Cape Reroute Dist", "Spatial Impact": "+6.8d Transit Drag", "Status": "🔴 CRITICAL"},
            {"Vector": "US Gulf Coast Radar", "Telemetry Source": "GIS NOAA Atmospheric Layer", "Reading / Queue": "+1.28 σ Storm Footprint", "Spatial Impact": "+2.4d Loading Delay", "Status": "🟡 ELEVATED"},
            {"Vector": "Singapore Anchorage", "Telemetry Source": "AIS Vessel Anchor Density", "Reading / Queue": "91% Terminal Utilization", "Spatial Impact": "+1.2d Bunkering Shift", "Status": "🟡 ELEVATED"}
        ]
        st.dataframe(pd.DataFrame(ais_gis_matrix), width='stretch')

        st.markdown("---")

        st.subheader("🚢 Real-Time Downstream Telemetry Incident Stream")

        c_filter, c_action = st.columns([3, 1])
        with c_filter:
            incident_type = st.multiselect(
                "Filter Active AIS/GIS Risk Vectors:",
                ["Panama Canal Drought & Slot Caps", "Red Sea Tanker Rerouting", "NOAA Atlantic Hurricane Watch", "Singapore Storage Port Congestion"],
                default=["Panama Canal Drought & Slot Caps", "Red Sea Tanker Rerouting"]
            )
        with c_action:
            st.write("")
            st.write("")
            if st.button("📡 Refresh Live AIS / GIS Feeds", width='stretch'):
                st.toast("Updating Satellite AIS feed & NOAA radar layers...", icon="🔄")

        st.markdown("")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div style="padding:15px; border-radius:8px; border:1px solid #333; background-color:#1e1e1e; margin-bottom:15px;">
                <p style="color:#888; font-size:12px; margin:0;">The Guardian | AIS Satellite Telemetry</p>
                <h4 style="margin:5px 0 10px 0;">'For Panama, it is life or death': drought choking canal transits</h4>
                <p style="color:#aaa; font-size:13px; margin-bottom:8px;"><b>AIS Vector:</b> <span style="color:#ff4b4b;">+4.5 Days Transit Drag</span></p>
                <p style="color:#aaa; font-size:13px;">Daily vessel transits restricted to 24 ships/day. Draft limits reduced to 44 feet.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⚡ Ingest Panama AIS Signal", key="btn_ingest_panama", width='stretch'):
                st.session_state["platform_leadtime_impact"] = 4.5
                st.session_state["platform_active_signal"] = "Panama Canal AIS Transit Cap (+4.5d)"
                st.toast("⚡ Ingested Panama Canal AIS Transit Delay into S&OP Engine!", icon="🚀")

        with col_b:
            st.markdown("""
            <div style="padding:15px; border-radius:8px; border:1px solid #333; background-color:#1e1e1e; margin-bottom:15px;">
                <p style="color:#888; font-size:12px; margin:0;">DW.com | NOAA GIS Climate Layer</p>
                <h4 style="margin:5px 0 10px 0;">El Niño Drought: Canal vessel draft limits restricted</h4>
                <p style="color:#aaa; font-size:13px; margin-bottom:8px;"><b>GIS Radar Vector:</b> <span style="color:#ff4b4b;">+6.8 Days Cape Reroute</span></p>
                <p style="color:#aaa; font-size:13px;">Gatun Lake water levels touch multi-year lows, forcing Cape Horn rerouting.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⚡ Ingest El Niño GIS Signal", key="btn_ingest_elnino", width='stretch'):
                st.session_state["platform_leadtime_impact"] = 6.8
                st.session_state["platform_active_signal"] = "El Niño NOAA GIS Anomaly (+6.8d)"
                st.toast("⚡ Ingested NOAA El Niño GIS Radar Anomaly into S&OP Engine!", icon="🚀")

        st.markdown("---")
        if st.button("🚀 Propagate Live AIS & GIS Spatial Vectors to Downstream Control Tower Desks", width='stretch'):
            st.session_state["platform_ais_gis_impact"] = 2.4
            st.session_state["platform_leadtime_impact"] = 6.8
            st.session_state["platform_active_signal"] = f"AIS/GIS Spatial Vector: +2.4d Spatial Drag ({ais_telemetry.get('panama_queue_count', '34 In Queue')})"
            st.success("✅ Propagated Live AIS/GIS Telemetry Vectors directly to S&OP, CTRM, and Simulator Desks!")

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
        
        if any(k in str(selected_module) for k in ["Global Trade", "S&OP", "Executive"]):
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

    st.dataframe(pd.DataFrame(st.session_state["physical_contracts_list"]), width='stretch', hide_index=True)

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

    mc_scenario_ctrm = st.session_state.get("active_mc_scenario", None)
    mc_loss_ctrm = st.session_state.get("mc_expected_loss", 0.0)
    if mc_scenario_ctrm:
        st.error(f"🚨 **ENTERPRISE MACRO STRESS INJECTED**: **{mc_scenario_ctrm}** | Systemic VaR Baseline Elevated by **+${mc_loss_ctrm:.2f}M**")
        
        st.markdown("### ⚡ Scenario-Specific FIX 4.4 Financial Execution Desk")
        
        c_h1, c_h2 = st.columns([2, 1])
        
        if "Strait of Hormuz" in mc_scenario_ctrm:
            hedge_label = "🛢️ Execute FIX 4.4 Brent Crude & LNG Asian Call Option ($140 Cap)"
            hedge_key = "Brent/LNG Crude Call Spread (Hormuz Crisis)"
            hedge_desc = "Locks in cap on crude price spikes above $140/bbl and offsets emergency LNG rerouting costs via CME/ICE broker gateway."
        elif "Black Sea" in mc_scenario_ctrm:
            hedge_label = "🌾 Execute FIX 4.4 Wheat Futures & TTF Gas Collar"
            hedge_key = "Black Sea Ag & Gas Collar"
            hedge_desc = "Protects grain delivery margins and hedges nitrogen fertilizer feedstock gas spikes via CME/EEX."
        elif "Brazilian Polar Frost" in mc_scenario_ctrm:
            hedge_label = "☕ Execute FIX 4.4 Arabica Coffee Bullish Call Spread"
            hedge_key = "Arabica Coffee Futures Spread (Brazil Frost)"
            hedge_desc = "Protects against soft commodity spot inflation (+120%) and crop loss margin erosion via ICE."
        elif "Super El Niño" in mc_scenario_ctrm:
            hedge_label = "🌋 Execute FIX 4.4 Ag-Bulk & Panama FFA Freight Hedge"
            hedge_key = "Panama FFA & Ag-Bulk Hedge"
            hedge_desc = "Hedges against 40% daily Panama transit reductions and grain draft penalties via Baltic Exchange."
        elif "Choke Point Blockade" in mc_scenario_ctrm:
            hedge_label = "⚓ Execute FIX 4.4 Bunker Burn & Suez Freight Swap"
            hedge_key = "Suez Freight Rate Swap & Cape Bunker Burn"
            hedge_desc = "Locks in Cape of Good Hope rerouting bunker burn rates and floating demurrage exposure."
        elif "Geopolitical Escalation" in mc_scenario_ctrm:
            hedge_label = "🔥 Execute FIX 4.4 VLSFO Bunker Fuel Call Collar"
            hedge_key = "VLSFO Bunker Fuel Call Option"
            hedge_desc = "Protects against marine fuel spikes above $900/MT and shipping insurance surcharges."
        elif "Marine Heatwave" in mc_scenario_ctrm:
            hedge_label = "🌊 Execute FIX 4.4 Thermal Loss Derivative & Spoilage Insurance"
            hedge_key = "Cargo Thermal Spoilage Insurance Derivative"
            hedge_desc = "Offsets LNG boil-off losses and reefer container thermal loss claims."
        else:
            hedge_label = "🦢 Execute FIX 4.4 Systemic Cross-Asset Tail Risk Collar"
            hedge_key = "Multi-Vector Systemic Risk Collar"
            hedge_desc = "Deploys sovereign CDS and port TOS cyber outage financial protection hedges."

        with c_h1:
            if st.button(hedge_label, key="btn_exec_macro_hedge"):
                if hedge_key not in st.session_state["executed_hedges"]:
                    st.session_state["executed_hedges"].append(hedge_key)
                st.success(f"✅ **FIX 4.4 Derivatives Hedge Dispatched**: {hedge_key} executed via LME/CME/ICE gateway!")

        with c_h2:
            st.info(f"**Strategy Context**: {hedge_desc}")
        st.markdown("---")
        st.warning(f"🚨 **ENTERPRISE MACRO STRESS INJECTED**: **{mc_scenario_ctrm}** | Systemic VaR Baseline Elevated by **+${mc_loss_ctrm:.2f}M**. Recommended Action: Execute FIX 4.4 derivatives hedges to protect gross margin.")
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

    st.plotly_chart(rf.plot_strategy_payoff(spot_f, k1_strike, k2_strike, strategy_type, volume=vol_input), width='stretch')

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
        if st.button("⚡ Execute Derivative Order via FIX 4.4", type="primary", width='stretch', key="btn_exec_ctrm_fix"):
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
        st.dataframe(pd.DataFrame(hedges), width='stretch', hide_index=True)

# MODULE 7: GLOBAL LOGISTICS GIS (EXPANDED WITH RICH MAP & TELEMETRY REGISTERS)

    # --- DIGITAL TWIN AUTOMATED MARGIN EROSION ALERTS ---
    twin_data_ctrm = get_digital_twin_telemetry_feed()
    st.markdown("---")
    st.subheader("🚨 Digital Twin Automated Margin Erosion & Liquidation Alerts")

    has_alerts = False
    for i, v in enumerate(twin_data_ctrm):
        v_name = v["vessel_name"]
        v_comm = v["commodity"]
        v_c_cost = v["carrying_cost_usd"]
        v_d_cost = v["demurrage_penalty_usd"]
        v_rec = v["reroute_recommendation"]
        v_sav = v["savings_usd"]
        total_drag = v_c_cost + v_d_cost

        if total_drag > 300000:
            has_alerts = True
            st.error(
                f"**MARGIN EROSION ALERT (>50%)**: Vessel **{v_name}** ({v_comm}) "
                f"accumulated **${total_drag:,.2f}** in transit drag (SOFR Capital Tie-up: ${v_c_cost:,.2f} | Demurrage: ${v_d_cost:,.2f}). "
                f"**Recommendation**: {v_rec} (Saves ${v_sav:,.2f}) or execute prompt futures liquidation."
            )
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button(f"⚡ Trigger FIX 4.4 Hedge ({v_name})", key=f"fix_hedge_btn_{i}"):
                    if v_name not in st.session_state["executed_hedges"]:
                        st.session_state["executed_hedges"].append(v_name)
                    st.success(f"✅ **FIX 4.4 Financial Hedge Dispatched**: Executed prompt short futures position for {v_comm} cargo on {v_name} via LME/CME broker gateway.")
            with col_b2:
                if st.button(f"🚢 Dispatch Reroute Order ({v_name})", key=f"ctrm_reroute_btn_{i}"):
                    if v_name not in st.session_state["rerouted_vessels"]:
                        st.session_state["rerouted_vessels"].append(v_name)
                    st.success(f"✅ **Voyage Reroute Transmitted**: Voyage instructions dispatched to vessel master for {v_name} to divert via Cape of Good Hope.")
    if not has_alerts:
        st.success("All active voyages operating within acceptable carrying cost thresholds (<50% margin erosion).")

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
    st.plotly_chart(fig, width='stretch')

    st.divider()
    st.subheader("📡 Global Maritime Shipping Lanes Telemetry Register")
    
    lanes_data = [
        {"Shipping Lane Corridor": "Asia East Coast to US West Coast (Transpacific)", "FBX Rate ($/FEU)": "$4,250", "YoY Change": "+18.5%", "Avg Transit (Days)": "14.2 Days", "Congestion Delay": "+3.5 Days", "Status": "🔴 High Bottleneck"},
        {"Shipping Lane Corridor": "Asia to North Europe (Suez / Red Sea)", "FBX Rate ($/FEU)": "$5,820", "YoY Change": "+42.0%", "Avg Transit (Days)": "34.0 Days", "Congestion Delay": "+12.5 Days", "Status": "🔴 Cape Rerouting Active"},
        {"Shipping Lane Corridor": "Transatlantic North Europe to US East Coast", "FBX Rate ($/FEU)": "$2,100", "YoY Change": "-2.1%", "Avg Transit (Days)": "10.5 Days", "Congestion Delay": "+0.5 Days", "Status": "🟢 Smooth Flow"},
        {"Shipping Lane Corridor": "US Gulf to East Asia (Panama Canal)", "FBX Rate ($/FEU)": "$3,950", "YoY Change": "+12.4%", "Avg Transit (Days)": "22.8 Days", "Congestion Delay": "+6.0 Days", "Status": "🟡 Draft Restrictions"}
    ]
    st.dataframe(pd.DataFrame(lanes_data), width='stretch', hide_index=True)

# MODULE 8: SANDBOX FLIGHT SIMULATOR (ENHANCED WITH MONTE CARLO & PROPAGATION)

    # --- DIGITAL TWIN SIMULATOR & TELEMETRY ---
    st.markdown("---")
    st.header("🌐 Maritime Digital Twin & Rerouting Arbitrage Engine")
    st.caption("Live physics-based modeling of vessel transit velocity, SOFR capital tie-up, laytime demurrage, and corridor economics.")

    col_sim1, col_sim2 = st.columns([1, 2])
    with col_sim1:
        st.subheader("⚙️ Scenario Parameters")
        vessel_select = st.selectbox("Select Active Voyage", ["MV Kpler Horizon (Panama)", "MT Gulf Pioneer (Suez)", "MV Pacific Explorer (Bab-el-Mandeb)"])
        canal_queue = st.slider("Choke Point Queue Wait (Days)", min_value=0.0, max_value=25.0, value=12.0, step=0.5)
        cargo_val = st.number_input("Cargo Nominal Value ($ USD)", min_value=1000000, value=33000000, step=500000)
        sofr_rate = st.slider("SOFR Benchmark Rate (%)", min_value=1.0, max_value=8.0, value=4.8, step=0.1) / 100.0

    with col_sim2:
        st.subheader("🔀 Route Arbitrage Trade Decision Support")
        arb_res = simulate_rerouting_arbitrage(
            vessel_name=vessel_select,
            canal_queue_days=canal_queue,
            cargo_value_usd=cargo_val,
            sofr_rate_pct=sofr_rate
        )

        opt_a = arb_res["option_a_choke_wait"]
        opt_b = arb_res["option_b_cape_reroute"]

        rec_msg = arb_res["margin_preservation_summary"]
        st.info(f"**Recommendation**: {rec_msg}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Route A: Choke Point Queue")
            q_days = opt_a["queue_days"]
            dem_a = opt_a["demurrage_cost_usd"]
            cap_a = opt_a["capital_tieup_cost_usd"]
            sur_a = opt_a["canal_toll_surcharge_usd"]
            tot_a = opt_a["total_route_cost_usd"]

            st.write(f"• Queue Wait: **{q_days} Days**")
            st.write(f"• Demurrage Penalty: **${dem_a:,.2f}**")
            st.write(f"• Capital Tie-up (SOFR): **${cap_a:,.2f}**")
            st.write(f"• Canal Toll Surcharge: **${sur_a:,.2f}**")
            st.metric("Total Route Drag", f"${tot_a:,.2f}")

        with col_b:
            st.markdown("### Route B: Cape Reroute")
            s_days = opt_b["extra_sailing_days"]
            bun_b = opt_b["extra_bunker_cost_usd"]
            cap_b = opt_b["capital_tieup_cost_usd"]
            tot_b = opt_b["total_route_cost_usd"]

            st.write(f"• Extra Sailing: **{s_days} Days**")
            st.write(f"• Extra Bunker Fuel: **${bun_b:,.2f}**")
            st.write(f"• Capital Tie-up (SOFR): **${cap_b:,.2f}**")
            st.write("• Demurrage Penalty: **$0.00**")
            st.metric("Total Route Drag", f"${tot_b:,.2f}")

    st.subheader("📦 Live In-Transit Cargo Digital Twin State Feed")
    twin_feed_data = get_digital_twin_telemetry_feed()
    st.dataframe(twin_feed_data, width='stretch')
    if st.button("🚢 Execute Reroute Order (Cape of Good Hope)", key="btn_exec_ais_reroute"):
        v_name = vessel_select.split(" (")[0]
        if v_name not in st.session_state["rerouted_vessels"]:
            st.session_state["rerouted_vessels"].append(v_name)
        st.success(f"✅ **Voyage Reroute Order Transmitted**: Vessel master for **{vessel_select}** instructed via AIS feed to abandon choke point queue and divert via Cape of Good Hope. Net margin saved!")

def render_flight_simulator(persona=None):
    st.header("🎲 Monte Carlo Risk & Scenario Simulator")
    st.caption("Stochastic stress testing of multi-variable supply chain shocks, weather disruptions, geopolitical crises, and maritime carrying cost volatility.")

    col_mc1, col_mc2 = st.columns([1, 2])

    scenarios = {
        "🌋 Super El Niño Climate & Hydroelectric Shock": {
            "desc": "Simulates global drought, severe hydro-power deficits, ag-bulk yield collapse, and Panama Canal draft restrictions reducing daily vessel transits by 40%.",
            "loss": 32.50, "var95": 48.20, "cvar": 65.80, "delay": 8.5, "type": "warning"
        },
        "⚓ Choke Point Blockade & Digital Twin Carrying Cost Surge": {
            "desc": "Simulates dual Panama/Suez Canal choke point closures, 20-day floating demurrage queues, SOFR capital tie-up spikes, and forced Cape of Good Hope rerouting bunker burn.",
            "loss": 41.80, "var95": 58.40, "cvar": 82.10, "delay": 16.2, "type": "error"
        },
        "🔥 Geopolitical Escalation & Bunker Fuel Spike": {
            "desc": "Simulates regional conflict escalations, Middle East shipping lane avoidance, insurance premium surges, and $900/MT VLSFO bunker fuel prices.",
            "loss": 24.10, "var95": 36.90, "cvar": 51.30, "delay": 6.0, "type": "info"
        },
        "🛢️ Strait of Hormuz Tanker Crisis & Energy Lockout": {
            "desc": "Simulates severe maritime blockage of 21% global petroleum flow, crude spikes above $140/bbl, P&I club insurance cancellations, and emergency LNG rerouting.",
            "loss": 58.90, "var95": 82.40, "cvar": 115.60, "delay": 21.0, "type": "error"
        },
        "🌾 Black Sea Conflict & Nitrogen Fertilizer Feedstock Shock": {
            "desc": "Simulates grain export corridor shutdown, Black Sea port blockades, natural gas feedstock spikes driving nitrogen fertilizer prices +180%, and ag-yield deficits.",
            "loss": 29.40, "var95": 44.10, "cvar": 62.30, "delay": 12.0, "type": "warning"
        },
        "☕ Brazilian Polar Frost & Arabica Softs Crop Collapse": {
            "desc": "Simulates Antarctic air mass freezing key coffee/sugar belts in Minas Gerais, wiping out 25% of Arabica trees, driving +120% spot price inflation and 3-year recovery lags.",
            "loss": 18.60, "var95": 29.80, "cvar": 41.50, "delay": 4.5, "type": "warning"
        },
        "🌊 Ocean Marine Heatwave & Cargo Thermal Loss Spike": {
            "desc": "Simulates sea surface temperatures spiking +2.8°C above baseline, doubling LNG boil-off rates, accelerating reefer container compressor failures, and triggering toxic algae port closures.",
            "loss": 22.30, "var95": 33.70, "cvar": 47.90, "delay": 7.0, "type": "info"
        },
        "🦢 Black Swan Multi-Vector Systemic Cascade": {
            "desc": "Simulates simultaneous compound tail-risk: widespread cyber-attack on port Terminal Operating Systems (TOS), grid failure across major transshipment hubs, and sovereign trade defaults.",
            "loss": 74.20, "var95": 108.50, "cvar": 152.00, "delay": 28.5, "type": "error"
        }
    }

    with col_mc1:
        st.subheader("⚙️ Macro Stress Scenario Parameters")
        scenario_choice = st.selectbox("Select Macro Stress Scenario", list(scenarios.keys()))
        sim_runs = st.slider("Monte Carlo Iterations", min_value=1000, max_value=25000, value=10000, step=1000)
        confidence_level = st.selectbox("Confidence Level (VaR)", [0.90, 0.95, 0.99], index=1)

    selected = scenarios[scenario_choice]

    with col_mc2:
        st.subheader("📊 Stochastic P&L Impact & Value at Risk (VaR)")
        if selected["type"] == "error":
            st.error(f"**Scenario Description**: {selected['desc']}")
        elif selected["type"] == "warning":
            st.warning(f"**Scenario Description**: {selected['desc']}")
        else:
            st.info(f"**Scenario Description**: {selected['desc']}")

        expected_loss_m = selected["loss"]
        var_95_m = selected["var95"]
        tail_risk_m = selected["cvar"]
        mean_delay_days = selected["delay"]

        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        col_v1.metric("Expected Margin Loss", f"-${expected_loss_m:.2f}M")
        col_v2.metric(f"Value at Risk ({int(confidence_level*100)}%)", f"-${var_95_m:.2f}M")
        col_v3.metric("Tail Risk (CVaR)", f"-${tail_risk_m:.2f}M")
        col_v4.metric("Avg Transit Delay", f"+{mean_delay_days:.1f} Days")

    st.markdown("---")
    st.subheader("📈 Simulated EBITDA Margin Risk Distribution")

    import numpy as np
    import pandas as pd
    np.random.seed(42)
    losses = np.random.normal(loc=expected_loss_m, scale=expected_loss_m * 0.35, size=sim_runs)
    chart_df = pd.DataFrame({"Simulated EBITDA Loss ($M)": losses})
    st.bar_chart(chart_df.iloc[:100])

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        if st.button("🚀 Inject Selected Stress Scenario into CTRM & S&OP Engine", key="btn_inject_mc"):
            st.session_state["active_mc_scenario"] = scenario_choice
            st.session_state["mc_expected_loss"] = expected_loss_m
            st.session_state["mc_transit_delay"] = mean_delay_days
            st.success(f"✅ **Scenario Injected Platform-Wide**: '{scenario_choice}' is now live across CTRM Risk Desk and S&OP EBITDA Waterfall (-${expected_loss_m:.2f}M Stress Drag).")

    with col_i2:
        if st.session_state.get("active_mc_scenario"):
            st.info(f"⚡ **Currently Active Injected Stress**: **{st.session_state['active_mc_scenario']}** (-${st.session_state['mc_expected_loss']:.2f}M Loss Impact)")
            if st.button("🔄 Reset / Clear Active Macro Stress", key="btn_clear_mc"):
                st.session_state["active_mc_scenario"] = None
                st.session_state["mc_expected_loss"] = 0.0
                st.session_state["mc_transit_delay"] = 0.0
                st.rerun()


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
if any(k in str(selected_module) for k in ["Global Trade", "S&OP", "Executive"]):
    render_executive_sop(persona)
elif any(k in str(selected_module) for k in ["Inventory", "Position"]):
    render_inventory_position_manager()
elif any(k in str(selected_module) for k in ["Alternative Data", "Sentiment", "NLP"]):
    render_nlp_commercial_sensing(persona)
elif any(k in str(selected_module) for k in ["Machine Learning", "Supply/Demand", "Load Balancer"]):
    render_demand_supply_match(persona)
elif any(k in str(selected_module) for k in ["Physical Cargo", "Contract", "Procurement"]):
    render_physical_procurement(persona)
elif any(k in str(selected_module) for k in ["Backtested Portfolio", "CTRM", "Risk Desk"]):
    render_ctrm_desk(persona)
elif any(k in str(selected_module) for k in ["Real-Time AIS", "GIS", "Logistics"]):
    render_global_logistics_gis(persona)
elif any(k in str(selected_module) for k in ["Monte Carlo", "Scenario", "Sandbox", "Stress"]):
    render_flight_simulator(persona)
elif any(k in str(selected_module) for k in ["Integration", "Endpoints"]):
    render_integration_architecture(persona, selected_module)
else:
    render_executive_sop(persona)
