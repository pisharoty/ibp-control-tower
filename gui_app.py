import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "custom_scenarios" not in st.session_state:
    st.session_state["custom_scenarios"] = {}
if "extracted_demand_surge" not in st.session_state:
    st.session_state["extracted_demand_surge"] = 65000
if "physical_contracts" not in st.session_state:
    st.session_state["physical_contracts"] = [
        {"Contract ID": "CTR-2026-A1", "Commodity": "Primary Aluminum / Heavy Metals", "Supplier": "Rio Tinto", "Volume": "15,000 MT", "Fixed Price": "$2,200 / MT", "Status": "Active"},
        {"Contract ID": "CTR-2026-B4", "Commodity": "Freight Futures (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "Status": "Under Review"},
        {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor Wafers / Components", "Supplier": "TSMC", "Volume": "100,000 Wafers", "Fixed Price": "$450 / Wafer", "Status": "Executing"}
    ]
if "ctrm_ledger" not in st.session_state:
    st.session_state["ctrm_ledger"] = []

st.set_page_config(page_title="IBP Enterprise Control Tower", layout="wide")

# Imports for CTRM Extension
try:
    from ctrm_engine import CTRMExtensionEngine, DSSolverOutput, RiskEventType
    CTRM_AVAILABLE = True
except ImportError:
    CTRM_AVAILABLE = False

# =====================================================================
# SIDEBAR: PERSONA SWITCHER & MODULE NAVIGATION
# =====================================================================
st.sidebar.title("⚡ IBP Control Tower")

persona = st.sidebar.selectbox(
    "🏢 Enterprise Platform Persona",
    [
        "🏭 Discrete & Heavy Industrial Enterprise",
        "📦 Process Goods & FMCG Enterprise",
        "📈 Merchant Trading & Commodity Risk Desk"
    ],
    key="platform_persona_v7"
)

selected_module = st.sidebar.radio(
    "Select Operational Module",
    [
        "📊 Executive S&OP Control Tower",
        "🧠 NLP Commercial Sensing & Email Intelligence",
        "⚖️ Demand/Supply Match & Plant Load Balancer",
        "📈 Physical Procurement & Contract Desk",
        "🛡️ CTRM Event-Driven Hedging Desk",
        "🌐 Global Logistics Network & GIS Control Tower"
    ],
    key="nav_module_selection_v7"
)

st.session_state["selected_module"] = selected_module

# Contextual Terminology Mapping based on Persona
if "Industrial" in persona:
    term_unit = "Units"
    term_raw = "Raw Metals & Components"
    plant1_name = "Detroit Main Assembly Plant"
    plant2_name = "Munich Component Line"
    toller_name = "3rd-Party Contract Manufacturer (CMO)"
elif "FMCG" in persona:
    term_unit = "Cases / Batches"
    term_raw = "Agri Softs & Ingredients"
    plant1_name = "Midwest Processing Facility"
    plant2_name = "Rotterdam Blending Plant"
    toller_name = "Regional Co-Packer & Cold Storage"
else:  # Merchant Trading
    term_unit = "Lots / Contracts"
    term_raw = "Physical Deliverable Cargoes"
    plant1_name = "Primary Import Terminal A"
    plant2_name = "Regional Hub Terminal B"
    toller_name = "3rd-Party Merchant Storage Arbitrage"

# =====================================================================
# MODULE 1: EXECUTIVE S&OP CONTROL TOWER
# =====================================================================
if "Executive S&OP" in selected_module:
    st.title("📊 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time financial alignment, demand-supply balance, and integrated operational KPIs.")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    unconstrained_val = 120.0 + (surge * 0.00025)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2%")
    col2.metric("Unconstrained Demand (AOP + NLP Surge)", f"${unconstrained_val:.1f}M", f"+{surge:,} {term_unit}")
    col3.metric("Constrained Supply Plan", "$118.2M", "-1.5%")
    col4.metric("Net Margin Gap", "$17.3M", "-2.1%", delta_color="inverse")
    
    st.markdown("---")
    st.subheader("📈 Integrated S&OP Financial Alignment Gap")
    df_sop = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "AOP Target": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        "Unconstrained Demand": [10.5, 11, 11.2, 11.8, 12, 12.5, 11.9, 11.5 + (surge/50000), 11.2, 11, 10.8, 10.1],
        "Constrained Supply": [9.8, 9.9, 10.0, 10.1, 9.7, 9.8, 9.9, 10.0, 9.8, 9.9, 9.7, 9.6]
    })
    fig_sop = px.line(df_sop, x="Month", y=["AOP Target", "Unconstrained Demand", "Constrained Supply"],
                      title="12-Month S&OP Demand vs. Supply vs. AOP ($M)")
    st.plotly_chart(fig_sop, use_container_width=True)

    st.subheader("📋 Physical & Paper Financial Reconciliation")
    st.markdown(f"Reconciling physical production load balancing across **{plant1_name}**, **{plant2_name}**, and paper CTRM hedges.")
    
    rec_df = pd.DataFrame({
        "Financial Vector": ["Base Unconstrained Demand", f"NLP Demand Surge ({surge:,} {term_unit})", "Internal Plant COGS", "3rd-Party Toller Premium", "CTRM Hedge Gains / Offsets"],
        "Physical Value ($M)": [120.0, surge * 0.00025, -82.5, -12.4, 0.0],
        "Paper Derivative Offset ($M)": [0.0, 0.0, 0.0, 0.0, 3.25],
        "Net S&OP Impact ($M)": [120.0, surge * 0.00025, -82.5, -12.4, 3.25]
    })
    st.dataframe(rec_df, use_container_width=True)

