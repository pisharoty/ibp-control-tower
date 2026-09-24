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
import streamlit as st
from robot_feeds import (
    calculate_composite_sentiment,
    compute_quantified_operational_impact,
    fetch_global_macro_telemetry,
    fetch_gmail_newsletters,
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


def fetch_live_or_fallback(url, fallback_list, timeout_sec=1.2):
    """RSS Stream reader with immediate enterprise synthetic fallback."""
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


import plotly.graph_objects as go
import streamlit as st


def render_executive_sop(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Render Executive S&OP Control Tower with dynamic persona baselines & Plotly waterfall."""
    st.title("📈 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown(
        "Real-time financial alignment, financial waterfalls, and trade hedge"
        " benefit reconciliation."
    )

    # 1. Dynamic Persona Baselines
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

    # 2. Extract Central Cascade State
    cascade = st.session_state.get("active_sop_cascade", {})
    demand_data = cascade.get("demand", {})
    exec_data = cascade.get("exec_sop", {})
    ctrm_data = cascade.get("ctrm", {})
    logistics_data = cascade.get("logistics", {})

    si_score = cascade.get(
        "si_composite", st.session_state.get("si_composite", -0.28)
    )
    surge_units = demand_data.get("total_surge_units", 102968)
    delta_units = demand_data.get("delta_surge_units", 0)

    # Financial inputs derived from Orchestrator Cascade
    revenue_upside = exec_data.get(
        "delta_revenue_usd", delta_units * unit_price
    )
    unconstrained_rev = base_aop_rev + revenue_upside

    fix_executed = st.session_state.get("fix_executed", False)
    mc_res = st.session_state.get("mc_results", None)

    if mc_res:
        cogs_drag = mc_res["mean_cost"]
        var_95_drag = mc_res["var_95"]
    else:
        cogs_drag = exec_data.get("delta_cogs_usd", 0.0) + logistics_data.get(
            "total_freight_surcharge_usd", 0.0
        )
        if cogs_drag == 0.0:
            cogs_drag = (base_aop_rev * 0.025) * (1.0 + abs(si_score) * 2.5)
        var_95_drag = cogs_drag * 1.4

    # CTRM Hedge Benefit
    ctrm_hedge_benefit = (
        ctrm_data.get(
            "capital_committed_usd",
            cogs_drag * 0.42 if fix_executed else 0.0,
        )
        if fix_executed
        else 0.0
    )

    net_cogs_drag = cogs_drag - ctrm_hedge_benefit
    base_cogs = base_aop_rev * cogs_pct
    net_ebitda = unconstrained_rev - base_cogs - net_cogs_drag
    sop_cash = st.session_state.get("sop_cash_balance", 5_000_000.0)

    # 3. Top KPI Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(
            "Annual Operating Plan (AOP)",
            f"${base_aop_rev / 1e6:.1f}M",
            "+4.2% YoY",
        )
    with col_m2:
        st.metric(
            "Unconstrained Demand",
            f"${unconstrained_rev / 1e6:.2f}M",
            f"+{surge_units:,} {term_unit}",
        )
    with col_m3:
        st.metric(
            "CTRM Hedge Benefit",
            f"+${ctrm_hedge_benefit / 1e6:.2f}M",
            "FIX Covered" if fix_executed else "0% Cover (Floating Risk)",
            delta_color="normal" if fix_executed else "inverse",
        )
    with col_m4:
        st.metric(
            "Available Treasury Cash",
            f"${sop_cash:,.2f}",
            delta=(
                "CRITICAL CASH RISK"
                if sop_cash < 0
                else f"SI Impact ({si_score:+.2f})"
            ),
            delta_color="normal" if sop_cash >= 0 else "inverse",
        )

    st.divider()

    if sop_cash < 0 or (mc_res and mc_res.get("insolvency_risk", 0) > 10):
        st.error(
            f"🚨 **STRESSED FINANCIAL RISK DETECTED**: Monte Carlo VaR indicates"
            f" **${var_95_drag / 1e6:.2f}M (95% VaR)** potential cost drag."
            f" Current Treasury Cash balance is **${sop_cash:,.2f}**."
        )

    # 4. Interactive Visual Waterfall & Desk Feeds
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
                    "total",
                ],
                x=[
                    "Base AOP",
                    "Demand Upside",
                    "COGS Drag",
                    "Hedge Benefit",
                    "Net EBITDA",
                ],
                textposition="outside",
                text=[
                    f"${base_aop_rev / 1e6:.1f}M",
                    f"+${revenue_upside / 1e6:.2f}M",
                    f"-${cogs_drag / 1e6:.2f}M",
                    f"+${ctrm_hedge_benefit / 1e6:.2f}M",
                    f"${net_ebitda / 1e6:.2f}M",
                ],
                y=[
                    base_aop_rev / 1e6,
                    revenue_upside / 1e6,
                    -cogs_drag / 1e6,
                    ctrm_hedge_benefit / 1e6,
                    net_ebitda / 1e6,
                ],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#ef553b"}},
                increasing={"marker": {"color": "#00cc96"}},
                totals={"marker": {"color": "#636efa"}},
            )
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            yaxis_title="USD ($ Millions)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_p2:
        st.subheader("🚩 Live Operational Desk Feeds")
        sig_title = st.session_state.get(
            "active_risk_signal_title", "Baseline Operations Target"
        )

        st.info(
            f"🔹 **Active NLP Signal**: `{sig_title}` ($SI = {si_score:+.2f}$)"
        )

        if fix_executed:
            st.success(
                f"🟢 **CTRM Risk Desk**: FIX Protocol Order Executed. Hedge"
                f" benefit locked at **+${ctrm_hedge_benefit / 1e6:.2f}M**."
            )
        else:
            st.warning(
                f"🔸 **CTRM Risk Desk**: Unhedged Volatility Gap ="
                f" **{delta_units:,} {term_unit}**."
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

    # 1. Pull Session State Metrics
    surge_units = st.session_state.get("extracted_demand_surge", 102968)
    si_score = st.session_state.get("si_composite", -0.33)
    fix_executed = st.session_state.get("fix_executed", False)
    active_sig = st.session_state.get("active_signal", {})

    # 2. Derive Persona Baseline Contract Values
    raw_contracts = get_persona_contracts(persona)
    contracts_df = pd.DataFrame(raw_contracts)

    # Enrich contracts with synthetic risk & valuation metrics
    if "Merchant" in persona:
        multiplier = 3500.0
    elif "FMCG" in persona:
        multiplier = 1200.0
    else:
        multiplier = 850.0

    base_deal_vol = 185000
    hedged_vol = base_deal_vol if fix_executed else int(base_deal_vol * 0.35)
    unhedged_vol = max(0, surge_units + base_deal_vol - hedged_vol)

    total_pipeline_val = (base_deal_vol + surge_units) * multiplier
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
            delta="100% Covered" if fix_executed else "35% Covered",
            delta_color="normal" if fix_executed else "inverse",
        )
    with kpi3:
        st.metric(
            "Unhedged Floating Exposure",
            f"${exposure_val / 1e6:.1f}M",
            delta=f"{unhedged_vol:,} {term_unit} Gap",
            delta_color="inverse",
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

        categories = ["Base Physical", "Surge Volume", "CTRM Hedge", "Net Open"]
        volumes = [
            base_deal_vol,
            surge_units,
            -hedged_vol,
            (base_deal_vol + surge_units - hedged_vol),
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
        st.info(f"**Active Signal**: {active_sig.get('title', 'Baseline Target')}")

        if not fix_executed:
            st.warning(
                "⚠️ **Action Required**: Unhedged price exposure detected."
            )
            if st.button(
                "🚀 Execute Auto-Hedge Order on CTRM Desk",
                key="btn_deal_desk_fix",
            ):
                st.session_state["fix_executed"] = True
                st.toast("FIX Protocol Order Executed Globally!", icon="🔒")
                st.rerun()
        else:
            st.success("🟢 **Status**: FIX Hedge Active & Executed.")
            if st.button("🔄 Reset Hedge Position", key="btn_reset_hedge"):
                st.session_state["fix_executed"] = False
                st.rerun()

    st.divider()

    # 5. Consolidated Master Deal Ledger
    st.subheader("📑 Consolidated Physical & Financial Deal Ledger")

    # Blend physical contracts with live signals
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

    # Add dynamic CTRM and Signal entries
    deal_records.append({
        "Deal ID": "CTRM-FIX-9942",
        "Counterparty": "LME / CME Clearinghouse",
        "Commodity / Material": f"Index Derivative Futures ({term_unit})",
        "Contract Type": "Financial Hedge",
        "Volume": f"{hedged_vol:,} {term_unit}",
        "Status": "🟢 Executed" if fix_executed else "🟡 Pending FIX Call",
        "Hedge State": "Financial Cover" if fix_executed else "Floating Risk",
    })

    deal_records.append({
        "Deal ID": "NLP-SIGNAL-018",
        "Counterparty": active_sig.get("source_type", "Field Sensing"),
        "Commodity / Material": active_sig.get("title", "Market Surge Signal"),
        "Contract Type": "Inferred Demand Spike",
        "Volume": f"+{surge_units:,} {term_unit}",
        "Status": "🔴 Unhedged Surge",
        "Hedge State": "Open Exposure",
    })

    st.dataframe(pd.DataFrame(deal_records), use_container_width=True)


def render_nlp_intelligence(persona=None, term_unit="Units", **kwargs):
    """Complete NLP Commercial Sensing & Intelligence Module with Hard Macro,

    LinkedIn Feeds, Email Parsing, and Downstream S&OP Cascade Hooks.
    """
    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption(
        "Ingest unstructured signals from news feeds, LinkedIn social posts,"
        " email debriefs, hard macro indicators (NY Fed, World Bank, FRED, ECB,"
        " PBOC, BOJ, KOSPI), and GIS telemetry."
    )

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & LinkedIn Signals",
        "📧 Email & Event Debrief Parser",
        "⚓ Freight, Weather & Black Swan Feeds",
    ])

    # =========================================================================
    # TAB 1: LIVE WEB, MACRO & LINKEDIN SOCIAL SIGNALS
    # =========================================================================
    with tab1:
        r_head1, r_head2 = st.columns([3, 1])
        with r_head1:
            st.caption(
                "🤖 **Triangulated Intelligence**: Hard Macro (NY Fed / FRED /"
                " ECB / PBOC / KOSPI) + Live Web RSS + LinkedIn Network"
            )
        with r_head2:
            if st.button(
                "🔄 Refresh Live Feeds & APIs", key="btn_refresh_robot_feeds"
            ):
                try:
                    feed_data = sync_robot_feeds()
                    newsletters = feed_data.get("newsletters", [])

                    if newsletters and newsletters[0].get("is_live"):
                        st.session_state["live_newsletters"] = newsletters
                        st.session_state["linkedin_score"] = feed_data.get(
                            "linkedin_score", -0.10
                        )
                        st.toast(
                            "Synced live signal:"
                            f" {newsletters[0].get('title', 'LinkedIn Feed')}",
                            icon="✅",
                        )
                    elif newsletters:
                        st.toast(
                            f"IMAP Status: {newsletters[0].get('status')}",
                            icon="⚠️",
                        )
                    else:
                        st.toast(
                            "Refreshed feeds from Gmail IMAP & Global Macro"
                            " APIs!",
                            icon="🔄",
                        )
                    st.rerun()
                except Exception as e:
                    st.error(f"Sync error: {e}")

        # Ensure robot_signals.json exists on load
        if not os.path.exists("robot_signals.json"):
            try:
                sync_robot_feeds()
            except Exception:
                pass

        robot_data = {}
        if os.path.exists("robot_signals.json"):
            try:
                with open("robot_signals.json", "r") as f:
                    robot_data = json.load(f)
            except Exception:
                pass

        # -------------------------------------------------------------------------
        # EXPANDED HARD MACROECONOMIC TELEMETRY DASHBOARD (5-COLUMN GRID)
        # -------------------------------------------------------------------------
        macro = fetch_global_macro_telemetry()
        with st.expander(
            "🏛️ Hard Macroeconomic Telemetry (NY Fed GSCPI, World Bank, FRED,"
            " ECB, PBOC, BOJ, KOSPI)",
            expanded=True,
        ):
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric(
                    "NY Fed GSCPI", macro["ny_fed_gscpi"], "Supply Pressure"
                )
                st.caption("Global Supply Chain Pressure")
            with m_col2:
                st.metric(
                    "US FRED Mfg Index", macro["us_fred"], "St. Louis Fed"
                )
                st.caption("US Industrial Output")
            with m_col3:
                st.metric(
                    "World Bank Commodity",
                    macro["world_bank"],
                    macro["china_pmi"],
                )
                st.caption("Global Benchmark / PBOC")
            with m_col4:
                st.metric(
                    "Eurozone (ECB)",
                    macro["eurozone_ecb"],
                    "Industrial Trend",
                )
                st.caption("ECB Telemetry")
            with m_col5:
                st.metric(
                    "Korea KOSPI / Japan",
                    macro["kospi_korea"],
                    macro["japan_pmi"],
                )
                st.caption("Asian Export Benchmark")

        # Extract dynamic score and calculate dynamic composite sentiment
        hard_macro = robot_data.get("hard_macro", {})
        linkedin_score = robot_data.get(
            "linkedin_score", st.session_state.get("linkedin_score", -0.10)
        )

        try:
            gscpi_sent = hard_macro.get("gscpi_sentiment", -0.15)
            feed_signals = {
                "gscpi_sentiment": gscpi_sent,
                "world_bank_score": st.session_state.get(
                    "world_bank_score", -0.20
                ),
                "linkedin_score": linkedin_score,
                "gis_score": st.session_state.get("gis_score", -0.10),
                "field_email_score": st.session_state.get(
                    "field_email_score", -0.30
                ),
            }
            sentiment_res = calculate_composite_sentiment(feed_signals)
            si_comp = sentiment_res.get("si_composite", -0.33)

            base_dem = st.session_state.get("base_demand", 129500)
            impact_res = compute_quantified_operational_impact(
                si_comp, base_dem
            )

            composite = {
                "si_composite": si_comp,
                "demand_surge_units": impact_res.get(
                    "delta_demand_units", 102968
                ),
                "leadtime_delay_days": impact_res.get(
                    "lead_time_buffer_days", 2.5
                ),
                "recommendation": impact_res.get(
                    "recommended_action", "Lock 60-Day Forward Exposure"
                ),
                "ctrm_hedge_required": (
                    impact_res.get("target_hedge_pct", 60.0) >= 60.0
                ),
            }
        except Exception:
            composite = {
                "si_composite": st.session_state.get("si_composite", -0.33),
                "demand_surge_units": st.session_state.get(
                    "extracted_demand_surge", 102968
                ),
                "leadtime_delay_days": st.session_state.get(
                    "active_leadtime_delay_days", 2.5
                ),
                "recommendation": (
                    "Lock in 60-day futures on CTRM Desk; extend vendor lead"
                    " times in ERP; trigger safety buffer in S&OP."
                ),
                "ctrm_hedge_required": True,
            }

        active_sig = st.session_state.get("active_signal", {})
        si_score = active_sig.get(
            "sentiment_index",
            st.session_state.get(
                "si_composite", composite.get("si_composite", -0.33)
            ),
        )
        surge_units = active_sig.get(
            "demand_surge_units",
            st.session_state.get(
                "extracted_demand_surge",
                composite.get("demand_surge_units", 102968),
            ),
        )
        lt_days = active_sig.get(
            "leadtime_delay_days",
            st.session_state.get(
                "active_leadtime_delay_days",
                composite.get("leadtime_delay_days", 2.5),
            ),
        )
        rec_text = composite.get(
            "recommendation",
            "Lock in 60-day raw material futures on CTRM Desk; extend vendor"
            " lead times in ERP.",
        )

        with st.container(border=True):
            st.markdown("### 🎯 Composite Market Sentiment Index ($SI$)")
            c_col1, c_col2, c_col3, c_col4 = st.columns([1.2, 1, 1, 1])
            with c_col1:
                st.metric(
                    "Net Sentiment Score",
                    f"{si_score:+.2f}",
                    delta="Moderate Supply Strain",
                    delta_color="inverse",
                )
            with c_col2:
                st.metric(
                    "Quantified Demand Surge", f"+{surge_units:,} {term_unit}"
                )
            with c_col3:
                st.metric("Lead Time Expansion", f"+{lt_days} Days")
            with c_col4:
                ctrm_status = (
                    "🔴 HEDGE REQUIRED"
                    if composite.get("ctrm_hedge_required", True)
                    else "🟢 STABLE"
                )
                st.metric("CTRM Risk Status", ctrm_status)

            st.info(f"**Quantified Action Plan**: {rec_text}")

            if "commit_nlp_signal" in globals():
                st.button(
                    "⚡ Propagate Triangulated Composite Index across Platform",
                    key="btn_propagate_composite",
                    on_click=commit_nlp_signal,
                    args=({
                        "source_type": "Macro Triangulation Engine",
                        "title": f"Triangulated Composite Index ({si_score:+.2f})",
                        "demand_surge_units": surge_units,
                        "leadtime_delay_days": lt_days,
                        "sentiment_index": si_score,
                    },),
                )

        st.divider()

        # -------------------------------------------------------------------------
        # LIVE GMAIL / LINKEDIN INGESTED FEED DISPLAY
        # -------------------------------------------------------------------------
        live_newsletters = fetch_gmail_newsletters(max_emails=5)
        st.subheader("📬 Live Ingested Newsletter Signal (LinkedIn Direct)")

        if live_newsletters and "title" in live_newsletters[0]:
            for news in live_newsletters:
                with st.container(border=True):
                    nl_col1, nl_col2 = st.columns([2.5, 1.5])
                    with nl_col1:
                        st.markdown(
                            f"**Subject:** `{news.get('title', 'LinkedIn Signal')}`"
                        )
                        tags = news.get("detected_commodities", [])
                        tag_str = (
                            ", ".join(tags)
                            if tags
                            else "GENERAL FREIGHT & LOGISTICS"
                        )
                        st.caption(
                            f"**Published:** {news.get('published', 'Recent')} |"
                            f" **Detected Commodity Tags:** `{tag_str}`"
                        )
                        st.markdown(f'"{news.get("summary", "")}"')
                    with nl_col2:
                        st.metric(
                            "Polarity Score ($s_i$)",
                            f"{news.get('sentiment_score', 0.0):+.2f}",
                        )
                        st.caption(
                            f"**Source:** {news.get('source', 'LinkedIn / Gmail Direct Feed')}"
                        )

                    if "commit_nlp_signal" in globals():
                        st.button(
                            "⚡ Ingest Live Newsletter Signal into S&OP Engine",
                            key=f"btn_ingest_{news.get('title', 'sig')[:10]}",
                            on_click=commit_nlp_signal,
                            args=({
                                "source_type": news.get(
                                    "source", "LinkedIn Direct Feed"
                                ),
                                "title": news.get(
                                    "title", "LinkedIn Live Signal"
                                ),
                                "demand_surge_units": int(
                                    abs(news.get("sentiment_score", -0.10))
                                    * 150000
                                ),
                                "leadtime_delay_days": round(
                                    abs(news.get("sentiment_score", -0.10))
                                    * 10,
                                    1,
                                ),
                                "sentiment_index": news.get(
                                    "sentiment_score", -0.10
                                ),
                            },),
                        )
        else:
            st.info(
                "No active LinkedIn commodity signals currently buffered in"
                " inbox."
            )

        st.divider()

        # -------------------------------------------------------------------------
        # LINKEDIN EXECUTIVE & SOCIAL NEWSFEED EXTRACTION DESK
        # -------------------------------------------------------------------------
        st.subheader("💼 LinkedIn Executive & Post-Trade Intelligence")
        st.caption(
            "Scrape and structure real-time executive posts, smelter outage"
            " announcements, and trader commentary."
        )

        LINKEDIN_POSTS = {
            "🔴 Codelco Operations Director | Smelter Outage Warning": {
                "author": "Carlos Mendoza (VP Supply Chain, Codelco)",
                "post_body": (
                    "Unplanned maintenance on Furnace #3 at Chuquicamata will"
                    " reduce refined cathode allocation by 25% over Q4. Expect"
                    " major force majeure notifications across primary buyers."
                ),
                "extracted_units": 185000,
                "extracted_delay": 8.5,
                "sentiment": -0.82,
                "source": "LinkedIn Executive Post",
            },
            "🟠 Maersk Chief Commercial Officer | Port Congestion": {
                "author": "Elena Rostova (Head of Maritime Freight, Maersk)",
                "post_body": (
                    "Bunker fuel cost spikes alongside berth congestion at"
                    " European hubs are extending ocean transit dwell times."
                    " Spot rate surcharges applied for non-contract cargo."
                ),
                "extracted_units": 120000,
                "extracted_delay": 6.0,
                "sentiment": -0.65,
                "source": "LinkedIn Executive Post",
            },
            "🟡 Glencore Senior Trader | Battery Nickel Quotas": {
                "author": "Marcus Vance (Global Commodity Desk, Glencore)",
                "post_body": (
                    "Indonesian nickel export quota approvals delayed until"
                    " late next month. Spot market premiums jumping rapidly as"
                    " battery precursor manufacturers scramble for material."
                ),
                "extracted_units": 95000,
                "extracted_delay": 4.5,
                "sentiment": -0.58,
                "source": "LinkedIn Executive Post",
            },
        }

        selected_post_key = st.selectbox(
            "Select Scraped LinkedIn Post / Industry Signal:",
            list(LINKEDIN_POSTS.keys()),
            key="linkedin_post_select",
        )
        post_data = LINKEDIN_POSTS[selected_post_key]

        with st.container(border=True):
            l_col1, l_col2 = st.columns([2.5, 1.5])
            with l_col1:
                st.markdown(f"**Author:** `{post_data['author']}`")
                st.caption(f'"{post_data["post_body"]}"')
            with l_col2:
                st.metric(
                    "Impact Volume Surge",
                    f"+{post_data['extracted_units']:,} Units",
                )
                st.metric(
                    "Expected Lead Time Shock",
                    f"+{post_data['extracted_delay']} Days",
                )

            author_clean = post_data["author"].split("(")[0].strip()
            title_clean = (
                selected_post_key.split("|")[1].strip()
                if "|" in selected_post_key
                else selected_post_key
            )

            if "commit_nlp_signal" in globals():
                st.button(
                    "⚡ Ingest LinkedIn Social Signal into S&OP Engine",
                    key="btn_ingest_linkedin",
                    on_click=commit_nlp_signal,
                    args=({
                        "source_type": "LinkedIn Executive Feed",
                        "title": f"[{author_clean}] {title_clean}",
                        "demand_surge_units": post_data["extracted_units"],
                        "leadtime_delay_days": post_data["extracted_delay"],
                        "sentiment_index": post_data["sentiment"],
                    },),
                )

        st.divider()

        # -------------------------------------------------------------------------
        # REAL-TIME DYNAMIC WEB & EXPANDED COMMODITY RSS STREAM
        # -------------------------------------------------------------------------
        st.subheader("📡 Real-Time Dynamic Web & Commodity RSS News Stream")
        NEWS_DOMAINS = {
            "🧱 Non-Ferrous Metals (Copper, Cathodes, Zinc, Aluminum)": (
                "copper supply chain OR smelter outage"
            ),
            "💎 Precious Metals & Rare Earth Elements (Lithium, Neodymium, REE)": (
                "lithium neodymium rare earth supply chain"
            ),
            "🧪 Industrial Chemicals, Resins & Base Polymers": (
                "ethylene resin force majeure chemical supply"
            ),
            "⚡ Essential Semiconductors, Wafers & High-Tech Hardware": (
                "semiconductor chip wafer shortage logistics"
            ),
            "🛢️ Energy, Natural Gas, Power & Petrochemicals": (
                "natural gas power outage smelter surcharge"
            ),
            "🚢 Maritime Freight, Container Ports & Ocean Logistics": (
                "container freight port congestion dwell time"
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
            live_rss_items = []
            try:
                from robot import fetch_live_sector_rss

                live_rss_items = fetch_live_sector_rss(topic_query)
            except Exception:
                pass

            if live_rss_items:
                headline_options = [
                    f"{item['title']} [Impact: {item['estimated_impact']:,}"
                    " Units]"
                    for item in live_rss_items
                ]
            else:
                headline_options = [
                    "Global Supply Bottleneck Reported in Sector Focus [Impact:"
                    " 110,000 Units]",
                    "Port Congestion and Lead Time Expansion Hits Sector"
                    " [Impact: 85,000 Units]",
                ]

            selected_headline = st.selectbox(
                "Select Live RSS / Scraped Headline Signal:",
                headline_options,
                key="nlp_web_headline_select",
            )

        with col_w2:
            match = re.search(
                r"\[Impact:\s*([\d,]+)\s*Units\]", selected_headline
            )
            extracted_default = (
                int(match.group(1).replace(",", "")) if match else 85000
            )
            web_impact = st.number_input(
                f"Extracted Signal Impact ({term_unit})",
                value=extracted_default,
                step=5000,
                key="web_signal_units",
            )

        headline_clean = selected_headline.split("[")[0].strip()
        domain_label = (
            selected_domain.split(" ")[1]
            if len(selected_domain.split(" ")) > 1
            else "Macro"
        )

        if "commit_nlp_signal" in globals():
            st.button(
                "📡 Ingest Scraped Domain News Signal",
                key="btn_ingest_web",
                on_click=commit_nlp_signal,
                args=({
                    "source_type": "Live Web Intelligence",
                    "title": f"[{domain_label}] {headline_clean}",
                    "demand_surge_units": web_impact,
                    "leadtime_delay_days": 4.0,
                    "sentiment_index": -0.45,
                },),
            )

    # =========================================================================
    # TAB 2: EMAIL & EVENT DEBRIEF PARSER
    # =========================================================================
    with tab2:
        st.subheader("📧 Email & Event Debrief Parser")
        st.caption(
            "Extract unstructured supplier updates, trip reports, and meeting"
            " debriefs."
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
                st.session_state["parsed_email_data"] = (
                    parse_unstructured_email(raw_text)
                )
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
            st.metric(
                "Recommended Safety Buffer",
                f"+{parsed['units_val']:,} {term_unit}",
            )

        st.caption(
            "**NLP Confidence Score**: `94.2%` | **Sentiment Score**: `-0.68`"
        )

        if "commit_nlp_signal" in globals():
            st.button(
                "⚡ Ingest Parsed Email Intelligence into Live S&OP Engine",
                key="btn_ingest_email",
                on_click=commit_nlp_signal,
                args=({
                    "source_type": "Supplier Email",
                    "title": f"[{parsed['vendor']}] {parsed['event']}",
                    "demand_surge_units": parsed["units_val"],
                    "leadtime_delay_days": parsed["delay_val"],
                    "sentiment_index": -0.68,
                },),
            )

    # =========================================================================
    # TAB 3: FREIGHT, WEATHER & BLACK SWAN FEEDS
    # =========================================================================
    with tab3:
        st.subheader("⚓ Freight, Weather & Black Swan Feeds")
        st.caption(
            "Track maritime vessel AIS feeds, port dwell anomalies, and climate"
            " disruptions."
        )

        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            st.metric(
                "Red Sea Bottleneck Index", "HIGH RISK", delta="+42% Dwell"
            )
        with w_col2:
            st.metric(
                "Panama Canal Water Draft",
                "44.0 ft (Restricted)",
                delta="-2.5 ft vs Avg",
            )
        with w_col3:
            st.metric(
                "Global Maritime Freight Index",
                "$3,850 / TEU",
                delta="+18.4% WoW",
            )

        st.divider()
        st.markdown("#### 🌍 Live Anomaly Feed Alerts")
        feed_df = pd.DataFrame([
            {
                "Region / Corridor": "Suez / Red Sea Transit",
                "Disruption Type": "Geopolitical Rerouting",
                "Severity": "Critical",
                "Transit Delay Impact": "+10 to 14 Days",
                "Cost Impact": "+35% Spot Freight",
            },
            {
                "Region / Corridor": "Panama Canal Transit",
                "Disruption Type": "Low Water Level / Drought",
                "Severity": "Elevated",
                "Transit Delay Impact": "+5 to 7 Days",
                "Cost Impact": "+20% Booking Premium",
            },
            {
                "Region / Corridor": "US Gulf Coast / Mississippi",
                "Disruption Type": "Barge Draft Restrictions",
                "Severity": "Moderate",
                "Transit Delay Impact": "+3 to 4 Days",
                "Cost Impact": "+12% Inland Freight",
            },
        ])
        st.dataframe(feed_df, use_container_width=True)

        if "commit_nlp_signal" in globals():
            st.button(
                "⚡ Ingest Freight & Weather Signals into Logistics Engine",
                key="btn_ingest_freight",
                on_click=commit_nlp_signal,
                args=({
                    "source_type": "Maritime AIS & Weather Telemetry",
                    "title": "Red Sea & Panama Canal Transit Bottlenecks",
                    "demand_surge_units": 150000,
                    "leadtime_delay_days": 10.0,
                    "sentiment_index": -0.75,
                },),
            )


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
    """Render Physical Procurement & Master Contract Desk bound to net uncovered volume."""
    st.title("📦 Physical Procurement & Master Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")

    # 1. Pull Net Uncovered Deficit
    gross_surge = st.session_state.get("extracted_demand_surge", 185000)
    active_contracts = st.session_state.get("active_contracts_volume", 129500)
    net_units = st.session_state.get(
        "net_uncovered_units", max(0, gross_surge - active_contracts)
    )

    fix_executed = st.session_state.get("fix_executed", False)
    unit_base_price = (
        3200.0 if "Merchant" in persona else (45.0 if "FMCG" in persona else 780.0)
    )

    # Calculate net invoice and hedge subsidy
    hedge_subsidy = (net_units * unit_base_price * 0.042) if fix_executed else 0.0
    gross_invoice = net_units * (unit_base_price * 1.02)  # Blended spot premium
    net_outlay = gross_invoice - hedge_subsidy

    st.info(
        f"🔗 **Physical Demand Signal Ingested**: Required Net Procurement"
        f" Volume: **{net_units:,} {term_unit}** (Gross Surge: {gross_surge:,} less"
        f" Baseline Contracts: {active_contracts:,}) | Financial Hedge Cash"
        f" Subsidy Available: **${hedge_subsidy:,.2f}**"
    )

    # 2. Key Procurement Metrics
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric(
        "Gross Material Need",
        f"{net_units:,} {term_unit}",
        f"Uncovered Deficit Only",
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

    # 3. Master Contract Sourcing Matrix (Splitting strictly the NET volume)
    st.subheader("📋 Master Contract Sourcing Matrix")

    # Allocations based on net deficit requirement
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

    # 4. Execution Gateway
    st.subheader("🏭 Physical PO Execution Gateway")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.selectbox("Primary Delivery Destination", ["Detroit Main Plant", "Munich Precision Stamping"])
        st.selectbox("Vendor Payment Terms", ["Net 60 Days", "Net 30 Days", "Letter of Credit"])
    with col_g2:
        st.selectbox("Inbound Logistics Mode", ["Standard Multi-Modal Rail & Truck", "Air Freight Expedited"])
        st.selectbox("Quality Standard", ["ISO 9001 Heavy Industrial", "Automotive IATF 16949"])

    if st.button("📦 Issue Physical Purchase Orders & Lock Schedules", type="primary"):
        st.success(f"✅ Physical POs successfully generated for {net_units:,} {term_unit} across 3 supplier tiers.")


def render_ctrm_desk(
    persona="Discrete & Heavy Industrial Enterprise",
    term_unit="Units",
    **kwargs,
):
    """Render CTRM Commodity Risk & Derivatives Desk with dynamic net exposure execution."""
    st.title("⚖️ CTRM Derivatives & Commodity Risk Desk")
    st.caption(f"Active Persona View: **{persona}**")

    # 1. Pull Global Session State & Calculate Net Deficit
    gross_surge = st.session_state.get("extracted_demand_surge", 185000)
    active_contracts_volume = st.session_state.get(
        "active_contracts_volume", 129500
    )

    # Net Uncovered Deficit (Only hedge what isn't already covered by baseline contracts)
    net_units = st.session_state.get(
        "net_uncovered_units", max(0, gross_surge - active_contracts_volume)
    )

    sig_title = st.session_state.get(
        "active_risk_signal_title", "Baseline Operations Target"
    )
    si_score = st.session_state.get("si_composite", -0.33)
    fix_executed = st.session_state.get("fix_executed", False)

    # Base price setup per persona
    unit_base_price = (
        3200.0 if "Merchant" in persona else (45.0 if "FMCG" in persona else 780.0)
    )

    # 2. Render Functional Tabs
    tab_std, tab_synth = st.tabs(
        [
            "⚖️ Standard Desk & FIX Execution",
            "🧪 Synthetic Derivative Builder & Model Lab",
        ]
    )

    # --- TAB 1: STANDARD DESK & FIX EXECUTION ---
    with tab_std:
        st.info(
            f"🚩 **Active Risk Signal**: `{sig_title}` | Upstream Sentiment **$SI"
            f" = {si_score:+.2f}$** | Gross Surge: **{gross_surge:,}"
            f" {term_unit}** | Contracted Baseline: **{active_contracts_volume:,}"
            f" {term_unit}** | **Net Open Deficit: {net_units:,} {term_unit}**"
        )

        # Top Executive Metrics
        hedged_pct = 85.0 if fix_executed else 15.0
        open_volume = int(net_units * (1.0 - (hedged_pct / 100.0)))
        open_exposure_usd = open_volume * unit_base_price
        mtm_pnl = (
            (net_units * unit_base_price * 0.042)
            if fix_executed
            else (-net_units * unit_base_price * 0.028)
        )

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric(
            "Net Open Physical Risk",
            f"{open_volume:,} {term_unit}",
            f"${open_exposure_usd / 1e6:.2f}M Floating Risk",
            delta_color="inverse",
        )
        col_m2.metric(
            "Current Benchmark Forward",
            f"${unit_base_price * 1.03:,.2f}",
            "+3.0% Volatility Surge",
        )
        col_m3.metric(
            "Net Deficit Hedge Coverage",
            f"{hedged_pct:.0f}%",
            "Target: 80% Net Coverage",
            delta_color="normal" if hedged_pct >= 80 else "inverse",
        )
        col_m4.metric(
            "Mark-to-Market (MtM) P&L",
            f"${mtm_pnl / 1e6:+.2f}M",
            "FIX Bound" if fix_executed else "Unhedged Floating Drag",
            delta_color="normal" if mtm_pnl >= 0 else "inverse",
        )

        st.divider()

        # FIX Protocol Order Execution Console
        col_c1, col_c2 = st.columns([1.2, 1])

        with col_c1:
            st.subheader("⚡ FIX Protocol Order Ticket (Net Hedge Execution)")
            order_type = st.selectbox(
                "Order Type",
                [
                    "Limit Order (Zero-Cost Collar)",
                    "Market Sweep (Fixed Forward Swap)",
                    "Asian Call Option Cap",
                ],
            )

            # Default order slider strictly to the Net Uncovered Deficit
            order_qty = st.slider(
                f"Hedge Volume ({term_unit}):",
                min_value=1000,
                max_value=max(100000, int(net_units * 1.5)),
                value=int(net_units),
                step=2500,
            )
            limit_price = st.number_input(
                "Limit Strike / Forward Fixed Price ($)",
                value=float(unit_base_price * 1.01),
            )

            if st.button(
                "🚀 Execute FIX Protocol Hedging Order",
                type="primary",
                disabled=fix_executed,
            ):
                st.session_state["fix_executed"] = True
                st.toast(
                    f"FIX Order Executed: {order_qty:,} {term_unit} @"
                    f" ${limit_price:,.2f}",
                    icon="✅",
                )
                st.rerun()

            if fix_executed:
                st.success(
                    f"🟢 **FIX Protocol Status: EXECUTED & BOUND** — Bound"
                    f" `{order_qty:,} {term_unit}` under Order ID"
                    " `#FIX-99428-NYMEX`."
                )
                if st.button("Reset FIX Hedge Position"):
                    st.session_state["fix_executed"] = False
                    st.rerun()

        with col_c2:
            st.subheader("📋 Active Commodity Contracts & Net Hedge Book")
            contracts_df = pd.DataFrame(
                [
                    {
                        "Contract ID": "CT-2026-Q4-01",
                        "Type": "Baseline Fixed Swap",
                        "Volume": f"74,000 {term_unit}",
                        "Strike": f"${unit_base_price:,.2f}",
                        "Status": "ACTIVE (CONTRACTED)",
                    },
                    {
                        "Contract ID": "CT-2026-Q4-02",
                        "Type": "Baseline Option Cap",
                        "Volume": f"55,500 {term_unit}",
                        "Strike": f"${unit_base_price * 1.05:,.2f}",
                        "Status": "ACTIVE (CONTRACTED)",
                    },
                    {
                        "Contract ID": "FIX-99428-NYMEX",
                        "Type": f"Net Hedge ({order_type.split(' ')[0]})",
                        "Volume": f"{order_qty:,} {term_unit}",
                        "Strike": f"${limit_price:,.2f}",
                        "Status": (
                            "EXECUTED" if fix_executed else "OPEN (UNCOVERED)"
                        ),
                    },
                ]
            )
            st.dataframe(contracts_df, use_container_width=True, hide_index=True)

    # --- TAB 2: SYNTHETIC DERIVATIVE BUILDER & MODEL LAB ---
    with tab_synth:
        st.subheader("🧪 Synthetic Derivative Structurer")
        st.caption(
            "Model customized derivative payoffs tailored to the net uncovered"
            f" gap of **{net_units:,} {term_unit}**."
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
            )
            cap_strike_pct = st.slider(
                "Cap Strike % (Upper Protection)", 100, 130, 110, 1
            )
            floor_strike_pct = st.slider(
                "Floor Strike % (Lower Subsidization)", 70, 100, 90, 1
            )
            implied_vol = st.slider("Implied Volatility (σ %)", 10, 60, 28, 1)

            cap_val = unit_base_price * (cap_strike_pct / 100.0)
            floor_val = unit_base_price * (floor_strike_pct / 100.0)

            st.markdown("**Net Deficit Pricing Summary**")
            st.json(
                {
                    "Net Exposure Volume": f"{net_units:,} {term_unit}",
                    "Underlying Spot": f"${unit_base_price:,.2f}",
                    "Cap Strike": f"${cap_val:,.2f}",
                    "Floor Strike": f"${floor_val:,.2f}",
                    "Net Premium Cost": "$0.00 / Unit (Zero-Cost Verified)",
                }
            )

        with col_s2:
            st.markdown("**2. Net Payoff Profile Simulation at Expiry**")

            # Calculate Net Payoff Curve
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
    """Render Global Logistics Network & GIS Control Tower bound to net shipment volume."""
    import pandas as pd
    import pydeck as pdk

    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption(f"Active Persona View: **{persona}**")

    # 1. Pull dynamic data from Central Orchestrator Cascade
    cascade = st.session_state.get("active_sop_cascade", {})
    demand_data = cascade.get("demand", {})
    proc_data = cascade.get("procurement", {})

    gross_surge = demand_data.get(
        "total_surge_units", st.session_state.get("extracted_demand_surge", 185000)
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

    st.info(
        f"🚢 **Inbound Logistics Feed**: Tracking **{net_units:,} {term_unit}**"
        f" in net physical PO movement across 3 Ocean & Rail Corridors |"
        f" Lead-Time Shock: **+{transit_delay:.0f} Days** | Status: **PO"
        " Dispatched**"
    )

    # 2. Executive Logistics Metrics
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
        "Global Route Risk Level",
        "ELEVATED",
        "↑ Port Congestion",
        delta_color="inverse",
    )
    col_l4.metric(
        "On-Time In-Full (OTIF) Target",
        "88.4%",
        "↓ -6.2% Stressed",
        delta_color="inverse",
    )

    st.divider()

    # 3. Dynamic Corridor Allocation
    c1_vol = int(net_units * 0.45)
    c2_vol = int(net_units * 0.35)
    c3_vol = net_units - (c1_vol + c2_vol)

    st.subheader("📦 Transit Corridor Health & Arrival Timeline")
    corridor_df = pd.DataFrame(
        [
            {
                "Corridor Name": "Pacific Ocean Expressway (Asia → LA)",
                "Primary Carrier": "Maersk Ocean Line",
                "Volume (Units)": f"{c1_vol:,}",
                "Original ETA": "14 Days",
                "Delay Shock": "+3 Days",
                "Adjusted ETA": "17 Days",
                "Bottleneck Reason": "Port Berth Queueing",
            },
            {
                "Corridor Name": (
                    "Trans-Suez / Atlantic Route (Asia → Europe → US)"
                ),
                "Primary Carrier": "MSC Freight Fleet",
                "Volume (Units)": f"{c2_vol:,}",
                "Original ETA": "16 Days",
                "Delay Shock": "+4 Days",
                "Adjusted ETA": "20 Days",
                "Bottleneck Reason": "Canal Capacity Constraints",
            },
            {
                "Corridor Name": "Domestic Overland Heavy Rail",
                "Primary Carrier": "BNSF Railway Co",
                "Volume (Units)": f"{c3_vol:,}",
                "Original ETA": "5 Days",
                "Delay Shock": "+0 Days",
                "Adjusted ETA": "5 Days (On Schedule)",
                "Bottleneck Reason": "Normal Operations",
            },
        ]
    )
    st.dataframe(corridor_df, use_container_width=True, hide_index=True)

    st.divider()

    # 4. Interactive Pydeck GIS Map Layer
    st.subheader("🗺️ Live Global Transit Arc Overlay")
    routes_df = pd.DataFrame(
        [
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
        ]
    )

    arc_layer = pdk.Layer(
        "ArcLayer",
        routes_df,
        get_source_position=["start_lon", "start_lat"],
        get_target_position=["end_lon", "end_lat"],
        get_source_color=[255, 75, 75, 200],
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
  st.title("⚡ Sandbox Flight Simulator & Stress Lab")
  st.caption(f"Active Persona View: **{persona}**")

  macro_scenario = st.session_state.get(
      "sandbox_scenario",
      st.session_state.get("sb_scenario_select", "Baseline Operations"),
  )
  sandbox_params = st.session_state.get("sandbox_params", {})

  if "Freight" in macro_scenario or "Red Sea" in macro_scenario:
    def_vol = float(sandbox_params.get("iv_multiplier", 1.4)) * 0.35
    def_delay = int(sandbox_params.get("transit_delay_days", 8))
    def_surge = float(sandbox_params.get("volume_multiplier", 1.10)) * 1.2
  elif "Drought" in macro_scenario or "Crop" in macro_scenario:
    def_vol = float(sandbox_params.get("iv_multiplier", 1.8)) * 0.35
    def_delay = int(sandbox_params.get("transit_delay_days", 4))
    def_surge = float(sandbox_params.get("volume_multiplier", 0.85)) * 1.3
  elif "Volatility" in macro_scenario or "Black Swan" in macro_scenario:
    def_vol = float(sandbox_params.get("iv_multiplier", 2.5)) * 0.35
    def_delay = int(sandbox_params.get("transit_delay_days", 0)) + 14
    def_surge = float(sandbox_params.get("volume_multiplier", 1.00)) * 1.5
  else:
    def_vol, def_delay, def_surge = 0.15, 2, 1.00

  if st.session_state.get("last_applied_sandbox_scenario") != macro_scenario:
    st.session_state["last_applied_sandbox_scenario"] = macro_scenario
    st.session_state["sim_vol"] = min(1.0, max(0.05, round(def_vol, 2)))
    st.session_state["sim_lt"] = max(1, min(30, def_delay))
    st.session_state["sim_dem"] = min(2.5, max(0.8, round(def_surge, 2)))
    st.session_state.pop("mc_results", None)

  st.session_state.setdefault("sim_vol", min(1.0, max(0.05, round(def_vol, 2))))
  st.session_state.setdefault("sim_lt", max(1, min(30, def_delay)))
  st.session_state.setdefault(
      "sim_dem", min(2.5, max(0.8, round(def_surge, 2)))
  )

  # Pull session state including baseline contract volume
  si_score = st.session_state.get("si_composite", -0.33)
  gross_surge = st.session_state.get("extracted_demand_surge", 185000)
  active_contracts = st.session_state.get("active_contracts_volume", 129500)
  cash_balance = st.session_state.get("sop_cash_balance", 5_000_000.0)
  fix_executed = st.session_state.get("fix_executed", False)
  curr_leadtime_delay = st.session_state.get("active_leadtime_delay_days", 2.5)

  # Compute current net uncovered open deficit
  net_units = st.session_state.get(
      "net_uncovered_units", max(0, gross_surge - active_contracts)
  )

  st.divider()
  st.subheader("⚙️ Monte Carlo Stress Test Parameters")
  st.info(
      f"🌐 Active Scenario Presets: **{macro_scenario}** | Gross Demand Surge:"
      f" **{gross_surge:,} {term_unit}** | Baseline Contracts:"
      f" **{active_contracts:,} {term_unit}** | **Net Deficit Exposure:"
      f" {net_units:,} {term_unit}**"
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

  if st.button("🚀 Run Monte Carlo Stress Simulation", key="btn_run_mc"):
    with st.spinner(f"Simulating {n_sims:,} market shocks..."):
      base_unit_price = 780.0 if "Heavy" in persona else 150.0
      price_shocks = np.random.lognormal(
          mean=np.log(base_unit_price), sigma=vol_shock, size=n_sims
      )

      # Simulate gross demand surge across iterations
      simulated_gross = gross_surge * demand_multiplier * np.random.uniform(
          0.9, 1.1, size=n_sims
      )

      # Subtract baseline contracted volume to evaluate floating net deficit
      simulated_net_deficit = np.maximum(0, simulated_gross - active_contracts)

      # FIX hedge reduces open floating exposure on the net deficit
      hedge_ratio = 0.85 if fix_executed else 0.0
      unhedged_deficit = simulated_net_deficit * (1.0 - hedge_ratio)
      hedged_deficit = simulated_net_deficit * hedge_ratio

      # Financial cost = floating market shocks on unhedged net volume + locked cost on hedged net volume
      unhedged_cost = unhedged_deficit * price_shocks
      hedged_cost = hedged_deficit * base_unit_price
      total_simulated_cost = unhedged_cost + hedged_cost
      net_cash_impact = cash_balance - total_simulated_cost

      st.session_state["mc_results"] = {
          "mean_cost": np.mean(total_simulated_cost),
          "var_95": np.percentile(total_simulated_cost, 95),
          "var_99": np.percentile(total_simulated_cost, 99),
          "insolvency_risk": np.mean(net_cash_impact < 0) * 100.0,
          "total_cost": total_simulated_cost,
      }

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
          delta="High Risk" if res["insolvency_risk"] > 5 else "Manageable",
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

    if st.button(
        "⚡ Inject Stressed Parameters Back into Live Operations",
        key="btn_inject_mc",
    ):
      new_gross_surge = int(gross_surge * demand_multiplier)
      new_net_deficit = max(0, new_gross_surge - active_contracts)

      st.session_state["extracted_demand_surge"] = new_gross_surge
      st.session_state["net_uncovered_units"] = new_net_deficit
      st.session_state["active_leadtime_delay_days"] = (
          curr_leadtime_delay + lead_time_shock
      )
      st.session_state["si_composite"] = max(-1.0, si_score - (vol_shock * 0.5))
      st.toast(
          f"Propagated! New Gross Surge: {new_gross_surge:,} | New Net Deficit:"
          f" {new_net_deficit:,}",
          icon="⚡",
      )
      st.rerun()


def render_handshake_simulator():
  st.subheader("🤝 Enterprise Handshake Simulator")
  sim_col1, sim_col2 = st.columns([1, 1])

  with sim_col1:
    target_endpoint = st.selectbox(
        "Select Target Enterprise Endpoint:",
        [
            "SAP S/4HANA (BAPI PO Creation)",
            "Oracle Financials (GL Journal Post)",
            "Salesforce CRM (Demand Opportunity Sync)",
            "Inbound Webhook (Platts/LME Market Feed)",
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
            " HMAC-SHA256 signature..."
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
              "roundtrip_latency": "38 ms",
          },
      })


def render_integration_architecture(
    persona="Discrete & Heavy Industrial Enterprise", **kwargs
):
  st.title("🔌 Integration & Architecture Endpoints")

  active_sector = st.session_state.get(
      "sector_focus", "Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)"
  )
  sector_cfg = SECTOR_BENCHMARK_MAP.get(
      active_sector,
      SECTOR_BENCHMARK_MAP["Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)"],
  )
  now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

  # 1. Pull dynamic pipeline state metrics
  gross_surge = st.session_state.get("extracted_demand_surge", 185000)
  active_contracts = st.session_state.get("active_contracts_volume", 129500)
  net_units = st.session_state.get(
      "net_uncovered_units", max(0, gross_surge - active_contracts)
  )
  term_unit = kwargs.get("term_unit", "Units")
  fix_executed = st.session_state.get("fix_executed", False)
  hedge_gain = (
      3_810_000.0 if fix_executed else 0.0
  )  # Net realized CTRM benefit

  st.info(
      f"🌐 **Active Sector**: **{active_sector}** | Primary Benchmark:"
      f" **{sector_cfg['primary_index']}** | Net Uncovered Target:"
      f" **{net_units:,} {term_unit}**"
  )

  st.subheader("📡 Real-Time Benchmark Gateway Status")
  gateway_df = pd.DataFrame({
      "Endpoint / Interface": [
          f"Primary Index Feed ({sector_cfg['primary_index'].split('/')[0].strip()})",
          f"Secondary Index ({sector_cfg['secondary_index']})",
          "SAP S/4HANA Enterprise ERP",
          "CME / LME FIX Gateway",
          "Salesforce CRM API",
          "Oracle / PeopleSoft GL Gateway",
      ],
      "Mapped Asset / Protocol": [
          sector_cfg["ticker_symbol"],
          "Market Benchmark Index",
          f"BAPI ({sector_cfg['sap_mat_code']})",
          "FIX 4.4 Engine",
          "REST / OAuth 2.0",
          f"GL Sync ({sector_cfg['oracle_gl_account']})",
      ],
      "Latency": ["14 ms", "22 ms", "45 ms", "4 ms", "88 ms", "62 ms"],
      "Status": [
          "🟢 HEALTHY",
          "🟢 HEALTHY",
          "🟢 HEALTHY",
          "🟢 HEALTHY",
          "🟢 HEALTHY",
          "🟢 HEALTHY",
      ],
  })
  st.table(gateway_df)

  st.divider()
  st.subheader("📡 Ingestion Webhook Schema")
  c1, c2 = st.columns(2)
  with c1:
    st.markdown("**Registered Sector Data Feeds**")
    feed_df = pd.DataFrame({
        "Source Feed": [
            f"{sector_cfg['primary_index'].split(' ')[0]} Direct Market Feed",
            "LinkedIn / Market Advisory Newsletter",
            "Global Freight & Logistics Radar",
        ],
        "Mapped Index": [
            sector_cfg["primary_index"],
            "NLP Sentiment Parser ($SI$)",
            "Transit Lead Time (+7 Days)",
        ],
        "Status": ["🟢 Active", "🟢 Active", "🟢 Active"],
    })
    st.table(feed_df)

  with c2:
    st.markdown(
        f"**Live API Ingestion Payload (`POST`) — {sector_cfg['ticker_symbol']}**"
    )
    st.code(
        f"""POST /api/v1/ingest/unstructured-feed
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
  "payload": {{
    "raw_text": "{sector_cfg['sample_headline']}",
    "timestamp": "{now_iso}"
  }}
}}""",
        language="json",
    )

  st.divider()
  st.subheader("🏛️ Enterprise Core Connectors")
  tab1, tab2 = st.tabs(
      ["SAP S/4HANA (Dynamic Material BAPI)", "Oracle GL Financial Gateway"]
  )

  with tab1:
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

  with tab2:
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

  st.divider()
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
  sandbox_scenario = st.sidebar.selectbox(
      "Select 'What-If' Stress Scenario:",
      [
          "Baseline Operations",
          "Red Sea Freight Bottleneck (+45% Freight, +8d Lag)",
          "Red River Drought / Crop Deficit (-30% Yield)",
          "Black Swan Volatility Spike (+250% IV Shock)",
      ],
      key="sb_scenario_select",
  )

  if st.sidebar.button("🧪 Launch Sim Scenario", key="btn_launch_sandbox"):
    st.session_state["sandbox_active"] = (
        sandbox_scenario != "Baseline Operations"
    )
    st.session_state["sandbox_scenario"] = sandbox_scenario

    if "Freight" in sandbox_scenario:
      st.session_state["sandbox_params"] = {
          "volume_multiplier": 1.10,
          "spot_cost_increase": 0.35,
          "transit_delay_days": 8,
          "iv_multiplier": 1.4,
          "description": (
              "Red Sea maritime rerouting forcing Cape of Good Hope transit."
          ),
      }
    elif "Drought" in sandbox_scenario:
      st.session_state["sandbox_params"] = {
          "volume_multiplier": 0.85,
          "spot_cost_increase": 0.50,
          "transit_delay_days": 4,
          "iv_multiplier": 1.8,
          "description": (
              "Severe agricultural crop failure inflating physical spot prices."
          ),
      }
    elif "Volatility" in sandbox_scenario:
      st.session_state["sandbox_params"] = {
          "volume_multiplier": 1.00,
          "spot_cost_increase": 0.15,
          "transit_delay_days": 0,
          "iv_multiplier": 2.5,
          "description": (
              "Financial market dislocation spiking derivative options implied"
              " volatility."
          ),
      }
    else:
      st.session_state["sandbox_params"] = {
          "volume_multiplier": 1.00,
          "spot_cost_increase": 0.00,
          "transit_delay_days": 0,
          "iv_multiplier": 1.0,
          "description": "Standard baseline parameters.",
      }
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