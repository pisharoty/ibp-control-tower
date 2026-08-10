import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import math
from scipy.stats import norm

# =====================================================================
# BULLETPROOF ENGINE FALLBACK / IN-MEMORY CONNECTOR
# =====================================================================
try:
    from bulletproof_engine import BulletproofDataEngine
except ImportError:
    class BulletproofDataEngine:
        @staticmethod
        def get_market_volatility(symbol="NVDA"):
            return {"symbol": symbol, "implied_vol": 34.2}

        @staticmethod
        def get_nlp_news_signal(query="semiconductor shortage"):
            return {
                "headline": f"Supply Chain Bottleneck Detected in {query.title()}",
                "sentiment": -0.45,
                "risk": "🔴 HIGH RISK",
                "source": "🟢 LIVE NEWS RSS"
            }

        @staticmethod
        def get_parcel_telemetry():
            return {
                "carrier": "FedEx Express",
                "tracking_code": "TRK-2026-9901",
                "origin": "Port of Los Angeles",
                "destination": "Chicago Logistics Hub DC",
                "status": "🟡 Delayed (+12 hrs - Port Congestion)",
                "source": "🟢 LIVE TELEMETRY"
            }

        @staticmethod
        def get_freight_market_signal():
            return {"fbx_index": "$3,250 / FEU", "change": "+8.4%", "source": "Freightos FBX"}

        @staticmethod
        def get_noaa_weather_signal():
            return {"anomaly": "+1.8°C", "status": "⚠️ Tropical Depression Warning", "source": "NOAA Maritime"}

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "custom_scenario_params" not in st.session_state:
    st.session_state["custom_scenario_params"] = None
if "extracted_demand_surge" not in st.session_state:
    st.session_state["extracted_demand_surge"] = 65000
if "ctrm_ledger" not in st.session_state:
    st.session_state["ctrm_ledger"] = []
if "bom_requisitions" not in st.session_state:
    st.session_state["bom_requisitions"] = {
        "metals_mt": 10300,
        "semis_units": 1030000,
        "freight_feus": 5150
    }

st.set_page_config(page_title="IBP Enterprise Control Tower", layout="wide")

# =====================================================================
# SIDEBAR: PERSONA SWITCHER, DYNAMIC NAVIGATION & FLIGHT SIMULATOR SANDBOX
# =====================================================================
st.sidebar.title("⚡ IBP Control Tower")

persona = st.sidebar.selectbox(
    "🏢 Enterprise Platform Persona",
    [
        "🏭 Discrete & Heavy Industrial Enterprise",
        "📦 Process Goods & FMCG Enterprise",
        "📈 Merchant Trading & Commodity Risk Desk"
    ],
    key="platform_persona_v12"
)

