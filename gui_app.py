import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import math
from scipy.stats import norm

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
# SIDEBAR: PERSONA SWITCHER & DYNAMIC MODULE NAVIGATION
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
        "🌐 Cold Chain & Regional Distribution GIS Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
    term_unit = "Cases / Batches"
    term_raw = "Agri Softs & Ingredients"
    plant1_name = "Midwest Processing Facility"
    plant2_name = "Rotterdam Blending Plant"
    toller_name = "Regional Co-Packer & Cold Storage"
else:  # Merchant Trading (Removed Load Balancer Module)
    module_options = [
        "📊 Daily Trading Balance Sheet & Position Tower",
        "🧠 Global Macro & Satellite Market Intelligence",
        "📈 Physical Off-Take & Merchant Storage Desk",
        "🛡️ CTRM Derivatives & Risk Arbitrage Desk",
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

# Helper function for NLP extraction
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

# Black76 / Black-Scholes Option Pricer Helper
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

# Dynamic Contracts Injector per Persona
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
# ROUTER 1: EXECUTIVE SOP / IBP CONTROL TOWER
# =====================================================================
if any(k in selected_module for k in ["Executive S&OP", "Integrated Business Planning", "IBP", "Daily Trading Balance Sheet"]):
    st.title("📊 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time financial alignment, financial waterfalls, and trade hedge benefit reconciliation.")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    unconstrained_val = 120.0 + (surge * 0.00025)
    trade_offset = 3.25
    cogs_drag = -12.4
    net_ebitda = round(120.0 + (surge * 0.00025) + cogs_drag + trade_offset, 2)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2%")
    col2.metric("Unconstrained Demand (AOP + Surge)", f"${unconstrained_val:.1f}M", f"+{surge:,} {term_unit}")
    col3.metric("CTRM Hedge & Trade Benefit", f"+${trade_offset:.2f}M", "Derivative Gain")
    col4.metric("Net Realized EBITDA", f"${net_ebitda:.2f}M", "+6.4%", delta_color="normal")
    
    st.markdown("---")
    st.subheader("📊 Executive Financial Waterfall (Volume-to-Value Bridge)")
    st.caption("Reconciling operational demand surge, toller premiums, and financial paper trade offsets into net realized margin.")
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="S&OP Bridge",
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "total"],
        x=["Base AOP Revenue", f"Trade Promo Surge (+{surge:,})", "Raw Material COGS Volatility", "CTRM Derivative Hedge Offset", "Net Realized EBITDA"],
        textposition="outside",
        text=[f"$120.0M", f"+${(surge * 0.00025):.2f}M", f"-${abs(cogs_drag):.2f}M", f"+${trade_offset:.2f}M", f"${net_ebitda:.2f}M"],
        y=[120.0, surge * 0.00025, cogs_drag, trade_offset, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#EF553B"}},
        increasing={"marker": {"color": "#00CC96"}},
        totals={"marker": {"color": "#636EFA"}}
    ))
    fig_waterfall.update_layout(title="Volume-to-Value S&OP Financial Bridge ($M)", showlegend=False, height=420)
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.subheader("📋 Executive Financial Audit Ledger & Variance Decomposition")
    rec_df = pd.DataFrame({
        "Financial Vector": ["Base Unconstrained Demand", f"NLP Demand Surge ({surge:,} {term_unit})", "Internal Plant COGS", f"3rd-Party Storage/Toller Premium ({toller_name})", "CTRM Derivative Offset / Hedge Gain"],
        "Physical Value ($M)": [120.0, round(surge * 0.00025, 2), -82.5, -12.4, 0.0],
        "Paper Derivative Offset ($M)": [0.0, 0.0, 0.0, 0.0, trade_offset],
        "Net S&OP Financial Impact ($M)": [120.0, round(surge * 0.00025, 2), -82.5, -12.4, trade_offset],
        "Audit Trail Reference": ["SAP-AOP-2026-Q3", "NLP-EML-2026-881", "MES-PLANT-LINE1", "PO-CMO-2026-904", "FIX-EXEC-ICE-4811"]
    })
    st.dataframe(rec_df, use_container_width=True)

