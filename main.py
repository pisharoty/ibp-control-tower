
# --- Comprehensive 22-Headline Stream Options ---
COMPREHENSIVE_RSS_HEADLINES = ["LME Copper Cathode: Copper extended losses toward $4.20/lb as US inflation policy fueled rate expectations & smelter bottlenecks in South America.", "Primary Aluminum Ingot: Aluminum slid to $2,450/t as dollar firmed and EGA restarted smelter capacity at Al Taweelah while European demand softened.", "Special High Grade Zinc: Zinc SHG Rotterdam premium surged to $330/t with spot concentrate TC at record low -$115/t in latest market scan.", "Battery-Grade Lithium Carbonate: Chinese lithium carbonate slumped 3.5% to CNY 104,400/t following spot market supply adjustments and EV battery destocking.", "LME Nickel Cathode: Indonesian NPI output expands as LME class 1 stocks rise to 18-month highs; stainless steel scrap discounts widening.", "Refined Cobalt Metal: DRC export quota discussions and Durban port congestion lead to prompt delivery tightness in European warehouse stocks.", "Iron Ore Fines 62% Fe: Qingdao port inventories tick higher to 142M MT as Chinese steel mills cap crude steel production ahead of winter emission controls.", "CBOT Milling Wheat: Dryness in Southern Plains and Black Sea export corridor tensions send milling wheat futures up +4.2% on Chicago board.", "CBOT Yellow Corn: US Midwest harvest progress reaches 68% complete; yield reports slightly above early August USDA estimates.", "Henry Hub Natural Gas: Early winter heating demand forecasts and Gulf Coast LNG export facility feedgas demand rising toward 14.5 Bcf/d.", "WTI Crude Oil: Crude trades near $78.50/bbl as non-OPEC supply growth balances voluntary OPEC+ supply cuts through end of year.", "Ethylene Monomer: US Gulf cracker restarts increase monomer availability; European derivative export margins remain squeezed by energy costs.", "Global Raw Materials Update: Spot Market Tightening Across Metals & Blocks [Executive LinkedIn Field Brief | Metals & Mining Channel]", "Glencore & Freight Forwarder Hedge Desk Force Majeure Reductions [Email & Event Debrief Parser | Procurement Advisory Desk]", "C-Suite Procurement Brief: Red Sea Carrier Surcharges & Cape Route Rerouting [Maritime & Ocean Freight Field Intelligence]", "Executive LinkedIn Disclosure: European Smelter Energy Price Hikes & Capacity Curtailment [C-Suite Social Monitor | Energy & Heavy Industry]", "Port Authority Telemetry: Rotterdam Container Dwell Times Spike +2.5 Days [Global Logistics & GIS Control Stream]", "South American Mining Association Field Note: Atacama Brine Water Rights Regulations [Field Intelligence Debrief | South America Desk]", "Agribusiness Supply Chain Alert: Black Sea Grain Shipping Insurance Rates Up +18% [Agricultural Trade & Event Debrief]", "Asian Freight Forwarder Telemetry: Singapore Port Bunkering & Bottlenecks Easing [Ocean Freight & Maritime Feeds]", "Chemical Industry Earnings Call Excerpt: Polymer Feedstock Demand Stabilization in Q4 [Executive Speech & Call Parser]", "Energy Desk Intelligence: LNG Vessel Spot Rates Adjusting Post-Maintenance Window [CTRM Derivatives & Commodity Risk Stream]"]

# Build comprehensive headline list for selectbox options
_rss_headline_options = []
try:
    with open("robot_signals.json", "r") as _sf:
        _sdata = json.load(_sf)
    _rss_headline_options += [s.get("summary") for s in _sdata.get("signals", []) if s.get("summary")]
    _rss_headline_options += [item.get("title") for item in _sdata.get("executive_social_stream", []) if item.get("title")]
except Exception:
    pass

if not _rss_headline_options:
    _rss_headline_options = ["Global Raw Materials Update: Spot Market Tightening Across Metals & Resins"]

from robot_feeds import render_genspark_overlay
import robot_feeds as rf
def render_nlp_intelligence(*args, **kwargs):
    fn = globals().get("render_nlp_commercial_sensing")
    if not fn:
        return None
    try:
        return fn(*args, **kwargs)
    except TypeError:
        return fn()
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk  # Added for GIS / Global Logistics map layers
import streamlit as st
from gru_attention_engine import run_gru_inference
import urllib.request
import xml.etree.ElementTree as ET
from robot_feeds import (
    render_freight_weather_blackswan_tab,
    render_si_subfactor_breakdown,
    refresh_genspark_signals_safe,
    get_genspark_signal_for_commodity,
    calculate_composite_sentiment,
    compute_quantified_operational_impact,
    fetch_baltic_indices,            # Exports live ocean FBX & air TAC rates
    fetch_global_macro_telemetry,
    fetch_gmail_newsletters,
    get_freight_telemetry_sync,      # Direct sync wrapper for live sea & air APIs
    run_end_to_end_sop_cascade,      # Orchestrates full S&OP, CTRM & Logistics impacts
    sync_robot_feeds,
)
from robot_feeds import fetch_live_or_fallback
from inventory_manager import init_session_state_inventory, render_inventory_position_manager

# =====================================================================
# 1. SESSION STATE INITIALIZATION ENGINE
# =====================================================================
def init_session_state():
    """Safely initialize global Streamlit session state variables without throwing errors."""
    st.session_state.setdefault(
        "active_signal",
        {
            "source_type": "Baseline S&OP",
            "title": "Baseline Operations Target",
            "demand_surge_units": 102968,
            "leadtime_delay_days": 2.5,
            "sentiment_index": -0.33,
            "is_propagated": False,
        },
    )
    st.session_state.setdefault("si_composite", -0.33)
    st.session_state.setdefault("extracted_demand_surge", 102968)
    st.session_state.setdefault("active_leadtime_delay_days", 2.5)
    st.session_state.setdefault("sop_cash_balance", 5_000_000.0)
    st.session_state.setdefault("fix_executed", False)
    st.session_state.setdefault("po_executed", False)
    st.session_state.setdefault("ctrm_hedged", False)
    st.session_state.setdefault("demand_plan_committed", False)
    st.session_state.setdefault(
        "active_risk_signal_title", "Baseline Operations Target"
    )
    st.session_state.setdefault("signal_category", "Baseline S&OP")

    # --- Attention-GRU Neural Engine Integration ---
    if "predicted_spot" not in st.session_state:
        try:
            _p_hist = np.linspace(14200.0, 14669.54, 60) + np.random.randn(60) * 10
            _s_hist = np.random.uniform(-0.6, -0.1, 60)
            _spot, _si = run_gru_inference(_p_hist, _s_hist)
            st.session_state["predicted_spot"] = float(_spot)
            st.session_state["triangulated_si"] = float(_si)
        except Exception:
            st.session_state["predicted_spot"] = 14669.54
            st.session_state["triangulated_si"] = -0.330

    # Ensure inventory tables are initialized
    init_session_state_inventory()

# =========================================================================
# GLOBAL SESSION STATE INIT & TRADE EXECUTION HELPER
# =========================================================================
if "executed_hedges" not in st.session_state:
    st.session_state["executed_hedges"] = []

if "fix_executed" not in st.session_state:
    st.session_state["fix_executed"] = False