# =====================================================================
# MODULE 2: NLP COMMERCIAL SENSING & EMAIL INTELLIGENCE
# =====================================================================
elif "NLP Commercial" in selected_module:
    st.title("🧠 NLP Commercial Sensing & Email Intelligence")
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
            key="email_preset_selector_v7"
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

        user_email = st.text_area("Email Content Body:", value=default_email, height=180, key="email_text_area_v7")
        
        if st.button("🧠 Extract NLP Demand Intent & Quantify Surge", type="primary", key="btn_parse_email_v7"):
            if user_email.strip():
                numbers = re.findall(r'(\d+[\d,]*)\s*units', user_email, re.IGNORECASE)
                extracted_vol = int(numbers[0].replace(',', '')) if numbers else 65000
                sentiment = "POSITIVE (High Intent)" if "overwhelming" in user_email.lower() or "blew past" in user_email.lower() else "NEUTRAL"
                
                st.session_state["extracted_demand_surge"] = extracted_vol
                st.toast(f"Parsed {extracted_vol:,} {term_unit} from Email!", icon="📧")
                
                col_e1, col_e2, col_e3 = st.columns(3)
                col_e1.metric("Extracted Event Type", "Trade Show / Promo Signal")
                col_e2.metric("Extracted Demand Surge", f"{extracted_vol:,} {term_unit}")
                col_e3.metric("NLP Confidence & Sentiment", sentiment)
                
                st.success(f"✅ Propagated **{extracted_vol:,} {term_unit}** of demand surge directly to **D/S Match Solver** and **Physical Procurement Desk**!")
            else:
                st.warning("Please paste email content first.")

    with tab3:
        st.subheader("🌐 Live Telemetry & Black Swan Feeds")
        st.caption("Direct telemetry hooks that trigger real-time updates across the platform.")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("### 🚢 FBX Freight Spot Rate Index")
            st.metric("FBX Global Container Freight Index", "$3,840 / FEU", "+14.2%")
            if st.button("📡 Stream Live FBX Rate Surge to Risk Injector", key="btn_fbx_stream_v7"):
                st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
                st.toast("Updated Risk Injector with Live FBX Freight Index!", icon="🚀")
                
        with col_t2:
            st.markdown("### 🌀 NOAA Maritime Weather Radar")
            st.metric("Pacific Water Anomaly Index", "+2.8°C", "El Niño Active")
            if st.button("📡 Stream NOAA Climate Signal to Risk Injector", key="btn_noaa_stream_v7"):
                st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
                st.toast("Updated Risk Injector with Live NOAA Weather Alert!", icon="🌊")

    st.markdown("---")
    st.subheader("🎯 Active Demand Shock Extractor Override")
    current_surge = st.session_state.get("extracted_demand_surge", 65000)
    demand_surge = st.slider(f"Extracted Surge Volume ({term_unit})", 10000, 200000, int(current_surge), step=5000, key="nlp_demand_surge_slider_v7")
    st.session_state["extracted_demand_surge"] = demand_surge