# =====================================================================
# ROUTER 2: NLP COMMERCIAL SENSING
# =====================================================================
elif any(k in selected_module for k in ["NLP Commercial", "Global Macro"]):
    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Ingest unstructured signals from news feeds, social media, **post-trade show emails**, and **marketing promo debriefs**.")
    
    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web Signals", 
        "📧 Email & Event Debrief Parser", 
        "🌐 Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        st.subheader("📡 Live Web Signals & Sentiment Ingestion")
        signals = pd.DataFrame({
            "Source": ["Twitter / X", "Bloomberg News", "Custom Tariff Feed", "Supplier Portal"],
            "Signal Detected": ["Port Congestion Warning", "Red Sea Shipping Surcharge", "Rare Earth Export Restriction", "Semiconductor Lead Time Spike"],
            "Sentiment Score": [-0.85, -0.62, -0.91, -0.45],
            "Confidence": ["94%", "88%", "97%", "82%"]
        })
        st.dataframe(signals, use_container_width=True)

    with tab2:
        st.subheader("📧 Unstructured Email & Field Report Extractor")
        st.caption("Parse post-trade show debriefs and promotional feedback to capture early demand spikes before formal ERP entry.")
        
        email_preset = st.selectbox(
            "Select Email Sample or Enter Custom Text:",
            [
                "🎪 Post-Trade Show Sales Debrief (CES Expo 2026)",
                "🚀 Post-Promo Campaign Feedback (Q3 Flash Sale)",
                "✍️ Custom Email Input"
            ],
            key="email_preset_selector_v12"
        )
        
        if email_preset == "🎪 Post-Trade Show Sales Debrief (CES Expo 2026)":
            default_email = """From: vpsales@enterprise.com
Date: Aug 3, 2026
Subject: CES 2026 Recap - Massive Foot Traffic & Verbal Commitments

Team, post-CES debrief: We experienced overwhelming interest in our primary commodity line. 
Major retail distributors (Walmart, Target) gave verbal commitments for Q3/Q4. 
We estimate an unconstrained demand spike of ~85,000 additional units over baseline over the next 60 days. 
Supply chain needs to prep flex capacity ASAP!"""
        elif email_preset == "🚀 Post-Promo Campaign Feedback (Q3 Flash Sale)":
            default_email = """From: marketing.lead@enterprise.com
Date: Aug 2, 2026
Subject: Q3 Promo Performance - Stockout Warning!

Our regional summer promotion blew past expectations. Conversion rates are up 340%. 
Distributors in EMEA are requesting an emergency replenishment of roughly 120,000 units. 
Margin risks are high if we get hit with freight surcharges."""
        else:
            default_email = ""

        user_email = st.text_area("Email Content Body:", value=default_email, height=180, key="email_text_area_v12")
        
        if st.button("🧠 Extract NLP Demand Intent & Quantify Surge", type="primary", key="btn_parse_email_v12"):
            if user_email.strip():
                extracted_vol = parse_demand_from_text(user_email)
                sentiment = "POSITIVE (High Intent)" if ("overwhelming" in user_email.lower() or "blew past" in user_email.lower()) else "NEUTRAL"
                
                st.session_state["extracted_demand_surge"] = extracted_vol
                st.toast(f"Parsed {extracted_vol:,} {term_unit} from Email!", icon="📧")
                
                col_e1, col_e2, col_e3 = st.columns(3)
                col_e1.metric("Extracted Event Type", "Trade Show / Promo Signal")
                col_e2.metric("Extracted Demand Surge", f"{extracted_vol:,} {term_unit}")
                col_e3.metric("NLP Confidence & Sentiment", sentiment)
                
                st.success(f"✅ Propagated **{extracted_vol:,} {term_unit}** of demand surge directly to **Physical Procurement Desk**!")
            else:
                st.warning("Please paste email content first.")

    with tab3:
        st.subheader("🌐 Live Telemetry & Black Swan Feeds")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("### 🚢 FBX Freight Spot Rate Index")
            st.metric("FBX Global Container Freight Index", "$3,840 / FEU", "+14.2%")
            if st.button("📡 Stream Live FBX Rate Surge to Risk Injector", key="btn_fbx_stream_v12"):
                st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
                st.toast("Updated Risk Injector with Live FBX Freight Index!", icon="🚀")
                
        with col_t2:
            st.markdown("### 🌀 NOAA Maritime Weather Radar")
            st.metric("Pacific Water Anomaly Index", "+2.8°C", "El Niño Active")
            if st.button("📡 Stream NOAA Climate Signal to Risk Injector", key="btn_noaa_stream_v12"):
                st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
                st.toast("Updated Risk Injector with Live NOAA Weather Alert!", icon="🌊")

    st.markdown("---")
    st.subheader("🎯 Active Demand Shock Extractor Override")
    current_surge = st.session_state.get("extracted_demand_surge", 65000)
    demand_surge = st.slider(f"Extracted Surge Volume ({term_unit})", 10000, 200000, int(current_surge), step=5000, key="nlp_demand_surge_slider_v12")
    st.session_state["extracted_demand_surge"] = demand_surge