def execute_ctrm_trade(
    trade_title="CTRM FIX Protocol Hedge", benefit_per_trade=0.0
):
    """Global callback to execute a trade, update state, and force instant rerun."""
    if "executed_hedges" not in st.session_state:
        st.session_state["executed_hedges"] = []

    trade_count = len(st.session_state["executed_hedges"]) + 1

    new_trade = {
        "title": f"{trade_title} #{trade_count}",
        "source_type": "CTRM Desk Trade Execution",
        "hedge_benefit_usd": benefit_per_trade,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # 1. Append trade record
    st.session_state["executed_hedges"].append(new_trade)
    st.session_state["fix_executed"] = True

    # 2. Recalculate total hedge benefit
    st.session_state["total_hedge_benefit"] = sum(
        t.get("hedge_benefit_usd", benefit_per_trade)
        for t in st.session_state["executed_hedges"]
    )

    # 3. Update Treasury Cash ($5.0M base - $0.57M freight + cumulative hedges)
    base_treasury = 5_000_000.0
    freight_surcharge = st.session_state.get("freight_surcharge_usd", 570_000.0)
    st.session_state["available_treasury_cash"] = (
        base_treasury
        + st.session_state["total_hedge_benefit"]
        - freight_surcharge
    )

    st.toast(
        f"🔒 Trade #{trade_count} Executed! Locked +${benefit_per_trade:,.2f}",
        icon="🚀",
    )

    # 4. CRITICAL: Force immediate Streamlit rerun to update Tab 1 KPIs
    st.rerun()


# =====================================================================
# 2. FIRST STREAMLIT EXECUTED COMMAND
# =====================================================================
st.set_page_config(
    page_title="IBP Control Tower",
    page_icon="⚡",
    layout="wide",  # Expands workspace to full screen width
    initial_sidebar_state="expanded",
)

# Execute state initialization immediately after set_page_config
init_session_state()


# Load cached signal data from robot_signals.json on startup
signals_file = os.path.join(os.path.dirname(__file__), "robot_signals.json")
if os.path.exists(signals_file):
  try:
    with open(signals_file, "r") as f:
      cached = json.load(f)
      if "linkedin_score" in cached:
        st.session_state["linkedin_score"] = cached["linkedin_score"]
      if "newsletters" in cached:
        st.session_state["live_newsletters"] = cached["newsletters"]
  except Exception:
    pass

# =====================================================================
# 3. GLOBAL CONFIGURATIONS & MAPPINGS
# =====================================================================
SECTOR_BENCHMARK_MAP = {
    "Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)": {
        "primary_index": "LME Cash Settlement Index (LME-3M)",
        "secondary_index": "CME Copper Futures",
        "ticker_symbol": "LME-CU / LME-AL",
        "sap_mat_code": "MAT_COPPER_CATHODE_ORD_A",
        "oracle_gl_account": "GL-SYNC-5100-NONFERROUS-HEDGE",
        "sample_headline": (
            "Copper & Aluminum cash settlement premiums surged +14% due to"
            " smelter energy curtailments."
        ),
    },
    "Semiconductors & High Tech": {
        "primary_index": "DRAMexchange Spot Index (DXI)",
        "secondary_index": "SOX Semiconductor Benchmark",
        "ticker_symbol": "DXI-32GB-DDR5",
        "sap_mat_code": "MAT_WAFER_300MM_SILICON",
        "oracle_gl_account": "GL-SYNC-5200-SEMICON-HEDGE",
        "sample_headline": (
            "300mm Silicon wafer lead times extended +6 weeks amid fab capacity"
            " constraints."
        ),
    },
    "Energy & Petrochemicals": {
        "primary_index": "S&P Global Platts Brent Crude",
        "secondary_index": "ICIS Ethylene Benchmark",
        "ticker_symbol": "PLATTS-BRENT-CRUDE",
        "sap_mat_code": "MAT_NAPHTHA_FEEDSTOCK_01",
        "oracle_gl_account": "GL-SYNC-5300-ENERGY-HEDGE",
        "sample_headline": (
            "Gulf Coast ethylene cracker outage drives immediate spot price"
            " surge of +18%."
        ),
    },
    "Logistics & Global Freight": {
        "primary_index": "Freightos Baltic Index (FBX)",
        "secondary_index": "Shanghai Containerized Freight Index",
        "ticker_symbol": "FBX-ASIA-USEC",
        "sap_mat_code": "MAT_LOGISTICS_40FT_HC",
        "oracle_gl_account": "GL-SYNC-5400-FREIGHT-HEDGE",
        "sample_headline": (
            "Suez Canal routing bottleneck causes spot container freight rates"
            " to spike +22%."
        ),
    },
}


# =====================================================================
# 4. HELPER FUNCTIONS & STATE CONTRACT CALLBACKS
# =====================================================================


@st.cache_data(ttl=10)
def fetch_live_noaa_marine_alerts():
    """Queries NOAA NWS API for live severe marine weather & coastal flood alerts."""
    url = "https://api.weather.gov/alerts/active?status=actual&severity=Severe,Extreme"
    headers = {
        "User-Agent": (
            "(SupplyChainControlTowerApp, contact@enterprise-logistics.com)"
        )
    }
    alerts = []
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            features = response.json().get("features", [])
            for feat in features[:10]:
                props = feat.get("properties", {})
                event = props.get("event", "Severe Environmental Warning")
                area = props.get("areaDesc", "Coastal Corridor")
                severity = props.get("severity", "Elevated")
                headline = props.get("headline", "Active Environmental Advisory")
                effective = props.get("effective", "")[:16].replace("T", " ")
                alerts.append({
                    "corridor": (
                        area[:40] + "..." if len(area) > 40 else area
                    ),
                    "event": event,
                    "severity": severity,
                    "headline": headline,
                    "timestamp": f"{effective} UTC",
                })
    except Exception:
        pass
    return alerts


@st.cache_data(ttl=10)
def fetch_live_freight_metrics():
    """Fetches real-time freight indices using yfinance and direct REST fallback with full diagnostic logging."""
    import requests
    import yfinance as yf

    logs = []

    # Method A: Try yfinance for BDRY and BDRY
    for symbol in ["BDRY", "BDRY"]:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty and len(hist) >= 1:
                curr_val = hist["Close"].iloc[-1]
                prev_val = (
                    hist["Close"].iloc[-2] if len(hist) > 1 else curr_val
                )
                wow_change = round(
                    ((curr_val - prev_val) / prev_val) * 100, 1)

                display_val = (
                    round(curr_val * 450, 0)
                    if symbol == "BDRY"
                    else round(curr_val, 0)
                )
                print(
                    f"✅ yfinance Success ({symbol}): {display_val} pts ({wow_change}%)")
                return display_val, wow_change, f"🟢 LIVE BALTIC TELEMETRY ({symbol})"
            else:
                print(f"⚠️ yfinance returned empty DataFrame for {symbol}")
        except Exception as e:
            print(
                f"❌ yfinance Error ({symbol}): {type(e).__name__} - {str(e)}")

    # Method B: Direct Yahoo Finance Query API with Desktop Browser Headers (bypasses yfinance wrapper blocks)
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BDRY"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            meta = res.json()["chart"]["result"][0]["meta"]
            curr_val = meta["regularMarketPrice"]
            prev_close = meta.get("chartPreviousClose", curr_val)
            wow_change = (
                round(((curr_val - prev_close) / prev_close) * 100, 1)
                if prev_close
                else 0.0
            )
            display_val = round(curr_val * 450, 0)
            print(
                f"✅ Direct REST Yahoo Success: BDRY proxy scaled to {display_val} pts")
            return display_val, wow_change, "🟢 LIVE BALTIC TELEMETRY (REST)"
        else:
            print(
                f"❌ Direct REST Yahoo Failed: HTTP {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"❌ Direct REST Yahoo Exception: {type(e).__name__} - {str(e)}")

    # Standard Fallback if both yfinance and REST API get blocked by cloud provider IP limits
    print("⚠️ All live freight endpoints failed. Reverting to fallback.")
    return 3178.0, 2.4, "🟡 SIMULATED FALLBACK"


def update_composite_si():
    """Recalculates composite sentiment penalty dynamically from active metrics."""
    surge = st.session_state.get("extracted_demand_surge", 102968)
    delay = st.session_state.get("active_leadtime_delay_days", 2.5)

    surge_penalty = (surge - 100000) / 200000.0
    delay_penalty = delay / 30.0
    new_si = max(-1.0, min(1.0, -0.10 - surge_penalty - delay_penalty))
    rounded_si = round(new_si, 2)

    st.session_state["si_composite"] = rounded_si

    if "active_signal" in st.session_state and isinstance(
        st.session_state["active_signal"], dict
    ):
        st.session_state["active_signal"]["sentiment_index"] = rounded_si


def commit_nlp_signal(signal_dict: dict):
    """Commits an ingested signal to session state and propagates to all downstream desks via the central S&OP orchestrator."""

    # 1. Update core session state keys
    st.session_state["active_signal"] = signal_dict
    st.session_state["active_risk_signal_title"] = signal_dict.get(
        "title", "Ingested Risk Signal"
    )
    st.session_state["active_transit_delay"] = signal_dict.get(
        "leadtime_delay_days", 8.5
    )
    st.session_state["si_composite"] = signal_dict.get("sentiment_index", -0.33)
    st.session_state["extracted_demand_surge"] = signal_dict.get(
        "demand_surge_units", 100000
    )

    # 2. Execute central S&OP cascade across all desks (Demand, Procurement, CTRM, Logistics, S&OP)
    cascade_results = robot_feeds.run_end_to_end_sop_cascade(
        base_demand_units=signal_dict.get("demand_surge_units", 200000),
        raw_mat_ratio_per_unit=1.25,
        current_spot_price=4.15,
    )

    st.toast(
        f"⚡ Ingested '{signal_dict.get('title')}' | Central Cascade"
        " Triggered Across All Desks!",
        icon="🚀",
    )




def black76_call_put(F, K, T, r, sigma):
    """Black76 Option Pricing Engine Proxy for UI calculation."""
    d1 = (np.log(F / K) + (sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call = np.exp(-r * T) * (F * 0.52 - K * 0.48)
    put = np.exp(-r * T) * (K * 0.52 - F * 0.48)
    delta = 0.52
    vega = 12.45
    return call, put, delta, vega



def get_persona_contracts(persona: str) -> list[dict]:
    """Return active physical supply contracts tailored to platform persona."""
    if "FMCG" in persona:
        return [
            {
                "Vendor": "Cargill Oils",
                "Material": "Refined Palm / Soy Oil",
                "Quantity": "15,000 MT",
                "Status": "🟢 Active",
                "Delivery": "Weekly Stream",
            },
            {
                "Vendor": "Tetra Pak Global",
                "Material": "Aseptic Packaging Board",
                "Quantity": "2,500,000 Units",
                "Status": "🟢 Active",
                "Delivery": "Bi-Weekly",
            },
            {
                "Vendor": "Archer Daniels Midland",
                "Material": "High-Fructose Corn Syrup",
                "Quantity": "8,000 MT",
                "Status": "⚠️ Delayed",
                "Delivery": "Monthly Spot",
            },
        ]
    elif "Merchant" in persona:
        return [
            {
                "Vendor": "Glencore Singapore",
                "Material": "Physical Copper Cathodes",
                "Quantity": "10,000 MT",
                "Status": "🟢 Active",
                "Delivery": "Prompt Shipment",
            },
            {
                "Vendor": "Trafigura Trading",
                "Material": "LNG Physical Cargo",
                "Quantity": "120,000 MWh",
                "Status": "🟢 Active",
                "Delivery": "CIF Rotterdam",
            },
            {
                "Vendor": "Bunge Global",
                "Material": "Yellow Corn #2",
                "Quantity": "45,000 MT",
                "Status": "🟡 Re-negotiating",
                "Delivery": "FOB Santos",
            },
        ]
    else:  # Discrete & Heavy Industrial
        return [
            {
                "Vendor": "Rio Tinto Metals",
                "Material": "Primary Aluminum Ingot",
                "Quantity": "12,000 MT",
                "Status": "🟢 Active",
                "Delivery": "Monthly Rail",
            },
            {
                "Vendor": "TSMC Wafer Foundry",
                "Material": "Automotive Microcontrollers",
                "Quantity": "500,000 Units",
                "Status": "⚠️ Bottleneck",
                "Delivery": "Quarterly Allocation",
            },
            {
                "Vendor": "POSCO Steel",
                "Material": "Cold-Rolled Sheet Coil",
                "Quantity": "25,000 MT",
                "Status": "🟢 Active",
                "Delivery": "Weekly Barge",
            },
        ]

# =====================================================================
# 5. MODULE RENDER ENGINES
# =====================================================================


def render_executive_sop(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Render Executive S&OP Control Tower with fully reconciled P&L, dynamic persona baselines, live telemetry, & Plotly waterfall."""
    st.title("📈 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown(
        "Real-time financial alignment, financial waterfalls, and trade hedge"
        " benefit reconciliation."
    )

    # 1. Dynamic Persona Baselines & ASP/COGS Rates
    if "FMCG" in persona:
        base_aop_rev = 450_000_000.0
        unit_price = 45.0
        cogs_pct = 0.58
    elif "Merchant" in persona:
        base_aop_rev = 850_000_000.0
        unit_price = 3_200.0
        cogs_pct = 0.82
    else:  # Discrete & Heavy Industrial
        base_aop_rev = 120_000_000.0
        unit_price = 780.0
        cogs_pct = 0.65

    # 2. Extract Central Cascade State & Live Signals
    cascade = st.session_state.get("active_sop_cascade", {})
    robot_signals = st.session_state.get("latest_robot_signals", {})
    prop_data = st.session_state.get("propagated_commodity_data")

    demand_data = cascade.get("demand", {})
    logistics_data = cascade.get("logistics", {})
    baltic_data = robot_signals.get("baltic_indices", {})

    # Retain finished product ASP (unit_price); capture commodity spot price separately
    comm_spot_price = prop_data.get("spot_price", 14643.09) if prop_data else 14643.09
    comm_target_price = prop_data.get("target_price", 15231.65) if prop_data else 15231.65

    si_score = st.session_state.get(
        "si_composite", cascade.get("si_composite", -0.28)
    )
    surge_units = st.session_state.get("extracted_demand_surge", st.session_state.get("gross_surge", 247122))

    # Extract Live Telemetry & Freight Surcharge ($0.57M default)
    modal_shift_air = logistics_data.get("modal_shift_air", True)
    freight_surcharge = st.session_state.get("freight_surcharge_usd", 570_000.0)
    fbx_sea_rate = baltic_data.get("freightos_fbx_ocean", {}).get("value", 3850)
    tac_air_rate = baltic_data.get("baltic_air_tac", {}).get("value", 2.48)

    # 3. Unified CTRM Trade Aggregation
    raw_executed_hedges = st.session_state.get("executed_hedges", [])
    raw_ctrm_trades = st.session_state.get("ctrm_trades", [])
    raw_ctrm_hedges = st.session_state.get("ctrm_hedges", [])
    all_executed_trades = (
        raw_executed_hedges + raw_ctrm_trades + raw_ctrm_hedges
    )

    if not all_executed_trades and st.session_state.get("fix_executed", False):
        live_benefit = st.session_state.get("fix_premium_paid", st.session_state.get("last_executed_hedge_benefit", 0.0))
        all_executed_trades = [
            {"title": "FIX Protocol Order", "hedge_benefit_usd": live_benefit}
        ]

    hedge_count = len(all_executed_trades)
    ctrm_hedge_benefit = (
        sum(
            (
                t.get("hedge_benefit_usd", 0.0)
                if isinstance(t, dict)
                else 0.0
            )
            for t in all_executed_trades
        )
        if hedge_count > 0
        else 0.0
    )

    # Save back to session state
    st.session_state["total_hedge_benefit"] = ctrm_hedge_benefit

    # 4. Reconciled Financial Engine ($ USD)
    revenue_upside = surge_units * unit_price
    unconstrained_rev = base_aop_rev + revenue_upside

    base_cogs = base_aop_rev * cogs_pct
    surge_cogs = revenue_upside * cogs_pct  # Deduct variable COGS for surge

    # Reconciled Net EBITDA Calculation
    net_ebitda = (
        base_aop_rev
        - base_cogs
        + revenue_upside
        - surge_cogs
        - freight_surcharge
        + ctrm_hedge_benefit
    )

    # Treasury Cash Reconciliation
    base_treasury = 5_000_000.0
    sop_cash = base_treasury + ctrm_hedge_benefit - freight_surcharge
    st.session_state["available_treasury_cash"] = sop_cash

    mc_res = st.session_state.get("mc_results", None)
    var_95_drag = (
        mc_res["var_95"] if mc_res else (freight_surcharge + surge_cogs) * 1.4
    )

    # 5. Top Metric Cards Row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(
            "Annual Operating Plan (AOP)",
            f"${base_aop_rev / 1e6:.1f}M",
            "+4.2% YoY Target",
        )
    with col_m2:
        st.metric(
            "Unconstrained Demand",
            f"${unconstrained_rev / 1e6:.2f}M",
            f"+{surge_units:,} {term_unit} (+${revenue_upside / 1e6:.2f}M)",
        )
    with col_m3:
        st.metric(
            "CTRM Hedge Benefit",
            f"+${ctrm_hedge_benefit / 1e6:.2f}M",
            (
                f"{hedge_count} Active Trade{'s' if hedge_count != 1 else ''} Executed"
                if hedge_count > 0
                else "0% Cover (Floating Risk)"
            ),
            delta_color="normal" if hedge_count > 0 else "inverse",
        )
    with col_m4:
        treasury_shift_pct = (
            (sop_cash - base_treasury) / base_treasury
        ) * 100
        st.metric(
            "Available Treasury Cash",
            f"${sop_cash:,.2f}",
            delta=(
                "CRITICAL CASH RISK"
                if sop_cash < 0
                else f"{treasury_shift_pct:+.2f}% Working Capital Shift"
            ),
            delta_color="normal" if sop_cash >= base_treasury else "inverse",
        )

    st.divider()

    if sop_cash < 0 or (mc_res and mc_res.get("insolvency_risk", 0) > 10):
        st.error(
            f"🚨 **STRESSED FINANCIAL RISK DETECTED**: Potential cost drag"
            f" **${var_95_drag / 1e6:.2f}M (95% VaR)**. Treasury Cash balance"
            f" **${sop_cash:,.2f}**."
        )

    # 6. Interactive Visual Waterfall & Live Operational Desk Feeds
    col_p1, col_p2 = st.columns([1.3, 1])
    with col_p1:
        st.subheader("💵 Financial P&L Margin Waterfall")
        fig = go.Figure(
            go.Waterfall(
                name="P&L Reconciliation",
                orientation="v",
                measure=[
                    "relative",
                    "relative",
                    "relative",
                    "relative",
                    "relative",
                    "relative",
                    "total",
                ],
                x=[
                    "Base AOP Rev",
                    "Base COGS",
                    "Surge Rev",
                    "Surge COGS",
                    "Freight Drag",
                    "Hedge Benefit",
                    "Net EBITDA",
                ],
                textposition="outside",
                text=[
                    f"${base_aop_rev / 1e6:.1f}M",
                    f"-${base_cogs / 1e6:.1f}M",
                    f"+${revenue_upside / 1e6:.2f}M",
                    f"-${surge_cogs / 1e6:.2f}M",
                    f"-${freight_surcharge / 1e6:.2f}M",
                    f"+${ctrm_hedge_benefit / 1e6:.2f}M",
                    f"${net_ebitda / 1e6:.2f}M",
                ],
                y=[
                    base_aop_rev / 1e6,
                    -base_cogs / 1e6,
                    revenue_upside / 1e6,
                    -surge_cogs / 1e6,
                    -freight_surcharge / 1e6,
                    ctrm_hedge_benefit / 1e6,
                    0,
                ],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#ef553b"}},
                increasing={"marker": {"color": "#00cc96"}},
                totals={"marker": {"color": "#636efa"}},
            )
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            yaxis_title="USD ($ Millions)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_p2:
        st.subheader("🚩 Live Operational Desk Feeds")
        sig_title = st.session_state.get(
            "active_risk_signal_title", "Baseline Operations Target"
        )

        if prop_data:
            st.success(
                f"⚡ **Predictive Commodity Engine Feed Active**\n\n"
                f"**Ingested Commodity:** {prop_data['commodity_name']}"
                f" [{prop_data.get('ticker', 'LME_CU')}]\n\n"
                f"**Spot:** ${prop_data['spot_price']:,.2f} ➔ **60D Target:**"
                f" ${prop_data['forecast_60d']:,.2f}"
                f" ({prop_data['price_delta_pct']:+.2%})\n\n*Margin Waterfall"
                " & CTRM Desk updated.*"
            )

        st.info(
            f"🔹 **Active NLP Signal**: `{sig_title}` ($SI = {si_score:+.2f}$)"
        )

        if modal_shift_air:
            st.warning(
                "✈️ **Logistics Desk**: **AIR FREIGHT MODAL SHIFT ACTIVE**\n\n"
                f"FBX Sea: **${fbx_sea_rate:,.0f}/FEU** | TAC Air:"
                f" **${tac_air_rate:.2f}/kg**\n\nSurcharge Impact:"
                f" **+${freight_surcharge / 1e6:.2f}M**"
            )
        else:
            st.caption(
                f"🚢 **Logistics Desk**: Standard Sea/Rail Corridor | FBX:"
                f" **${fbx_sea_rate:,.0f}/FEU** | TAC Air:"
                f" **${tac_air_rate:.2f}/kg**"
            )

        if hedge_count > 0:
            st.success(
                f"🟢 **CTRM Risk Desk**: {hedge_count} Order(s) Executed. Hedge"
                f" benefit locked at **+${ctrm_hedge_benefit / 1e6:.2f}M**."
            )
        else:
            st.warning(
                f"🔸 **CTRM Risk Desk**: Unhedged Volatility Gap ="
                f" **{surge_units:,} {term_unit}**."
            )

        if mc_res:
            st.error(
                f"💥 **Monte Carlo Engine**: 95% VaR tail risk elevated to"
                f" **${mc_res['var_95'] / 1e6:.2f}M**."
            )
        else:
            st.success(
                "🟢 **Monte Carlo Engine**: Standard distribution parameters"
                " active."
            )


# =============================================================================
# MAIN MODULE RENDERER
# =============================================================================


def render_aggregated_deal_desk(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Executive Aggregated Deal Desk & Global Portfolio Monitor."""
    st.title("🤝 Aggregated Executive Deal Desk")
    st.caption(
        f"Cross-Functional Commercial Ledger | Active Persona: **{persona}**"
    )
    st.markdown(
        "Consolidated view of physical procurement contracts, financial"
        " derivative hedges, and pending NLP-triggered trade executions."
    )

    # 1. Pull Session State Metrics & Trade Lists
    surge_units = st.session_state.get("extracted_demand_surge", 102968)
    si_score = st.session_state.get("si_composite", -0.33)
    active_sig = st.session_state.get("active_signal", {})

    # Retrieve accumulated hedges list
    if "executed_hedges" not in st.session_state:
        st.session_state["executed_hedges"] = []

    executed_hedges = st.session_state["executed_hedges"]
    hedge_count = len(executed_hedges)
    fix_executed = st.session_state.get("fix_executed", False) or (
        hedge_count > 0
    )

    # 2. Derive Persona Baseline Contract Values
    raw_contracts = get_persona_contracts(persona)
    contracts_df = pd.DataFrame(raw_contracts)

    if "Merchant" in persona:
        multiplier = 3500.0
    elif "FMCG" in persona:
        multiplier = 1200.0
    else:
        multiplier = 850.0

    base_deal_vol = 185000
    total_target_vol = base_deal_vol + surge_units

    # Scale hedged volume dynamically with each executed trade (35% baseline + 32.5% per trade up to 100%)
    if hedge_count > 0:
        coverage_ratio = min(1.0, 0.35 + (0.325 * hedge_count))
    elif fix_executed:
        coverage_ratio = 1.0
    else:
        coverage_ratio = 0.35

    hedged_vol = int(total_target_vol * coverage_ratio)
    unhedged_vol = max(0, total_target_vol - hedged_vol)

    total_pipeline_val = total_target_vol * multiplier
    hedged_val = hedged_vol * multiplier
    exposure_val = unhedged_vol * multiplier

    # 3. Executive Summary KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            "Total Active Deal Pipeline", f"${total_pipeline_val / 1e6:.1f}M"
        )
    with kpi2:
        st.metric(
            "Covered / Hedged Value",
            f"${hedged_val / 1e6:.1f}M",
            delta=(
                f"{int(coverage_ratio * 100)}% Covered ({hedge_count} Trade{'s' if hedge_count != 1 else ''})"
            ),
            delta_color="normal" if coverage_ratio >= 0.9 else "inverse",
        )
    with kpi3:
        st.metric(
            "Unhedged Floating Exposure",
            f"${exposure_val / 1e6:.1f}M",
            delta=f"{unhedged_vol:,} {term_unit} Gap",
            delta_color="normal" if unhedged_vol == 0 else "inverse",
        )
    with kpi4:
        st.metric(
            "Composite Risk Index ($SI$)",
            f"{si_score:+.2f}",
            delta="High Market Strain" if si_score < -0.3 else "Stable",
            delta_color="inverse",
        )

    st.divider()

    # 4. Interactive Exposure & Coverage Chart
    c_left, c_right = st.columns([1.4, 1])

    with c_left:
        st.subheader("📊 Physical Allocation vs. Derivatives Hedge Cover")

        categories = [
            "Base Physical",
            "Surge Volume",
            "CTRM Hedge",
            "Net Open",
        ]
        volumes = [
            base_deal_vol,
            surge_units,
            -hedged_vol,
            unhedged_vol,
        ]

        fig = go.Figure(
            go.Bar(
                x=categories,
                y=volumes,
                text=[f"{v:,}" for v in volumes],
                textposition="auto",
                marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
            )
        )
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=10, b=20),
            yaxis_title=f"Volume ({term_unit})",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.subheader("⚡ Executive Quick Actions")
        st.info(
            f"**Active Signal**: {active_sig.get('title', 'Baseline Target')}"
        )

        if coverage_ratio < 1.0:
            st.warning(
                f"⚠️ **Action Required**: Unhedged price exposure detected ({int((1 - coverage_ratio)*100)}% floating)."
            )
        else:
            st.success("🟢 **Status**: 100% Covered & Fully Hedged.")

        # Trade Execution Action Button
        if st.button(
            "🚀 Execute Auto-Hedge Order on CTRM Desk",
            key="btn_deal_desk_fix",
        ):
            st.session_state["fix_executed"] = True

            # Construct structured trade dictionary
            trade_number = len(st.session_state["executed_hedges"]) + 1
            new_trade = {
                "title": f"CTRM FIX Hedge #{trade_number}",
                "source_type": "CTRM Desk Trade Execution",
                "hedge_benefit_usd": 0.0,
                "demand_surge_units": surge_units,
                "timestamp": datetime.utcnow().strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                ),
            }

            # Append to accumulated trade list
            st.session_state["executed_hedges"].append(new_trade)

            # Propagate cascade to S&OP Control Tower & Treasury
            _propagate_signal_to_sop_cascade(new_trade)

            st.toast(
                f"FIX Protocol Trade #{trade_number} Executed & S&OP Cascade Updated!",
                icon="🔒",
            )
            st.rerun()

        # Position Reset Button
        if hedge_count > 0 or fix_executed:
            if st.button("🔄 Reset Hedge Positions", key="btn_reset_hedge"):
                st.session_state["fix_executed"] = False
                st.session_state["executed_hedges"] = []
                st.session_state["total_hedge_benefit"] = 0.0

                # Reset Treasury Cash back to baseline
                base_treasury = 5_000_000.0
                freight_surcharge = 570_000.0
                st.session_state["available_treasury_cash"] = (
                    base_treasury - freight_surcharge
                )

                st.toast("Hedge portfolio reset to baseline floating risk.")
                st.rerun()

    st.divider()

    # 5. Consolidated Master Deal Ledger
    st.subheader("📑 Consolidated Physical & Financial Deal Ledger")

    deal_records = []
    for idx, row in contracts_df.iterrows():
        deal_records.append({
            "Deal ID": f"PHY-2026-00{idx+1}",
            "Counterparty": row.get("Vendor", "Global Supplier"),
            "Commodity / Material": row.get("Material", "Raw Input"),
            "Contract Type": "Physical Supply",
            "Volume": row.get("Quantity", "10,000 Units"),
            "Status": row.get("Status", "🟢 Active"),
            "Hedge State": "Physical Covered",
        })

    # Render each executed trade in the master ledger
    if executed_hedges:
        for idx, trade in enumerate(executed_hedges):
            deal_records.append({
                "Deal ID": f"CTRM-FIX-99{42 + idx}",
                "Counterparty": "LME / CME Clearinghouse",
                "Commodity / Material": f"Index Derivative Futures ({term_unit})",
                "Contract Type": "Financial Hedge",
                "Volume": f"{int(hedged_vol / max(1, hedge_count)):,} {term_unit}",
                "Status": "🟢 Executed",
                "Hedge State": "Financial Cover",
            })
    else:
        deal_records.append({
            "Deal ID": "CTRM-FIX-9942",
            "Counterparty": "LME / CME Clearinghouse",
            "Commodity / Material": f"Index Derivative Futures ({term_unit})",
            "Contract Type": "Financial Hedge",
            "Volume": f"{hedged_vol:,} {term_unit}",
            "Status": "🟡 Pending FIX Call",
            "Hedge State": "Floating Risk",
        })

    deal_records.append({
        "Deal ID": "NLP-SIGNAL-018",
        "Counterparty": active_sig.get("source_type", "Field Sensing"),
        "Commodity / Material": active_sig.get("title", "Market Surge Signal"),
        "Contract Type": "Inferred Demand Spike",
        "Volume": f"+{surge_units:,} {term_unit}",
        "Status": "🔴 Unhedged Surge" if unhedged_vol > 0 else "🟢 Covered",
        "Hedge State": (
            "Open Exposure" if unhedged_vol > 0 else "Fully Hedged"
        ),
    })

    st.dataframe(pd.DataFrame(deal_records), use_container_width=True)

# =========================================================================
# CASCADE PROPAGATION HELPERS (TOP-LEVEL SCOPE)
# =========================================================================


def commit_physical_procurement_contract(
    vendor_name, material_type, contract_units, unit_price_usd
):
    """Callback for Physical Procurement Desk contract signing."""
    procurement_payload = {
        "title": f"Physical Contract: {vendor_name} ({material_type})",
        "source_type": "Physical Procurement Desk",
        "demand_surge_units": 0,
        "cogs_impact_usd": contract_units * unit_price_usd,
        "freight_surcharge_usd": 0.0,
        "hedge_benefit_usd": 0.0,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    if "physical_contracts" not in st.session_state:
        st.session_state["physical_contracts"] = []
    st.session_state["physical_contracts"].append(procurement_payload)

    _propagate_signal_to_sop_cascade(procurement_payload)


def commit_demand_supply_rebalance(revised_demand_units, region_corridor):
    """Callback for Demand/Supply Load Balancer allocation changes."""
    demand_payload = {
        "title": f"Demand Allocation Shift: {region_corridor}",
        "source_type": "Demand/Supply Load Balancer",
        "demand_surge_units": revised_demand_units,
        "sentiment_index": st.session_state.get("si_composite", -0.28),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    st.session_state["extracted_demand_surge"] = revised_demand_units
    _propagate_signal_to_sop_cascade(demand_payload)


def _propagate_signal_to_sop_cascade(signal_data: dict):
    """Helper to commit signal state and trigger end-to-end S&OP cascade execution."""
    if not isinstance(signal_data, dict):
        signal_data = {}

    # Safely resolve title string to prevent NoneType slicing exceptions
    signal_title = signal_data.get("title") or "Market Signal Update"

    # Initialize accumulation list if not present in session state
    if "executed_hedges" not in st.session_state:
        st.session_state["executed_hedges"] = []

    # If this signal contains hedge telemetry or CTRM data, append to accumulation list
    if (
        "hedge_benefit_usd" in signal_data
        or "CTRM" in signal_data.get("source_type", "")
    ):
        st.session_state["executed_hedges"].append(signal_data)

    # Commit active signal state
    st.session_state["active_signal"] = signal_data
    st.session_state["latest_signals"] = signal_data
    st.session_state["active_risk_signal_title"] = signal_title
    st.session_state["si_composite"] = signal_data.get(
        "sentiment_index", -0.28
    )

    # Run End-to-End Operational & Financial Cascade Engine
    cascade_output = run_end_to_end_sop_cascade(
        base_demand_units=st.session_state.get("base_demand", 200000)
    )
    st.session_state["active_sop_cascade"] = cascade_output

    # Recalculate cumulative hedge benefits across all executed hedges
    total_hedge_benefit = (
        sum(
            h.get("hedge_benefit_usd", 0.0)
            for h in st.session_state["executed_hedges"]
        )
        if st.session_state["executed_hedges"]
        else signal_data.get("hedge_benefit_usd", 0.0)
    )

    st.session_state["total_hedge_benefit"] = total_hedge_benefit

    # Dynamically update Treasury Working Capital in session state
    base_treasury = 5_000_000.0
    freight_surcharge = signal_data.get("freight_surcharge_usd", 570_000.0)
    st.session_state["available_treasury_cash"] = (
        base_treasury + total_hedge_benefit - freight_surcharge
    )

    st.toast(
        f"✅ Signal propagated to Executive Control Tower: {signal_title[:30]}...",
        icon="🚀",
    )


    import urllib.request
import xml.etree.ElementTree as ET


def fetch_live_sector_rss(topic_query=None, persona_materials=None):
    """Fetch and score live breaking commodity & logistics news from RSS feeds."""
    
    # Construct broad multi-commodity search query if none provided
    if topic_query:
        clean_query = topic_query.replace(" ", "+").replace("&", "%26")
    elif persona_materials and isinstance(persona_materials, list):
        mat_str = "+OR+".join([f'"{m}"' for m in persona_materials])
        clean_query = f"({mat_str})+AND+(force+majeure+OR+outage+OR+strike+OR+shortage+OR+disruption)"
    else:
        clean_query = (
            "(copper+OR+tin+OR+polymers+OR+petrochemicals+OR+resins+OR+lithium+OR+oil)"
            "+AND+(force+majeure+OR+outage+OR+strike+OR+shortage+OR+disruption)"
        )

    rss_url = f"https://news.google.com/rss/search?q={clean_query}&hl=en-US&gl=US&ceid=US:en"

    # Define fallback articles for offline / rate-limited execution
    fallback_articles = [
        {
            "title": "Global Raw Materials Update: Spot Market Tightening Across Metals & Resins",
            "source": "Reuters Telemetry",
            "published": "Live Ingest",
            "link": "#",
        },
        {
            "title": "Ethylene & Polymer Cracker Outages Extend Force Majeure Declarations",
            "source": "ICIS Chemical Intelligence",
            "published": "Live Ingest",
            "link": "#",
        },
    ]

    # Leverage low-level fetcher
    raw_articles, is_live = fetch_live_or_fallback(rss_url, fallback_articles, timeout_sec=3.0)

    # Apply sentiment analysis & operational shock scoring
    processed_articles = []
    for item in raw_articles:
        title = item.get("title", "")
        t_lower = title.lower()

        # Route headline through robot_feeds NLP analysis engine
        if hasattr(rf, "analyze_headline_nlp"):
            nlp_res = rf.analyze_headline_nlp(title)
            sentiment = nlp_res.get("sentiment", 0.0)
            if sentiment < -0.2:
                impact_units = int(145000 * max(0.5, abs(sentiment)))
            elif sentiment > 0.2:
                impact_units = int((1.0 - abs(sentiment)) * 90000)
            else:
                impact_units = 110000
        elif any(w in t_lower for w in ["strike", "outage", "disruption", "force majeure", "surge", "shortage", "halt", "delay", "curtailment"]):
            sentiment = -0.75
            impact_units = int(abs(sentiment) * 180000) if sentiment != 0 else 110000
        elif any(w in t_lower for w in ["growth", "boost", "rebound", "expansion", "surplus", "gain"]):
            sentiment = +0.50
            impact_units = int((1.0 - abs(sentiment)) * 90000)
        else:
            sentiment = -0.35
            impact_units = 110000

        processed_articles.append({
            "title": title,
            "source": item.get("source", "Market Feed"),
            "published": item.get("published", ""),
            "link": item.get("link", "#"),
            "sentiment": sentiment,
            "estimated_impact": impact_units,
            "is_live": is_live,
        })

    return processed_articles


 

# -----------------------------------------------------------------------------
# 1. ENHANCED LIVE COMMODITY FETCH ENGINE WITH UNIT CONVERSION MULTIPLIERS
# -----------------------------------------------------------------------------

# --- PREDICTIVE COMMODITY ENGINE (IMPORTED FROM ROBOT_FEEDS.PY) ---
from robot_feeds import render_predictive_commodity_engine

# render_predictive_commodity_engine() moved to dedicated tab

def render_nlp_commercial_sensing():
    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption("Active Persona View: Discrete & Heavy Industrial Enterprise | Ingest unstructured signals from live RSS feeds, executive LinkedIn disclosures, email debriefs, hard macro indicators (NY Fed, FRED, World Bank, ECB, PBOC, KOSPI), and ocean/air freight telemetry.")
    
    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals", 
        "📧 Email & Event Debrief Parser", 
        "⚓ Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        st.subheader("📡 Live Genspark Tactical Market Signals")
        try:
            render_genspark_overlay()
        except Exception as e:
            st.error(f"Error rendering Genspark Overlay: {e}")

    with tab2:
        st.subheader("📧 Email & Executive Event Debrief Stream")
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            debrief_list = sig_data.get("executive_social_stream", sig_data.get("email_debriefs", []))
        except Exception:
            debrief_list = []
        
        if not debrief_list:
            st.info("No active executive event debriefs available.")
        else:
            cols_t2 = st.columns(2)
            for idx, item in enumerate(debrief_list):
                with cols_t2[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Executive Briefing')}** | {item.get('commodity', 'General')}")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Debrief'))}")
                        st.write(item.get('content', 'Executive field intelligence update.'))
                        si = float(item.get('sentiment_score', -0.33))
                        st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                        if st.button(f"⚡ Ingest Debrief #{idx+1}", key=f"btn_tab2_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 15400)
                            st.session_state["platform_leadtime_impact"] = item.get("impact_leadtime", 4.2)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast(f"⚡ Executive Debrief #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()

    with tab3:
        st.subheader("⚓ Freight, Weather & Black Swan Feeds")
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            freight_list = sig_data.get("freight_weather_feeds", sig_data.get("freight_telemetry_feeds", []))
        except Exception:
            freight_list = []
        
        if not freight_list:
            st.info("No active freight or weather feeds available.")
        else:
            cols_t3 = st.columns(2)
            for idx, item in enumerate(freight_list):
                with cols_t3[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Telemetry Feed')}** | {item.get('commodity', 'Logistics')}")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Freight Disruption'))}")
                        si = float(item.get('sentiment_score', -0.42))
                        lt = float(item.get('impact_leadtime', 4.5))
                        st.metric("Lead Time Drag", f"+{lt:.1f} Days", delta=f"SI: {si:+.2f}")
                        if st.button(f"⚡ Ingest Freight Signal #{idx+1}", key=f"btn_tab3_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_leadtime_impact"] = lt
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 16500)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast(f"⚡ Freight Signal #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()



def render_nlp_intelligence(*args, **kwargs):
    fn = globals().get("render_nlp_commercial_sensing")
    if not fn:
        return None
    try:
        return fn(*args, **kwargs)
    except TypeError:
        return fn()
render_nlp_sensing = render_nlp_intelligence

def render_demand_supply_match(
    persona=None,
    term_unit="Units",
    plant1_name=None,
    plant2_name=None,
    toller_name=None,
    *args,
    **kwargs,
):
    """Demand/Supply Match, Inventory Netting & MRP Order Offset Module connected to Centralized Orchestration."""
    import datetime
    import pandas as pd

    st.title("⚙️ Demand/Supply Match & Plant Load Balancer")
    st.caption(
        "Automated inventory netting, multi-horizon S&OP scheduling, and"
        " dynamic order offsets."
    )

    # -------------------------------------------------------------------------
    # 1. READ & INITIALIZE CENTRALIZED ORCHESTRATOR CASCADE
    # -------------------------------------------------------------------------
    if "active_sop_cascade" not in st.session_state:
        st.session_state["active_sop_cascade"] = {}

    cascade = st.session_state["active_sop_cascade"]

    demand_data = cascade.get("demand", {})
    proc_data = cascade.get("procurement", {})

    gross_surge = demand_data.get(
        "total_surge_units", st.session_state.get("extracted_demand_surge", 185000)
    )
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_deficit = demand_data.get(
        "delta_surge_units",
        st.session_state.get(
            "net_uncovered_units", max(0, gross_surge - active_contracts)
        ),
    )
    delta_lt_transit = proc_data.get(
        "transit_delay_days", st.session_state.get("active_transit_delay", 8.5)
    )
    active_signal_title = cascade.get(
        "signal_title",
        st.session_state.get(
            "active_risk_signal_title",
            "Red Sea & Panama Canal Transit Bottlenecks",
        ),
    )

    # Central Orchestrator Banner
    st.info(
        f"🔗 **Centralized Orchestrator Active Signal**: `{active_signal_title}`"
        f" | **Gross Surge**: {gross_surge:,} {term_unit} | **Net Deficit**:"
        f" {net_deficit:,} {term_unit} | **Transit Delay (ΔLT)**:"
        f" +{delta_lt_transit} Days"
    )

    tab1, tab2 = st.tabs([
        "📊 Netting & Forward MRP Horizon (30-180 Days)",
        "⚙️ Dynamic Plant Load Balancing & Capacity Allocation",
    ])

    with tab1:
        # ---------------------------------------------------------------------
        # FORWARD PLANNING HORIZON CONTROLS
        # ---------------------------------------------------------------------
        st.subheader("🗓️ Multi-Period Forward Demand & Netting Horizon")

        default_horizon = st.session_state.get("planner_horizon_days", 60)
        horizon_days = st.select_slider(
            "Select Demand Planner Forward Planning Window (Days Ahead):",
            options=[30, 45, 60, 90, 180],
            value=default_horizon,
            help=(
                "Adjust horizon to evaluate forward gross requirements, safety"
                " stock buffers, and MRP order releases."
            ),
        )

        # WRITE BACK TO CENTRALIZED ORCHESTRATOR STATE
        st.session_state["planner_horizon_days"] = horizon_days
        if "demand" in st.session_state["active_sop_cascade"]:
            st.session_state["active_sop_cascade"]["demand"][
                "planning_horizon"
            ] = horizon_days

        # Horizon scaling
        daily_run_rate = gross_surge / 90.0
        horizon_gross_req = int(daily_run_rate * horizon_days)
        horizon_contract_cover = int((active_contracts / 90.0) * horizon_days)
        horizon_net_req = max(0, horizon_gross_req - horizon_contract_cover)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selected Horizon", f"{horizon_days} Days")
        m2.metric(
            f"Gross Demand ({horizon_days}d)",
            f"{horizon_gross_req:,} {term_unit}",
        )
        m3.metric("Contracted Cover", f"{horizon_contract_cover:,} {term_unit}")
        m4.metric(
            "Net Uncovered Deficit",
            f"{horizon_net_req:,} {term_unit}",
            delta="Uncovered Risk" if horizon_net_req > 0 else "Fully Covered",
            delta_color="inverse",
        )

        st.markdown("---")

        # Multi-Period Schedule Matrix
        st.markdown(
            "##### 📋 Forward Horizon Netting Schedule Matrix (30 → 180 Days)"
        )
        periods = [30, 45, 60, 90, 180]
        schedule_data = []
        for p in periods:
            p_req = int(daily_run_rate * p)
            p_cov = int((active_contracts / 90.0) * p)
            p_net = max(0, p_req - p_cov)
            p_safety = int(p_req * 0.12)
            schedule_data.append({
                "Planning Horizon": f"T+{p} Days",
                "Gross Requirements": f"{p_req:,} {term_unit}",
                "Contracted Inbound": f"{p_cov:,} {term_unit}",
                "Safety Stock Buffer (12%)": f"{p_safety:,} {term_unit}",
                "Net MRP Planned Release": f"{p_net + p_safety:,} {term_unit}",
                "Status": (
                    "⚠️ Deficit / Release Required"
                    if p_net > 0
                    else "✅ Balanced"
                ),
            })

        st.dataframe(
            pd.DataFrame(schedule_data),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # Dynamic ERP Order Offset Recalculation
        st.subheader(
            "⚙️ Dynamic ERP Planned Order Release (POR) Recalculation"
        )
        st.caption(
            "Automatically shifts Material Requirements Planning (MRP) release"
            " dates upstream based on orchestrator transit telemetry."
        )

        por_baseline = "2026-11-15"

        try:
            from robot_feeds import calculate_dynamic_erp_order_offset

            por_offset = calculate_dynamic_erp_order_offset(
                por_baseline, delta_lt_transit
            )
        except Exception:
            base_dt = datetime.datetime.strptime(por_baseline, "%Y-%m-%d")
            offset_dt = base_dt - datetime.timedelta(
                days=float(delta_lt_transit)
            )
            por_offset = offset_dt.strftime("%Y-%m-%d")

        col1, col2, col3 = st.columns(3)
        col1.metric("Baseline Planned Release Date", por_baseline)
        col2.metric(
            "Upstream Transit Bottleneck (ΔLT)", f"+{delta_lt_transit} Days"
        )
        col3.metric("Shifted ERP Order Release Date", por_offset)

        st.success(
            "**Centralized Orchestrator Action:** Planned Order Release date"
            f" automatically shifted backward to **`{por_offset}`** to absorb"
            f" the **+{delta_lt_transit} day** transit bottleneck for the"
            f" **{horizon_days}-day horizon**."
        )

    
    with tab2:
        st.subheader("📧 Email & Executive Event Debrief Stream")
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            debrief_list = sig_data.get("executive_social_stream", sig_data.get("email_debriefs", []))
        except Exception:
            debrief_list = []
        
        if not debrief_list:
            st.info("No active executive event debriefs.")
        else:
            cols_t2 = st.columns(2)
            for idx, item in enumerate(debrief_list):
                with cols_t2[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Executive Briefing')}** | {item.get('commodity', 'General')}")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Debrief'))}")
                        st.write(item.get('content', 'Executive field intelligence update.'))
                        si = float(item.get('sentiment_score', -0.33))
                        st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                        if st.button(f"⚡ Ingest Debrief #{idx+1}", key=f"btn_tab2_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 15400)
                            st.session_state["platform_leadtime_impact"] = item.get("impact_leadtime", 4.2)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast("⚡ Executive Debrief Ingested!")
                            st.rerun()


    with tab3:
        st.subheader("⚓ Freight, Weather & Black Swan Feeds")
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            freight_list = sig_data.get("freight_weather_feeds", sig_data.get("freight_telemetry_feeds", []))
        except Exception:
            freight_list = []
        
        if not freight_list:
            st.info("No active freight or weather feeds.")
        else:
            cols_t3 = st.columns(2)
            for idx, item in enumerate(freight_list):
                with cols_t3[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Telemetry Feed')}** | {item.get('commodity', 'Logistics')}")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Freight/Weather Disruption'))}")
                        si = float(item.get('sentiment_score', -0.42))
                        lt = float(item.get('impact_leadtime', 4.5))
                        st.metric("Lead Time Drag", f"+{lt:.1f} Days", delta=f"SI: {si:+.2f}")
                        if st.button(f"⚡ Ingest Freight Signal #{idx+1}", key=f"btn_tab3_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_leadtime_impact"] = lt
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 16500)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast("⚡ Freight Disruption Signal Ingested!")
                            st.rerun()



    # Payload Mapping:
# - Benchmark Index Trigger : {sector_cfg['primary_index']}
# - Net Physical Deficit    : {net_units:,} {term_unit}
# - Financial Gain Realized : Credit {sector_cfg['oracle_gl_account']} (${hedge_gain:,.2f})
# - Treasury Cash Outlay    : Debit Treasury Operations Balance""",
# language="json",
# )

# with tab4:
# st.markdown("**Automated Hedge Execution via FIX 4.4 Protocol**")
# st.code(
# f"""8=FIX.4.4|9=245|35=D|49=PLATFORM_DESK|56=CME_LME_GATEWAY|34=1082|52={now_iso}|
# 11=ORDER_HEDGE_{now_iso[:10]}|55={sector_cfg['ticker_symbol']}|54=1|38={net_units}|
# 40=2|44=MARKET_BENCHMARK|59=0|47=A|21=1|10=182|""",
# language="text",
# )

# with tab5:
# st.markdown("**Real-Time Macro Telemetry Streaming (FRED & NY Fed)**")
# st.code(
# f"""GET /api/v1/telemetry/stream
Headers: {{ "Authorization": "Bearer telemetry_live_token_******" }}

    # Response Stream:
    # {{
    # "timestamp": "{now_iso}",
    # "ny_fed_gscpi": +0.82,
    # "us_fred_mfg_index": 102.4,
    # "freightos_fbx_ocean_feu": 3850.0
    # }}""",
    # language="json",
    # )