# =====================================================================
# MODULE 3: DEMAND/SUPPLY MATCH & PLANT LOAD BALANCER
# =====================================================================
elif "D/S Match" in selected_module:
    st.title("⚖️ Demand/Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Linear programming optimization for global plant load balancing, make vs. buy arbitrage, and profit maximization.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Solver Inputs & Cost Parameters")
        base_price = st.number_input("Base Selling Price ($/unit)", value=250.0, key="ds_base_price_v7")
        flex_cost = st.number_input("3rd-Party Toller / CMO Cost ($/unit)", value=165.0, key="ds_flex_cost_v7")
        penalty_cost = st.number_input("Unmet Demand Penalty ($/unit)", value=80.0, key="ds_penalty_cost_v7")
        
    with col2:
        st.subheader("📊 Dynamic Optimal Allocation Summary")
        surge_vol = st.session_state.get("extracted_demand_surge", 65000)
        primary_cap = 450000
        flex_alloc = min(surge_vol, 100000)
        unmet_units = max(0, surge_vol - flex_alloc)
        
        calc_profit = (primary_cap * (base_price - 110.0)) + (flex_alloc * (base_price - flex_cost)) - (unmet_units * penalty_cost)
        
        st.metric("Primary Internal Plant Capacity", f"{primary_cap:,} {term_unit}")
        st.metric(f"Flex Allocation to {toller_name}", f"{flex_alloc:,} {term_unit}", delta=f"Surge: {surge_vol:,} {term_unit}")
        st.metric("Maximized Gross Profit", f"${calc_profit/1e6:,.2f}M")

    st.markdown("---")
    st.subheader("🏭 Internal Manufacturing Plant Balancing vs. External Toller Arbitrage")
    
    plant_df = pd.DataFrame({
        "Production Facility / Source": [plant1_name, plant2_name, toller_name],
        "Facility Type": ["Internal Plant A", "Internal Plant B", "3rd-Party CMO / Toller"],
        "Max Capacity": [300000, 150000, 100000],
        "Allocated Volume": [300000, 150000, flex_alloc],
        "Unit Cost ($/unit)": [110.0, 125.0, flex_cost],
        "Utilization Rate (%)": ["100%", "100%", f"{(flex_alloc/100000)*100:.1f}%"]
    })
    st.dataframe(plant_df, use_container_width=True)

    st.subheader(f"📦 Raw Material Bill of Materials (BOM) Generator ({term_raw})")
    st.caption("Quantifies physical raw material inputs required for internal manufacturing and external tollers.")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Metals / Primary Commodity Required", f"{(primary_cap + flex_alloc) * 0.02:,.0f} MT")
    col_b2.metric("Semiconductor / Component Units", f"{(primary_cap + flex_alloc) * 2.0:,.0f} Units")
    col_b3.metric("Freight Capacity Needed", f"{(primary_cap + flex_alloc) / 50:,.0f} Container FEUs")
    
    if st.button("📦 Push Requisitions to Physical Procurement Desk", type="primary", key="btn_push_req_v7"):
        st.toast("Successfully generated physical procurement requisitions!", icon="📦")

# =====================================================================
# MODULE 4: PHYSICAL PROCUREMENT & CONTRACT DESK
# =====================================================================
elif "Procurement" in selected_module:
    st.title("📈 Physical Procurement & Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Physical contract management, supplier allocation, and raw material requisitioning.")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    st.info(f"📦 **Active BOM Requisitions Ingested from D/S Solver**: Requesting **{(450000 + surge) * 0.02:,.0f} MT** of raw metals/inputs and **{(450000 + surge) / 50:,.0f} FEUs** of maritime freight.")

    st.subheader("💼 Active Physical Procurement Contracts")
    df_contracts = pd.DataFrame(st.session_state["physical_contracts"])
    st.dataframe(df_contracts, use_container_width=True)

    st.markdown("---")
    st.subheader("✍️ Book New Physical Procurement Contract")
    with st.form("new_physical_contract_form_v7"):
        col_c1, col_c2, col_c3 = st.columns(3)
        c_id = col_c1.text_input("Contract ID", f"CTR-2026-D{len(st.session_state['physical_contracts'])+1}")
        c_comm = col_c2.text_input("Commodity / Input", "Primary Aluminum / Copper Rods")
        c_supp = col_c3.text_input("Physical Supplier", "BHP / Rio Tinto")
        
        col_c4, col_c5, col_c6 = st.columns(3)
        c_vol = col_c4.text_input("Contract Volume", "25,000 MT")
        c_price = col_c5.text_input("Fixed Unit Price", "$2,150 / MT")
        c_status = col_c6.selectbox("Contract Status", ["Executing", "Active", "Under Review"])
        
        submit_contract = st.form_submit_button("📝 Register Physical Contract", type="primary")
        if submit_contract:
            st.session_state["physical_contracts"].append({
                "Contract ID": c_id, "Commodity": c_comm, "Supplier": c_supp,
                "Volume": c_vol, "Fixed Price": c_price, "Status": c_status
            })
            st.toast(f"Registered Contract {c_id}!", icon="📝")

    st.subheader("📜 Executed Physical Deal Register")
    st.caption("Flows committed physical purchasing spend directly into the Executive S&OP Financial Waterfall.")
    st.dataframe(pd.DataFrame(st.session_state["physical_contracts"]), use_container_width=True)