# =====================================================================
# ROUTER 3: DEMAND/SUPPLY MATCH & PLANT LOAD BALANCER (Industrial / FMCG Only)
# =====================================================================
elif any(k in selected_module for k in ["Demand/Supply", "Plant Load", "Batch Processing"]):
    st.title("⚖️ Demand/Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Linear programming optimization for global plant load balancing, make vs. buy arbitrage, and profit maximization.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Interactive Solver Optimization Parameters")
        base_price = st.number_input("Base Selling Price ($/unit)", value=250.0, key="ds_base_price_v12")
        flex_cost = st.number_input(f"3rd-Party Toller / CMO Cost ($/unit): {toller_name}", value=165.0, key="ds_flex_cost_v12")
        cmo_penalty = st.slider("CMO Expedited Surcharge / Penalty Rate (%)", 0, 50, 15, key="ds_cmo_penalty_slider_v12")
        unmet_penalty = st.number_input("Unmet Demand Penalty ($/unit)", value=80.0, key="ds_penalty_cost_v12")
        
    with col2:
        st.subheader("📊 Dynamic Optimal Allocation Summary")
        surge_vol = st.session_state.get("extracted_demand_surge", 65000)
        primary_cap = 450000
        effective_flex_cost = flex_cost * (1.0 + (cmo_penalty / 100.0))
        flex_alloc = min(surge_vol, 100000)
        unmet_units = max(0, surge_vol - flex_alloc)
        
        calc_profit = (primary_cap * (base_price - 110.0)) + (flex_alloc * (base_price - effective_flex_cost)) - (unmet_units * unmet_penalty)
        
        st.metric("Primary Internal Plant Capacity", f"{primary_cap:,} {term_unit}")
        st.metric(f"Flex Allocation to {toller_name}", f"{flex_alloc:,} {term_unit}", delta=f"Effective Cost: ${effective_flex_cost:.2f}/unit")
        st.metric("Maximized Gross Profit", f"${calc_profit/1e6:,.2f}M")

    st.markdown("---")
    st.subheader("🏭 Internal Manufacturing Plant Balancing vs. External Toller Arbitrage")
    
    plant_df = pd.DataFrame({
        "Production Facility / Source": [plant1_name, plant2_name, toller_name],
        "Facility Type": ["Internal Plant A", "Internal Plant B", "3rd-Party CMO / Toller"],
        "Max Capacity": [300000, 150000, 100000],
        "Allocated Volume": [300000, 150000, flex_alloc],
        "Unit Production Cost ($/unit)": [110.0, 125.0, effective_flex_cost],
        "Utilization Rate (%)": ["100.0%", "100.0%", f"{(flex_alloc/100000)*100:.1f}%"]
    })
    st.dataframe(plant_df, use_container_width=True)

    st.subheader(f"📦 Automated Raw Material Bill of Materials (BOM) Requisition Generator ({term_raw})")
    st.caption("Quantifies physical raw material inputs required for internal manufacturing and external tollers based on LP solver allocation.")
    
    req_metals = (primary_cap + flex_alloc) * 0.02
    req_semis = (primary_cap + flex_alloc) * 2.0
    req_freight = (primary_cap + flex_alloc) / 50.0
    
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Metals / Primary Commodity Required", f"{req_metals:,.0f} MT")
    col_b2.metric("Semiconductor / Component Units", f"{req_semis:,.0f} Units")
    col_b3.metric("Freight Capacity Needed", f"{req_freight:,.0f} Container FEUs")
    
    if st.button("📦 Generate & Push Requisitions to Physical Procurement Desk", type="primary", key="btn_push_req_v12"):
        st.session_state["bom_requisitions"] = {
            "metals_mt": req_metals,
            "semis_units": req_semis,
            "freight_feus": req_freight
        }
        st.toast("Successfully generated & pushed physical procurement requisitions!", icon="📦")