# st.divider()

    # 4. RETAIN EXISTING HANDSHAKE SIMULATOR HELPER
# render_handshake_simulator()

def render_sidebar_navigation():
  st.sidebar.title("⚡ IBP Control Tower")

  persona = st.sidebar.selectbox(
      "Enterprise Operating Persona:",
      [
          "Discrete & Heavy Industrial Enterprise",
          "FMCG, Food & Beverage Enterprise",
          "Merchant Trading & Commodity Enterprise",
      ],
      key="platform_persona_select",
  )

  config = get_persona_config(persona)

  # Dynamically inject Enterprise Inventory & Position Manager if missing from persona list
  if "📦 Enterprise Inventory & Position Manager" not in config["modules"]:
      config["modules"].insert(1, "📦 Enterprise Inventory & Position Manager")

  selected_module = st.sidebar.radio(
      "Navigation Modules:", config["modules"], key="sidebar_module_radio"
  )

  st.sidebar.markdown("---")
  st.sidebar.subheader("🧪 Macro Flight Simulator")

  # Centralized scenario definitions map
  SCENARIO_CONFIGS = {
      "Baseline Operations": {
          "volume_multiplier": 1.00,
          "spot_cost_increase": 0.00,
          "transit_delay_days": 0,
          "iv_multiplier": 1.0,
          "description": "Nominal baseline operating conditions.",
      },
      "Super El Niño (Drought & Hydro Disruption)": {
          "volume_multiplier": 1.25,
          "spot_cost_increase": 0.30,
          "transit_delay_days": 8,
          "iv_multiplier": 1.45,
          "description": (
              "Severe weather disrupting Panama Canal, hydro energy, and agri"
              " yields."
          ),
      },
      "Straits of Hormuz Blockade (+85% Vol, +20d Lag)": {
          "volume_multiplier": 1.60,
          "spot_cost_increase": 0.65,
          "transit_delay_days": 20,
          "iv_multiplier": 2.85,
          "description": (
              "Critical oil & freight transit chokepoint blocked; major market"
              " dislocation."
          ),
      },
      "Bab-el-Mandeb Blockage (+55% Vol, +12d Lag)": {
          "volume_multiplier": 1.30,
          "spot_cost_increase": 0.40,
          "transit_delay_days": 12,
          "iv_multiplier": 1.55,
          "description": (
              "Red Sea route closure forcing Cape of Good Hope rerouting."
          ),
      },
      "Semiconductor Shortage (+50% Vol, +25d Lag)": {
          "volume_multiplier": 1.40,
          "spot_cost_increase": 0.45,
          "transit_delay_days": 25,
          "iv_multiplier": 1.50,
          "description": (
              "Global microchip deficit stalling production lines and"
              " expanding lead times."
          ),
      },
      "Oil Crisis (+70% Vol, +10d Lag)": {
          "volume_multiplier": 1.35,
          "spot_cost_increase": 0.50,
          "transit_delay_days": 10,
          "iv_multiplier": 2.00,
          "description": (
              "OPEC production shocks inflating energy, raw materials, and"
              " freight surcharges."
          ),
      },
      "Earthquake (Supply Chain Disruption)": {
          "volume_multiplier": 1.20,
          "spot_cost_increase": 0.35,
          "transit_delay_days": 15,
          "iv_multiplier": 1.70,
          "description": (
              "Seismic disruption halting Tier-1 component manufacturing and"
              " regional port ops."
          ),
      },
      "Red Sea Freight Bottleneck (+45% Freight, +8d Lag)": {
          "volume_multiplier": 1.10,
          "spot_cost_increase": 0.35,
          "transit_delay_days": 8,
          "iv_multiplier": 1.40,
          "description": (
              "Red Sea maritime rerouting forcing Cape of Good Hope transit."
          ),
      },
      "Red River Drought / Crop Deficit (-30% Yield)": {
          "volume_multiplier": 0.85,
          "spot_cost_increase": 0.50,
          "transit_delay_days": 4,
          "iv_multiplier": 1.80,
          "description": (
              "Severe agricultural crop failure inflating physical spot"
              " prices."
          ),
      },
      "Black Swan Volatility Spike (+250% IV Shock)": {
          "volume_multiplier": 1.00,
          "spot_cost_increase": 0.15,
          "transit_delay_days": 14,
          "iv_multiplier": 2.50,
          "description": (
              "Financial market dislocation spiking derivative options implied"
              " volatility."
          ),
      },
  }

  sandbox_scenario = st.sidebar.selectbox(
      "Select 'What-If' Stress Scenario:",
      list(SCENARIO_CONFIGS.keys()),
      key="sb_scenario_select",
  )

  if st.sidebar.button("🧪 Launch Sim Scenario", key="btn_launch_sandbox"):
    st.session_state["sandbox_active"] = (
        sandbox_scenario != "Baseline Operations"
    )
    st.session_state["sandbox_scenario"] = sandbox_scenario
    st.session_state["sandbox_params"] = SCENARIO_CONFIGS[sandbox_scenario]

    st.toast(f"Activated: {sandbox_scenario}", icon="🧪")

  return persona, selected_module, config


