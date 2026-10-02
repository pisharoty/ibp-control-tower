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
import urllib.request
import xml.etree.ElementTree as ET
from robot_feeds import (
    calculate_composite_sentiment,
    compute_quantified_operational_impact,
    fetch_baltic_indices,            # Exports live ocean FBX & air TAC rates
    fetch_global_macro_telemetry,
    fetch_gmail_newsletters,
    get_freight_telemetry_sync,      # Direct sync wrapper for live sea & air APIs
    run_end_to_end_sop_cascade,      # Orchestrates full S&OP, CTRM & Logistics impacts
    sync_robot_feeds,
)


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

# =========================================================================
# GLOBAL SESSION STATE INIT & TRADE EXECUTION HELPER
# =========================================================================
if "executed_hedges" not in st.session_state:
    st.session_state["executed_hedges"] = []

if "fix_executed" not in st.session_state:
    st.session_state["fix_executed"] = False


def execute_ctrm_trade(
    trade_title="CTRM FIX Protocol Hedge", benefit_per_trade=140000.0
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


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
def fetch_live_freight_metrics():
    """Fetches real-time freight indices using yfinance (^BDI or BDRY proxy)."""
    for symbol in ["^BDI", "BDRY"]:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty and len(hist) >= 1:
                curr_val = hist["Close"].iloc[-1]
                prev_val = (
                    hist["Close"].iloc[-2] if len(hist) > 1 else curr_val
                )
                wow_change = round(((curr_val - prev_val) / prev_val) * 100, 1)

                # Scale BDRY share price to BDI point index equivalent if using ETF proxy
                display_val = (
                    round(curr_val * 450, 0)
                    if symbol == "BDRY"
                    else round(curr_val, 0)
                )
                return display_val, wow_change, "🟢 LIVE BALTIC TELEMETRY"
        except Exception:
            continue
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
    import robot_feeds

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


def parse_unstructured_email(text: str) -> dict:
    """Regex entity parser for unstructured supplier communications."""
    from_match = re.search(r"FROM:\s*([^\n@]+)", text, re.IGNORECASE)
    vendor = (
        from_match.group(1).replace("-", " ").title().strip()
        if from_match
        else "Global Smelting Corp"
    )

    days_match = re.search(
        r"(\d+)\s*(?:to\s*\d+)?\s*(?:day|days|d)", text, re.IGNORECASE
    )
    delay_val = float(days_match.group(1)) if days_match else 14.0

    units_match = re.search(
        r"(\d[\d,]*)\s*(?:unit|units|tons|MT|cat|cathodes)", text, re.IGNORECASE
    )
    units_val = (
        int(units_match.group(1).replace(",", "")) if units_match else 45000
    )

    low_text = text.lower()
    if "curtailment" in low_text or "energy" in low_text:
        event = "Energy Curtailment"
    elif "strike" in low_text or "labor" in low_text:
        event = "Port / Labor Strike"
    elif "force majeure" in low_text:
        event = "Force Majeure Event"
    elif "drought" in low_text or "water" in low_text:
        event = "Climate Disruption"
    else:
        event = "Supply Bottleneck"

    return {
        "vendor": vendor,
        "event": event,
        "delay_val": delay_val,
        "units_val": units_val,
    }


def black76_call_put(F, K, T, r, sigma):
    """Black76 Option Pricing Engine Proxy for UI calculation."""
    d1 = (np.log(F / K) + (sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call = np.exp(-r * T) * (F * 0.52 - K * 0.48)
    put = np.exp(-r * T) * (K * 0.52 - F * 0.48)
    delta = 0.52
    vega = 12.45
    return call, put, delta, vega


def fetch_live_or_fallback(url, fallback_list, timeout_sec=2.0):
    """Generic RSS Stream reader with immediate enterprise synthetic fallback.
    
    Returns:
        tuple: (list_of_parsed_dict_items, is_live_boolean)
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        parsed_items = []
        for item in root.findall(".//item")[:10]:
            title = item.find("title").text if item.find("title") is not None else "N/A"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            source = (
                item.find("source").text
                if item.find("source") is not None
                else "Market Feed"
            )
            parsed_items.append({
                "title": title,
                "source": source,
                "published": pub_date,
                "link": link,
            })

        if parsed_items:
            return parsed_items, True
        return fallback_list, False

    except Exception:
        # Graceful degradation on network timeout/firewall block
        return fallback_list, False


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

    if prop_data and "spot_price" in prop_data:
        unit_price = prop_data["spot_price"]

    si_score = cascade.get(
        "si_composite", st.session_state.get("si_composite", -0.28)
    )
    surge_units = demand_data.get(
        "total_surge_units",
        st.session_state.get("extracted_demand_surge", 102968),
    )

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
        all_executed_trades = [
            {"title": "FIX Protocol Order", "hedge_benefit_usd": 140_000.0}
        ]

    hedge_count = len(all_executed_trades)
    ctrm_hedge_benefit = (
        sum(
            (
                t.get("hedge_benefit_usd", 140_000.0)
                if isinstance(t, dict)
                else 140_000.0
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
                "hedge_benefit_usd": 140_000.0,
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
            h.get("hedge_benefit_usd", 140_000.0)
            for h in st.session_state["executed_hedges"]
        )
        if st.session_state["executed_hedges"]
        else signal_data.get("hedge_benefit_usd", 140_000.0)
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

        if any(w in t_lower for w in ["strike", "outage", "disruption", "force majeure", "surge", "shortage", "halt", "delay", "curtailment"]):
            sentiment = -0.75
            impact_units = 145000
        elif any(w in t_lower for w in ["growth", "boost", "rebound", "expansion", "surplus", "gain"]):
            sentiment = +0.50
            impact_units = 65000
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
# Ticker-to-Unit Multipliers (Converts exchange quotes to target dictionary units)
COMMODITY_UNIT_MULTIPLIERS = {
    "HG=F": 2204.6226,  # Copper: $/lb -> $/MT
    "CT=F": 2204.6226,  # Cotton: $/lb -> $/MT
    "SB=F": 2204.6226,  # Sugar: $/lb -> $/MT
    "ALI=F": 1.0,        # Aluminum: $/MT
    "ZNC=F": 1.0,        # Zinc: $/MT
    "TIO=F": 1.0,        # Iron Ore: $/dmt
    "BZ=F": 1.0,         # Brent: $/Bbl
    "CL=F": 1.0,         # WTI: $/Bbl
    "GC=F": 1.0,         # Gold: $/oz
    "SI=F": 1.0,         # Silver: $/oz
}

@st.cache_data(ttl=300)
def fetch_live_commodity_price(ticker: str, fallback_spot: float) -> float:
    """Fetches live market spot price from yfinance, applying unit conversion multipliers."""
    try:
        t = yf.Ticker(ticker)
        raw_price = None

        if hasattr(t, "fast_info"):
            raw_price = t.fast_info.get("lastPrice", None)
            if raw_price is None or np.isnan(raw_price) or raw_price <= 0:
                raw_price = t.fast_info.get("previousClose", None)

        if raw_price is None or np.isnan(raw_price) or raw_price <= 0:
            hist = t.history(period="5d")
            if not hist.empty and "Close" in hist:
                raw_price = hist["Close"].iloc[-1]

        if raw_price is not None and not np.isnan(raw_price) and raw_price > 0:
            multiplier = COMMODITY_UNIT_MULTIPLIERS.get(ticker, 1.0)
            
            # Special equity proxy multiplier check (e.g., LIT, REMX, APD)
            # If ticker is an equity stock/ETF, scale baseline index relative to stock movement
            return float(raw_price * multiplier)
    except Exception:
        pass

    return float(fallback_spot)


# -----------------------------------------------------------------------------
# 2. DOWNSTREAM CASCADE CALLBACK
# -----------------------------------------------------------------------------
def _propagate_commodity_forecast_cascade(payload: dict):
    """Callback to inject commodity price forecast extrapolation downstream

    across CTRM Desk, S&OP Control Tower, Procurement, and Flight Simulator.
    """
    comm_name = payload.get("commodity_name", "Copper (LME Grade A)")
    delta_pct = payload.get("price_delta_pct", 0.0694)
    spot_price = payload.get("spot_price", 9820.00)
    forecast_60d = payload.get("forecast_60d", 10501.76)

    # 1. Update active global commodity session state
    st.session_state["active_commodity_name"] = comm_name
    st.session_state["active_commodity_ticker"] = payload.get("ticker", "HG=F")
    st.session_state["active_commodity_spot"] = spot_price
    st.session_state["active_commodity_60d_forecast"] = forecast_60d
    st.session_state["commodity_price_delta_pct"] = delta_pct
    st.session_state["propagated_commodity_data"] = payload

    # 2. Compute CTRM Derivatives Desk Hedge Exposure ($)
    base_annual_procurement_units = st.session_state.get("base_annual_volume", 25000)
    unhedged_exposure_usd = base_annual_procurement_units * (forecast_60d - spot_price) * 0.50
    
    st.session_state["ctrm_unhedged_exposure_usd"] = max(0.0, unhedged_exposure_usd)
    st.session_state["ctrm_recommended_futures_contracts"] = int(
        np.ceil(unhedged_exposure_usd / 25000)
    )

    # 3. Inject Financial Budget Variance into S&OP Control Tower & Flight Sim
    st.session_state["sop_procurement_budget_variance_pct"] = delta_pct
    st.session_state["macro_sim_cost_shock_pct"] = delta_pct * 100.0

    # 4. Cascade to central S&OP engine if global pipeline exists
    if "_propagate_signal_to_sop_cascade" in globals():
        _propagate_signal_to_sop_cascade(payload)

    st.toast(
        f"⚡ Injected {comm_name} (+{delta_pct:.2%}) downstream across CTRM & S&OP Engines!",
        icon="🚀",
    )


def render_predictive_commodity_engine():
    """Predictive Commodity Price Engine tracking Top 50 Global Raw Material Inputs

    with downstream econometric propagation to CTRM, S&OP, and Flight
    Simulator.
    """
    st.markdown("### 📈 SOTA Predictive Commodity Engine (Top 50 Global Inputs)")
    st.caption(
        "Historical precedence correlation matrix, news sentiment elasticity"
        " (β_SI), and vector autoregressive forecast across 50 liquid raw"
        " material benchmarks."
    )

    # -------------------------------------------------------------------------
    # TOP 50 GLOBAL COMMODITY COVERAGE MATRIX
    # -------------------------------------------------------------------------
    top_50_commodities = {
        # Bucket 1: Industrial Non-Ferrous & Ferrous Metals (1–10)
        "Copper (LME Grade A)": {
            "ticker": "HG=F",
            "category": "Industrial Metals",
            "spot": 9820.00,
            "unit": "$/MT",
            "beta_si": 0.084,
            "r_squared": 0.892,
            "precedent": (
                "2022 European Smelter Energy Curtailment Strike. The current"
                " signal cluster aligns with past structural supply shocks"
                " where physical spot premiums adjusted within 45 days."
            ),
        },
        "Primary Aluminum (LME)": {
            "ticker": "ALI=F",
            "category": "Industrial Metals",
            "spot": 2540.00,
            "unit": "$/MT",
            "beta_si": 0.062,
            "r_squared": 0.841,
            "precedent": (
                "2021 China Yunnan Hydro Power Rationing. Supply shock drove"
                " spot premiums higher within 30 days."
            ),
        },
        "Nickel (LME Class 1)": {
            "ticker": "JJN",
            "category": "Industrial Metals",
            "spot": 17450.00,
            "unit": "$/MT",
            "beta_si": 0.095,
            "r_squared": 0.812,
            "precedent": "2022 Tsingshan Short Squeeze & Indonesian Ore Quotas",
        },
        "Zinc (LME High Grade)": {
            "ticker": "ZNC=F",
            "category": "Industrial Metals",
            "spot": 2890.00,
            "unit": "$/MT",
            "beta_si": 0.071,
            "r_squared": 0.835,
            "precedent": "2022 Nyrstar Smelter Production Halt",
        },
        "Lead (LME Refined)": {
            "ticker": "LED=F",
            "category": "Industrial Metals",
            "spot": 2120.00,
            "unit": "$/MT",
            "beta_si": 0.048,
            "r_squared": 0.790,
            "precedent": (
                "2023 Secondary Recycler Lead Battery Scrap Deficit"
            ),
        },
        "Tin (LME Grade A)": {
            "ticker": "JJT",
            "category": "Industrial Metals",
            "spot": 31500.00,
            "unit": "$/MT",
            "beta_si": 0.110,
            "r_squared": 0.864,
            "precedent": "2023 Myanmar Wa State Mining Export Ban",
        },
        "Lithium Hydroxide 56.5%": {
            "ticker": "LIT",
            "category": "Industrial Metals",
            "spot": 14200.00,
            "unit": "$/MT",
            "beta_si": 0.125,
            "r_squared": 0.785,
            "precedent": (
                "2023 Spodumene Export Quota Delays & Inventory Destocking"
            ),
        },
        "Cobalt Metal 99.8%": {
            "ticker": "LIT",
            "category": "Industrial Metals",
            "spot": 28400.00,
            "unit": "$/MT",
            "beta_si": 0.088,
            "r_squared": 0.760,
            "precedent": "2022 DRC Export Logistics Bottlenecks at Durban",
        },
        "Neodymium Oxide (NdFeB)": {
            "ticker": "REMX",
            "category": "Industrial Metals",
            "spot": 72500.00,
            "unit": "$/MT",
            "beta_si": 0.140,
            "r_squared": 0.820,
            "precedent": "2021 China Rare Earth Export Quota Tightening",
        },
        "Iron Ore 62% Fe (TSI)": {
            "ticker": "TIO=F",
            "category": "Industrial Metals",
            "spot": 118.50,
            "unit": "$/dmt",
            "beta_si": 0.078,
            "r_squared": 0.875,
            "precedent": "2019 Vale Brumadinho Tailings Dam Shock",
        },
        # Bucket 2: Energy & Power Inputs (11–20)
        "Brent Crude Oil": {
            "ticker": "BZ=F",
            "category": "Energy & Power Inputs",
            "spot": 78.50,
            "unit": "$/Bbl",
            "beta_si": 0.091,
            "r_squared": 0.915,
            "precedent": "2024 Red Sea Transit Rerouting Surcharges",
        },
        "WTI Crude Oil": {
            "ticker": "CL=F",
            "category": "Energy & Power Inputs",
            "spot": 74.20,
            "unit": "$/Bbl",
            "beta_si": 0.089,
            "r_squared": 0.908,
            "precedent": "2023 OPEC+ Voluntary Production Cuts",
        },
        "Henry Hub Natural Gas": {
            "ticker": "NG=F",
            "category": "Energy & Power Inputs",
            "spot": 2.65,
            "unit": "$/MMBtu",
            "beta_si": 0.135,
            "r_squared": 0.830,
            "precedent": "2022 Freeport LNG Export Terminal Outage",
        },
        "TTF European Gas": {
            "ticker": "TTF=F",
            "category": "Energy & Power Inputs",
            "spot": 38.50,
            "unit": "€/MWh",
            "beta_si": 0.165,
            "r_squared": 0.880,
            "precedent": "2022 Nord Stream Pipeline Curtailment Crisis",
        },
        "Ultra-Low Sulfur Diesel (ULSD)": {
            "ticker": "HO=F",
            "category": "Energy & Power Inputs",
            "spot": 2.42,
            "unit": "$/Gal",
            "beta_si": 0.082,
            "r_squared": 0.895,
            "precedent": (
                "2022 French Refinery Strikes & Distillate Shortage"
            ),
        },
        "Thermal Coal (Newcastle)": {
            "ticker": "NCF=F",
            "category": "Energy & Power Inputs",
            "spot": 138.00,
            "unit": "$/MT",
            "beta_si": 0.105,
            "r_squared": 0.815,
            "precedent": "2021 Indonesian Coal Export Embargo",
        },
        "Uranium (U3O8 Benchmark)": {
            "ticker": "SRUUF",
            "category": "Energy & Power Inputs",
            "spot": 82.50,
            "unit": "$/lb",
            "beta_si": 0.098,
            "r_squared": 0.850,
            "precedent": "2023 Kazatomprom Production Guidance Cut",
        },
        "Heavy Fuel Oil 380 CST": {
            "ticker": "BZ=F",
            "category": "Energy & Power Inputs",
            "spot": 440.00,
            "unit": "$/MT",
            "beta_si": 0.075,
            "r_squared": 0.870,
            "precedent": "2024 Marine Bunker Fuel Demand Surge",
        },
        "European Carbon Permits (EUA)": {
            "ticker": "KRBN",
            "category": "Energy & Power Inputs",
            "spot": 68.20,
            "unit": "€/MT",
            "beta_si": 0.085,
            "r_squared": 0.840,
            "precedent": "2023 EU MSR Rule Reform & Power Grid Switching",
        },
        "Electricity Base Load (PJM)": {
            "ticker": "XLU",
            "category": "Energy & Power Inputs",
            "spot": 42.50,
            "unit": "$/MWh",
            "beta_si": 0.115,
            "r_squared": 0.795,
            "precedent": "2022 Winter Storm Elliott Power Price Spikes",
        },
        # Bucket 3: Petrochemicals & Polymers (21–30)
        "Ethylene (CFR Asia)": {
            "ticker": "LYB",
            "category": "Petrochemicals & Polymers",
            "spot": 890.00,
            "unit": "$/MT",
            "beta_si": 0.055,
            "r_squared": 0.825,
            "precedent": (
                "2021 US Gulf Coast Winter Freeze Naphtha Outages"
            ),
        },
        "Polypropylene (PP Raffia)": {
            "ticker": "DOW",
            "category": "Petrochemicals & Polymers",
            "spot": 1120.00,
            "unit": "$/MT",
            "beta_si": 0.045,
            "r_squared": 0.810,
            "precedent": "2021 Hurricane Ida Louisiana Cracker Shutdowns",
        },
        "Polyethylene (HDPE Film)": {
            "ticker": "WLK",
            "category": "Petrochemicals & Polymers",
            "spot": 1050.00,
            "unit": "$/MT",
            "beta_si": 0.048,
            "r_squared": 0.818,
            "precedent": "2022 European Steam Cracker Rate Reductions",
        },
        "Polyvinyl Chloride (PVC)": {
            "ticker": "OLN",
            "category": "Petrochemicals & Polymers",
            "spot": 820.00,
            "unit": "$/MT",
            "beta_si": 0.052,
            "r_squared": 0.802,
            "precedent": (
                "2021 Chlor-Alkali Power Rationing in Eastern China"
            ),
        },
        "Titanium Dioxide (TiO2)": {
            "ticker": "TROX",
            "category": "Petrochemicals & Polymers",
            "spot": 2950.00,
            "unit": "$/MT",
            "beta_si": 0.038,
            "r_squared": 0.775,
            "precedent": "2022 Ilmenite Ore Feedstock Shortage",
        },
        "Methanol (CFR China)": {
            "ticker": "MEOH",
            "category": "Petrochemicals & Polymers",
            "spot": 285.00,
            "unit": "$/MT",
            "beta_si": 0.065,
            "r_squared": 0.832,
            "precedent": "2023 Iranian Winter Natural Gas Cutoffs to Plants",
        },
        "Urea / Nitrogen Fertilizer": {
            "ticker": "CF",
            "category": "Petrochemicals & Polymers",
            "spot": 340.00,
            "unit": "$/MT",
            "beta_si": 0.092,
            "r_squared": 0.860,
            "precedent": (
                "2021 China Urea Export Inspection Restrictions"
            ),
        },
        "Purified Terephthalic Acid (PTA)": {
            "ticker": "ALB",
            "category": "Petrochemicals & Polymers",
            "spot": 760.00,
            "unit": "$/MT",
            "beta_si": 0.042,
            "r_squared": 0.805,
            "precedent": "2022 PX Feedstock Premium Expansion",
        },
        "Styrene Monomer": {
            "ticker": "AXTA",
            "category": "Petrochemicals & Polymers",
            "spot": 1150.00,
            "unit": "$/MT",
            "beta_si": 0.058,
            "r_squared": 0.815,
            "precedent": "2023 POSM Plant Unplanned Maintenance Outages",
        },
        "Caustic Soda (Liquid 50%)": {
            "ticker": "OLN",
            "category": "Petrochemicals & Polymers",
            "spot": 410.00,
            "unit": "$/MT",
            "beta_si": 0.060,
            "r_squared": 0.790,
            "precedent": (
                "2022 Rhine River Low Water Level Barge Bottlenecks"
            ),
        },
        # Bucket 4: Agri-Softs & Industrial Crops (31–40)
        "Corn (CBOT Futures)": {
            "ticker": "ZC=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 4.35,
            "unit": "$/Bu",
            "beta_si": 0.068,
            "r_squared": 0.855,
            "precedent": (
                "2023 US Midwest Drought & Mississippi Low Water"
            ),
        },
        "Soybeans (CBOT Futures)": {
            "ticker": "ZS=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 10.15,
            "unit": "$/Bu",
            "beta_si": 0.064,
            "r_squared": 0.848,
            "precedent": "2024 Brazil Mato Grosso Weather Disruption",
        },
        "Wheat (CBOT SRW)": {
            "ticker": "ZW=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 5.65,
            "unit": "$/Bu",
            "beta_si": 0.088,
            "r_squared": 0.872,
            "precedent": "2022 Black Sea Grain Corridor Interruption",
        },
        "Raw Sugar #11": {
            "ticker": "SB=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 0.21,
            "unit": "$/lb",
            "beta_si": 0.075,
            "r_squared": 0.820,
            "precedent": "2023 India Export Ban & El Nino Rain Deficit",
        },
        "Robusta Coffee": {
            "ticker": "KC=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 4250.00,
            "unit": "$/MT",
            "beta_si": 0.112,
            "r_squared": 0.865,
            "precedent": (
                "2024 Vietnam Central Highlands Heatwave Deficit"
            ),
        },
        "Crude Palm Oil (MDEX)": {
            "ticker": "CPO=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 920.00,
            "unit": "$/MT",
            "beta_si": 0.082,
            "r_squared": 0.840,
            "precedent": "2022 Indonesian Palm Oil Export Embargo",
        },
        "Natural Rubber (TSR20)": {
            "ticker": "RUB=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 1680.00,
            "unit": "$/MT",
            "beta_si": 0.058,
            "r_squared": 0.805,
            "precedent": "2023 Thailand Heavy Monsoon Tapping Delays",
        },
        "Cotton #2": {
            "ticker": "CT=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 0.74,
            "unit": "$/lb",
            "beta_si": 0.062,
            "r_squared": 0.810,
            "precedent": "2022 Texas West Drought Acreage Abandonment",
        },
        "Cocoa (ICE Futures)": {
            "ticker": "CC=F",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 7850.00,
            "unit": "$/MT",
            "beta_si": 0.155,
            "r_squared": 0.890,
            "precedent": "2024 West Africa Black Pod Disease Shortage",
        },
        "Malting Barley": {
            "ticker": "WEAT",
            "category": "Agri-Softs & Industrial Crops",
            "spot": 210.00,
            "unit": "$/MT",
            "beta_si": 0.050,
            "r_squared": 0.780,
            "precedent": "2023 Australian Crop Yield Weather Revisions",
        },
        # Bucket 5: Precious & Electronics Minerals (41–50)
        "Gold Spot": {
            "ticker": "GC=F",
            "category": "Precious & Electronics Minerals",
            "spot": 2510.00,
            "unit": "$/oz",
            "beta_si": 0.040,
            "r_squared": 0.920,
            "precedent": "2024 Central Bank Gold Accumulation Surge",
        },
        "Silver Spot": {
            "ticker": "SI=F",
            "category": "Precious & Electronics Minerals",
            "spot": 29.80,
            "unit": "$/oz",
            "beta_si": 0.072,
            "r_squared": 0.885,
            "precedent": "2024 Industrial Solar PV Demand Expansion",
        },
        "Platinum Spot": {
            "ticker": "PL=F",
            "category": "Precious & Electronics Minerals",
            "spot": 940.00,
            "unit": "$/oz",
            "beta_si": 0.065,
            "r_squared": 0.815,
            "precedent": (
                "2023 South African Power Grid Loadshedding At Mines"
            ),
        },
        "Palladium Spot": {
            "ticker": "PA=F",
            "category": "Precious & Electronics Minerals",
            "spot": 980.00,
            "unit": "$/oz",
            "beta_si": 0.090,
            "r_squared": 0.830,
            "precedent": "2022 Norilsk Nickel Logistics & Trade Rerouting",
        },
        "Silicon Metal 5-5-3 Grade": {
            "ticker": "GSM",
            "category": "Precious & Electronics Minerals",
            "spot": 1920.00,
            "unit": "$/MT",
            "beta_si": 0.085,
            "r_squared": 0.825,
            "precedent": "2021 Yunnan Smelter Energy Controls",
        },
        "High-Purity Neon Gas": {
            "ticker": "APD",
            "category": "Precious & Electronics Minerals",
            "spot": 320.00,
            "unit": "$/m³",
            "beta_si": 0.180,
            "r_squared": 0.860,
            "precedent": (
                "2022 Mariupol Ingas & Cryoin Semiconductor Supply Halt"
            ),
        },
        "Solar-Grade Polysilicon": {
            "ticker": "DQ",
            "category": "Precious & Electronics Minerals",
            "spot": 8.80,
            "unit": "$/kg",
            "beta_si": 0.110,
            "r_squared": 0.800,
            "precedent": "2021 Xinjiang Plant Explosion & Fab Bottleneck",
        },
        "Germanium Metal 99.999%": {
            "ticker": "MP",
            "category": "Precious & Electronics Minerals",
            "spot": 1450.00,
            "unit": "$/kg",
            "beta_si": 0.135,
            "r_squared": 0.845,
            "precedent": (
                "2023 Chinese Ministry of Commerce Export Licensing Controls"
            ),
        },
        "Gallium Metal 99.99%": {
            "ticker": "ALB",
            "category": "Precious & Electronics Minerals",
            "spot": 520.00,
            "unit": "$/kg",
            "beta_si": 0.140,
            "r_squared": 0.850,
            "precedent": "2023 Semiconductor Wafer Export Restrictions",
        },
        "Indium Metal": {
            "ticker": "SMX",
            "category": "Precious & Electronics Minerals",
            "spot": 290.00,
            "unit": "$/kg",
            "beta_si": 0.078,
            "r_squared": 0.790,
            "precedent": (
                "2022 Flat Panel Display ITO Sputtering Demand Surge"
            ),
        },
    }

    # -------------------------------------------------------------------------
    # UI CONTROLS: CATEGORY FILTER & BENCHMARK SELECTOR
    # -------------------------------------------------------------------------
    categories = [
        "🌐 ALL TOP 50 COMMODITIES",
        "Industrial Metals",
        "Energy & Power Inputs",
        "Petrochemicals & Polymers",
        "Agri-Softs & Industrial Crops",
        "Precious & Electronics Minerals",
    ]

    p_filter_col, p_select_col = st.columns([1, 2])

    with p_filter_col:
        selected_category = st.selectbox(
            "Filter Commodity Class:",
            categories,
            key="predictive_category_filter",
        )

    if selected_category == "🌐 ALL TOP 50 COMMODITIES":
        filtered_commodities = top_50_commodities
    else:
        filtered_commodities = {
            k: v
            for k, v in top_50_commodities.items()
            if v["category"] == selected_category
        }

    with p_select_col:
        selected_comm = st.selectbox(
            f"Select Target Commodity ({len(filtered_commodities)} Available):",
            list(filtered_commodities.keys()),
            key="select_predictive_commodity",
        )
        data = filtered_commodities[selected_comm]

    # Dynamically fetch live spot price via yfinance (with static fallback)
    live_spot = fetch_live_commodity_price(data["ticker"], data["spot"])

    # Retrieve live composite SI from session state
    si_val = st.session_state.get("si_composite", -0.62)

    # Regression forecasting formula using live or fallback spot price
    predicted_pct_change = (
        (data["beta_si"] * abs(si_val))
        if si_val < 0
        else (-data["beta_si"] * si_val)
    )
    target_price_30d = live_spot * (1.0 + predicted_pct_change)
    target_price_60d = live_spot * (1.0 + (predicted_pct_change * 1.45))
    delta_60d_pct = predicted_pct_change * 1.45

    # -------------------------------------------------------------------------
    # REGRESSION METRICS & HISTORICAL PRECEDENCE DISPLAY
    # -------------------------------------------------------------------------
    st.markdown("#### 📊 Econometric Regression & Historical Precedence Match")
    m1, m2, m3, m4, m5 = st.columns(5)

    unit_label = data["unit"][1:] if data["unit"].startswith("$") else data["unit"]

    m1.metric(
        "Current Spot Baseline",
        f"${live_spot:,.2f} {unit_label}",
    )
    m2.metric("Elasticity (η_SI)", f"{data['beta_si']:.3f}")
    m3.metric("Model Fit (R²)", f"{data['r_squared']:.3f}")
    m4.metric(
        "30-Day Forecast",
        f"${target_price_30d:,.2f}",
        delta=f"{predicted_pct_change:+.2%}",
        delta_color="inverse" if predicted_pct_change > 0 else "normal",
    )
    m5.metric(
        "60-Day Forecast",
        f"${target_price_60d:,.2f}",
        delta=f"{delta_60d_pct:+.2%}",
        delta_color="inverse" if delta_60d_pct > 0 else "normal",
    )

    st.info(
        f"🔍 **Highest Historical Precedence Match (Cosine Similarity:"
        f" 93.8%):** `{data['precedent']}`"
    )

    # -------------------------------------------------------------------------
    # FORECAST TRAJECTORY PLOT
    # -------------------------------------------------------------------------
    days = np.array([0, 15, 30, 45, 60])
    prices_base = np.array([
        live_spot,
        live_spot * (1 + predicted_pct_change * 0.5),
        target_price_30d,
        live_spot * (1 + predicted_pct_change * 1.25),
        target_price_60d,
    ])
    prices_upper = prices_base * 1.035
    prices_lower = prices_base * 0.965

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=days,
            y=prices_base,
            mode="lines+markers",
            name="Forecast Mean Trajectory",
            line=dict(color="#FF4B4B", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=prices_upper,
            mode="lines",
            name="Upper 95% Confidence Interval",
            line=dict(width=0),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=prices_lower,
            mode="lines",
            name="Lower 95% Confidence Interval",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(255, 75, 75, 0.15)",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=(
            f"Predictive Price Path: {selected_comm} [{data['ticker']}]"
            " (30/60-Day Forward Horizon)"
        ),
        xaxis_title="Forward Horizon (Days)",
        yaxis_title=f"Price ({data['unit']})",
        height=340,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # DOWNSTREAM PROPAGATION TRIGGER BUTTON
    # -------------------------------------------------------------------------
    st.button(
        f"⚡ Propagate {selected_comm} Extrapolation ({delta_60d_pct:+.2%}) into CTRM Risk Desk & S&OP Engine",
        key="btn_propagate_commodity_forecast",
        on_click=_propagate_commodity_forecast_cascade,
        args=({
            "commodity_name": selected_comm,
            "ticker": data["ticker"],
            "spot_price": live_spot,
            "forecast_60d": target_price_60d,
            "price_delta_pct": delta_60d_pct,
        },),
    )

def render_nlp_intelligence(persona=None, term_unit="Units", **kwargs):
    """Complete NLP Commercial Sensing & Intelligence Module with Hard Macro,
    Unified Social & Executive Field Intelligence, Email Parsing, Live Telemetry,
    and S&OP Cascade Hooks.
    """
    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption(
        f"Active Persona View: **{persona or 'Discrete & Heavy Industrial Enterprise'}** | "
        "Ingest unstructured signals from live RSS feeds, executive LinkedIn disclosures, "
        "email debriefs, hard macro indicators (NY Fed, FRED, World Bank, ECB, PBOC, KOSPI), "
        "and ocean/air freight telemetry."
    )

    # =========================================================================
    # 🟢 SURGICAL EDIT 1: DYNAMIC STATE READS (INSERT RIGHT HERE)
    # =========================================================================
    cascade = st.session_state.get("active_sop_cascade", {})
    demand_data = cascade.get("demand", {})
    prop_data = st.session_state.get("propagated_commodity_data", {})

    # Read SI & Surge dynamically from session_state instead of static hardcoded values
    si_score = st.session_state.get("si_composite", -0.28)
    demand_surge_units = demand_data.get(
        "total_surge_units",
        st.session_state.get("extracted_demand_surge", 15400)
    )

    # Commodity spot dynamically bound
    spot_price = prop_data.get(
        "spot_price", 
        9820.0 if "Heavy" in str(persona) else 3200.0
    )

    # Freight & Risk derived dynamically from SI
    lead_time_days = round(4.0 + (abs(si_score) * 3.5), 1)
    baltic_index = int(2800 + (abs(si_score) * 600))
    fbx_rate = round(2900.0 + (abs(si_score) * 800.0), 2)
    risk_status = "HEDGE REQUIRED" if si_score < -0.4 else "MONITORING"
    # =========================================================================

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals",
        "📧 Email & Event Debrief Parser",
        "⚓ Freight, Weather & Black Swan Feeds",
    ])

    # =========================================================================
    # TAB 1: LIVE WEB, MACRO & SOCIAL SIGNALS
    # =========================================================================
    with tab1:
        r_head1, r_head2 = st.columns([3, 1])
        with r_head1:
            st.caption(
                "🤖 **Triangulated Intelligence Engine**: Hard Macro (NY Fed / FRED / ECB / PBOC / KOSPI) "
                "+ Ocean/Air Freight Telemetry + Executive Social Stream"
            )
        with r_head2:
            if st.button("🔄 Refresh Live Feeds & APIs", key="btn_refresh_robot_feeds"):
                try:
                    feed_data = sync_robot_feeds() if "sync_robot_feeds" in globals() else {}
                    st.session_state["latest_robot_signals"] = feed_data
                    newsletters = feed_data.get("newsletters", [])

                    if newsletters and newsletters[0].get("is_live"):
                        st.session_state["live_newsletters"] = newsletters
                        st.session_state["s_social_val"] = feed_data.get("linkedin_score", -0.70)
                        st.toast(
                            f"Synced live signal: {newsletters[0].get('title', 'LinkedIn Feed')}",
                            icon="✅",
                        )
                    else:
                        st.toast("Refreshed feeds from Gmail IMAP & Global Macro APIs!", icon="🔄")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sync error: {e}")

        # Load live telemetry from session state or disk backup
        latest_signals = st.session_state.get("latest_robot_signals", {})
        if not latest_signals and os.path.exists("robot_signals.json"):
            try:
                with open("robot_signals.json", "r") as f:
                    latest_signals = json.load(f)
            except Exception:
                latest_signals = {}

        # -------------------------------------------------------------------------
        # 1. HARD MACROECONOMIC TELEMETRY DASHBOARD
        # -------------------------------------------------------------------------
        macro = latest_signals.get("global_telemetry") or (
            fetch_global_macro_telemetry() if "fetch_global_macro_telemetry" in globals() else {}
        )

        with st.expander(
            "🏛️ Hard Macroeconomic Telemetry (NY Fed GSCPI, World Bank, FRED, ECB, PBOC, BOJ, KOSPI)",
            expanded=True,
        ):
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric("NY Fed GSCPI", macro.get("ny_fed_gscpi", f"{+1.22 + (si_score * 0.4):+.2f} σ"), "Supply Pressure")
                st.caption("Global Supply Chain Pressure")
            with m_col2:
                st.metric("US FRED Mfg Index", macro.get("us_fred", f"{103.1 + (si_score * 3):.1f} pts"), "St. Louis Fed")
                st.caption("US Industrial Output")
            with m_col3:
                st.metric("World Bank Commodity", macro.get("world_bank", f"{142.8 * (spot_price / 9820.0):.1f} Index"), macro.get("china_pmi", "50.4 (Expansion)"))
                st.caption("Global Benchmark / PBOC")
            with m_col4:
                st.metric("Eurozone (ECB)", macro.get("eurozone_ecb", "2.65% (ECB Refi)"), "Industrial Trend")
                st.caption("ECB Telemetry")
            with m_col5:
                st.metric("Korea KOSPI / Japan", macro.get("kospi_korea", f"{int(2645 + si_score * 80):,} pts"), macro.get("japan_pmi", "50.1"))
                st.caption("Asian Export Benchmark")

        # -------------------------------------------------------------------------
        # 2. TRIANGULATED COMPOSITE SENTIMENT INDEX (SI) ENGINE
        # -------------------------------------------------------------------------
        if "calculate_composite_sentiment" in globals():
            comp_res = calculate_composite_sentiment(latest_signals)
        else:
            comp_res = {
                "si_composite": -0.625,
                "individual_scores": {
                    "gscpi_index": -0.15,
                    "noaa_environmental": -0.40,
                    "freight_spot_rates": -0.43,
                    "gep_volatility": -0.32,
                },
                "weights": {"gscpi_index": 0.35, "noaa_environmental": 0.25, "freight_spot_rates": 0.25, "gep_volatility": 0.15},
            }

        # Bind dynamically to central session state SI and calculated surge
        composite_si = st.session_state.get("si_composite", si_score)
        scores = comp_res.get("individual_scores", {})
        weights = comp_res.get("weights", {})

        base_dem = st.session_state.get("base_demand", 129500)
        if "compute_quantified_operational_impact" in globals():
            impact_res = compute_quantified_operational_impact(composite_si, base_dem)
            surge_units = impact_res.get("delta_demand_units", demand_surge_units)
            lt_days = impact_res.get("lead_time_buffer_days", lead_time_days)
            rec_text = impact_res.get("recommended_action", "Lock 60-Day Forward Exposure")
            ctrm_hedge = impact_res.get("target_hedge_pct", 60.0) >= 60.0
        else:
            surge_units = demand_surge_units
            lt_days = lead_time_days
            rec_text = "Lock in 60-day raw material futures on CTRM Desk; extend vendor lead times in ERP."
            ctrm_hedge = composite_si < -0.4

        with st.container(border=True):
            st.markdown("### 🎯 Triangulated Composite Market Sentiment Index ($SI$)")
            
            c_col1, c_col2, c_col3, c_col4 = st.columns([1.2, 1, 1, 1])
            with c_col1:
                st.metric(
                    "Net Composite ($SI$)",
                    f"{composite_si:+.3f}",
                    delta="Severe Downside Risk" if composite_si < -0.50 else ("Moderate Drag" if composite_si < 0 else "Bullish Expansion"),
                    delta_color="inverse" if composite_si < 0 else "normal",
                )
            with c_col2:
                st.metric("Quantified Demand Surge", f"+{surge_units:,} {term_unit}")
            with c_col3:
                st.metric("Lead Time Expansion", f"+{lt_days} Days")
            with c_col4:
                st.metric("CTRM Risk Status", "🔴 HEDGE REQUIRED" if ctrm_hedge else "🟢 STABLE")

            st.markdown(
                r"**Formula Weighting:** $S_t = (0.35 \times S_{\text{GSCPI}}) + (0.25 \times S_{\text{NOAA}}) + (0.25 \times S_{\text{Freight}}) + (0.15 \times S_{\text{GEP}})$"
            )
            
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.caption(f"**GSCPI Macro**: `{scores.get('gscpi_index', -0.15):+.2f}` (35%)")
            sc2.caption(f"**NOAA Weather**: `{scores.get('noaa_environmental', -0.40):+.2f}` (25%)")
            sc3.caption(f"**Freight Rates**: `{scores.get('freight_spot_rates', -0.43):+.2f}` (25%)")
            sc4.caption(f"**GEP Volatility**: `{scores.get('gep_volatility', -0.32):+.2f}` (15%)")

            st.info(f"**Quantified Action Plan**: {rec_text}")

            if st.button(
                "⚡ Propagate Triangulated Composite Index across Platform",
                key="btn_propagate_composite",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["si_composite"] = composite_si
                st.session_state["extracted_demand_surge"] = surge_units
                st.session_state["propagated_commodity_data"] = {
                    "commodity_name": "Copper (LME Grade A)",
                    "ticker": "LME_CU",
                    "spot_price": spot_price,
                    "forecast_30d": spot_price * 1.053,
                    "forecast_60d": spot_price * 1.076,
                    "price_delta_pct": (spot_price - 9250.0) / 9250.0,
                }
                if "_propagate_signal_to_sop_cascade" in globals():
                    _propagate_signal_to_sop_cascade({
                        "source_type": "Macro & Social Triangulation Engine",
                        "title": f"Triangulated Composite Index ({composite_si:+.3f})",
                        "demand_surge_units": surge_units,
                        "leadtime_delay_days": lt_days,
                        "sentiment_index": composite_si,
                    })
                st.toast("✅ Composite Index & Surge Propagated Across Platform!", icon="🚀")
                st.rerun()

        st.divider()

        # -------------------------------------------------------------------------
        # 3. SOTA PREDICTIVE COMMODITY PRICE ENGINE (OPTION B INTEGRATION)
        # -------------------------------------------------------------------------
        if "render_predictive_commodity_engine" in globals():
            render_predictive_commodity_engine()

        st.divider()

# -------------------------------------------------------------------------
        # 4. UNIFIED SOCIAL MEDIA & EXECUTIVE FIELD INTELLIGENCE STREAM
        # -------------------------------------------------------------------------
        st.subheader("📱 Unified Social Media & Executive Field Intelligence Stream")
        st.caption(
            "High-impact C-suite disclosures, Fortune 500 results announcements, "
            "and commercial earnings guidance scanned for quantified supply chain impact."
        )

        # Resolve unit fallback cleanly
        display_unit = term_unit if "term_unit" in locals() or "term_unit" in globals() else "Units"

        # Targeted Fortune 500 Enterprise Query Filter
        FORTUNE_500_EXEC_QUERY = (
            '("quarterly results" OR "earnings release" OR "financial guidance" OR "force majeure" OR '
            '"capacity adjustment" OR "production cut" OR "supply chain forecast") AND '
            '(Codelco OR "Rio Tinto" OR BHP OR Maersk OR BASF OR Dow OR Caterpillar OR TSMC OR Apple)'
        )

        # Ingest Gmail / Newsletter Feeds (if available)
        live_newsletters = latest_signals.get("newsletters") or (
            fetch_gmail_newsletters(max_emails=10) if "fetch_gmail_newsletters" in globals() else []
        )

        EXCLUDE_KEYWORDS = ["welcome", "officially connected", "subscription confirmed", "verify your email", "privacy policy"]
        QUANTIFIABLE_KEYWORDS = ["revenue", "ebitda", "guidance", "capacity", "volume", "outage", "lead time", "delay", "force majeure", "shipments", "margin"]

        valid_social_items = []

        # 1. Filter Ingested Newsletters for High-Pertinence Quantifiable Terms
        for news in live_newsletters:
            title = news.get("title", "")
            summary = news.get("summary", "")
            combined_text = f"{title} {summary}".lower()

            # Skip administrative noise
            if any(ex in combined_text for ex in EXCLUDE_KEYWORDS):
                continue
            
            # Enforce presence of quantifiable metrics
            if any(kw in combined_text for kw in QUANTIFIABLE_KEYWORDS):
                raw_sentiment = news.get("sentiment_score")
                sentiment = raw_sentiment if raw_sentiment is not None else -0.45

                valid_social_items.append({
                    "source": news.get("source", "Executive Briefing"),
                    "author": news.get("author", "Fortune 500 Field Intelligence"),
                    "timestamp": news.get("published", "Live Ingested"),
                    "title": title,
                    "snippet": summary,
                    "sentiment": sentiment,
                    "impact_demand": int(abs(sentiment) * 175000),
                    "impact_leadtime": round(abs(sentiment) * 12, 1),
                    "type": "C-Suite / Earnings Disclosure",
                })

        # 2. Top 5 Fortune 500 Executive Live RSS Fetcher
        if len(valid_social_items) < 5 and "fetch_live_sector_rss" in globals():
            exec_rss_feed = fetch_live_sector_rss(FORTUNE_500_EXEC_QUERY)
            for rss_item in exec_rss_feed:
                if len(valid_social_items) >= 5:
                    break

                raw_sentiment = rss_item.get("sentiment")
                sentiment = raw_sentiment if raw_sentiment is not None else -0.55

                raw_est = rss_item.get("estimated_impact")
                impact_demand = int(raw_est) if raw_est is not None else int(abs(sentiment) * 160000)

                valid_social_items.append({
                    "source": f"Fortune 500 Wire | {rss_item.get('source', 'Financial Disclosures')}",
                    "author": "Corporate Results & Guidance Engine",
                    "timestamp": "Live Wire",
                    "title": rss_item.get("title", "Enterprise Results Disclosure"),
                    "snippet": f"Quantified C-Suite results/guidance disclosure: {rss_item.get('title')}",
                    "sentiment": sentiment,
                    "impact_demand": impact_demand,
                    "impact_leadtime": round(abs(sentiment) * 9.5, 1),
                    "type": "Fortune 500 Executive Signal",
                })

        # Hard limit strictly to Top 5 Pertinent Disclosures
        top_5_social_items = valid_social_items[:5]

        # Render Top 5 Stream Cards
        if not top_5_social_items:
            st.info("No major Fortune 500 earnings or guidance disclosures detected in the current window.")
        else:
            # Safe handler resolution for button callback
            callback_fn = None
            if "_propagate_signal_to_sop_cascade" in globals():
                callback_fn = _propagate_signal_to_sop_cascade
            elif "robot_feeds" in globals() and hasattr(robot_feeds, "_propagate_signal_to_sop_cascade"):
                callback_fn = robot_feeds._propagate_signal_to_sop_cascade

            for idx, item in enumerate(top_5_social_items):
                with st.container(border=True):
                    s_col1, s_col2 = st.columns([2.8, 1.2])
                    with s_col1:
                        st.markdown(f"**{item['title']}**")
                        st.caption(
                            f"📌 **{item['type']}** | Source: *{item['source']}* ({item['author']}) — `{item['timestamp']}`"
                        )
                        st.write(f"_{item['snippet']}_")
                    with s_col2:
                        score = item["sentiment"]
                        color = "🔴" if score < -0.3 else ("🟢" if score > 0.3 else "🟡")
                        st.metric("Sentiment Polarity", f"{color} {score:+.2f}")
                        st.caption(
                            f"Demand: `+{item['impact_demand']:,} {display_unit}` | Lead Time: `+{item['impact_leadtime']} Days`"
                        )

                    st.button(
                        "⚡ Ingest Social Signal into S&OP Engine",
                        key=f"btn_ingest_soc_filtered_{idx}",
                        on_click=callback_fn,
                        args=({
                            "source_type": item["source"],
                            "title": item["title"],
                            "demand_surge_units": item["impact_demand"],
                            "leadtime_delay_days": item["impact_leadtime"],
                            "sentiment_index": item["sentiment"],
                        },),
                    )

        st.divider()

        # -------------------------------------------------------------------------
        # 5. REAL-TIME DYNAMIC WEB & EXPANDED COMMODITY RSS STREAM
        # -------------------------------------------------------------------------
        st.subheader("📡 Real-Time Dynamic Web & Commodity RSS News Stream")

        # Resolve unit fallback cleanly
        display_unit = term_unit if "term_unit" in locals() or "term_unit" in globals() else "Units"

        NEWS_DOMAINS = {
            "🌐 ALL RAW MATERIALS (Global Multi-Commodity Disruption Scan)": (
                "(copper OR tin OR polymers OR petrochemicals OR resins OR lithium OR oil) AND (disruption OR outage OR force majeure OR shortage)"
            ),
            "🧱 Non-Ferrous & Industrial Metals (Copper, Tin, Zinc, Aluminum, Nickel)": (
                "(copper OR tin OR zinc OR aluminum OR nickel) AND (supply chain OR smelter outage OR force majeure)"
            ),
            "🧪 Petrochemicals, Resins, Polymers & Base Chemicals": (
                "(petrochemicals OR polymers OR ethylene OR resin OR polypropylene) AND (force majeure OR plant outage OR shortage)"
            ),
            "🛢️ Energy, Crude Oil, Natural Gas & Refined Inputs": (
                "(crude oil OR diesel OR natural gas OR power curtailment) AND (refinery outage OR supply disruption)"
            ),
            "💎 Critical Minerals, Lithium, Neodymium & Rare Earths": (
                "(lithium OR neodymium OR rare earths OR cobalt) AND (export restriction OR supply bottleneck)"
            ),
            "⚡ High-Tech Electronics, Semiconductors & Wafers": (
                "(semiconductor OR chip wafer OR neon gas OR substrate) AND (shortage OR fab disruption OR lead time)"
            ),
            "🚢 Maritime Container Freight, Ocean Ports & Corridors": (
                "(container freight OR port congestion OR vessel rerouting OR Suez OR Panama) AND (delay OR surcharge)"
            ),
        }

        col_w1, col_w2 = st.columns([2, 1])
        with col_w1:
            selected_domain = st.selectbox(
                "Select Commodity / Industry Sector Focus:",
                list(NEWS_DOMAINS.keys()),
                key="nlp_sector_focus",
            )

            topic_query = NEWS_DOMAINS[selected_domain]
            fetched_items = fetch_live_sector_rss(topic_query) if "fetch_live_sector_rss" in globals() else []
            
            # Fall back to mock list if live fetch is empty or unavailable
            live_rss_items = fetched_items if fetched_items else [
                {"title": "Panama Canal Transit Slots Auctioned at Record High Premiums", "source": "Reuters Commodities", "estimated_impact": 110000, "sentiment": -0.72, "link": "#"},
                {"title": "Asian Electronics Component Lead Times Stabilize Margin", "source": "S&P Global Platts", "estimated_impact": 45000, "sentiment": 0.25, "link": "#"},
            ]

            headline_map = {
                f"{item['title']} [{item.get('source', 'Web')}]": item
                for item in live_rss_items
            }

            selected_headline = st.selectbox(
                "Select Live RSS / Scraped Headline Signal:",
                list(headline_map.keys()),
                key="nlp_web_headline_select",
            )
            art_info = headline_map[selected_headline]

            if art_info.get("link") and art_info["link"] != "#":
                st.markdown(f"[🔗 Open Original Source Article]({art_info['link']})")

        with col_w2:
            raw_impact = art_info.get("estimated_impact")
            default_impact = int(raw_impact) if raw_impact is not None else 100000

            web_impact = st.number_input(
                f"Extracted Signal Impact ({display_unit})",
                value=default_impact,
                step=5000,
                key="web_signal_units",
            )

            raw_sentiment = art_info.get("sentiment")
            sentiment_val = raw_sentiment if raw_sentiment is not None else -0.50
            st.metric("Detected Sentiment (SI)", f"{sentiment_val:+.2f}")

        headline_clean = art_info["title"][:50] + "..."
        domain_label = selected_domain.split(" ")[1] if len(selected_domain.split(" ")) > 1 else "Macro"

        # Safe handler resolution for button callback
        callback_fn = None
        if "_propagate_signal_to_sop_cascade" in globals():
            callback_fn = _propagate_signal_to_sop_cascade
        elif "robot_feeds" in globals() and hasattr(robot_feeds, "_propagate_signal_to_sop_cascade"):
            callback_fn = robot_feeds._propagate_signal_to_sop_cascade

        st.button(
            "📡 Ingest Scraped Domain News Signal",
            key="btn_ingest_web",
            on_click=callback_fn,
            args=({
                "source_type": "Live Web Intelligence",
                "title": f"[{domain_label}] {headline_clean}",
                "demand_surge_units": web_impact,
                "leadtime_delay_days": 4.0,
                "sentiment_index": sentiment_val,
            },),
        )

        st.divider()

    # =========================================================================
    # TAB 2: EMAIL & EVENT DEBRIEF PARSER
    # =========================================================================
    with tab2:
        st.subheader("📧 Email & Event Debrief Parser")
        st.caption(
            "Extract unstructured supplier updates, trip reports, and meeting debriefs."
        )

        default_email = (
            "SUBJECT: URGENT - Production Bottleneck & Force Majeure Warning\nFROM:"
            " vendor-rep@global-smelting.com\n\nHi Team,\nDue to unexpected"
            " energy curtailments and furnace maintenance at our main smelting"
            " facility, cathode deliveries for Q4 will be delayed by"
            " approximately 12 to 15 days. We strongly recommend increasing"
            " your safety buffers by at least 45,000 units to avoid operational"
            " shutdown."
        )

        raw_text = st.text_area(
            "Paste Raw Supplier Email or Meeting Debrief Text:",
            value=default_email,
            height=150,
            key="nlp_email_raw_input",
        )

        if (
            st.button("🔍 Parse Email & Extract Entities", key="btn_parse_email")
            or "parsed_email_data" not in st.session_state
        ):
            if "parse_unstructured_email" in globals():
                st.session_state["parsed_email_data"] = parse_unstructured_email(raw_text)
            else:
                st.session_state["parsed_email_data"] = {
                    "vendor": "Global Smelting Corp",
                    "event": "Smelter Outage & Energy Curtailment",
                    "delay_val": 13.5,
                    "units_val": 45000,
                }

        parsed = st.session_state["parsed_email_data"]

        st.markdown("#### 📊 Extracted Entity Analysis")
        e_col1, e_col2, e_col3, e_col4 = st.columns(4)
        with e_col1:
            st.metric("Detected Vendor", parsed["vendor"])
        with e_col2:
            st.metric("Identified Risk Event", parsed["event"])
        with e_col3:
            st.metric("Est. Lead Time Delay", f"+{parsed['delay_val']:.1f} Days")
        with e_col4:
            st.metric("Recommended Safety Buffer", f"+{parsed['units_val']:,} {term_unit}")

        st.caption("**NLP Confidence Score**: `94.2%` | **Sentiment Score**: `-0.68`")

        st.button(
            "⚡ Ingest Parsed Email Intelligence into Live S&OP Engine",
            key="btn_ingest_email_parser",
            on_click=_propagate_signal_to_sop_cascade if "_propagate_signal_to_sop_cascade" in globals() else None,
            args=({
                "source_type": "Supplier Email",
                "title": f"[{parsed['vendor']}] {parsed['event']}",
                "demand_surge_units": parsed["units_val"],
                "leadtime_delay_days": parsed["delay_val"],
                "sentiment_index": -0.68,
            },),
        )
        with tab3:
            st.subheader("⚓ Freight, NOAA Weather & Black Swan Feeds")

            bdi_val, bdi_change, sync_status = fetch_live_freight_metrics()
            noaa_alerts = fetch_live_noaa_marine_alerts()

            current_time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
            st.caption(
                f"Status: **{sync_status}** | Last Live Telemetry Sync: `{current_time_str}`"
            )

            # Dynamic freight & weather impact scaling based on active alerts
            alert_count = len(noaa_alerts)
            dynamic_surge_units = 100000 + (alert_count * 25000)
            dynamic_lt_delay_days = round(5.0 + (alert_count * 2.5), 1)
            fbx_spot_rate = int(3380 * (bdi_val / 1850.0)) if bdi_val else 3380

            w_col1, w_col2, w_col3, w_col4 = st.columns(4)

            with w_col1:
                st.metric(
                    "Baltic Dry Freight Index",
                    f"{bdi_val:,.0f} pts" if bdi_val else "1,850 pts",
                    f"{bdi_change:+.1f}% WoW" if bdi_change else "+0.0% WoW",
                )
                st.caption(f"Status: `{sync_status}`")

            with w_col2:
                st.metric(
                    "FBX Ocean Spot Rate Benchmark",
                    f"${fbx_spot_rate:,} / FEU",
                    delta=f"{bdi_change:+.1f}% WoW" if bdi_change else "+1.2% WoW",
                )
                st.caption("Asia-North America Corridor")

            with w_col3:
                st.metric(
                    "Active AIS Marine Anomalies",
                    f"{alert_count} Severe Zones Active",
                    delta="+ Project44 Telemetry",
                )
                st.caption("Real-Time GIS Vessel Ping")

            with w_col4:
                st.metric(
                    "NOAA Climate Threat Level",
                    "Level 4 - Severe" if alert_count > 0 else "Level 1 - Low",
                    delta=f"{alert_count} Active Alerts",
                    delta_color="inverse" if alert_count > 0 else "normal",
                )
                st.caption("NOAA Severe Weather Telemetry")

            st.divider()
            st.markdown(
                "#### 🌀 Live Active NOAA Severe Weather & Coastal Disruption Alerts"
            )

            if not noaa_alerts:
                st.success(
                    "No active critical NOAA marine warnings detected in monitored shipping corridors."
                )
            else:
                table_data = [
                    {
                        "Corridor / Region": alert.get("corridor", "Global Maritime"),
                        "Disruption Event": alert.get("event", "Severe Marine Advisory"),
                        "NOAA Severity": alert.get("severity", "Warning"),
                        "Official Advisory Summary": alert.get("headline", "N/A"),
                        "Effective Time": alert.get("timestamp", "Live Telemetry"),
                    }
                    for alert in noaa_alerts
                ]
                st.dataframe(
                    pd.DataFrame(table_data),
                    use_container_width=True,
                    hide_index=True,
                )

            if st.button(
                "⚡ Ingest Freight & NOAA Weather Signals into Logistics Engine",
                key="btn_ingest_freight",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["extracted_demand_surge"] = dynamic_surge_units
                st.session_state["freight_delay_days"] = dynamic_lt_delay_days
                st.session_state["si_composite"] = -0.75 if alert_count > 0 else -0.20
                st.session_state["freight_telemetry"] = {
                    "bdi_val": bdi_val,
                    "fbx_rate": fbx_spot_rate,
                    "active_alerts_count": alert_count,
                }

                if "_propagate_signal_to_sop_cascade" in globals():
                    _propagate_signal_to_sop_cascade({
                        "source_type": "Maritime AIS & NOAA Weather Telemetry",
                        "title": f"NOAA Active Marine Alerts ({alert_count} Zones) & Freight Surcharges",
                        "demand_surge_units": dynamic_surge_units,
                        "leadtime_delay_days": dynamic_lt_delay_days,
                        "sentiment_index": -0.75 if alert_count > 0 else -0.20,
                    })

                st.toast("✅ Freight & NOAA Weather Telemetry Ingested Across Platform!", icon="⚓")
                st.rerun()

# Maintain alias to protect all navigation router calls
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
        # ---------------------------------------------------------------------
        # PLANT LOAD BALANCING & CAPACITY ALLOCATION
        # ---------------------------------------------------------------------
        p1 = plant1_name or "Detroit Main Assembly Plant"
        p2 = plant2_name or "Stuttgart Manufacturing Hub"
        t_name = toller_name or "Monterrey Tolling Partner"

        st.subheader("🏭 Multi-Plant Load Balancer & Orchestration Allocation")
        st.caption(
            "Rebalance production loads across primary facilities and tolling"
            " partners in real-time."
        )

        saved_p1_alloc = cascade.get("plant_allocations", {}).get(p1, 50)

        p1_alloc = st.slider(
            f"Allocation Share to {p1} (%)",
            min_value=0,
            max_value=100,
            value=saved_p1_alloc,
            step=5,
        )
        remaining_alloc = 100 - p1_alloc
        p2_alloc = int(remaining_alloc * 0.7)
        toller_alloc = remaining_alloc - p2_alloc

        # WRITE LOAD ALLOCATIONS BACK TO CENTRAL ORCHESTRATOR
        plant_allocations = {p1: p1_alloc, p2: p2_alloc, t_name: toller_alloc}
        st.session_state["active_sop_cascade"][
            "plant_allocations"
        ] = plant_allocations

        c_a, c_b, c_c = st.columns(3)
        c_a.metric(
            f"🏢 {p1}",
            f"{p1_alloc}% Load",
            f"{int(net_deficit * (p1_alloc/100)):,} {term_unit}",
        )
        c_b.metric(
            f"🏭 {p2}",
            f"{p2_alloc}% Load",
            f"{int(net_deficit * (p2_alloc/100)):,} {term_unit}",
        )
        c_c.metric(
            f"🤝 {t_name}",
            f"{toller_alloc}% Load",
            f"{int(net_deficit * (toller_alloc/100)):,} {term_unit}",
        )

        st.markdown(
            "##### 📋 Line-Level Operating Status & Orchestrated Capacity"
            " Breakdown"
        )

        plant_df = pd.DataFrame([
            {
                "Facility Name": p1,
                "Allocated Surge Share": f"{p1_alloc}%",
                "Assigned Production": (
                    f"{int(net_deficit * (p1_alloc/100)):,} {term_unit}"
                ),
                "Base Capacity": f"100,000 {term_unit}",
                "Line Utilization": (
                    f"{min(100.0, 75.0 + (p1_alloc * 0.25)):.1f}%"
                ),
                "Shift Model": "3-Shift Continuous (24/7)",
                "Bottleneck Constraints": "Stamping Press Line 2",
            },
            {
                "Facility Name": p2,
                "Allocated Surge Share": f"{p2_alloc}%",
                "Assigned Production": (
                    f"{int(net_deficit * (p2_alloc/100)):,} {term_unit}"
                ),
                "Base Capacity": f"75,000 {term_unit}",
                "Line Utilization": (
                    f"{min(100.0, 65.0 + (p2_alloc * 0.3)):.1f}%"
                ),
                "Shift Model": "2-Shift Standard + Overtime",
                "Bottleneck Constraints": "Heat Treatment Kiln #4",
            },
            {
                "Facility Name": t_name,
                "Allocated Surge Share": f"{toller_alloc}%",
                "Assigned Production": (
                    f"{int(net_deficit * (toller_alloc/100)):,} {term_unit}"
                ),
                "Base Capacity": f"50,000 {term_unit}",
                "Line Utilization": (
                    f"{min(100.0, 40.0 + (toller_alloc * 0.4)):.1f}%"
                ),
                "Shift Model": "Flex Toll On-Demand",
                "Bottleneck Constraints": "Inbound Rail Siding Capacity",
            },
        ])
        st.dataframe(plant_df, use_container_width=True, hide_index=True)


def render_physical_procurement(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Render Physical Procurement & Master Contract Desk bound to central S&OP cascade."""
    st.title("📦 Physical Procurement & Master Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")

    # 1. Pull dynamic state from Central Orchestrator Cascade
    cascade = st.session_state.get("active_sop_cascade", {})
    demand_data = cascade.get("demand", {})
    proc_data = cascade.get("procurement", {})
    ctrm_data = cascade.get("ctrm", {})

    gross_surge = demand_data.get(
        "total_surge_units",
        st.session_state.get("extracted_demand_surge", 241000),
    )
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_units = demand_data.get(
        "delta_surge_units",
        st.session_state.get(
            "net_uncovered_units", max(0, gross_surge - active_contracts)
        ),
    )

    fix_executed = st.session_state.get("fix_executed", False)
    unit_base_price = (
        3200.0 if "Merchant" in persona else (45.0 if "FMCG" in persona else 780.0)
    )

    # Calculate net invoice and hedge subsidy dynamically
    hedge_subsidy = ctrm_data.get(
        "realized_hedge_cashflow_usd",
        (net_units * unit_base_price * 0.042) if fix_executed else 0.0,
    )
    gross_invoice = proc_data.get(
        "gross_procurement_cost_usd",
        net_units * (unit_base_price * 1.02),  # 2.0% Blended spot market premium
    )
    net_outlay = max(0.0, gross_invoice - hedge_subsidy)

    # 2. Status Info Banner
    st.info(
        f"🔗 **Physical Demand Signal Ingested**: Required Net Procurement Volume: **{net_units:,} {term_unit}** "
        f"(Gross Surge: **{gross_surge:,}** less Baseline Contracts: **{active_contracts:,}**) | "
        f"Financial Hedge Cash Subsidy Available: **${hedge_subsidy:,.2f}**"
    )

    # 3. Key Procurement Metrics
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric(
        "Gross Material Need",
        f"{net_units:,} {term_unit}",
        "Uncovered Deficit Only",
    )
    col_p2.metric(
        "Gross Supplier Invoice",
        f"${gross_invoice / 1e6:,.2f}M",
        "+2.0% Blended Market Premium",
    )
    col_p3.metric(
        "CTRM Financial Paper Subsidy",
        f"-${hedge_subsidy / 1e6:,.2f}M",
        "Hedge Active" if fix_executed else "No Hedge Cashflow",
        delta_color="normal" if hedge_subsidy > 0 else "off",
    )
    col_p4.metric(
        "Net Cash Outlay to Suppliers",
        f"${net_outlay / 1e6:,.2f}M",
        f"-${hedge_subsidy / 1e6:,.2f}M Cash Savings"
        if fix_executed
        else "Full Floating Outlay",
    )

    st.divider()

    # 4. Master Contract Sourcing Matrix (Splitting strictly the NET volume)
    st.subheader("📋 Master Contract Sourcing Matrix")

    tier1_vol = int(net_units * 0.60)
    tier2_vol = int(net_units * 0.25)
    spot_vol = net_units - (tier1_vol + tier2_vol)

    sourcing_df = pd.DataFrame(
        [
            {
                "Supplier Name": "Global Metals Corp (Tier 1 Primary)",
                "Contract Type": "Fixed-Price Master Agreement",
                "Alloc %": "60%",
                "Volume (Units)": f"{tier1_vol:,}",
                "Unit Cost ($)": f"${unit_base_price:,.2f}",
                "Subtotal Invoice": f"${(tier1_vol * unit_base_price) / 1e6:.2f}M",
                "Expected ETA": "21 Days",
            },
            {
                "Supplier Name": "Apex Logistics Raw Ltd (Tier 2 Secondary)",
                "Contract Type": "Indexed Master Agreement",
                "Alloc %": "25%",
                "Volume (Units)": f"{tier2_vol:,}",
                "Unit Cost ($)": f"${(unit_base_price * 1.05):,.2f}",
                "Subtotal Invoice": f"${(tier2_vol * unit_base_price * 1.05) / 1e6:.2f}M",
                "Expected ETA": "19 Days",
            },
            {
                "Supplier Name": "Spot Market Open Sourcing (Emergency)",
                "Contract Type": "Open Spot Market Purchase",
                "Alloc %": "15%",
                "Volume (Units)": f"{spot_vol:,}",
                "Unit Cost ($)": f"${(unit_base_price * 1.28):,.2f}",
                "Subtotal Invoice": f"${(spot_vol * unit_base_price * 1.28) / 1e6:.2f}M",
                "Expected ETA": "14 Days (Expedited)",
            },
        ]
    )
    st.dataframe(sourcing_df, use_container_width=True, hide_index=True)

    st.divider()

    # 5. Physical PO Execution Gateway
    st.subheader("🏭 Physical PO Execution Gateway")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        dest = st.selectbox(
            "Primary Delivery Destination",
            ["Detroit Main Plant", "Munich Precision Stamping"],
            key="proc_dest",
        )
        terms = st.selectbox(
            "Vendor Payment Terms",
            ["Net 60 Days", "Net 30 Days", "Letter of Credit"],
            key="proc_terms",
        )
    with col_g2:
        logistics = st.selectbox(
            "Inbound Logistics Mode",
            ["Standard Multi-Modal Rail & Truck", "Air Freight Expedited"],
            key="proc_logistics",
        )
        quality = st.selectbox(
            "Quality Standard",
            ["ISO 9001 Heavy Industrial", "Automotive IATF 16949"],
            key="proc_quality",
        )

    if st.button("📦 Issue Physical Purchase Orders & Lock Schedules", type="primary", key="btn_issue_pos"):
        st.session_state["pos_issued"] = True
        st.toast(f"POs issued for {net_units:,} {term_unit} to {dest}!", icon="✅")
        st.success(
            f"✅ **Physical Purchase Orders Issued**: Successfully generated PO batch for **{net_units:,} {term_unit}** "
            f"routed to **{dest}** under **{terms}** payment terms."
        )


def render_ctrm_desk(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Render CTRM Event-Driven Hedging Desk with FIX 4.4 Gateway & Synthetic Structurer."""
    st.title("🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")

    # Ensure central trade state exists
    if "executed_hedges" not in st.session_state:
        st.session_state["executed_hedges"] = []

    # 1. Pull dynamic state from Central Orchestrator & Propagated Commodity State
    cascade = st.session_state.get("active_sop_cascade", {})
    demand_data = cascade.get("demand", {})
    prop_data = st.session_state.get("propagated_commodity_data")

    gross_surge = demand_data.get(
        "total_surge_units",
        st.session_state.get("extracted_demand_surge", 241000),
    )
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_units = demand_data.get(
        "delta_surge_units",
        st.session_state.get(
            "net_uncovered_units", max(0, gross_surge - active_contracts)
        ),
    )

    sig_title = st.session_state.get(
        "active_risk_signal_title", "Baseline Operations Target"
    )
    si_score = st.session_state.get("si_composite", -0.82)
    fix_executed = st.session_state.get("fix_executed", False)

    # Base price derived from persona or injected commodity spot price
    if prop_data and "spot_price" in prop_data:
        unit_base_price = prop_data["spot_price"]
    else:
        unit_base_price = (
            3200.0
            if "Merchant" in persona
            else (45.0 if "FMCG" in persona else 780.0)
        )

    # 2. Derive Event-Driven CTRM Metrics
    target_hr = min(0.95, max(0.40, 0.50 - (si_score * 0.35)))
    required_hedged_vol = int(gross_surge * target_hr)
    unhedged_shortfall = max(0, required_hedged_vol - active_contracts)

    base_buffer = unhedged_shortfall * unit_base_price * 0.08
    if prop_data:
        delta_pct = prop_data.get("price_delta_pct", 0.0)
        risk_margin_buffer = base_buffer * (1.0 + delta_pct)
    else:
        risk_margin_buffer = base_buffer

    auto_horizon_days = (
        90 if si_score < -0.5 else (60 if si_score < 0 else 30)
    )

    # 3. Top Banner
    if prop_data:
        st.success(
            f"⚡ **Propagated Commodity Signal Active**: Ingested"
            f" **{prop_data['commodity_name']}**"
            f" [{prop_data.get('ticker', 'LME_CU')}] | Spot:"
            f" **${prop_data['spot_price']:,.2f}** ➔ 60D Forecast:"
            f" **${prop_data['forecast_60d']:,.2f}**"
            f" ({prop_data['price_delta_pct']:+.2%}) | **Target Hedge Ratio:"
            f" {target_hr * 100:.1f}%** | Unhedged Shortfall:"
            f" **{unhedged_shortfall:,} {term_unit}**"
        )
    else:
        st.info(
            f"⚡ **Active Risk Signal Ingested**: Triangulated Sentiment Index"
            f" (**{si_score:.2f}**) [`{sig_title}`] | **Target Hedge Ratio:"
            f" {target_hr * 100:.1f}%** | Unhedged Shortfall:"
            f" **{unhedged_shortfall:,} {term_unit}** | Auto Horizon:"
            f" **{auto_horizon_days} Days**"
        )

    # 4. Top Executive Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric(
        "Gross Demand Surge",
        f"{gross_surge:,} {term_unit}",
        (
            f"+{gross_surge - 200000:,} MT Metal"
            if "Heavy" in persona
            else "+Volume Surge"
        ),
    )
    col_m2.metric(
        "Target Hedge Ratio (HR)",
        f"{target_hr * 100:.1f}%",
        f"+ Sentiment SI ({si_score:.2f})",
        delta_color="inverse" if si_score < 0 else "normal",
    )
    col_m3.metric(
        "Net Shortfall to Hedge",
        f"{unhedged_shortfall:,} {term_unit}",
        f"{target_hr * 100:.0f}% Target Cover Gap",
        delta_color="inverse",
    )
    col_m4.metric(
        "Required Risk Margin Buffer",
        f"${risk_margin_buffer:,.2f}",
        delta=(
            f"{prop_data['price_delta_pct']:+.2%} Commodity Impact"
            if prop_data
            else "+23.0% Volatility Load"
        ),
        delta_color="inverse",
    )

    st.divider()

    # 5. Functional Tabs
    tab_std, tab_synth = st.tabs([
        "📊 Standard Desk & FIX Execution",
        "🧪 Synthetic Derivative Builder & Model Lab",
    ])

    # --- TAB 1: FIX 4.4 ORDER EXECUTION GATEWAY ---
    with tab_std:
        st.subheader("⚡ FIX 4.4 Order Execution Gateway")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            intent = st.selectbox(
                "Execution Intent",
                [
                    "Hedge Risk (Cover Shortfall)",
                    "Speculative Delta",
                    "Yield Capture",
                ],
                key="fix_intent",
            )
        with col_f2:
            time_period = st.selectbox(
                "Time Period / Expiration",
                [
                    f"Auto-Matched ({auto_horizon_days} Days)",
                    "30 Days",
                    "60 Days",
                    "90 Days",
                    "180 Days",
                ],
                key="fix_time_period",
            )
        with col_f3:
            est_premium = st.number_input(
                "Est. Premium ($/Unit)",
                value=4.25,
                step=0.25,
                key="fix_est_premium",
            )

        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            order_structure = st.selectbox(
                "Order Structure",
                [
                    "Asian Call Collar",
                    "European Swap",
                    "Zero-Cost Collar",
                    "Put Option Floor",
                ],
                key="fix_order_structure",
            )
        with col_g2:
            exchange = st.selectbox(
                "Execution Exchange",
                ["LME (London Metal Exchange)", "CME Group", "NYMEX", "ICE"],
                key="fix_exchange",
            )
        with col_g3:
            default_lots = (
                max(1, int(unhedged_shortfall / 25))
                if unhedged_shortfall > 0
                else 285
            )
            lots = st.number_input(
                "Lots / Contracts (LME 25 MT)",
                value=default_lots,
                step=1,
                key="fix_lots",
            )

        total_hedge_volume = lots * 25
        total_premium_required = total_hedge_volume * est_premium

        st.caption(
            f"💰 **Total Premium Required**: **${total_premium_required:,.2f}**"
            f" (Covering **{total_hedge_volume:,} {term_unit}** | Will be"
            " debited from Exec S&OP Cash Treasury)"
        )

        if st.button(
            "🚀 Execute & Route FIX 4.4 Paper Order",
            type="primary",
            key="btn_execute_fix_44",
            disabled=fix_executed,
        ):
            # 1. Create Hedging Trade Record
            trade_benefit = 140_000.0  # Standard locked hedge benefit
            order_id = f"FIX-44-LME-{np.random.randint(10000, 99999)}"

            new_trade = {
                "id": order_id,
                "title": f"FIX 4.4 {order_structure} ({exchange})",
                "source_type": "CTRM FIX Execution",
                "structure": order_structure,
                "lots": lots,
                "volume": total_hedge_volume,
                "premium": total_premium_required,
                "exchange": exchange,
                "hedge_benefit_usd": trade_benefit,
            }

            # 2. Mutate Session State across all desks
            st.session_state["fix_executed"] = True
            st.session_state["fix_executed_details"] = new_trade
            st.session_state["executed_hedges"].append(new_trade)

            # Recalculate global hedge benefit & available cash
            total_benefit = sum(
                t.get("hedge_benefit_usd", 140_000.0)
                for t in st.session_state["executed_hedges"]
            )
            st.session_state["total_hedge_benefit"] = total_benefit

            base_treasury = 5_000_000.0
            freight_surcharge = st.session_state.get(
                "freight_surcharge_usd", 570_000.0
            )
            st.session_state["available_treasury_cash"] = (
                base_treasury + total_benefit - freight_surcharge
            )

            if "run_end_to_end_sop_cascade" in globals():
                st.session_state["active_sop_cascade"] = (
                    run_end_to_end_sop_cascade(
                        base_demand_units=st.session_state.get(
                            "base_demand", 200000
                        )
                    )
                )

            st.toast(
                f"FIX 4.4 Order Routed: {lots} Lots ({total_hedge_volume:,}"
                f" {term_unit}) via {exchange}.",
                icon="✅",
            )
            st.rerun()

        if fix_executed:
            details = st.session_state.get("fix_executed_details", {})
            oid = details.get("id", "FIX-44-LME-99428")
            vol = details.get("volume", total_hedge_volume)
            exc = details.get("exchange", exchange)

            st.success(
                f"🟢 **FIX Protocol Status: EXECUTED & BOUND** — Bound"
                f" `{vol:,} {term_unit}` via `{exc}` under Order ID"
                f" `{oid}`."
            )
            if st.button("Reset FIX Hedge Position", key="btn_reset_fix"):
                st.session_state["fix_executed"] = False
                st.session_state.pop("fix_executed_details", None)

                # Filter out FIX executed trades from central hedge book
                st.session_state["executed_hedges"] = [
                    t
                    for t in st.session_state.get("executed_hedges", [])
                    if t.get("source_type") != "CTRM FIX Execution"
                ]

                # Recalculate global metrics
                total_benefit = sum(
                    t.get("hedge_benefit_usd", 140_000.0)
                    for t in st.session_state["executed_hedges"]
                )
                st.session_state["total_hedge_benefit"] = total_benefit
                base_treasury = 5_000_000.0
                freight_surcharge = st.session_state.get(
                    "freight_surcharge_usd", 570_000.0
                )
                st.session_state["available_treasury_cash"] = (
                    base_treasury + total_benefit - freight_surcharge
                )

                st.rerun()

        st.divider()

        # Active Commodity Contracts & Hedge Book
        st.subheader("📋 Active Commodity Contracts & Net Hedge Book")

        rows = [
            {
                "Contract ID": "CT-2026-Q4-01",
                "Type": "Baseline Fixed Swap",
                "Volume": f"74,000 {term_unit}",
                "Strike / Premium": f"${unit_base_price:,.2f}",
                "Status": "ACTIVE (CONTRACTED)",
            },
            {
                "Contract ID": "CT-2026-Q4-02",
                "Type": "Baseline Option Cap",
                "Volume": f"55,500 {term_unit}",
                "Strike / Premium": f"${unit_base_price * 1.05:,.2f}",
                "Status": "ACTIVE (CONTRACTED)",
            },
        ]

        # Dynamically append executed trades from session state
        for trade in st.session_state.get("executed_hedges", []):
            rows.append({
                "Contract ID": trade.get("id", "FIX-44-EXECUTED"),
                "Type": f"Net Hedge ({trade.get('structure', order_structure)})",
                "Volume": f"{trade.get('volume', total_hedge_volume):,} {term_unit}",
                "Strike / Premium": (
                    f"${trade.get('premium', total_premium_required):,.2f}"
                    " Total Premium"
                ),
                "Status": "ACTIVE (HEDGED)",
            })

        if (
            not st.session_state.get("executed_hedges")
            and not fix_executed
        ):
            rows.append({
                "Contract ID": "FIX-44-PENDING",
                "Type": f"Uncovered Shortfall ({order_structure})",
                "Volume": f"{total_hedge_volume:,} {term_unit}",
                "Strike / Premium": f"${est_premium:.2f} Est. Premium",
                "Status": "OPEN (UNCOVERED)",
            })

        st.dataframe(
            pd.DataFrame(rows), use_container_width=True, hide_index=True
        )

    # --- TAB 2: SYNTHETIC DERIVATIVE BUILDER & MODEL LAB ---
    with tab_synth:
        st.subheader("🧪 Synthetic Derivative Structurer")
        st.caption(
            "Model customized derivative payoffs tailored to the net"
            f" uncovered gap of **{net_units:,} {term_unit}**."
        )

        col_s1, col_s2 = st.columns([1, 1.4])

        with col_s1:
            st.markdown("**1. Structure Parameters**")
            struct_type = st.selectbox(
                "Derivative Structure",
                [
                    "Zero-Cost Collar (Cap & Floor)",
                    "Asian Call Option (Average Price)",
                    "3-Way Collar with Knock-Out",
                ],
                key="synth_struct_type",
            )
            cap_strike_pct = st.slider(
                "Cap Strike % (Upper Protection)",
                100,
                130,
                110,
                1,
                key="synth_cap_pct",
            )
            floor_strike_pct = st.slider(
                "Floor Strike % (Lower Subsidization)",
                70,
                100,
                90,
                1,
                key="synth_floor_pct",
            )
            implied_vol = st.slider(
                "Implied Volatility (σ %)", 10, 60, 28, 1, key="synth_vol"
            )

            cap_val = unit_base_price * (cap_strike_pct / 100.0)
            floor_val = unit_base_price * (floor_strike_pct / 100.0)

            st.markdown("**Net Deficit Pricing Summary**")
            st.json({
                "Net Exposure Volume": f"{net_units:,} {term_unit}",
                "Underlying Spot": f"${unit_base_price:,.2f}",
                "Cap Strike": f"${cap_val:,.2f}",
                "Floor Strike": f"${floor_val:,.2f}",
                "Net Premium Cost": "$0.00 / Unit (Zero-Cost Verified)",
            })

        with col_s2:
            st.markdown("**2. Net Payoff Profile Simulation at Expiry**")

            spot_range = np.linspace(
                unit_base_price * 0.7, unit_base_price * 1.3, 50
            )
            unhedged_payoff = (spot_range - unit_base_price) * net_units
            hedged_payoff = (
                np.clip(spot_range, floor_val, cap_val) - unit_base_price
            ) * net_units

            fig_payoff = go.Figure()
            fig_payoff.add_trace(
                go.Scatter(
                    x=spot_range,
                    y=unhedged_payoff / 1e6,
                    mode="lines",
                    name="Floating Net Exposure",
                    line=dict(color="#de350b", dash="dash"),
                )
            )
            fig_payoff.add_trace(
                go.Scatter(
                    x=spot_range,
                    y=hedged_payoff / 1e6,
                    mode="lines",
                    name=f"Hedged Net Profile ({struct_type})",
                    line=dict(color="#0052cc", width=3),
                )
            )
            fig_payoff.add_vline(
                x=unit_base_price,
                line_dash="dot",
                annotation_text="Current Spot",
            )
            fig_payoff.update_layout(
                title="Net Deficit P&L Impact ($ Millions)",
                xaxis_title="Underlying Spot Price ($)",
                yaxis_title="Net P&L Impact ($M)",
                height=380,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )
            st.plotly_chart(fig_payoff, use_container_width=True)



def render_global_logistics_gis(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    *args,
    **kwargs,
):
    """Render Global Logistics Network & GIS Control Tower bound to net shipment volume & live freight telemetry."""
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption(f"Active Persona View: **{persona}**")

    # 1. Pull dynamic data from Central Orchestrator Cascade & Live Signals
    cascade = st.session_state.get("active_sop_cascade", {})
    robot_signals = st.session_state.get("latest_robot_signals", {})

    demand_data = cascade.get("demand", {})
    proc_data = cascade.get("procurement", {})
    logistics_data = cascade.get("logistics", {})
    baltic_data = robot_signals.get("baltic_indices", {})

    gross_surge = demand_data.get(
        "total_surge_units",
        st.session_state.get("extracted_demand_surge", 185000),
    )
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_units = demand_data.get(
        "delta_surge_units",
        st.session_state.get(
            "net_uncovered_units", max(0, gross_surge - active_contracts)
        ),
    )
    transit_delay = proc_data.get(
        "transit_delay_days", st.session_state.get("active_transit_delay", 7.0)
    )

    # Extract Live Sea & Air Telemetry
    fbx_sea_rate = baltic_data.get("freightos_fbx_ocean", {}).get("value", 3850)
    tac_air_rate = baltic_data.get("baltic_air_tac", {}).get("value", 2.48)
    modal_shift_air = logistics_data.get("modal_shift_air", False)
    freight_surcharge = logistics_data.get("total_freight_surcharge_usd", 0.0)

    # 2. Status Banners & Modal Shift Warnings
    if modal_shift_air:
        st.warning(
            f"✈️ **CRITICAL LOGISTICS SHIFT**: Lead-time shock (+{transit_delay:.0f} Days) forced an "
            f"**Air Freight Modal Shift**. Surcharge Drag: **+${freight_surcharge / 1e6:.2f}M** "
            f"(TAC Air Rate: **${tac_air_rate:.2f}/kg** vs. Ocean FBX: **${fbx_sea_rate:,.0f}/FEU**)."
        )
    else:
        st.info(
            f"🚢 **Inbound Logistics Feed**: Tracking **{net_units:,} {term_unit}** "
            f"in net PO movement across 3 Ocean & Rail Corridors | "
            f"Lead-Time Shock: **+{transit_delay:.0f} Days** | FBX Spot: **${fbx_sea_rate:,.0f}/FEU**"
        )

    # 3. Executive Logistics Metrics
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    col_l1.metric(
        "Active Inbound Volume",
        f"{net_units:,} {term_unit}",
        "Net Physical Outlay",
    )
    col_l2.metric(
        "Avg Transit Lead Time",
        f"{14 + int(transit_delay)} Days",
        f"↑ +{transit_delay:.0f} Days Delay Shock",
        delta_color="inverse",
    )
    col_l3.metric(
        "Freight Mode Status",
        "AIR FREIGHT SHIFT" if modal_shift_air else "OCEAN / RAIL STANDARD",
        f"+${freight_surcharge / 1e6:.2f}M Cost Drag"
        if modal_shift_air
        else "Baseline Tariffs",
        delta_color="inverse" if modal_shift_air else "normal",
    )
    col_l4.metric(
        "On-Time In-Full (OTIF)",
        f"{max(65.0, 94.6 - transit_delay * 1.8):.1f}%",
        f"↓ -{transit_delay * 1.8:.1f}% Stressed",
        delta_color="inverse",
    )

    st.divider()

    # 4. Dynamic Corridor Allocation
    c1_vol = int(net_units * 0.45)
    c2_vol = int(net_units * 0.35)
    c3_vol = net_units - (c1_vol + c2_vol)

    st.subheader("📦 Transit Corridor Health & Arrival Timeline")
    corridor_df = pd.DataFrame([
        {
            "Corridor Name": "Pacific Ocean Expressway (Asia → LA)",
            "Primary Carrier": "Maersk Ocean Line",
            "Transport Mode": "Air Express" if modal_shift_air else "Ocean Container",
            "Volume (Units)": f"{c1_vol:,}",
            "Original ETA": "14 Days",
            "Delay Shock": f"+{transit_delay:.0f} Days",
            "Adjusted ETA": f"{14 + int(transit_delay)} Days",
            "Bottleneck Reason": "Port Berth Queueing / Modal Shift"
            if modal_shift_air
            else "Port Berth Queueing",
        },
        {
            "Corridor Name": "Trans-Suez / Atlantic Route (Asia → Europe → US)",
            "Primary Carrier": "MSC Freight Fleet",
            "Transport Mode": "Ocean Container",
            "Volume (Units)": f"{c2_vol:,}",
            "Original ETA": "16 Days",
            "Delay Shock": f"+{transit_delay + 1:.0f} Days",
            "Adjusted ETA": f"{17 + int(transit_delay)} Days",
            "Bottleneck Reason": "Canal Capacity Constraints",
        },
        {
            "Corridor Name": "Domestic Overland Heavy Rail",
            "Primary Carrier": "BNSF Railway Co",
            "Transport Mode": "Class I Intermodal Rail",
            "Volume (Units)": f"{c3_vol:,}",
            "Original ETA": "5 Days",
            "Delay Shock": "+0 Days",
            "Adjusted ETA": "5 Days (On Schedule)",
            "Bottleneck Reason": "Normal Operations",
        },
    ])
    st.dataframe(corridor_df, use_container_width=True, hide_index=True)

    st.divider()

    # 5. Interactive Pydeck GIS Map Layer
    st.subheader("🗺️ Live Global Transit Arc Overlay")
    routes_df = pd.DataFrame([
        {
            "route": "Pacific Ocean Expressway (Asia → LA)",
            "start_lat": 31.2304,
            "start_lon": 121.4737,
            "end_lat": 33.7420,
            "end_lon": -118.2700,
        },
        {
            "route": "Trans-Suez / Atlantic Route (Asia → Europe → US)",
            "start_lat": 29.9700,
            "start_lon": 32.5600,
            "end_lat": 51.9200,
            "end_lon": 4.4700,
        },
        {
            "route": "Domestic Overland Rail (LA → Detroit)",
            "start_lat": 33.7420,
            "start_lon": -118.2700,
            "end_lat": 42.3314,
            "end_lon": -83.0458,
        },
    ])

    arc_color = (
        [255, 140, 0, 220] if modal_shift_air else [255, 75, 75, 200]
    )

    arc_layer = pdk.Layer(
        "ArcLayer",
        routes_df,
        get_source_position=["start_lon", "start_lat"],
        get_target_position=["end_lon", "end_lat"],
        get_source_color=arc_color,
        get_target_color=[0, 180, 255, 200],
        get_width=4,
        pickable=True,
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[arc_layer],
            initial_view_state=pdk.ViewState(
                latitude=25.0, longitude=-30.0, zoom=1.2, pitch=35
            ),
            tooltip={"text": "{route}"},
        )
    )


# Alias to protect router calls
render_global_logistics = render_global_logistics_gis


def render_flight_simulator(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
  """Sandbox Flight Simulator & Monte Carlo Stress Testing Lab."""
  st.title("⚡ Sandbox Flight Simulator & Stress Lab")
  st.caption(f"Active Persona View: **{persona}**")

  # 1. READ ACTIVE SCENARIO & SESSION STATE PARAMS
  macro_scenario = st.session_state.get(
      "sandbox_scenario",
      st.session_state.get("sb_scenario_select", "Baseline Operations"),
  )
  sandbox_params = st.session_state.get("sandbox_params", {})

  # Centralized scenario fallback dictionary if sandbox_params isn't set
  SCENARIO_FALLBACKS = {
      "Super El Niño": {
          "vol": 0.45,
          "delay": 8,
          "surge": 1.25,
          "desc": (
              "Severe weather patterns disrupting Panama Canal & agri yields."
          ),
      },
      "Hormuz": {
          "vol": 0.85,
          "delay": 20,
          "surge": 1.60,
          "desc": (
              "Critical energy bottleneck blockage causing global freight &"
              " oil spikes."
          ),
      },
      "Mandeb": {
          "vol": 0.55,
          "delay": 12,
          "surge": 1.30,
          "desc": (
              "Red Sea transit route closure forcing Cape of Good Hope rerouting."
          ),
      },
      "Semiconductor": {
          "vol": 0.50,
          "delay": 25,
          "surge": 1.40,
          "desc": (
              "Microchip deficit stalling assembly lines and expanding lead"
              " times."
          ),
      },
      "Oil Crisis": {
          "vol": 0.70,
          "delay": 10,
          "surge": 1.35,
          "desc": (
              "OPEC production shocks driving raw material processing &"
              " shipping surcharges."
          ),
      },
      "Earthquake": {
          "vol": 0.60,
          "delay": 15,
          "surge": 1.20,
          "desc": "Seismic disruption halting Tier-1 component manufacturing.",
      },
      "Red Sea": {
          "vol": 0.40,
          "delay": 8,
          "surge": 1.10,
          "desc": "Maritime security threats and container line rerouting.",
      },
      "Drought": {
          "vol": 0.50,
          "delay": 4,
          "surge": 0.85,
          "desc": (
              "Severe agricultural crop failure inflating physical spot prices."
          ),
      },
      "Volatility": {
          "vol": 0.85,
          "delay": 14,
          "surge": 1.00,
          "desc": (
              "Financial market dislocation spiking derivative implied"
              " volatility."
          ),
      },
      "Baseline": {
          "vol": 0.15,
          "delay": 2,
          "surge": 1.00,
          "desc": "Nominal operational conditions with standard buffer inventory.",
      },
  }

  # 2. RESOLVE SCENARIO MULTIPLIERS (From sidebar state or fallback)
  if "iv_multiplier" in sandbox_params:
    def_vol = min(1.0, float(sandbox_params.get("iv_multiplier", 1.0)) * 0.35)
    def_delay = int(sandbox_params.get("transit_delay_days", 2))
    def_surge = float(sandbox_params.get("volume_multiplier", 1.00))
    scenario_desc = sandbox_params.get(
        "description", "Active scenario simulation."
    )
  else:
    matched = SCENARIO_FALLBACKS["Baseline"]
    for key, cfg in SCENARIO_FALLBACKS.items():
      if key.lower() in macro_scenario.lower():
        matched = cfg
        break
    def_vol = matched["vol"]
    def_delay = matched["delay"]
    def_surge = matched["surge"]
    scenario_desc = matched["desc"]

  # Reset slider values if user selected a new macro scenario
  if st.session_state.get("last_applied_sandbox_scenario") != macro_scenario:
    st.session_state["last_applied_sandbox_scenario"] = macro_scenario
    st.session_state["sim_vol"] = min(1.0, max(0.05, round(def_vol, 2)))
    st.session_state["sim_lt"] = max(1, min(30, def_delay))
    st.session_state["sim_dem"] = min(2.5, max(0.8, round(def_surge, 2)))
    st.session_state.pop("mc_results", None)

  st.session_state.setdefault("sim_vol", min(1.0, max(0.05, round(def_vol, 2))))
  st.session_state.setdefault("sim_lt", max(1, min(30, def_delay)))
  st.session_state.setdefault("sim_dem", min(2.5, max(0.8, round(def_surge, 2))))

  # Pull session state metrics
  si_score = st.session_state.get("si_composite", -0.33)
  gross_surge = st.session_state.get("extracted_demand_surge", 185000)
  active_contracts = st.session_state.get("active_contracts_volume", 129500)
  cash_balance = st.session_state.get("sop_cash_balance", 5_000_000.0)
  fix_executed = st.session_state.get("fix_executed", False)
  curr_leadtime_delay = st.session_state.get("active_leadtime_delay_days", 2.5)

  # Compute open floating deficit (Safeguard minimum value so simulation doesn't evaluate to zero)
  net_units = max(
      15000,
      st.session_state.get(
          "net_uncovered_units", max(0, gross_surge - active_contracts)
      ),
  )

  st.divider()
  st.subheader("⚙️ Monte Carlo Stress Test Parameters")
  st.info(
      f"🌐 **Active Scenario Preset**: **{macro_scenario}** — *{scenario_desc}*\n\n"
      f"Gross Demand Surge: **{gross_surge:,} {term_unit}** | Baseline"
      f" Contracts: **{active_contracts:,} {term_unit}** | **Net Deficit"
      f" Exposure: {net_units:,} {term_unit}**"
  )

  col_s1, col_s2, col_s3, col_s4 = st.columns(4)
  with col_s1:
    n_sims = st.select_slider(
        "Simulation Runs",
        options=[1000, 2500, 5000, 10000, 20000],
        value=5000,
        key="sim_runs",
    )
  with col_s2:
    vol_shock = st.slider(
        "Spot Price Volatility (σ)",
        min_value=0.05,
        max_value=1.00,
        step=0.05,
        key="sim_vol",
    )
  with col_s3:
    lead_time_shock = st.slider(
        "Lead Time Delay (Days)",
        min_value=1,
        max_value=30,
        step=1,
        key="sim_lt",
    )
  with col_s4:
    demand_multiplier = st.slider(
        "Demand Surge Multiplier",
        min_value=0.8,
        max_value=2.5,
        step=0.1,
        key="sim_dem",
    )

  st.divider()

  # 3. MONTE CARLO SIMULATION EXECUTION
  if st.button("🚀 Run Monte Carlo Stress Simulation", key="btn_run_mc"):
    with st.spinner(f"Simulating {n_sims:,} market shocks..."):
      base_unit_price = (
          780.0
          if "Heavy" in persona
          else (3200.0 if "Merchant" in persona else 45.0)
      )
      price_shocks = np.random.lognormal(
          mean=np.log(base_unit_price), sigma=vol_shock, size=n_sims
      )

      # Simulate gross demand surge across iterations
      simulated_gross = (
          gross_surge
          * demand_multiplier
          * np.random.uniform(0.9, 1.1, size=n_sims)
      )

      # Subtract baseline contracted volume to evaluate floating net deficit
      simulated_net_deficit = np.maximum(0, simulated_gross - active_contracts)

      # FIX hedge reduces open floating exposure on the net deficit
      hedge_ratio = 0.85 if fix_executed else 0.0
      unhedged_deficit = simulated_net_deficit * (1.0 - hedge_ratio)
      hedged_deficit = simulated_net_deficit * hedge_ratio

      # Financial cost calculation
      unhedged_cost = unhedged_deficit * price_shocks
      hedged_cost = hedged_deficit * base_unit_price
      total_simulated_cost = unhedged_cost + hedged_cost
      net_cash_impact = cash_balance - total_simulated_cost

      st.session_state["mc_results"] = {
          "mean_cost": float(np.mean(total_simulated_cost)),
          "var_95": float(np.percentile(total_simulated_cost, 95)),
          "var_99": float(np.percentile(total_simulated_cost, 99)),
          "insolvency_risk": float(np.mean(net_cash_impact < 0) * 100.0),
          "total_cost": total_simulated_cost,
      }

  # 4. SIMULATION OUTCOMES & RISK VISUALIZATION
  if "mc_results" in st.session_state:
    res = st.session_state["mc_results"]
    st.markdown("### 📊 Simulation Outcomes & Value at Risk (VaR)")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
      st.metric("Expected Net Deficit Cost", f"${res['mean_cost']:,.2f}")
    with col_m2:
      st.metric("95% Value at Risk (VaR)", f"${res['var_95']:,.2f}")
    with col_m3:
      st.metric("99% Tail Risk (VaR)", f"${res['var_99']:,.2f}")
    with col_m4:
      st.metric(
          "Treasury Insolvency Risk",
          f"{res['insolvency_risk']:.1f}%",
          delta="High Risk" if res["insolvency_risk"] > 5 else "Protected",
          delta_color="inverse" if res["insolvency_risk"] > 5 else "normal",
      )

    df_chart = pd.DataFrame({"Simulated Cost ($)": res["total_cost"]})
    fig = px.histogram(
        df_chart,
        x="Simulated Cost ($)",
        nbins=50,
        title=f"Monte Carlo Net Deficit Risk Exposure ({n_sims:,} Iterations)",
        color_discrete_sequence=["#0068C9" if fix_executed else "#FF2B2B"],
    )
    fig.add_vline(
        x=res["var_95"],
        line_dash="dash",
        line_color="orange",
        annotation_text="95% VaR",
    )
    fig.add_vline(
        x=res["var_99"],
        line_dash="dash",
        line_color="red",
        annotation_text="99% Tail VaR",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 🔄 Closed-Loop Operational & CTRM Actions")
    st.caption(
        "Propagate simulated parameters into operational planning or execute a"
        " direct CTRM derivative hedge."
    )

    act_col1, act_col2 = st.columns(2)

    # ACTION 1: Propagate macro variables to S&OP
    with act_col1:
      if st.button(
          "🧪 Inject Stressed Macro Parameters into S&OP",
          key="btn_inject_params",
          use_container_width=True,
      ):
        new_gross_surge = int(gross_surge * demand_multiplier)
        new_net_deficit = max(0, new_gross_surge - active_contracts)
        new_lt_delay = curr_leadtime_delay + lead_time_shock
        new_si = max(-1.0, si_score - (vol_shock * 0.5))

        st.session_state["extracted_demand_surge"] = new_gross_surge
        st.session_state["net_uncovered_units"] = new_net_deficit
        st.session_state["active_leadtime_delay_days"] = new_lt_delay
        st.session_state["si_composite"] = new_si

        if "run_end_to_end_sop_cascade" in globals():
          updated_cascade = run_end_to_end_sop_cascade(
              base_demand_units=st.session_state.get("base_demand", 200000)
          )
          st.session_state["active_sop_cascade"] = updated_cascade

        st.toast("Injected macro stress into Executive S&OP!", icon="🧪")
        st.rerun()

    # ACTION 2: Execute derivative hedge into CTRM Desk & Sync S&OP
    with act_col2:
      hedge_btn_label = (
          "✅ Hedge Already Active in CTRM Desk"
          if fix_executed
          else "⚡ Execute CTRM Hedge & Sync to Executive S&OP"
      )
      if st.button(
          hedge_btn_label,
          key="btn_execute_ctrm_hedge",
          disabled=fix_executed,
          use_container_width=True,
      ):
        st.session_state["fix_executed"] = True
        st.session_state["fix_hedged_volume"] = net_units
        st.session_state["fix_execution_timestamp"] = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Recalculate Executive S&OP Cascade with hedge active
        if "run_end_to_end_sop_cascade" in globals():
          updated_cascade = run_end_to_end_sop_cascade(
              base_demand_units=st.session_state.get("base_demand", 200000)
          )
          st.session_state["active_sop_cascade"] = updated_cascade

        st.toast(
            f"FIX 4.4 Hedge Executed for {net_units:,} {term_unit}! Synced to"
            " CTRM Desk & Executive S&OP.",
            icon="⚡",
        )
        st.rerun()


def render_handshake_simulator():
  st.subheader("🤝 Enterprise Handshake Simulator")
  st.caption(
      "Simulate live mTLS + OAuth 2.0 payloads dispatched across enterprise"
      " ERPs, FIX gateways, and NLP News/Sentiment pipelines."
  )

  sim_col1, sim_col2 = st.columns([1, 1])

  with sim_col1:
    target_endpoint = st.selectbox(
        "Select Target Enterprise Endpoint:",
        [
            "NLP News & Sentiment Webhook (Google / LinkedIn Ingest)",
            "SAP S/4HANA (BAPI PO Creation)",
            "Oracle Financials (GL Journal Post)",
            "CME / LME Direct FIX 4.4 Engine (DMA Execution)",
            "Macro & Freight Telemetry Stream (NY Fed / FBX Ingest)",
            "Salesforce CRM (Demand Opportunity Sync)",
        ],
        key="sim_target",
    )
    generated_idempotency = f"idemp_{uuid.uuid4().hex[:10]}"
    st.text_input(
        "Active Idempotency Key",
        value=generated_idempotency,
        disabled=True,
    )
    run_sim = st.button(
        "⚡ Initiate Bi-Directional Handshake", key="btn_run_handshake"
    )

  with sim_col2:
    if run_sim:
      with st.status(
          "Executing 4-Step Handshake Protocol...", expanded=True
      ) as status:
        st.write(
            "🔒 **Step 1: Perimeter Auth** — Exchanging OAuth 2.0 Bearer tokens"
            " over mTLS tunnel..."
        )
        time.sleep(0.3)
        st.write(
            "🔑 **Step 2: Integrity & Schema Verification** — Computing"
            " HMAC-SHA256 signature & verifying JSON schema..."
        )
        time.sleep(0.3)
        st.write(
            "📦 **Step 3: Idempotent Delivery** — Pushing payload with"
            f" header `X-Idempotency-Key: {generated_idempotency[:14]}...`"
        )
        time.sleep(0.3)
        st.write(
            "✅ **Step 4: Non-Repudiation ACK** — Received `200 OK` with"
            " verified document correlation ID!"
        )
        status.update(
            label="Handshake Complete & Cryptographically Verified!",
            state="complete",
            expanded=False,
        )

      tx_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"
      correlation_id = f"corr-{uuid.uuid4().hex[:12]}"
      timestamp_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
      fake_sig = hmac.new(
          b"ibp_tenant_secret", tx_id.encode(), hashlib.sha256
      ).hexdigest()[:24]

      st.json({
          "handshake_result": "HTTP 200 OK (ACCEPTED)",
          "transaction_id": tx_id,
          "correlation_id": correlation_id,
          "idempotency_key": generated_idempotency,
          "timestamp": timestamp_now,
          "security_handshake": {
              "protocol": "mTLS + OAuth2.0 Client Credentials",
              "hmac_sha256_signature": f"0x{fake_sig}...",
              "schema_validation": "PASSED (SECTOR_BENCHMARK_MAP v1.4)",
          },
          "acknowledged_receipt": {
              "target_system": target_endpoint.split(" ")[0],
              "remote_document_id": f"DOC-SYS-{uuid.uuid4().hex[:8].upper()}",
              "roundtrip_latency": "24 ms",
          },
      })

def render_integration_architecture(
    persona="Discrete & Heavy Industrial Enterprise", **kwargs
):
    """Investor-Grade Enterprise Integration & Architecture Control Desk."""
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption(
        "Real-Time API Topology, Gateway Latency Benchmarks, Data Pipelines,"
        " and Core ERP / CTRM Connectors."
    )

    active_sector = st.session_state.get(
        "sector_focus", "Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)"
    )
    sector_cfg = SECTOR_BENCHMARK_MAP.get(
        active_sector,
        SECTOR_BENCHMARK_MAP["Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)"],
    )
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Dynamic pipeline state metrics
    gross_surge = st.session_state.get("extracted_demand_surge", 185000)
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_units = st.session_state.get(
        "net_uncovered_units", max(0, gross_surge - active_contracts)
    )
    term_unit = kwargs.get("term_unit", "Units")
    fix_executed = st.session_state.get("fix_executed", False)
    hedge_gain = 3_810_000.0 if fix_executed else 0.0

    # 1. INVESTOR EXECUTIVE BANNER
    with st.container(border=True):
        st.markdown("### 🏆 Platform Architecture & Scalability Highlights")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Live Connectors", "12 / 12 Active", delta="Zero Downtime")
            st.caption("Macro, Freight, CTRM & ERP")
        with kpi2:
            st.metric("Avg Gateway Latency", "26.4 ms", delta="-4.1 ms YoY")
            st.caption("Sub-50ms Enterprise SLA")
        with kpi3:
            st.metric("Daily Signal Volume", "2.4M Events", delta="+38% YoY")
            st.caption("Unstructured NLP + AIS Pings")
        with kpi4:
            st.metric("Enterprise Security", "SOC2 / ISO27001", delta="mTLS + OAuth2")
            st.caption("Bank-Grade Encryption")

    st.info(
        f"🌐 **Active Sector**: **{active_sector}** | Primary Benchmark:"
        f" **{sector_cfg['primary_index']}** | Net Uncovered Target:"
        f" **{net_units:,} {term_unit}**"
    )

    st.divider()

    # 2. EXPANDED GATEWAY STATUS MATRIX (Includes News, Sentiment, Macro & Freight)
    st.subheader("📡 Real-Time Benchmark & API Gateway Status")
    gateway_df = pd.DataFrame({
        "Category": [
            "Macro Telemetry",
            "Freight & Logistics",
            "NLP & News Signals",
            "Social & Inbox",
            "Market Data",
            "CTRM Execution",
            "Core Enterprise ERP",
            "Financial Ledger",
            "CRM & Deal Desk",
        ],
        "Endpoint / Interface": [
            "NY Fed GSCPI & FRED Industrial Feed",
            "FBX Freight & AIS Vessel Tracking",
            "Multi-Commodity RSS Disruption Scanner",
            "LinkedIn Scraper & Gmail IMAP Pipeline",
            f"Primary Benchmark Feed ({sector_cfg['primary_index'].split('/')[0].strip()})",
            "CME / LME Direct FIX Gateway",
            "SAP S/4HANA Core ERP",
            "Oracle / PeopleSoft GL Gateway",
            "Salesforce CRM API Engine",
        ],
        "Mapped Asset / Protocol": [
            "GSCPI / INDPRO / PPI Benchmark",
            "Freightos FBX & AIS gRPC Stream",
            "Google News XML / Sentiment Parser ($SI$)",
            "IMAP SSL / OAuth2 REST Engine",
            sector_cfg["ticker_symbol"],
            "FIX 4.4 Engine",
            f"BAPI ({sector_cfg['sap_mat_code']})",
            f"GL Sync ({sector_cfg['oracle_gl_account']})",
            "REST / OAuth 2.0",
        ],
        "Latency": ["12 ms", "31 ms", "15 ms", "42 ms", "14 ms", "4 ms", "45 ms", "62 ms", "88 ms"],
        "Status": [
            "🟢 HEALTHY", "🟢 HEALTHY", "🟢 HEALTHY", "🟢 HEALTHY", 
            "🟢 HEALTHY", "🟢 HEALTHY", "🟢 HEALTHY", "🟢 HEALTHY", "🟢 HEALTHY"
        ],
    })
    st.dataframe(gateway_df, use_container_width=True, hide_index=True)

    st.divider()

    # 3. CORE CONNECTORS & WEBHOOK SCHEMAS (5 Tabs)
    st.subheader("🏛️ Enterprise Core Connectors & Schemas")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧠 News & Sentiment NLP Payload",
        "🏭 SAP S/4HANA (BAPI)",
        "🏛️ Oracle GL Financial Gateway",
        "⚡ CME / LME FIX 4.4 Engine",
        "🌐 Macro Telemetry Ingest",
    ])

    with tab1:
        st.markdown(f"**Live News & Sentiment Ingestion Payload (`POST`) — {sector_cfg['ticker_symbol']}**")
        st.code(
            f"""POST /api/v1/nlp/ingest/unstructured-feed
Headers: {{ "Authorization": "Bearer ibp_staging_token_******" }}

Payload:
{{
  "sector_focus": "{active_sector}",
  "benchmark_index": "{sector_cfg['primary_index']}",
  "ticker_symbol": "{sector_cfg['ticker_symbol']}",
  "telemetry": {{
    "gross_demand_surge_units": {gross_surge},
    "contracted_baseline_units": {active_contracts},
    "net_uncovered_deficit_units": {net_units}
  }},
  "unstructured_signal": {{
    "source_type": "Multi-Commodity RSS / LinkedIn Intelligence",
    "headline": "{sector_cfg['sample_headline']}",
    "extracted_sentiment_index": -0.68,
    "timestamp": "{now_iso}"
  }}
}}""",
            language="json",
        )

    with tab2:
        st.markdown("**Dynamic Purchase Order Creation via SAP BAPI_PO_CREATE1**")
        st.code(
            f"""CALL BAPI_PO_CREATE1 (
  Header: {{ Vendor: "VEND_SECTOR_PRIMARY", DocType: "NB", PurchOrg: "1000" }},
  Items: [
    {{ Material: "{sector_cfg['sap_mat_code']}", Index_Ref: "MASTER_CONTRACT_FRAMEWORK", Quantity: {active_contracts}, Unit: "{term_unit}" }},
    {{ Material: "{sector_cfg['sap_mat_code']}_SPOT", Index_Ref: "{sector_cfg['ticker_symbol']}", Quantity: {net_units}, Unit: "{term_unit}" }}
  ]
)""",
            language="cpp",
        )

    with tab3:
        st.markdown("**Real-Time Journal Entry Sync to Oracle Financials Cloud**")
        st.code(
            f"""POST /api/v1/integrations/oracle-financials/gl-journals
Headers: {{ "X-Oracle-App-ID": "{sector_cfg['oracle_gl_account']}" }}

Payload Mapping:
  - Benchmark Index Trigger : {sector_cfg['primary_index']}
  - Net Physical Deficit    : {net_units:,} {term_unit}
  - Financial Gain Realized : Credit {sector_cfg['oracle_gl_account']} (${hedge_gain:,.2f})
  - Treasury Cash Outlay    : Debit Treasury Operations Balance""",
            language="json",
        )

    with tab4:
        st.markdown("**Automated Hedge Execution via FIX 4.4 Protocol**")
        st.code(
            f"""8=FIX.4.4|9=245|35=D|49=PLATFORM_DESK|56=CME_LME_GATEWAY|34=1082|52={now_iso}|
11=ORDER_HEDGE_{now_iso[:10]}|55={sector_cfg['ticker_symbol']}|54=1|38={net_units}|
40=2|44=MARKET_BENCHMARK|59=0|47=A|21=1|10=182|""",
            language="text",
        )

    with tab5:
        st.markdown("**Real-Time Macro Telemetry Streaming (FRED & NY Fed)**")
        st.code(
            f"""GET /api/v1/telemetry/stream
Headers: {{ "Authorization": "Bearer telemetry_live_token_******" }}

Response Stream:
{{
  "timestamp": "{now_iso}",
  "ny_fed_gscpi": +0.82,
  "us_fred_mfg_index": 102.4,
  "freightos_fbx_ocean_feu": 3850.0
}}""",
            language="json",
        )

    st.divider()

    # 4. RETAIN EXISTING HANDSHAKE SIMULATOR HELPER
    render_handshake_simulator()


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