# =====================================================================
# MODULE 5: CTRM EVENT-DRIVEN HEDGING DESK (ISOLATED CLEAN MODULE)
# =====================================================================
elif "CTRM Event-Driven" in selected_module:
    st.title("🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Financial commodity risk engine, Hawkes jump-diffusion pricing models, and paper options execution.")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    active_label = st.session_state.get("active_disruption", "Standard Market Price Volatility")
    
    st.info(f"📡 **Active Risk Signal Ingested**: {active_label} | **Notional Surge Exposure**: {surge:,} {term_unit}")
    
    if CTRM_AVAILABLE:
        shock_matrix = {
            "El Niño Climate Shock (Pacific Ocean Warm Current)": {"commodity": "ICE Arabica Coffee & Softs", "event": RiskEventType.CLIMATE_SHOCK_EL_NINO, "p_base": 22.50, "p_spot": 28.40, "vol": 0.32},
            "Icelandic Volcanic Ash (North Atlantic Freight Corridor)": {"commodity": "CME Freight Futures (FBX Air/Sea)", "event": RiskEventType.VOLCANIC_ASH_DISRUPTION, "p_base": 85.00, "p_spot": 135.00, "vol": 0.55},
            "Seismic Earthquake Shock (Port Facilities Damage)": {"commodity": "Semiconductor Wafers & Rare Metals", "event": RiskEventType.SEISMIC_EARTHQUAKE_SHOCK, "p_base": 450.00, "p_spot": 720.00, "vol": 0.65},
            "Standard Market Price Volatility": {"commodity": "LME Primary Aluminum", "event": RiskEventType.STANDARD_VOLATILITY, "p_base": 2200.00, "p_spot": 2350.00, "vol": 0.18}
        }
        
        s_info = shock_matrix.get(active_label, shock_matrix["Standard Market Price Volatility"])
        
        ds_run = DSSolverOutput(
            scenario_name=active_label,
            commodity_name=s_info["commodity"],
            incremental_gross_profit=7137631.0,
            flex_capacity_cost=930194.0,
            volume_shortfall_units=float(surge),
            baseline_price=s_info["p_base"],
            spot_price=s_info["p_spot"],
            implied_volatility=s_info["vol"],
            risk_event_type=s_info["event"],
            network_throughput_ratio=0.30
        )
        
        ctrm_bridge = CTRMExtensionEngine()
        arbitrage_info = ctrm_bridge.detect_arbitrage_risk(ds_run)
        staged_ticket = ctrm_bridge.select_model_and_structure_hedge(ds_run)
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Unhedged Margin Risk", f"${arbitrage_info['unhedged_margin_risk_usd']:,.2f}")
        col_b.metric("Pricing Engine", staged_ticket.selected_model.value.replace("_", " "))
        col_c.metric("Notional Volume", f"{staged_ticket.notional_volume:,.0f} {term_unit}")
        col_d.metric("Option Premium", f"${staged_ticket.estimated_premium:,.2f}")
        
        st.success(f"💡 **Recommendation**: Activate **{staged_ticket.selected_model.value}** to cap price volatility at **${staged_ticket.strike_price:.2f}/unit**.")
        
        if st.button("⚡ Approve & Execute CTRM Option Trade", type="primary", key="btn_exec_ctrm_v7"):
            approved_ticket = ctrm_bridge.approve_hedge_order(staged_ticket)
            results = ctrm_bridge.execute_and_close_loop(ds_run, approved_ticket, market_price_at_expiry=s_info["p_spot"] * 1.1)
            
            st.session_state["ctrm_ledger"].append(results)
            st.balloons()
            st.success(f"Trade **{approved_ticket.order_id}** EXECUTED on Exchange for **{s_info['commodity']}**!")
            
            st.subheader("📊 Closed-Loop Financial Waterfall Output")
            st.json(results["financial_waterfall"])
    else:
        st.warning("CTRM Engine extension module loading...")