# =====================================================================
# ROUTER 4: PHYSICAL PROCUREMENT & CONTRACT DESK / OFF-TAKE
# =====================================================================
elif any(k in selected_module for k in ["Physical Procurement", "Agri-Ingredients", "Physical Off-Take", "Procurement"]):
    st.title("📈 Physical Procurement & Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Physical contract management, supplier allocation, and raw material requisitioning.")
    
    reqs = st.session_state.get("bom_requisitions", {"metals_mt": 10300, "freight_feus": 5150})
    st.info(f"📦 **Active BOM Requisitions Ingested from D/S Solver**: Requesting **{reqs.get('metals_mt', 10300):,.0f} MT** of raw materials/inputs and **{reqs.get('freight_feus', 5150):,.0f} FEUs** of maritime freight.")

    col_pr1, col_pr2 = st.columns([3, 1])
    with col_pr1:
        st.subheader("💼 Active Physical Procurement Contracts")
    with col_pr2:
        if st.button("🛡️ Execute Paper Hedge for BOM", type="primary", key="btn_proc_hedge_v12"):
            st.session_state["active_disruption"] = "Standard Market Price Volatility"
            st.toast("Routed BOM exposure to CTRM Engine for option pricing!", icon="🛡️")

    active_contracts = get_persona_contracts(persona)
    st.dataframe(pd.DataFrame(active_contracts), use_container_width=True)

    st.markdown("---")
    st.subheader("⚖️ Product Arbitrage Comparison Matrix: Internal Warehouse/Plants vs. 3rd-Party Suppliers")
    st.caption("Evaluates landed unit costs, stock availability, lead times, and automated draw/call-off recommendations.")
    
    col_arb1, col_arb2 = st.columns(2)
    with col_arb1:
        freight_tariff = st.number_input("Inbound Freight & Tariff Surcharge ($/unit)", value=45.0, key="arb_tariff_v12")
    with col_arb2:
        holding_cost = st.number_input("Internal Storage / Holding Cost ($/unit)", value=15.0, key="arb_holding_v12")

    if "Industrial" in persona:
        arb_data = [
            {
                "Commodity / Item": "Primary Aluminum Ingot",
                "Internal Warehouse Landed Cost": f"${2100.0 + holding_cost:.2f} / MT",
                "3rd-Party Spot Supplier Landed Cost": f"${2280.0 + freight_tariff:.2f} / MT",
                "Cost Spread ($/unit)": f"-${(2280.0 + freight_tariff) - (2100.0 + holding_cost):.2f} / MT",
                "Internal On-Hand Stock": "8,500 MT",
                "3rd-Party Spot Alloc.": "15,000 MT",
                "Lead Time (Internal vs Spot)": "1 Day vs 14 Days",
                "Automated Arbitrage Recommendation": "🟢 DRAW Internal Stockyard before 3rd-party call-off"
            },
            {
                "Commodity / Item": "Semiconductor Wafers 300mm",
                "Internal Warehouse Landed Cost": f"${480.0 + holding_cost:.2f} / Wafer",
                "3rd-Party Spot Supplier Landed Cost": f"${450.0 + freight_tariff:.2f} / Wafer",
                "Cost Spread ($/unit)": f"+${(450.0 + freight_tariff) - (480.0 + holding_cost):.2f} / Wafer",
                "Internal On-Hand Stock": "12,000 Wafers",
                "3rd-Party Spot Alloc.": "100,000 Wafers",
                "Lead Time (Internal vs Spot)": "2 Days vs 21 Days",
                "Automated Arbitrage Recommendation": "🟡 CALL-OFF Spot Allocation (Landed Arbitrage Favorable)"
            }
        ]
    elif "FMCG" in persona:
        arb_data = [
            {
                "Commodity / Item": "Raw Cocoa Beans (Grade A)",
                "Internal Warehouse Landed Cost": f"${3200.0 + holding_cost:.2f} / MT",
                "3rd-Party Spot Supplier Landed Cost": f"${3420.0 + freight_tariff:.2f} / MT",
                "Cost Spread ($/unit)": f"-${(3420.0 + freight_tariff) - (3200.0 + holding_cost):.2f} / MT",
                "Internal On-Hand Stock": "4,200 MT",
                "3rd-Party Spot Alloc.": "8,500 MT",
                "Lead Time (Internal vs Spot)": "1 Day vs 10 Days",
                "Automated Arbitrage Recommendation": "🟢 DRAW Internal Cold Silos (Save $205/MT)"
            },
            {
                "Commodity / Item": "Flexible Packaging Film",
                "Internal Warehouse Landed Cost": f"${19.50 + holding_cost:.2f} / Roll",
                "3rd-Party Spot Supplier Landed Cost": f"${18.50 + freight_tariff:.2f} / Roll",
                "Cost Spread ($/unit)": f"+${(18.50 + freight_tariff) - (19.50 + holding_cost):.2f} / Roll",
                "Internal On-Hand Stock": "50,000 Rolls",
                "3rd-Party Spot Alloc.": "450,000 Rolls",
                "Lead Time (Internal vs Spot)": "0.5 Days vs 5 Days",
                "Automated Arbitrage Recommendation": "🟡 CALL-OFF Spot Contract (Lower Landed Cost)"
            }
        ]
    else:  # Merchant
        arb_data = [
            {
                "Commodity / Item": "Physical Gold Bullion (Zurich)",
                "Internal Warehouse Landed Cost": f"${2350.0 + holding_cost:.2f} / Oz",
                "3rd-Party Spot Supplier Landed Cost": f"${2380.0 + freight_tariff:.2f} / Oz",
                "Cost Spread ($/unit)": f"-${(2380.0 + freight_tariff) - (2350.0 + holding_cost):.2f} / Oz",
                "Internal On-Hand Stock": "15,000 Oz",
                "3rd-Party Spot Alloc.": "50,000 Oz",
                "Lead Time (Internal vs Spot)": "Instant vs 3 Days",
                "Automated Arbitrage Recommendation": "🟢 RELEASE Internal Vault Stock"
            },
            {
                "Commodity / Item": "Light Sweet Crude (Cushing)",
                "Internal Warehouse Landed Cost": f"${78.20 + holding_cost:.2f} / Bbl",
                "3rd-Party Spot Supplier Landed Cost": f"${76.50 + freight_tariff:.2f} / Bbl",
                "Cost Spread ($/unit)": f"+${(76.50 + freight_tariff) - (78.20 + holding_cost):.2f} / Bbl",
                "Internal On-Hand Stock": "250,000 Bbls",
                "3rd-Party Spot Alloc.": "1,200,000 Bbls",
                "Lead Time (Internal vs Spot)": "1 Day vs 7 Days",
                "Automated Arbitrage Recommendation": "🟡 EXECUTE Contango Spot Call-Off"
            }
        ]
        
    st.dataframe(pd.DataFrame(arb_data), use_container_width=True)