# =====================================================================
# 6. PERSONA CONFIG ENGINE & NAVIGATION ROUTER
# =====================================================================


def get_persona_config(persona_name: str) -> dict:
  if "FMCG" in persona_name:
    return {
        "term_unit": "Cases",
        "term_raw": "Ingredients & Concentrates",
        "plant1_name": "Atlanta Bottling Hub",
        "plant2_name": "Dallas Co-Packing Facility",
        "toller_name": "Midwest CMO Partner Node",
        "modules": [
            "Executive S&OP Control Tower",
            "NLP Commercial Sensing & Field Intelligence",
            "Demand/Supply Match & Plant Load Balancer",
            "Physical Procurement & Master Contract Desk",
            "CTRM Derivatives & Commodity Risk Desk",
            "Global Logistics Network & GIS Control Tower",
            "Sandbox Flight Simulator & Stress Lab",
            "Integration & Architecture Endpoints",
        ],
    }
  elif "Merchant" in persona_name:
    return {
        "term_unit": "MT",
        "term_raw": "Physical Cargo",
        "plant1_name": "Rotterdam Terminal Hub",
        "plant2_name": "Singapore Storage Facility",
        "toller_name": "Houston Toll Processing Terminal",
        "modules": [
            "Daily Trading Balance Sheet & Executive S&OP",
            "NLP Commercial Sensing & Global Macro",
            "Physical Off-Take & Terminal Load Balancer",
            "Physical Procurement & Master Contract Desk",
            "CTRM Event-Driven Hedging Desk",
            "Global Logistics Network & GIS Control Tower",
            "Sandbox Flight Simulator & Stress Lab",
            "Integration & Architecture Endpoints",
        ],
    }
  else:  # Discrete & Heavy Industrial
    return {
        "term_unit": "Units",
        "term_raw": "Raw Metals & Components",
        "plant1_name": "Detroit Main Stamping & Assembly",
        "plant2_name": "Munich Precision Stamping",
        "toller_name": "Ohio Sub-Assembly Partner",
        "modules": [
            "Executive S&OP Control Tower",
            "NLP Commercial Sensing & Field Intelligence",
            "Demand/Supply Match & Plant Load Balancer",
            "Physical Procurement & Master Contract Desk",
            "CTRM Derivatives & Commodity Risk Desk",
            "Global Logistics Network & GIS Control Tower",
            "Sandbox Flight Simulator & Stress Lab",
            "Integration & Architecture Endpoints",
        ],
    }