# =====================================================================
# MODULE 6: GLOBAL LOGISTICS NETWORK & GIS CONTROL TOWER
# =====================================================================
elif "Global Logistics" in selected_module:
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Geospatial tracking of plants, maritime choke points, and black swan disruption zones.")
    
    nodes = pd.DataFrame({
        "Name": [plant1_name, plant2_name, toller_name, "Port of Rotterdam", "Port of Shanghai", "Panama Canal Node", "Suez Canal Corridor"],
        "lat": [42.3314, 48.1351, 32.7767, 51.9244, 31.2304, 9.0800, 30.5852],
        "lon": [-83.0458, 11.5820, -96.7970, 4.4777, 121.4737, -79.6800, 32.3132],
        "Node Type": ["Internal Plant A", "Internal Plant B", "3rd-Party CMO", "Port", "Port", "Maritime Bottleneck", "War Risk Zone"],
        "Status": ["Operational (100%)", "Operational (100%)", "Flex Active", "Congested", "Operational", "Drought Hazard", "High Risk"],
        "Size": [20, 20, 15, 12, 12, 25, 25]
    })
    
    fig_map = px.scatter_mapbox(
        nodes,
        lat="lat",
        lon="lon",
        hover_name="Name",
        hover_data=["Node Type", "Status"],
        color="Status",
        size="Size",
        color_discrete_map={"Operational (100%)": "green", "Flex Active": "blue", "Congested": "orange", "High Risk": "red", "Drought Hazard": "purple"},
        zoom=1,
        height=550
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# =====================================================================
# GLOBAL SIDEBAR: RISK SCENARIO INJECTOR
# =====================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("🌋 Risk Scenario Injector")
st.sidebar.caption("⚡ Auto-Ingest Telemetry Alerts:")

col_nlp1, col_nlp2 = st.sidebar.columns(2)
if col_nlp1.button("🌋 Iceland Ash", use_container_width=True, key="ctrm_ash_v7"):
    st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
    st.toast("Ingested: Volcanic Ash Cloud Alert!", icon="🌋")

if col_nlp2.button("🌊 El Niño AIS", use_container_width=True, key="ctrm_elnino_v7"):
    st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
    st.toast("Ingested: Sea surface anomaly confirmed!", icon="🌊")

col_nlp3, col_nlp4 = st.sidebar.columns(2)
if col_nlp3.button("💥 Seismic Feed", use_container_width=True, key="ctrm_seismic_v7"):
    st.session_state["active_disruption"] = "Seismic Earthquake Shock (Port Facilities Damage)"
    st.toast("Ingested: Port Infrastructure Impaired!", icon="💥")

if col_nlp4.button("🪧 Flash Strike", use_container_width=True, key="ctrm_strike_v7"):
    st.session_state["active_disruption"] = "Port Union Flash Strike (Zero Cargo Discharge)"
    st.toast("Ingested: Union Strike Active!", icon="🪧")

with st.sidebar.expander("🎨 Custom Disruption Builder (CME/ICE)"):
    with st.form("custom_disruption_form_v7"):
        c_name = st.text_input("Disruption Title", "Panama Canal Drought Bottleneck")
        c_comm = st.text_input("Target Commodity", "CME Freight Futures (FBX)")
        c_base = st.number_input("Base Price ($)", value=120.0)
        c_spot = st.number_input("Spot Price ($)", value=195.0)
        submit_custom = st.form_submit_button("🚀 Inject Custom Scenario", type="primary")
        if submit_custom:
            st.session_state["active_disruption"] = c_name
            st.toast(f"Custom Scenario Injected: {c_name}!", icon="🎯")

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
    key="ctrm_shock_select_v7"
)

if st.sidebar.button("🚨 Inject Selected Shock to Platform", type="primary", use_container_width=True, key="ctrm_inject_v7"):
    st.session_state["active_disruption"] = selected_event_label
    st.sidebar.success(f"Injected: {selected_event_label}")

active_label = st.session_state["active_disruption"]
st.sidebar.info(f"📡 **Active Signal Ingested:** {active_label}")