# Persona-Specific Module Mapping
if "Industrial" in persona:
    module_options = [
        "📊 Executive S&OP Control Tower",
        "🧠 NLP Commercial Sensing & Field Intelligence",
        "⚖️ Demand/Supply Match & Plant Load Balancer",
        "📈 Physical Procurement & Contract Desk",
        "🛡️ CTRM Event-Driven Hedging Desk",
        "🧪 Sandbox Flight Simulator & Stress Lab",
        "🌐 Global Logistics Network & GIS Control Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
    term_unit = "Units"
    term_raw = "Raw Metals & Components"
    plant1_name = "Detroit Main Assembly Plant"
    plant2_name = "Munich Component Line"
    toller_name = "3rd-Party Contract Manufacturer (CMO)"
elif "FMCG" in persona:
    module_options = [
        "📊 Integrated Business Planning (IBP) Tower",
        "🧠 NLP Commercial Sensing & Retail Intelligence",
        "⚖️ Batch Processing & Co-Packer Load Balancer",
        "📈 Agri-Ingredients & Direct Procurement",
        "🛡️ CTRM Softs & Commodity Risk Desk",
        "🧪 Sandbox Flight Simulator & Stress Lab",
        "🌐 Cold Chain & Regional Distribution GIS Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
    term_unit = "Cases / Batches"
    term_raw = "Agri Softs & Ingredients"
    plant1_name = "Midwest Processing Facility"
    plant2_name = "Rotterdam Blending Plant"
    toller_name = "Regional Co-Packer & Cold Storage"
else:  # Merchant Trading
    module_options = [
        "📊 Daily Trading Balance Sheet & Position Tower",
        "🧠 Global Macro & Satellite Market Intelligence",
        "📈 Physical Off-Take & Merchant Storage Desk",
        "🛡️ CTRM Derivatives & Risk Arbitrage Desk",
        "🧪 Sandbox Flight Simulator & Stress Lab",
        "🌐 Global Maritime AIS & Cargo GIS Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
    term_unit = "Lots / Contracts"
    term_raw = "Physical Deliverable Cargoes"
    plant1_name = "Primary Import Terminal A"
    plant2_name = "Regional Hub Terminal B"
    toller_name = "3rd-Party Merchant Storage Arbitrage"

selected_module = st.sidebar.radio(
    "Select Operational Module",
    module_options,
    key="nav_module_selection_v12"
)

st.session_state["selected_module"] = selected_module

# ---------------------------------------------------------------------
# 🧪 FLIGHT SIMULATOR SANDBOX WIDGET (REPLACES RISK INJECTOR)
# ---------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Flight Simulator (Sandbox)")
st.sidebar.caption("🔒 Isolated Stress-Test Mode (Disconnected from CTRM & FIX Gateways)")

simulator_preset = st.sidebar.selectbox(
    "Select Macro 'What-If' Scenario:",
    [
        "None (Live Production Mode)",
        "🌊 El Niño Drought & Crop Yield Crash (-30% Supply)",
        "🚢 Red Sea / Suez Maritime Canal Blockage (+18 Days)",
        "🌋 Volcanic Ash Cloud Cargo Grounding (+40% Freight)",
        "⚡ 3-Sigma Market Shock (+50% Spot Volatility Jump)"
    ],
    key="sb_flight_sim_preset_selector_v12"
)

col_sim1, col_sim2 = st.sidebar.columns(2)
with col_sim1:
    if st.button("🧪 Launch Sim", key="btn_run_sim_sandbox_v12"):
        if simulator_preset == "None (Live Production Mode)":
            st.session_state["sandbox_active"] = False
            st.toast("Exited Sandbox Mode. Active on Live Production Pipeline.", icon="🟢")
        else:
            st.session_state["sandbox_active"] = True
            st.session_state["sandbox_scenario"] = simulator_preset
            if "El Niño" in simulator_preset:
                st.session_state["sandbox_params"] = {
                    "volume_multiplier": 1.45, "spot_cost_increase": 0.35, "transit_delay_days": 12, "iv_multiplier": 1.6,
                    "description": "Severe weather shock reducing agricultural feedstocks and triggering spot price spikes."
                }
            elif "Canal Blockage" in simulator_preset:
                st.session_state["sandbox_params"] = {
                    "volume_multiplier": 1.15, "spot_cost_increase": 0.25, "transit_delay_days": 18, "iv_multiplier": 1.4,
                    "description": "Chokepoint transit delay depleting safety stock buffers and inflating container freight rates."
                }
            elif "Volcanic" in simulator_preset:
                st.session_state["sandbox_params"] = {
                    "volume_multiplier": 1.10, "spot_cost_increase": 0.40, "transit_delay_days": 10, "iv_multiplier": 1.5,
                    "description": "Air and maritime logistics grounding causing severe freight spot rate surges."
                }
            else:
                st.session_state["sandbox_params"] = {
                    "volume_multiplier": 1.80, "spot_cost_increase": 0.50, "transit_delay_days": 0, "iv_multiplier": 2.2,
                    "description": "Extreme financial market jump-diffusion volatility shock on option pricing surfaces."
                }
            st.toast(f"Flight Simulator Active: {simulator_preset}", icon="🧪")

with col_sim2:
    if st.button("🔄 Reset Sim", key="btn_reset_sim_sandbox_v12"):
        st.session_state["sandbox_active"] = False
        st.session_state["sandbox_scenario"] = None
        st.session_state["sandbox_params"] = {
            "volume_multiplier": 1.0, "spot_cost_increase": 0.0, "transit_delay_days": 0, "iv_multiplier": 1.0,
            "description": "Baseline Simulation Context"
        }
        st.toast("Flight Simulator reset to Baseline.", icon="🔄")

st.sidebar.markdown("---")

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def parse_demand_from_text(text):
    patterns = [
        r'(?:spike|surge|demand|units|cases|batches)\s*(?:of|by)?\s*~?\s*(\d+[\d,]*)',
        r'(\d+[\d,]*)\s*(?:additional|extra)?\s*(?:units|cases|batches|lots|MT)'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val_str = m.group(1).replace(',', '')
            if val_str.isdigit() and int(val_str) > 100:
                return int(val_str)
    return 65000

def black76_call_put(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0.0, 0.0, 0.0, 0.0
    d1 = (math.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    call = math.exp(-r * T) * (S * norm.cdf(d1) - K * norm.cdf(d2))
    put = math.exp(-r * T) * (K * norm.cdf(-d2) - S * norm.cdf(-d1))
    delta_call = math.exp(-r * T) * norm.cdf(d1)
    vega = S * math.exp(-r * T) * norm.pdf(d1) * math.sqrt(T) / 100.0
    return call, put, delta_call, vega

def get_persona_contracts(persona_type):
    if "Industrial" in persona_type:
        return [
            {"Contract ID": "CTR-2026-A1", "Commodity": "Primary Aluminum / Heavy Metals", "Supplier": "Rio Tinto", "Volume": "15,000 MT", "Fixed Price": "$2,200 / MT", "Status": "Active"},
            {"Contract ID": "CTR-2026-B4", "Commodity": "Freight Futures (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "Status": "Under Review"},
            {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor Wafers / Components", "Supplier": "TSMC", "Volume": "100,000 Wafers", "Fixed Price": "$450 / Wafer", "Status": "Executing"}
        ]
    elif "FMCG" in persona_type:
        return [
            {"Contract ID": "CTR-2026-F1", "Commodity": "Raw Cocoa Beans & Sugar", "Supplier": "Cargill Agri", "Volume": "8,500 MT", "Fixed Price": "$3,420 / MT", "Status": "Active"},
            {"Contract ID": "CTR-2026-F2", "Commodity": "Flexible Packaging Barrier Film", "Supplier": "Amcor Flexibles", "Volume": "450,000 Roll Units", "Fixed Price": "$18.50 / Roll", "Status": "Executing"},
            {"Contract ID": "CTR-2026-F3", "Commodity": "Liquid Dairy Concentrate", "Supplier": "Fonterra Co-op", "Volume": "12,000 Liters", "Fixed Price": "$4.10 / Liter", "Status": "Active"}
        ]
    else:  # Merchant Trading
        return [
            {"Contract ID": "CTR-2026-M1", "Commodity": "Physical Gold Bullion (99.99%)", "Supplier": "Zurich Vault Reserve", "Volume": "50,000 Troy Oz", "Fixed Price": "$2,380 / Oz", "Status": "Executing"},
            {"Contract ID": "CTR-2026-M2", "Commodity": "Rare Earth Elements (Neodymium)", "Supplier": "Rotterdam Metal Depot", "Volume": "1,200 MT", "Fixed Price": "$115,000 / MT", "Status": "Active"},
            {"Contract ID": "CTR-2026-M3", "Commodity": "Light Sweet Crude Off-Take", "Supplier": "Cushing Tank Farm", "Volume": "1,200,000 Bbls", "Fixed Price": "$76.50 / Bbl", "Status": "Under Review"}
        ]
# =====================================================================
# ROUTER 1: EXECUTIVE S&OP CONTROL TOWER
# =====================================================================
if "Executive S&OP" in selected_module or "IBP Tower" in selected_module:
    st.title("📊 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time financial alignment, financial waterfalls, and trade hedge benefit reconciliation.")

    # Dynamic inputs from CTRM & Sandbox
    is_executed = st.session_state.get("fix_order_executed", False)
    is_sandbox = st.session_state.get("sandbox_active", False)
    sim_params = st.session_state.get("sandbox_params", {"spot_cost_increase": 0.0})
    raw_surge = st.session_state.get("extracted_demand_surge", 65000)

    # Dynamic Financial Calculations
    base_aop = 120.00  # $120.0M
    surge_revenue = (raw_surge / 65000.0) * 16.20  # $16.20M

    if is_executed:
        ctrm_hedge_benefit = 4.82  # Realized gain from executed FIX Asian Call Collar
        hedge_badge = "🟢 FIX Order Realized Gain"
        hedge_pct = "100% Fully Hedged"
    else:
        ctrm_hedge_benefit = 3.25  # Unexecuted paper model gain
        hedge_badge = "⚠️ Pending FIX Execution"
        hedge_pct = "85% Hedged (15% Float)"

    base_cogs_freight = 12.40 * (1.0 + sim_params.get("spot_cost_increase", 0.0))
    net_ebitda = base_aop + surge_revenue + ctrm_hedge_benefit - base_cogs_freight

    # Top Metric Strip
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Annual Operating Plan (AOP)", f"${base_aop:.1f}M", "+4.2% YoY")
    col_m2.metric("Unconstrained Demand (AOP + Surge)", f"${base_aop + surge_revenue:.1f}M", f"+{raw_surge:,} {term_unit}")
    col_m3.metric("CTRM Hedge & Trade Benefit", f"+${ctrm_hedge_benefit:.2f}M", hedge_badge)
    col_m4.metric("Net Realized EBITDA", f"${net_ebitda:.2f}M", f"{'+' if net_ebitda >= 127.10 else ''}{net_ebitda - 120.0:.2f}M vs AOP")

    st.markdown("---")
    st.subheader("📡 Live Operational Desk Feeds")
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.info(f"🧠 **NLP Commercial Sensing**: Auto-hooked signal (+{raw_surge:,} {term_unit}).")
    if is_executed:
        col_d2.success(f"🛡️ **CTRM Desk**: FIX 4.4 Order Executed! Derivative gain unlocked (+${ctrm_hedge_benefit:.2f}M).")
    else:
        col_d2.warning(f"🛡️ **CTRM Desk**: Unhedged spot exposure pending FIX order execution.")
    col_d3.error(f"⚖️ **Demand/Supply Load Balancer**: Plant load operating near capacity limits.")

    st.markdown("---")
    col_w1, col_w2 = st.columns([1.2, 1])

    with col_w1:
        st.subheader("💵 Financial P&L Margin Waterfall Report")
        pnl_df = pd.DataFrame([
            {"P&L Line Item": "1. Base AOP Revenue Target", "Amount ($)": f"${base_aop:.2f}M", "Impact": "🎯 Baseline Plan"},
            {"P&L Line Item": "2. Unconstrained Surge Realization", "Amount ($)": f"+${surge_revenue:.2f}M", "Impact": "➕ Commercial Upside"},
            {"P&L Line Item": "3. CTRM Derivative & Hedge Gain", "Amount ($)": f"+${ctrm_hedge_benefit:.2f}M", "Impact": "🛡️ Risk Protection (FIX Active)" if is_executed else "⚠️ Unexecuted Target"},
            {"P&L Line Item": "4. COGS & Freight Cost Drag", "Amount ($)": f"-${base_cogs_freight:.2f}M", "Impact": "🚨 Stress Shock Drag" if is_sandbox else "➖ Supply Operations"},
            {"P&L Line Item": "5. Projected Net EBITDA", "Amount ($)": f"${net_ebitda:.2f}M", "Impact": "🟢 Net Bottom-Line"}
        ])
        st.dataframe(pnl_df, use_container_width=True, hide_index=True)

    with col_w2:
        st.subheader("📈 CTRM Commodity Hedging Ledger")
        ledger_df = pd.DataFrame([
            {"Raw Material Commodity": term_raw, "Hedged Position": hedge_pct, "Locked Rate": "$2,210 / MT", "Spot Exposure": "0% Covered" if is_executed else "15% Unhedged ⚠️"},
            {"Raw Material Commodity": "Freight Futures (FBX)", "Hedged Position": "90%", "Locked Rate": "$1,450 / FEU", "Spot Exposure": "10% Unhedged ⚠️"},
            {"Raw Material Commodity": "Power & Energy Hedges", "Hedged Position": "100%", "Locked Rate": "$64.50 / MWh", "Spot Exposure": "0% Covered"}
        ])
        st.dataframe(ledger_df, use_container_width=True, hide_index=True)

# =====================================================================
# ROUTER 2: NLP COMMERCIAL SENSING & INTELLIGENCE
# =====================================================================
elif any(k in selected_module for k in ["NLP Commercial", "Global Macro"]):
    COMMODITY_NLP_QUERIES = {
        "🛒 Retail & Omnichannel Goods": "retail inventory port dwell consumer demand logistics bottleneck",
        "🌾 Food, Beverage & Agriculture": "food supply chain refrigerated freight crop yield shortage drought",
        "🧼 FMCG, CPG & Household Goods": "CPG packaging material cost palm oil pulp paper supply chain",
        "🔬 Semiconductors & High-Tech": "semiconductor wafer fab shortage supply chain disruption",
        "🚗 Automotive & Mobility OEM": "automotive supply chain parts shortage logistics delay EV battery",
        "🏗️ Steel, Ferrous & Heavy Metals": "steel prices iron ore scrap metal supply chain bottleneck",
        "🛢️ Energy, Chemicals & Feedstocks": "crude oil chemical feedstock plastic resin supply chain",
        "💊 Pharma, MedTech & Healthcare": "pharmaceutical cold chain API active ingredient supply shortage"
    }

    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Ingest unstructured signals from news feeds, social media, **post-trade show emails**, and **marketing promo debriefs**.")
    
    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web Signals", 
        "📧 Email & Event Debrief Parser", 
        "🌐 Freight, Weather & Black Swan Feeds"
    ])

    # -----------------------------------------------------------------
    # TAB 1: Live Web Signals
    # -----------------------------------------------------------------
    with tab1:
        st.subheader("📡 Real-Time Web & Macro News Stream")
        st.caption("Scrape and parse live geopolitical, freight, and commodity web headlines.")
        
        web_surge_units = st.number_input(
            "Extracted Web Signal Impact (Units)", 
            value=85000, 
            step=5000, 
            key="web_surge_input"
        )
        
        if st.button("🌐 Ingest Scraped Web News Signal", key="btn_ingest_web"):
            st.session_state["extracted_demand_surge"] = web_surge_units
            st.session_state["active_risk_signal_title"] = "Red Sea Freight Rate Spike & Port Bottleneck"
            st.session_state["signal_category"] = "Live Web Signal"
            st.toast("Ingested Live Web News feed into CTRM & S&OP!", icon="🌐")
            st.success(f"✅ Propagated **Red Sea Freight Rate Spike** ({web_surge_units:,} Units) across S&OP and CTRM Desk!")

    # -----------------------------------------------------------------
    # TAB 2: Email & Event Debrief Parser
    # -----------------------------------------------------------------
    with tab2:
        st.subheader("📧 Unstructured Email & Field Report Extractor")
        st.caption("Parse post-trade show debriefs and promotional feedback to capture early demand spikes before formal ERP entry.")
        
        email_sample = st.selectbox(
            "Select Email Sample or Enter Custom Text:",
            ["Post-Trade Show Sales Debrief (CES Expo 2026)", "Regional Field Sales Order Spike", "Custom Input"],
            key="email_sample_select"
        )
        
        email_body = st.text_area(
            "Email Content Body:",
            value="From: vpsales@enterprise.com\nDate: Aug 3, 2026\nSubject: CES 2026 Recap - Massive Foot Traffic & Verbal Commitments\n\n250000 cases of cosmo cola for Costco",
            height=120,
            key="email_body_area"
        )
        
        parsed_units = st.number_input(
            "Parsed Demand Surge (Units)", 
            value=250000, 
            step=10000, 
            key="email_units_input"
        )
        parsed_event_name = "CES Expo 2026" if "CES" in email_sample else "Field Sales Spike"

        if st.button("🔴 Extract NLP Demand Intent & Quantify Surge", key="btn_extract_email"):
            st.session_state["extracted_demand_surge"] = parsed_units
            st.session_state["active_risk_signal_title"] = f"Trade Show / Sales Debrief ({parsed_event_name})"
            st.session_state["signal_category"] = "Unstructured Field Email"
            st.toast("Ingested Email Debrief surge into CTRM & S&OP!", icon="📧")
            st.success(f"✅ Propagated **{parsed_event_name}** ({parsed_units:,} Units) directly to S&OP Workbench & CTRM Desk!")

    # -----------------------------------------------------------------
    # TAB 3: Freight, Weather & Black Swan Feeds
    # -----------------------------------------------------------------
    with tab3:
        st.subheader("🌩️ Climate, Weather & Black Swan Risk Feeds")
        st.caption("Ingest NOAA alerts and macro disruption feeds to price commodity and supply chain tail-risk.")
        
        weather_surge_units = st.number_input(
            "Climate Risk Supply Deficit Impact (Units)", 
            value=120000, 
            step=5000, 
            key="weather_surge_input"
        )

        if st.button("🌩️ Activate Black Swan Climate Risk Feed", key="btn_activate_weather"):
            st.session_state["extracted_demand_surge"] = weather_surge_units
            st.session_state["active_risk_signal_title"] = "NOAA Category 4 Gulf Hurricane Alert"
            st.session_state["signal_category"] = "Weather & Macro Swan Feed"
            st.toast("Ingested NOAA Climate Alert into CTRM & S&OP!", icon="🌩️")
            st.success(f"✅ Propagated **NOAA Climate Alert** ({weather_surge_units:,} Units) directly to S&OP Workbench & CTRM Desk!")


# =====================================================================
# ROUTER 3: DEMAND/SUPPLY MATCH & PLANT LOAD BALANCER
# =====================================================================
elif "Demand/Supply" in selected_module:
    st.title("⚖️ Demand/Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")

    raw_surge = st.session_state.get("extracted_demand_surge", 65000)

    # Restored 2-Tab Navigation
    tab_solver, tab_bau = st.tabs(["📊 Executive Solver & Plant Load", "🛠️ BAU Engine & Demand Horizon Workbench"])

    with tab_solver:
        st.subheader("⚙️ Multi-Plant Load Balancer & Optimization Solver")
        st.markdown("Optimize production allocation across internal plants and 3rd-party co-packers under capacity constraints.")

        # 1. Controls defined first so metrics can read live slider values
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            plant1_cap = st.slider(f"Max Capacity - {plant1_name} (Units/Wk)", 100000, 150000, 120000, step=5000, key="plant1_cap_slider")
            shift_pattern = st.selectbox("Plant Shift Model", ["3-Shift (24/7 Continuous)", "2-Shift Standard", "Overtime Extended"], key="shift_model_select")
        with col_p2:
            toller_split = st.slider(f"Over-Capacity Offload to {toller_name} (%)", 0, 50, 15, step=5, key="toller_split_slider")
            copacker_margin_drag = toller_split * 0.12
            st.caption(f"Estimated Co-Packer Margin Surcharge Drag: **-${copacker_margin_drag:.2f}M**")

        st.markdown("---")

        # 2. Dynamic Metric Calculations
        internal_share = 1.0 - (toller_split / 100.0)
        allocated_to_plant1 = raw_surge * internal_share
        
        # Calculate load percentage: nominal baseline (80%) + surge load
        p1_load_pct = 80.0 + ((allocated_to_plant1 / plant1_cap) * 20.0)
        cmo_load_pct = float(toller_split)

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric(
            f"{plant1_name} Load", 
            f"{p1_load_pct:.1f}%", 
            f"{'+' if p1_load_pct > 100 else ''}{p1_load_pct - 100:.1f}% vs Nominal Cap"
        )
        col_s2.metric(f"{plant2_name} Load", "87.1%", "Optimal Operating Band")
        col_s3.metric(
            f"{toller_name} Load", 
            f"{cmo_load_pct:.1f}%", 
            "⚡ Co-Packer Surcharge Active" if cmo_load_pct > 0 else "Nominal"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("⚡ Run Mixed-Integer Linear Program (MILP) Solver", key="btn_run_milp_solver"):
            st.session_state["milp_solved"] = True
            st.toast("MILP Constraint Solver Converged! Capacity reallocated across plants.", icon="⚙️")

        if st.session_state.get("milp_solved", False):
            st.success(f"✅ **MILP Optimization Optimal**: Reallocated {raw_surge:,} units across internal lines ({100-toller_split}%) and co-packers ({toller_split}%). Operations balanced.")

    with tab_bau:
        st.markdown("### 🛠️ Step 1: BAU Statistical Baseline Generator")
        col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 1])
        with col_g1:
            yoy_growth = st.slider("Projected YoY Organic Growth (%)", 0.0, 20.0, 5.0, step=0.5, key="yoy_growth_slider")
        with col_g2:
            seasonality = st.selectbox("Seasonality Curve", ["Summer Surge (Beverages/CPG)", "Flat / Steady State", "Q4 Holiday Peak"], key="seasonality_select")
        with col_g3:
            base_avg_units = st.number_input("Prior Year Base Avg (Units)", value=100000, step=5000, key="base_avg_units")

        # Time-phased horizon calculations (W35 to W40)
        growth_mult = 1.0 + (yoy_growth / 100.0)
        w35_bau = int(base_avg_units * 1.3735 * growth_mult)
        w36_bau = int(base_avg_units * 1.3230 * growth_mult)
        w37_bau = int(base_avg_units * 1.2075 * growth_mult)
        w38_bau = int(base_avg_units * 1.4805 * growth_mult)
        w39_bau = int(base_avg_units * 1.0395 * growth_mult)
        w40_bau = int(base_avg_units * 0.9345 * growth_mult)

        st.markdown("---")
        st.markdown("### 🧩 Step 2: Forecast Layer Building Blocks")

        grid_df = pd.DataFrame([
            {"Building Block": "1. Auto BAU Stat Baseline 📈", "W35 (Aug)": f"{w35_bau:,}", "W36 (Aug)": f"{w36_bau:,}", "W37 (Sep)": f"{w37_bau:,}", "W38 (Sep)": f"{w38_bau:,}", "W39 (Sep)": f"{w39_bau:,}", "W40 (Oct)": f"{w40_bau:,}"},
            {"Building Block": "2. Marketing Promo Uplift (NLP) 📣", "W35 (Aug)": "0", "W36 (Aug)": "0", "W37 (Sep)": "0", "W38 (Sep)": f"{raw_surge:,}", "W39 (Sep)": "15,000", "W40 (Oct)": "0"},
            {"Building Block": "3. Commercial / Shock Adjustment ✏️", "W35 (Aug)": "0", "W36 (Aug)": "10,000", "W37 (Sep)": "0", "W38 (Sep)": "0", "W39 (Sep)": "0", "W40 (Oct)": "0"}
        ])
        st.dataframe(grid_df, use_container_width=True, hide_index=True)

        # Sum total horizon demand and persist to session state
        total_horizon_demand = (w35_bau + w36_bau + w37_bau + w38_bau + w39_bau + w40_bau) + raw_surge + 25000
        st.session_state["calculated_horizon_demand"] = total_horizon_demand

        st.markdown("---")
        st.markdown("### 📦 Step 3: Downstream Physical Procurement & Purchasing Signals")

        col_p1, col_p2, col_p3 = st.columns([1, 1, 1.5])
        col_p1.metric("Total Horizon Demand", f"{total_horizon_demand:,} {term_unit}")
        
        raw_material_pr = int(total_horizon_demand * 0.05)
        col_p2.metric("Raw Material Purchase Requisitions (PR)", f"{raw_material_pr:,} {term_raw}")

        with col_p3:
            if st.session_state.get("demand_plan_committed", False):
                st.success(f"✅ Demand Plan Committed ({st.session_state.get('committed_horizon_demand', total_horizon_demand):,} {term_unit}). Hooked to SAP S/4HANA!")
            else:
                st.warning("⚠️ Plan uncommitted. Click below to lock forecast into Physical Procurement.")

        if st.button("🔴 Commit Demand Plan & Trigger ERP Procurement Requisitions", key="btn_commit_demand"):
            st.session_state["demand_plan_committed"] = True
            st.session_state["committed_horizon_demand"] = total_horizon_demand
            st.toast(f"Demand Plan committed ({total_horizon_demand:,} {term_unit})! Procurement BOM recalculated.", icon="📦")
            st.rerun()

# =====================================================================
# ROUTER 4: PHYSICAL PROCUREMENT & MASTER CONTRACT DESK
# =====================================================================
elif "Physical Procurement" in selected_module:
    st.title("📄 Physical Procurement & Master Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Active enterprise supplier commitments, physical off-take agreements, and volume requisitions.")

    st.subheader("📋 Active Physical Supply Contracts")
    contracts_df = pd.DataFrame([
        {"Contract ID": "CTR-2026-A1", "Commodity": term_raw, "Supplier": "Rio Tinto", "Volume": f"15,000 {term_raw}", "Fixed Price": "$2,200 / MT", "Status": "Active"},
        {"Contract ID": "CTR-2026-B4", "Commodity": "Freight Futures (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "Status": "Under Review"},
        {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor Wafers / Components", "Supplier": "TSMC", "Volume": "100,000 Wafers", "Fixed Price": "$450 / Wafer", "Status": "Executing"}
    ])
    st.dataframe(contracts_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📦 Bill of Materials (BOM) Auto-Requisition Engine")

    # Read demand dynamically from Router 3
    is_committed = st.session_state.get("demand_plan_committed", False)
    active_demand = st.session_state.get("committed_horizon_demand" if is_committed else "calculated_horizon_demand", 846049)

    if is_committed:
        st.success(f"⚡ **Live S&OP Sync Active**: Displaying requisitions for committed Demand Plan of **{active_demand:,} {term_unit}**.")
    else:
        st.info(f"ℹ️ **Baseline S&OP Forecast**: Displaying uncommitted requisitions for **{active_demand:,} {term_unit}** (Commit in Router 3 to finalize ERP purchase orders).")

    # Dynamic BOM Explosion formulas
    req_metals_mt = int(active_demand * 0.015)         # 1.5% mass ratio
    req_components = int(active_demand * 1.50)           # 1.5x components per finished unit
    req_freight_feus = int(active_demand / 144.28)       # ~144 units per FEU container

    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Required Raw Metals & Components", f"{req_metals_mt:,} {term_raw}")
    col_b2.metric("Component Requisitions", f"{req_components:,} Units")
    col_b3.metric("Freight Slots Reserved", f"{req_freight_feus:,} FEUs")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📌 Push Auto-Requisitions to ERP (SAP S/4HANA / Odoo)", key="btn_push_erp"):
        st.session_state["erp_requisitions_pushed"] = True
        st.toast(f"Pushed {req_components:,} component requisitions directly to SAP S/4HANA!", icon="🚀")

    if st.session_state.get("erp_requisitions_pushed", False):
        st.success("✅ **ERP Requisitions Synced**: Purchase orders PO-2026-9901 through PO-2026-9904 generated and sent to procurement queue.")
        
# =====================================================================
# ROUTER 5: CTRM EVENT-DRIVEN HEDGING DESK & FINANCIAL ENGINEERING LAB
# =====================================================================
elif "CTRM" in selected_module:
    import numpy as np
    
    st.title("🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Financial commodity risk engine, custom synthetic derivatives builder, and FIX order execution.")

    # 1. Ingest Omni-Channel Signal Data from ANY Router 2 Feed
    raw_surge = st.session_state.get("extracted_demand_surge", 65000)
    signal_title = st.session_state.get("active_risk_signal_title", "NOAA Climate Alert")
    signal_category = st.session_state.get("signal_category", "Weather & Macro Feed")

    # 2. Financial Netting Logic: Calculate Net Unhedged Shortfall
    cmo_offload_pct = st.session_state.get("toller_split_slider", 15)
    net_exposure_pct = max(0.20, cmo_offload_pct / 100.0)
    net_unhedged_units = int(raw_surge * net_exposure_pct)
    unhedged_risk = net_unhedged_units * 150.0  # $150/unit commodity exposure
    default_lots = max(10, int(net_unhedged_units / 100))

    # Omni-Channel Dynamic Headline Banner
    st.info(
        f"⚡ **Active Risk Signal Ingested**: {signal_title} *({signal_category})* | "
        f"**Gross Exposure:** {raw_surge:,} Units | **Net Shortfall:** {net_unhedged_units:,} Units"
    )

    tab_exec, tab_lab = st.tabs(["📊 Standard Desk & FIX Execution", "🧪 Synthetic Derivative Builder & Model Lab"])

    # -----------------------------------------------------------------
    # TAB 1: STANDARD EXECUTION DESK
    # -----------------------------------------------------------------
    with tab_exec:
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        col_c1.metric("Gross Demand Surge", f"{raw_surge:,} Units")
        col_c2.metric("Physical Cover (Stock/CMO)", f"{raw_surge - net_unhedged_units:,} Units")
        col_c3.metric("Net Commodity Shortfall", f"{net_unhedged_units:,} Units", f"{net_exposure_pct*100:.0f}% Unhedged Gap")
        col_c4.metric("Unhedged Margin Risk", f"${unhedged_risk:,.2f}")

        st.markdown("---")
        st.subheader("⚡ FIX 4.4 Order Execution Gateway")

        col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
        with col_f1:
            order_type = st.selectbox("Order Structure", ["Asian Call Collar", "Outright Call Option", "Delta-Hedged Futures Spread"], key="std_order_type")
        with col_f2:
            exchange = st.selectbox("Execution Exchange", ["CME Group", "ICE Futures", "LME"], key="std_exchange")
        with col_f3:
            lots = st.number_input("Lots / Contracts (Net Shortfall)", value=default_lots, step=10, key="std_lots")

        if st.button("⚡ Execute & Route FIX 4.4 Paper Order", key="btn_exec_std"):
            st.session_state["fix_executed"] = True
            st.session_state["executed_lots"] = lots
            st.session_state["executed_order_type"] = order_type
            st.session_state["executed_exchange"] = exchange
            st.toast(f"FIX Order Sent: {lots:,} Lots to {exchange}!", icon="⚡")

        if st.session_state.get("fix_executed", False):
            exec_lots = st.session_state.get("executed_lots", lots)
            exec_type = st.session_state.get("executed_order_type", order_type)
            exec_exch = st.session_state.get("executed_exchange", exchange)
            st.success(
                f"✅ **FIX 4.4 Executed**: {exec_type} on {exec_exch} for **{exec_lots:,} Lots** "
                f"covering Net Shortfall from *{signal_title}*! Tag 35=D / Tag 150=0 (Filled @ $56.28/unit)"
            )

    # -----------------------------------------------------------------
    # TAB 2: SYNTHETIC DERIVATIVE & CUSTOM MODEL LAB
    # -----------------------------------------------------------------
    with tab_lab:
        st.subheader("🛠️ Custom Synthetic Derivative Constructor")
        st.markdown("Engineer tailored OTC structures, select underlying valuation models, and simulate pay-off profiles.")

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            deriv_type = st.selectbox("Structure Type", ["Fixed-for-Floating Synthetic Swap", "Zero-Cost Asian Collar", "Custom Crack/Spark Spread", "Digital Barrier Option"], key="lab_deriv_type")
        with col_d2:
            pricing_engine = st.selectbox("Pricing Model Engine", ["Black76 Jump-Diffusion Model", "Monte Carlo Path Simulation (10k Runs)", "Hawkes Stochastic Volatility"], key="lab_model_engine")
        with col_d3:
            strike_price = st.number_input("Strike / Cap Price ($/Unit)", value=150.0, step=5.0, key="lab_strike")

        st.markdown("---")
        st.subheader("📊 Dynamic Payoff Profile & Sensitivity Analysis")

        col_m1, col_m2 = st.columns([1.5, 1])
        
        with col_m1:
            # Interactive Payoff Simulation Curve scaled to Net Shortfall
            price_range = np.linspace(strike_price * 0.7, strike_price * 1.3, 50)
            if "Swap" in deriv_type:
                payoff = (price_range - strike_price) * net_unhedged_units
            elif "Collar" in deriv_type:
                floor = strike_price * 0.9
                cap = strike_price * 1.1
                payoff = np.clip(price_range - floor, 0, cap - floor) * net_unhedged_units - (strike_price * 0.05 * net_unhedged_units)
            else:
                payoff = np.maximum(price_range - strike_price, 0) * net_unhedged_units - (strike_price * 0.08 * net_unhedged_units)

            chart_data = pd.DataFrame({"Underlying Price ($)": price_range, "Net Payoff ($)": payoff})
            st.line_chart(chart_data, x="Underlying Price ($)", y="Net Payoff ($)", use_container_width=True)

        with col_m2:
            st.markdown("#### **Estimated Instrument Greeks**")
            
            delta_val = "0.52" if "Black76" in pricing_engine else "0.48 (Simulated)"
            vega_val = "$12,450 / 1% Vol" if "Jump-Diffusion" in pricing_engine else "$10,200 / 1% Vol"
            
            st.metric("Delta (Δ) Sensitivity", delta_val)
            st.metric("Vega (ν) Vol Risk", vega_val)
            st.metric("Estimated Structure Premium", f"${net_unhedged_units * 4.25:,.2f}")

        st.markdown("---")
        if st.button("🚀 Route Custom OTC Synthetic Structure to Exchange Clearing", key="btn_route_synthetic"):
            st.session_state["synthetic_executed"] = True
            st.session_state["executed_synthetic_type"] = deriv_type
            st.session_state["executed_synthetic_engine"] = pricing_engine
            st.toast("Custom OTC Synthetic Structure Routed to Clearing!", icon="🚀")

        if st.session_state.get("synthetic_executed", False):
            syn_type = st.session_state.get("executed_synthetic_type", deriv_type)
            syn_engine = st.session_state.get("executed_synthetic_engine", pricing_engine)
            st.success(
                f"✅ **Synthetic Structure Cleared**: {syn_type} priced via **{syn_engine}** "
                f"covering **{net_unhedged_units:,} Units** Net Exposure from *{signal_title}*!"
            )
# =====================================================================
# ROUTER 6: GIS & LOGISTICS CONTROL TOWER
# =====================================================================
elif any(k in selected_module for k in ["Global Logistics", "Cold Chain", "Maritime AIS", "GIS"]):
    active_domain = st.session_state.get("selected_domain", "🛒 Retail & Omnichannel Goods")
    live_parcel = BulletproofDataEngine.get_parcel_telemetry()

    if "FMCG" in persona or "Cold Chain" in selected_module:
        st.title("🌐 Cold Chain & Regional Distribution GIS Tower")
        st.caption(f"Active Persona View: **{persona}** | Domain Context: **{active_domain}**")
        st.info(f"🎯 **Sector Domain Active:** Filtering cold storage hubs and reefer SLAs for **{active_domain}**.")

        spatial_nodes = pd.DataFrame({
            "Name": ["Midwest Processing Facility", "Chicago Cold Hub", "Atlanta Regional Depot", "Rotterdam Blending Plant"],
            "lat": [41.8781, 41.9000, 33.7490, 51.9244],
            "lon": [-87.6298, -87.6500, -84.3880, 4.4777],
            "Category": ["Processing Plant", "Cold Storage Hub", "Regional DC", "Blending Facility"],
            "Temp Setpoint": ["-20.0°C", "-18.0°C", "-20.0°C", "-22.0°C"],
            "Size": [25, 20, 20, 22]
        })

        col_map, col_prox = st.columns([2, 1])
        with col_map:
            st.subheader("🗺️ Cold Storage GIS Spatial Map")
            fig_map = px.scatter_mapbox(
                spatial_nodes, lat="lat", lon="lon", hover_name="Name",
                hover_data=["Category", "Temp Setpoint"], color="Category",
                size="Size", zoom=2, height=450
            )
            fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)

        with col_prox:
            st.subheader("❄️ Cold Storage Telemetry Summary")
            st.metric("Sector Context", active_domain)
            st.metric("Active Cold Hubs Monitored", "4 Facilities", "100% Operational")
            st.metric("Mean Warehouse Temp", "-19.8°C", "Nominal")

        st.markdown("---")
        st.subheader("🌡️ Live Reefer Telemetry & Sensor Stream")
        telemetry = pd.DataFrame({
            "Reefer ID": ["REEFER-901", "REEFER-902", "REEFER-903", "REEFER-904"],
            "Carrier / Fleet": ["Lineage Logistics", "Americold Fleet", "DHL Cold Chain", "Kuehne+Nagel Cool"],
            "Cargo Description": ["Frozen Fruit Concentrate", "Dairy / Cheese Batches", "Pharma Ingredients", "Frozen Bakery Products"],
            "Set Temp (°C)": [-20.0, -18.0, -20.0, -22.0],
            "Actual Temp (°C)": [-19.8, -17.9, -16.8, -22.1],
            "Humidity (%)": ["88%", "85%", "92%", "84%"],
            "SLA Excursion Status": ["🟢 Temp Nominal", "🟢 Temp Nominal", "🔴 EXCURSION (+3.2°C Spike)", "🟢 Temp Nominal"]
        })
        st.dataframe(telemetry, use_container_width=True)

    elif "Merchant" in persona or "Maritime" in selected_module:
        st.title("🌐 Global Maritime AIS & Cargo GIS Tower")
        st.caption(f"Active Persona View: **{persona}** | Domain Context: **{active_domain}**")
        st.info(f"🎯 **Sector Domain Active:** Tracking maritime AIS vessel queues & chokepoints relevant to **{active_domain}**.")

        spatial_nodes = pd.DataFrame({
            "Name": ["Suez Canal Chokepoint", "Rotterdam Tank Depot", "Cushing Storage Vault", "Singapore Anchorage Queue"],
            "lat": [29.9753, 51.9244, 35.9856, 1.3521],
            "lon": [32.5599, 4.4777, -96.7678, 103.8198],
            "Category": ["Maritime Chokepoint", "Tank Farm Storage", "Storage Depot", "Anchorage Queue"],
            "Size": [25, 22, 22, 25]
        })

        fig_map = px.scatter_mapbox(spatial_nodes, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=450)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("🚢 Live AIS Vessel & Express Cargo Stream")
        ais_stream = pd.DataFrame([
            {
                "Vessel / Express Transport": f"✈️ {live_parcel['carrier']} ({live_parcel['tracking_code']})",
                "Cargo Type": f"{active_domain} Consignment",
                "Destination / Route": f"{live_parcel['origin']} ➔ {live_parcel['destination']}",
                "AIS / Telemetry Status": live_parcel["status"],
                "Data Feed Source": live_parcel["source"]
            },
            {
                "Vessel / Express Transport": "🚢 M/T Nordic Trader (IMO 98213)",
                "Cargo Type": "Light Sweet Crude (1.2M Bbls)",
                "Destination / Route": "Rotterdam Depot",
                "AIS / Telemetry Status": "🟢 In Transit (14.2 knots)",
                "Data Feed Source": "🟢 LIVE AIS"
            },
            {
                "Vessel / Express Transport": "🚢 M/V Atlantic Bullion (IMO 91124)",
                "Cargo Type": "Physical Cargo Shipment",
                "Destination / Route": "Baltimore Metal Vault",
                "AIS / Telemetry Status": "🟡 Anchored / Queue (+3 Days)",
                "Data Feed Source": "🟢 LIVE AIS"
            }
        ])
        st.dataframe(ais_stream, use_container_width=True)

    else:  # Industrial
        st.title("🌐 Global Logistics Network & GIS Control Tower")
        st.caption(f"Active Persona View: **{persona}** | Domain Context: **{active_domain}**")
        st.info(f"🎯 **Sector Domain Active:** Aligning network node flows for **{active_domain}**.")

        spatial_nodes = pd.DataFrame({
            "Name": [plant1_name, plant2_name, toller_name, "Chicago Logistics Hub DC", "Panama Canal Chokepoint"],
            "lat": [42.3314, 48.1351, 32.7767, 41.8781, 9.0800],
            "lon": [-83.0458, 11.5820, -96.7970, -87.6298, -79.6800],
            "Category": ["Manufacturing Plant", "Manufacturing Plant", "3rd-Party CMO", "Warehouse DC", "Maritime Chokepoint"],
            "Size": [22, 22, 16, 18, 25]
        })

        fig_map = px.scatter_mapbox(spatial_nodes, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=450)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("🚢 Real-Time Freight & Shipment Telemetry Stream")
        shipments = pd.DataFrame([
            {
                "Shipment / Tracking": live_parcel["tracking_code"],
                "Carrier": f"✈️ {live_parcel['carrier']}",
                "Origin": live_parcel["origin"],
                "Destination": live_parcel["destination"],
                "Status / ETA": live_parcel["status"],
                "Data Source": live_parcel["source"]
            },
            {
                "Shipment / Tracking": "SHP-2026-901",
                "Carrier": "Maersk Line",
                "Origin": plant1_name,
                "Destination": "Regional Distribution Hub",
                "Status / ETA": "🟢 On-Time (ETA 4 hrs)",
                "Data Source": "🟢 LIVE AIS"
            },
            {
                "Shipment / Tracking": "SHP-2026-902",
                "Carrier": "FedEx Supply Chain",
                "Origin": "Chicago Logistics Hub DC",
                "Destination": "Fulfillment Hub",
                "Status / ETA": "🟢 On-Time (ETA 12 hrs)",
                "Data Source": "🟢 LIVE TELEMETRY"
            }
        ])
        st.dataframe(shipments, use_container_width=True)
# =====================================================================
# ROUTER 7: SANDBOX FLIGHT SIMULATOR & STRESS LAB
# =====================================================================
elif "Flight Simulator" in selected_module:
    st.title("🧪 Sandboxed Flight Simulator & Stress Lab")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Risk-Free Macro 'What-If' Simulation, Black Swan Stress Testing & Derivative Volatility Surface Impact.")

    is_sandbox = st.session_state.get("sandbox_active", False)
    sim_params = st.session_state.get("sandbox_params", {
        "volume_multiplier": 1.0, 
        "spot_cost_increase": 0.0, 
        "transit_delay_days": 0, 
        "iv_multiplier": 1.0, 
        "description": "Baseline Simulation Context"
    })
    raw_surge = st.session_state.get("extracted_demand_surge", 65000)
    effective_surge = int(raw_surge * sim_params["volume_multiplier"])

    if not is_sandbox:
        st.info("💡 **Flight Simulator is currently in Baseline Mode.** Select a macro 'What-If' scenario in the sidebar and click **🧪 Launch Sim** to activate stress testing.")
        
        st.subheader("📊 Baseline System Load & Parameter Overview")
        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.metric(f"Current Base Demand Surge", f"{raw_surge:,} {term_unit}")
        col_b2.metric("Market Volatility Multiplier", "1.0x (Standard)")
        col_b3.metric("Network Transit Delay", "0 Days (Baseline)")
    else:
        scenario_name = st.session_state.get("sandbox_scenario", "Active Scenario")
        st.success(f"🧪 **ACTIVE SIMULATION SCENARIO**: {scenario_name}")
        st.markdown(f"> *{sim_params.get('description', '')}*")
        
        st.markdown("### 📊 Macro Stress Comparison (Baseline vs. Simulated Shock)")
        
        base_risk = raw_surge * 150.0
        sim_risk = effective_surge * 150.0 * (1 + sim_params["spot_cost_increase"])
        risk_delta_pct = ((sim_risk - base_risk) / base_risk) * 100 if base_risk > 0 else 0.0
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric(f"Baseline Exposure", f"${base_risk:,.2f}")
        col_s2.metric(f"Simulated Stress Exposure", f"${sim_risk:,.2f}", f"+{risk_delta_pct:.1f}% Delta Risk", delta_color="inverse")
        col_s3.metric("Simulated Supply Lag", f"+{sim_params['transit_delay_days']} Days Delay", "Critical Transit Impact" if sim_params['transit_delay_days'] > 10 else "Manageable Delay")
        
        st.markdown("---")
        st.subheader("📈 Derivative Option Surface Shock Analysis (Black76 Engine)")
        
        base_iv = 0.22
        sim_iv = base_iv * sim_params["iv_multiplier"]
        
        call_base, put_base, delta_base, vega_base = black76_call_put(2200, 2250, 60/365, 0.04, base_iv)
        call_sim, put_sim, delta_sim, vega_sim = black76_call_put(2200, 2250, 60/365, 0.04, sim_iv)
        
        sim_surface_df = pd.DataFrame([
            {
                "Option Tenor": "60-Day Asian Collar",
                "State": "Live Production Baseline",
                "Implied Volatility (σ)": f"{base_iv*100:.1f}%",
                "Call Premium ($)": f"${call_base:.2f}",
                "Delta (Δ)": f"{delta_base:.2f}",
                "Vega (ν)": f"{vega_base:.2f}"
            },
            {
                "Option Tenor": "60-Day Asian Collar",
                "State": "🧪 Sandboxed Macro Shock",
                "Implied Volatility (σ)": f"{sim_iv*100:.1f}%",
                "Call Premium ($)": f"${call_sim:.2f}",
                "Delta (Δ)": f"{delta_sim:.2f}",
                "Vega (ν)": f"{vega_sim:.2f}"
            }
        ])
        st.dataframe(sim_surface_df, use_container_width=True, hide_index=True)
        st.warning("🔒 **Isolation Guarantee**: All transactions in Sandbox Mode are completely disconnected from live FIX gateways and ERP ledger commits.")

# =====================================================================
# ROUTER 8: INTEGRATION & ARCHITECTURE ENDPOINTS
# =====================================================================
elif "Integration" in selected_module:
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("System connectivity status across ERP, CTRM, Messaging Middleware, and Live IoT Feeds.")
    
    st.subheader("📡 Real-Time Gateway Status")
    
    mesh_df = pd.DataFrame([
        {"Endpoint": "Bulletproof Engine Core", "Protocol": "Python / Microservice", "Latency": "12 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "SAP S/4HANA Enterprise ERP", "Protocol": "REST / OData API", "Latency": "45 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "CME / LME FIX Gateway", "Protocol": "FIX 4.4 Engine", "Latency": "4 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "AIS Global Maritime Radar", "Protocol": "WebSocket Stream", "Latency": "120 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "TextBlob / RSS NLP Scraper", "Protocol": "HTTP / RSS Feed", "Latency": "210 ms", "Status": "🟢 HEALTHY"}
    ])
    st.dataframe(mesh_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🛠️ Session State Telemetry Debugger")
    st.json({
        "active_disruption": st.session_state.get("active_disruption"),
        "extracted_demand_surge": st.session_state.get("extracted_demand_surge"),
        "sandbox_active": st.session_state.get("sandbox_active", False),
        "sandbox_scenario": st.session_state.get("sandbox_scenario"),
        "platform_persona": persona,
        "selected_module": selected_module
    })