# =====================================================================
# 7. MAIN EXECUTION ROUTER
# =====================================================================

persona, selected_module, config = render_sidebar_navigation()

term_unit = config["term_unit"]
term_raw = config["term_raw"]
plant1_name = config["plant1_name"]
plant2_name = config["plant2_name"]
toller_name = config["toller_name"]

if any(
    term in selected_module
    for term in [
        "Executive S&OP",
        "Integrated Business Planning",
        "Daily Trading Balance Sheet",
    ]
):
  render_executive_sop(persona=persona, term_unit=term_unit)

elif any(
    term in selected_module
    for term in ["Inventory", "Position Manager"]
):
  render_inventory_position_manager()

elif any(
    term in selected_module
    for term in [
        "NLP Commercial Sensing",
        "Macro & Satellite",
        "Global Macro",
        "Retail Intelligence",
    ]
):
  render_nlp_intelligence(persona=persona, term_unit=term_unit)

elif any(
    term in selected_module
    for term in ["Demand/Supply Match", "Batch Processing", "Physical Off-Take"]
):
  render_demand_supply_match(
      persona, term_unit, plant1_name, plant2_name, toller_name
  )

elif any(
    term in selected_module for term in ["Physical Procurement", "Agri-Ingredients"]
):
  render_physical_procurement(
      persona=persona, term_unit=term_unit, term_raw=term_raw
  )