# =====================================================================
# ROUTER 5: CTRM EVENT-DRIVEN HEDGING DESK
# =====================================================================
elif any(k in selected_module for k in ["CTRM", "Hedging", "Derivatives"]):
    st.title("🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Financial commodity risk engine, Hawkes jump-diffusion pricing models, and paper options execution.")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    active_label = st.session_state.get("active_disruption", "Standard Market Price Volatility")
    custom_params = st.session_state.get("custom_scenario_params")
    
    st.info(f"📡 **Active Risk Signal Ingested**: {active_label} | **Notional Surge Exposure**: {surge:,} {term_unit}")

    # Dynamic Pricing Header based on Custom Scenario
    if custom_params:
        S = 2200.0  # Spot base
        K = custom_params["strike"]
        T = custom_params["duration_days"] / 365.0
        r = custom_params["rate"]
        sigma = custom_params["iv"]
        
        c_price, p_price, delta_c, vega_c = black76_call_put(S, K, T, r, sigma)
        
        st.success(f"⚡ **Custom Option Priced Live**: Call Premium: **${c_price:.2f}** | Put Premium: **${p_price:.2f}** | Delta (Δ): **{delta_c:.2f}** | Vega (ν): **{vega_c:.2f}**")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Unhedged Margin Risk", f"${(surge * 150.0):,.2f}")
    col_b.metric("Pricing Engine", "Black76 Jump-Diffusion")
    col_c.metric("Notional Volume", f"{surge:,} {term_unit}")
    col_d.metric("Recommended Structure", "Asian Call Option Collar")

    st.markdown("---")
    st.subheader("📊 Black76 Option Volatility Surface Matrix & Greeks")
    st.caption("Pricing European and Asian options across strike prices, tenors, and implied volatility curves:")

    if custom_params:
        # Dynamically Render Surface around Custom Scenario Inputs
        S_spot = 2200.0
        r = custom_params["rate"]
        sigma = custom_params["iv"]
        
        surface_rows = []
        for days, label in [(30, "1 Month (30D)"), (60, "2 Months (60D)"), (90, "3 Months (90D)"), (180, "6 Months (180D)")]:
            T = days / 365.0
            K = custom_params["strike"]
            cp, pp, d_val, v_val = black76_call_put(S_spot, K, T, r, sigma)
            surface_rows.append({
                "Option Tenor": label,
                "Strike Price ($)": f"${K:,.0f}",
                "Call Premium ($)": f"${cp:.2f}",
                "Put Premium ($)": f"${pp:.2f}",
                "Implied Vol (σ)": f"{sigma*100:.1f}%",
                "Delta (Δ)": round(d_val, 2),
                "Vega (ν)": round(v_val, 2)
            })
        st.dataframe(pd.DataFrame(surface_rows), use_container_width=True)
    else:
        vol_surface = pd.DataFrame({
            "Option Tenor": ["1 Month (30D)", "2 Months (60D)", "3 Months (90D)", "6 Months (180D)"],
            "Strike Price ($)": ["$2,200 (ATM)", "$2,250 (OTM)", "$2,300 (OTM)", "$2,400 (DOTM)"],
            "Call Premium ($)": ["$42.50", "$38.20", "$31.10", "$22.40"],
            "Put Premium ($)": ["$41.10", "$49.50", "$58.00", "$74.20"],
            "Implied Vol (σ)": ["18.5%", "22.4%", "26.1%", "31.0%"],
            "Delta (Δ)": [0.52, 0.44, 0.38, 0.27],
            "Gamma (Γ)": [0.012, 0.010, 0.008, 0.005],
            "Vega (ν)": [14.2, 18.5, 22.1, 28.4]
        })
        st.dataframe(vol_surface, use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ FIX 4.4 Order Execution Gateway")
    col_f1, col_f2, col_f3 = st.columns(3)
    order_type = col_f1.selectbox("Order Type", ["Asian Call Collar", "Outright Call Option", "Put Option Hedge", "Futures Calendar Spread"])
    exchange = col_f2.selectbox("Execution Exchange", ["CME Group", "ICE Futures Europe", "London Metal Exchange (LME)"])
    lots = col_f3.number_input("Lots / Contracts", value=int(surge / 100))

    if st.button("⚡ Execute & Route FIX 4.4 Paper Order to Exchange", type="primary", key="btn_fix_exec_v12"):
        st.balloons()
        st.success(f"✅ FIX 4.4 Order Executed: {order_type} on **{exchange}** for **{lots:,} Lots**! Tag 35=D / Tag 150=0 (Filled @ $38.20/unit)")
        st.json({
            "FIX_Tag_35": "D (New Order Single)",
            "FIX_Tag_11_ClOrdID": f"ORD-CTRM-2026-{np.random.randint(1000, 9999)}",
            "FIX_Tag_55_Symbol": "AL-CME-2026Q3",
            "FIX_Tag_38_OrderQty": lots,
            "FIX_Tag_44_Price": 38.20,
            "FIX_Tag_150_ExecType": "0 (New/Filled)",
            "Hedge_Margin_Protected_USD": round(surge * 38.20, 2)
        })

# =====================================================================
# ROUTER 6: GIS & LOGISTICS CONTROL TOWER
# =====================================================================
elif any(k in selected_module for k in ["Global Logistics", "Cold Chain", "Maritime AIS", "GIS"]):
    if "FMCG" in persona or "Cold Chain" in selected_module:
        st.title("🌐 Cold Chain & Regional Distribution GIS Tower")
        st.caption(f"Active Persona View: **{persona}**")
        st.markdown("Geospatial tracking of cold storage hubs, refrigerated reefer fleets, and real-time SLA temperature excursion telemetry.")

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
            st.metric("Active Cold Hubs Monitored", "4 Facilities", "100% Operational")
            st.metric("Mean Warehouse Temp", "-19.8°C", "Nominal")
            st.metric("SLA Excursion Alerts", "0 Critical", "1 Warning (Atlanta)")

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
        st.caption(f"Active Persona View: **{persona}**")
        st.markdown("Geospatial tracking of oil tankers, dry bulk carriers, port queue bottlenecks, and global tank farm storage.")

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

        st.subheader("🚢 Live AIS Vessel & Cargo Telemetry Stream")
        ais_stream = pd.DataFrame({
            "Vessel Name / IMO": ["M/T Nordic Trader (IMO 98213)", "M/V Atlantic Bullion (IMO 91124)", "M/T Pacific Energy (IMO 94511)"],
            "Cargo Type": ["Light Sweet Crude (1.2M Bbls)", "Physical Rare Earths (25,000 MT)", "LNG Liquefied Gas (170k m³)"],
            "Destination Port": ["Rotterdam Depot", "Baltimore Metal Vault", "Tokyo Gas Terminal"],
            "AIS Status": ["🟢 In Transit (14.2 knots)", "🟡 Anchored / Queue (+3 Days)", "🟢 In Transit (16.0 knots)"],
            "Contango Arbitrage Status": ["In the Money (+$1.80/Bbl)", "Spread Secured", "In the Money"]
        })
        st.dataframe(ais_stream, use_container_width=True)

    else:  # Industrial
        st.title("🌐 Global Logistics Network & GIS Control Tower")
        st.caption(f"Active Persona View: **{persona}**")
        st.markdown("Geospatial tracking of plants, regional DCs, customer proximity, and live freight telematic streams.")

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
        shipments = pd.DataFrame({
            "Shipment ID": ["SHP-2026-901", "SHP-2026-902", "SHP-2026-903"],
            "Carrier": ["Maersk Line", "FedEx Supply Chain", "Hapag-Lloyd"],
            "Origin": [plant1_name, "Chicago Logistics Hub DC", plant2_name],
            "Destination": ["Walmart Bentonville Hub", "Target Midwest Depot", "Frankfurt Regional DC"],
            "Cargo Ingested": ["45,000 Cases", "22,000 Units", "15,000 MT Metals"],
            "Status / ETA": ["🟢 On-Time (ETA 4 hrs)", "🟢 On-Time (ETA 12 hrs)", "🟡 Congested (ETA +1 Day)"]
        })
        st.dataframe(shipments, use_container_width=True)

# =====================================================================
# ROUTER 7: INTEGRATION & ARCHITECTURE ENDPOINTS
# =====================================================================
elif any(k in selected_module for k in ["Integration"]):
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption("Live system integration waypoints, REST/GraphQL endpoints, and enterprise API connections.")
    
    col_ep1, col_ep2 = st.columns(2)
    with col_ep1:
        st.subheader("📡 Active Enterprise Integration Waypoints")
        endpoints_data = [
            {"Tab / Module": "Executive S&OP", "Protocol": "REST / OData", "Endpoint URL": "/api/v1/sop/financial-waterfall", "Target System": "SAP S/4HANA / Anaplan", "Status": "🟢 ACTIVE 200 OK"},
            {"Tab / Module": "NLP Sensing", "Protocol": "Webhook / RSS", "Endpoint URL": "/api/v1/nlp/ingest-email-signal", "Target System": "Microsoft Exchange / LLM Engine", "Status": "🟢 ACTIVE 200 OK"},
            {"Tab / Module": "Physical Procurement", "Protocol": "REST / EDI 850", "Endpoint URL": "/api/v1/procurement/po-bridge", "Target System": "SAP Ariba / Oracle SCM", "Status": "🟢 ACTIVE 200 OK"},
            {"Tab / Module": "CTRM Hedging Desk", "Protocol": "FIX 4.4 / REST", "Endpoint URL": "/api/v1/ctrm/fix-order-execution", "Target System": "CME Group / ICE / LME Gateway", "Status": "🟢 ACTIVE 200 OK"},
            {"Tab / Module": "GIS Logistics Tower", "Protocol": "WebSocket / REST", "Endpoint URL": "/api/v1/gis/project44-telemetry", "Target System": "Project44 / FourKites Telematics", "Status": "🟢 ACTIVE 200 OK"}
        ]
        st.dataframe(pd.DataFrame(endpoints_data), use_container_width=True)

    with col_ep2:
        st.subheader("🧪 Interactive Endpoint Tester & Payload Inspection")
        selected_endpoint = st.selectbox(
            "Select Integration Waypoint to Test:",
            ["/api/v1/sop/financial-waterfall", "/api/v1/nlp/ingest-email-signal", "/api/v1/procurement/po-bridge", "/api/v1/ctrm/fix-order-execution", "/api/v1/gis/project44-telemetry"],
            key="select_ep_test_v12"
        )
        if st.button("⚡ Test Endpoint Ping", type="primary", key="btn_test_ep_v12"):
            st.toast(f"Ping successful for {selected_endpoint}!", icon="⚡")
            sample_payloads = {
                "/api/v1/sop/financial-waterfall": {"status": 200, "base_aop_usd": 120000000, "hedge_gain_usd": 3250000, "net_ebitda_usd": 127100000},
                "/api/v1/nlp/ingest-email-signal": {"status": 200, "parsed_units": 85000, "confidence": 0.94, "event": "Trade Show Signal"},
                "/api/v1/procurement/po-bridge": {"status": 200, "po_number": "PO-2026-9921", "vendor": "Rio Tinto", "status": "APPROVED"},
                "/api/v1/ctrm/fix-order-execution": {"status": 200, "order_id": "ORD-CTRM-2026-8831", "exchange": "ICE", "exec_price": 38.20},
                "/api/v1/gis/project44-telemetry": {"status": 200, "container_id": "REEFER-901", "temp_celsius": -19.8, "gps": [41.87, -87.62]}
            }
            st.json(sample_payloads[selected_endpoint])

# =====================================================================
# GLOBAL SIDEBAR: RISK SCENARIO INJECTOR & CUSTOM PRICER BUILDER
# =====================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("🌋 Risk Scenario Injector")
st.sidebar.caption("⚡ Auto-Ingest Telemetry Alerts:")

col_nlp1, col_nlp2 = st.sidebar.columns(2)
if col_nlp1.button("🌋 Iceland Ash", use_container_width=True, key="ctrm_ash_v12"):
    st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
    st.session_state["custom_scenario_params"] = None
    st.toast("Ingested: Volcanic Ash Cloud Alert!", icon="🌋")

if col_nlp2.button("🌊 El Niño AIS", use_container_width=True, key="ctrm_elnino_v12"):
    st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
    st.session_state["custom_scenario_params"] = None
    st.toast("Ingested: Sea surface anomaly confirmed!", icon="🌊")

disruption_options = [
    "Standard Market Price Volatility",
    "El Niño Climate Shock (Pacific Ocean Warm Current)",
    "Icelandic Volcanic Ash (North Atlantic Freight Corridor)",
    "Seismic Earthquake Shock (Port Facilities Damage)",
    "Port Union Flash Strike (Zero Cargo Discharge)",
    "Panama Canal Drought Bottleneck"
]

current_selection = st.session_state.get("active_disruption", "Standard Market Price Volatility")
default_idx = disruption_options.index(current_selection) if current_selection in disruption_options else 0

selected_event_label = st.sidebar.selectbox(
    "Select Supply Chain Shock:",
    options=disruption_options,
    index=default_idx,
    key="ctrm_shock_select_v12"
)

if st.sidebar.button("🚨 Inject Selected Shock to Platform", type="primary", use_container_width=True, key="ctrm_inject_v12"):
    st.session_state["active_disruption"] = selected_event_label
    st.session_state["custom_scenario_params"] = None
    st.sidebar.success(f"Injected: {selected_event_label}")

# ---------------------------------------------------------------------
# CUSTOM SCENARIO INJECTION BUILDER & OPTION PRICER
# ---------------------------------------------------------------------
with st.sidebar.expander("🛠️ Custom Scenario & Option Pricer", expanded=False):
    st.caption("Inject user-defined shocks with dynamic derivative option pricing:")
    c_name = st.text_input("Scenario Name", "Red Sea Geopolitical Surge", key="c_name_v12")
    c_surge = st.number_input(f"Surge Impact Volume ({term_unit})", value=75000, step=5000, key="c_surge_v12")
    c_strike = st.number_input("Option Strike Price ($)", value=2250.0, step=25.0, key="c_strike_v12")
    c_iv = st.slider("Implied Volatility (σ %)", 10, 150, 35, key="c_iv_v12")
    c_rate = st.number_input("Risk-Free Rate (r %)", value=4.5, step=0.25, key="c_rate_v12")
    c_days = st.slider("Option Duration (Days)", 7, 365, 60, key="c_days_v12")

    if st.button("🚀 Inject Custom Scenario & Price Derivative", type="primary", use_container_width=True, key="btn_custom_inject_v12"):
        st.session_state["active_disruption"] = f"Custom Shock: {c_name}"
        st.session_state["extracted_demand_surge"] = c_surge
        st.session_state["custom_scenario_params"] = {
            "name": c_name,
            "surge": c_surge,
            "strike": c_strike,
            "iv": c_iv / 100.0,
            "rate": c_rate / 100.0,
            "duration_days": c_days
        }
        st.toast(f"Custom Scenario '{c_name}' Injected & Priced!", icon="🚀")

active_label = st.session_state["active_disruption"]
st.sidebar.info(f"📡 **Active Signal Ingested:** {active_label}")