elif "CTRM" in selected_module:
  render_ctrm_desk(persona=persona, term_unit=term_unit)

elif any(
    term in selected_module for term in ["Sandbox", "Flight Simulator", "Stress Lab"]
):
  render_flight_simulator(persona=persona, term_unit=term_unit)

elif any(
    term in selected_module
    for term in ["Global Logistics", "GIS", "Cold Chain", "Maritime AIS"]
):
  render_global_logistics_gis(persona=persona, term_unit=term_unit)

elif "Integration" in selected_module:
  render_integration_architecture(
      persona=persona, selected_module=selected_module
  )

else:
  st.warning(f"⚠️ Unmapped operational module selected: **{selected_module}**")

def render_si_factor_breakdown_chart():
    import plotly.graph_objects as go
    import streamlit as st
    si_factors = ['GSCPI Macro (35%)', 'NOAA Weather (25%)', 'Ocean Freight (25%)', 'GEP Volatility (15%)']
    si_values = [-0.112, -0.090, -0.100, -0.028]
    fig = go.Figure(go.Bar(
        x=si_factors,
        y=si_values,
        marker_color=['#E74C3C', '#F39C12', '#E67E22', '#9B59B6'],
        text=[f"{v:.3f}" for v in si_values],
        textposition='auto'
    ))
    fig.update_layout(
        title="<b>Triangulated Factor Contribution Breakdown (Net $S_i$ = -0.330)</b>",
        yaxis_title="Weighted Drag Contribution",
        height=260,
        margin=dict(l=30, r=30, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,247,250,0.5)"
    )
    st.plotly_chart(fig, use_container_width=True)
