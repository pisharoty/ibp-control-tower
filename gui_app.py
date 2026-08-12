import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import math
import requests
import xml.etree.ElementTree as ET
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
# SCREEN RENDER FUNCTIONS (PASTE HERE!)
# =====================================================================

def render_flight_simulator(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
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
        col_b1.metric("Current Base Demand Surge", f"{raw_surge:,} {term_unit}")
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
        col_s1.metric("Baseline Exposure", f"${base_risk:,.2f}")
        col_s2.metric("Simulated Stress Exposure", f"${sim_risk:,.2f}", f"+{risk_delta_pct:.1f}% Delta Risk", delta_color="inverse")
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


def render_integration_architecture(persona="Discrete & Heavy Industrial Enterprise", selected_module=""):
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
        "demand_plan_committed": st.session_state.get("demand_plan_committed", False),
        "committed_horizon_demand": st.session_state.get("committed_horizon_demand"),
        "fix_executed": st.session_state.get("fix_executed", False),
        "sandbox_active": st.session_state.get("sandbox_active", False),
        "sandbox_scenario": st.session_state.get("sandbox_scenario"),
        "platform_persona": persona,
        "selected_module": selected_module
    })


def render_nlp_intelligence(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🧠 NLP Commercial Sensing & Intelligence")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Ingest unstructured signals from news feeds, social media, post-trade show emails, and GIS weather/freight telemetry.")

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web Signals", 
        "📧 Email & Event Debrief Parser", 
        "🌐 Freight, Weather & Black Swan Feeds"
    ])

    # -----------------------------------------------------------------
    # TAB 1: LIVE WEB SIGNALS & AI NEWS SCRAPER
    # -----------------------------------------------------------------
    with tab1:
        st.subheader("📡 Real-Time Web & Macro News Stream")
        st.markdown("Scrape and parse live geopolitical, commodity, and industry news using AI domain indexing.")

        NEWS_DOMAINS = {
            "⚡ Essential Semiconductors & High-Tech Hardware": [
                "TSMC Packaging Bottleneck Delays Advanced ASIC Deliveries [Impact: 175,000 Units]",
                "Asahi Kasei Resin Shortage Hits Chip Substrate Supply Chain [Impact: 110,000 Units]",
                "Critical Neon Gas Export Restrictions Target European Fabs [Impact: 140,000 Units]"
            ],
            "🛢️ Energy, Power & Petrochemicals": [
                "European Natural Gas Spike (+32%) Triggers Smelter Surcharge [Impact: 85,000 Units]",
                "Gulf Coast Refinery Outage Restricts Polymer Feedstock [Impact: 95,000 Units]",
                "Crude Oil Benchmark Breaches $95/bbl Increasing Freight Matrix [Impact: 50,000 Units]"
            ],
            "🍊 Agricultural Commodities & Cold-Chain (Orange Juice, Crop)": [
                "Brazil & Florida Citrus Greening Deficit Drives Concentrated OJ Spikes [Impact: 120,000 Units]",
                "Midwest Cold-Storage Trucking Freeze Disrupts Produce Routes [Impact: 45,000 Units]",
                "Panama Canal Auction Rates Hit $3M for Refrigerated Transit Slots [Impact: 70,000 Units]"
            ],
            "🚢 Maritime Freight, Ports & Logistics": [
                "Red Sea Vessel Diversions Drive +45% FBX Container Index Surge [Impact: 130,000 Units]",
                "US East Coast Port Labor Negotiations Risk Q4 Stocking [Impact: 210,000 Units]",
                "Singapore Transshipment Dwell Time Peaks at 4.8 Days [Impact: 80,000 Units]"
            ]
        }

        FEED_ENDPOINTS = {
            "Bloomberg Terminal RSS Feed (Macro & Commodities)": "https://feeds.bloomberg.com/markets/news.rss",
            "Reuters Supply Chain & Commodities Monitor": "https://www.reutersagency.com/feed/?best-topics=commodities&post_type=best",
            "Freightos Baltic Index (FBX) Real-Time Alert": "https://www.shippingwatch.com/rss",
            "Custom Web Scraper Pipeline (NLP Crawler)": ""
        }

        col_w1, col_w2 = st.columns([2, 1])
        
        with col_w1:
            web_feed_source = st.selectbox(
                "Select Live Data Feed Provider:",
                list(FEED_ENDPOINTS.keys()),
                key="nlp_web_feed_source"
            )

            selected_domain = st.selectbox(
                "Select Commodity / Industry Sector Focus:",
                list(NEWS_DOMAINS.keys()),
                key="nlp_sector_focus"
            )

            fallback_list = NEWS_DOMAINS[selected_domain]
            feed_url = FEED_ENDPOINTS.get(web_feed_source, "")
            active_headlines, is_live = fetch_live_or_fallback(feed_url, fallback_list, timeout_sec=1.2)

            if is_live:
                st.caption("🟢 **Status:** Connected to Live RSS API Gateway (Latency: < 1.2s)")
            else:
                st.caption("🛡️ **Status:** High-Speed Enterprise Synthetic Fallback Active")

            selected_headline = st.selectbox(
                "Select AI-Scraped Headline Signal:",
                active_headlines,
                key="nlp_web_headline_select"
            )

            search_query = st.text_input(
                "🔍 Live AI Scraper Keyword Filter (Optional):", 
                value=selected_domain.split(" ")[1] if " " in selected_domain else "Commodity Risk",
                key="nlp_search_query_input"
            )

        with col_w2:
            match = re.search(r'\[Impact:\s*([\d,]+)\s*Units\]', selected_headline)
            extracted_default = int(match.group(1).replace(',', '')) if match else 85000

            web_impact = st.number_input(
                f"Extracted Signal Impact ({term_unit})", 
                value=extracted_default, 
                step=5000, 
                key="web_signal_units"
            )

        if st.button("📡 Ingest Scraped Domain News Signal", key="btn_ingest_web"):
            headline_clean = selected_headline.split("[")[0].strip()
            domain_label = selected_domain.split(" ")[1] if len(selected_domain.split(" ")) > 1 else "Macro"
            
            st.session_state["extracted_demand_surge"] = web_impact
            st.session_state["active_risk_signal_title"] = f"[{domain_label}] {headline_clean}"
            st.session_state["signal_category"] = f"Live Web ({'Live Stream' if is_live else 'Cached Fallback'})"
            st.toast(f"Ingested '{headline_clean}' ({web_impact:,} {term_unit})", icon="📡")
            st.success(f"✅ Propagated **[{domain_label}] {headline_clean}** ({web_impact:,} {term_unit}) across S&OP and CTRM Desk!")

    # -----------------------------------------------------------------
    # TAB 2: EMAIL & EVENT DEBRIEF PARSER
    # -----------------------------------------------------------------
    with tab2:
        st.subheader("📧 Unstructured Email & Sales Debrief Parser")
        st.markdown("Extract commercial surge signals from raw unstructured rep text or custom communications.")

        input_mode = st.radio(
            "Select Debrief Input Mode:",
            ["📋 Select Preset Communication", "✍️ Paste Custom Email / Debrief"],
            horizontal=True,
            key="email_input_mode"
        )

        if input_mode == "📋 Select Preset Communication":
            email_selection = st.selectbox(
                "Select Ingested Field Communication / Debrief:",
                [
                    f"Trade Show / Sales Debrief (CES Expo 2026) - 250,000 {term_unit} Uplift",
                    f"Q3 Distributor Stocking Order Email - 150,000 {term_unit} Uplift",
                    f"OEM Emergency Spares Requisition - 75,000 {term_unit} Uplift"
                ],
                key="email_debrief_select"
            )

            default_email_val = 250000
            if "Distributor" in email_selection:
                default_email_val = 150000
            elif "OEM" in email_selection:
                default_email_val = 75000

            email_text_preview = f"Parsed from inbox: Rep indicates major commercial surge following {email_selection}. Demand spike expected to hit W38."
            email_title_parsed = email_selection.split("-")[0].strip()

        else:
            custom_email_text = st.text_area(
                "Paste Unstructured Email / Sales Rep Notes:",
                value=f"From: regional_sales_vp@enterprise.com\nSubject: URGENT: Q3 Automotive OEM Order Expansion\n\nTeam, following our executive review, Key Customer Apex Motors is requesting an immediate supply ramp of 180,000 additional {term_unit.lower()} for Q3 to cover their assembly line expansion in W38.",
                height=140,
                key="custom_email_text_area"
            )
            
            units_found = re.findall(r'([\d,]+)\s*(?:additional\s*)?(?:units|cases|batches|lots|contracts)?', custom_email_text, re.IGNORECASE)
            extracted_custom_val = int(units_found[0].replace(',', '')) if units_found and units_found[0].replace(',', '').isdigit() else 180000

            default_email_val = extracted_custom_val
            email_text_preview = custom_email_text
            email_title_parsed = "Custom Rep Email Signal"

        col_e1, col_e2 = st.columns([2, 1])
        with col_e1:
            st.text_area(
                "Parsed Raw Text Preview:",
                value=email_text_preview,
                height=100,
                disabled=True,
                key="email_preview_disabled"
            )
        with col_e2:
            email_impact = st.number_input(
                f"Parsed Demand Surge Impact ({term_unit})", 
                value=default_email_val, 
                step=10000, 
                key="email_units"
            )

        if st.button("📧 Parse & Ingest Selected Email Debrief", key="btn_ingest_email"):
            st.session_state["extracted_demand_surge"] = email_impact
            st.session_state["active_risk_signal_title"] = f"Email Debrief: {email_title_parsed}"
            st.session_state["signal_category"] = "Field Sales Debrief"
            st.toast(f"Parsed {email_title_parsed} ({email_impact:,} {term_unit})", icon="📧")
            st.success(f"✅ Propagated **{email_title_parsed}** ({email_impact:,} {term_unit}) directly to S&OP Horizon & CTRM Desk!")

    # -----------------------------------------------------------------
    # TAB 3: FREIGHT, WEATHER & BLACK SWAN FEEDS
    # -----------------------------------------------------------------
    with tab3:
        st.subheader("⛈️ Climate, Weather & Black Swan Risk Feeds")
        st.markdown("Ingest NOAA alerts, GIS spatial telemetry, and macro disruption feeds to price commodity and supply chain tail-risk.")

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            weather_alert = st.selectbox(
                "Select NOAA / GIS Telemetry Alert:",
                [
                    "NOAA Category 4 Gulf Coast Hurricane Warning (Houston Port Closure) [Impact: 120,000 Units]",
                    "Panama Canal Drought & Slot Auction Spike [Impact: 60,000 Units]",
                    "Midwest Inland Rail Freeze & Bottleneck [Impact: 25,000 Units]"
                ],
                key="nlp_weather_alert_select"
            )

        with col_b2:
            default_weather_val = 120000
            if "Panama" in weather_alert:
                default_weather_val = 60000
            elif "Midwest" in weather_alert:
                default_weather_val = 25000

            weather_impact = st.number_input(
                f"Climate Risk Deficit Impact ({term_unit})", 
                value=default_weather_val, 
                step=5000, 
                key="weather_signal_units"
            )

        if st.button("⛈️ Activate Black Swan Climate Risk Feed", key="btn_ingest_weather"):
            alert_title = weather_alert.split("[")[0].strip()
            st.session_state["extracted_demand_surge"] = weather_impact
            st.session_state["active_risk_signal_title"] = f"GIS/NOAA Alert: {alert_title}"
            st.session_state["signal_category"] = "Climate & GIS Telemetry"
            st.toast(f"Activated {alert_title} ({weather_impact:,} {term_unit})", icon="⛈️")
            st.success(f"✅ Propagated **{alert_title}** ({weather_impact:,} {term_unit}) directly to S&OP Workbench & CTRM Desk!")


def render_physical_procurement(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", term_raw="Raw Material"):
    st.title("📄 Physical Procurement & Master Contract Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Active enterprise supplier commitments, physical off-take agreements, and volume requisitions.")

    # Ingest GIS Control Tower Lead-Time Offset
    rop_offset_active = st.session_state.get("rop_offset_executed", False)
    delay_days = st.session_state.get("active_leadtime_delay_days", 4.2 if rop_offset_active else 0.0)

    # Dynamic GIS Alert Banner
    if rop_offset_active:
        st.warning(
            f"⚡ **Dynamic Lead-Time Offset Active (from GIS Control Tower):** "
            f"Carrier delays added **+{delay_days:.1f} Days** to active transit corridors. "
            f"Purchase Order release triggers have automatically shifted from **Day T-4.0** to **Day T-{(4.0 + delay_days):.1f}**."
        )
    else:
        st.info("ℹ️ **Standard MRP Mode:** Lead times running on static baseline vendor contracts.")

    # Physical Contract Table
    st.subheader("📋 Active Physical Supply Contracts")
    contracts_data = get_persona_contracts(persona)
    contracts_df = pd.DataFrame(contracts_data)

    if not contracts_df.empty and rop_offset_active:
        contracts_df["GIS Transit Delay"] = f"+{delay_days:.1f} Days"
        contracts_df["Adjusted ROP Trigger"] = f"Day T-{(4.0 + delay_days):.1f} ⚠️"

    st.dataframe(contracts_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # BOM Auto-Requisition Engine
    st.subheader("📦 Bill of Materials (BOM) Auto-Requisition Engine")

    is_committed = st.session_state.get("demand_plan_committed", False)
    active_demand = st.session_state.get(
        "committed_horizon_demand" if is_committed else "calculated_horizon_demand", 
        846049
    )

    if is_committed:
        st.success(f"⚡ **Live S&OP Sync Active**: Displaying requisitions for committed Demand Plan of **{active_demand:,} {term_unit}**.")
    else:
        st.info(f"ℹ️ **Baseline S&OP Forecast**: Displaying uncommitted requisitions for **{active_demand:,} {term_unit}** (Commit in Router 3 to finalize ERP purchase orders).")

    req_metals_mt = int(active_demand * 0.015)
    req_components = int(active_demand * 1.50)
    req_freight_feus = int(active_demand / 144.28)

    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric(f"Required {term_raw}", f"{req_metals_mt:,} MT")
    col_b2.metric("Component Requisitions", f"{req_components:,} Units")
    col_b3.metric("Freight Slots Reserved", f"{req_freight_feus:,} FEUs")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📌 Push Auto-Requisitions to ERP (SAP S/4HANA / Odoo)", key="btn_push_erp", type="primary"):
        st.session_state["erp_requisitions_pushed"] = True
        st.toast(f"Pushed {req_components:,} component requisitions directly to SAP S/4HANA!", icon="🚀")

    if st.session_state.get("erp_requisitions_pushed", False):
        if rop_offset_active:
            st.success(
                f"✅ **ERP Requisitions Synced with +{delay_days:.1f} Day Lead-Time Offset**: "
                f"Purchase orders PO-2026-9901 through PO-2026-9904 generated and sent to procurement queue "
                f"with recalculated release windows (Day T-{(4.0 + delay_days):.1f})."
            )
        else:
            st.success("✅ **ERP Requisitions Synced**: Purchase orders PO-2026-9901 through PO-2026-9904 generated and sent to procurement queue.")


def render_ctrm_desk(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Financial commodity risk engine, custom synthetic derivatives builder, and FIX order execution.")

    raw_surge = st.session_state.get("extracted_demand_surge", 65000)
    signal_title = st.session_state.get("active_risk_signal_title", "NOAA Climate Alert")
    signal_category = st.session_state.get("signal_category", "Weather & Macro Feed")

    cmo_offload_pct = st.session_state.get("toller_split_slider", 15)
    net_exposure_pct = max(0.20, cmo_offload_pct / 100.0)
    net_unhedged_units = int(raw_surge * net_exposure_pct)
    unhedged_risk = net_unhedged_units * 150.0
    default_lots = max(10, int(net_unhedged_units / 100))

    st.info(
        f"⚡ **Active Risk Signal Ingested**: {signal_title} *({signal_category})* | "
        f"**Gross Exposure:** {raw_surge:,} {term_unit} | **Net Shortfall:** {net_unhedged_units:,} {term_unit}"
    )

    tab_exec, tab_lab = st.tabs(["📊 Standard Desk & FIX Execution", "🧪 Synthetic Derivative Builder & Model Lab"])

    # -----------------------------------------------------------------
    # TAB 1: STANDARD EXECUTION DESK
    # -----------------------------------------------------------------
    with tab_exec:
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        col_c1.metric(f"Gross Demand Surge", f"{raw_surge:,} {term_unit}")
        col_c2.metric(f"Physical Cover (Stock/CMO)", f"{raw_surge - net_unhedged_units:,} {term_unit}")
        col_c3.metric(f"Net Commodity Shortfall", f"{net_unhedged_units:,} {term_unit}", f"{net_exposure_pct*100:.0f}% Unhedged Gap")
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
            st.session_state["fix_order_executed"] = True
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
                f"covering Net Shortfall from *{signal_title}*! Tag 35=D / Tag 150=0 (Filled @ $56.28/{term_unit[:-1] if term_unit.endswith('s') else term_unit})"
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
                f"covering **{net_unhedged_units:,} {term_unit}** Net Exposure from *{signal_title}*!"
            )


def render_executive_sop(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("📊 Executive S&OP Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time financial alignment, financial waterfalls, and trade hedge benefit reconciliation.")

    # 1. STATE INGESTION & DYNAMIC FINANCIAL AUDIT
    baseline_volume = 781049
    is_committed = st.session_state.get("demand_plan_committed", False)
    active_demand = st.session_state.get(
        "committed_horizon_demand" if is_committed else "extracted_demand_surge", 
        65000
    ) + baseline_volume
    
    surge_units = max(0, active_demand - baseline_volume)
    
    # Financial Inputs ($ Millions) - FIXED DIVISOR (/ 1_000_000)
    base_aop_revenue = 120.00
    surge_revenue_upside = round((surge_units * 249.23) / 1_000_000, 2)  # Yields +$16.20M (NOT $16,199M)
    unconstrained_demand_rev = base_aop_revenue + surge_revenue_upside
    
    # Check procurement sync state from Procurement / GIS Desks
    pos_synced = st.session_state.get("procurement_pos_synced", False) or st.session_state.get("rop_offset_executed", False)
    delay_days = st.session_state.get("active_leadtime_delay_days", 4.2)
    
    # Dynamic Freight Drag & Hedging Benefit
    base_freight_drag = 3.20 + (delay_days * 0.15 if st.session_state.get("sandbox_active", False) else 0.0)
    total_freight_drag = round(base_freight_drag * 0.6 if pos_synced else base_freight_drag, 2)
    ctrm_gain = 3.25
    net_ebitda = round(unconstrained_demand_rev + ctrm_gain - total_freight_drag - 10.0, 2)

    # 2. EXECUTIVE METRICS CARDS
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Annual Operating Plan (AOP)", f"${base_aop_revenue:.1f}M", "+4.2% YoY")
    col_m2.metric("Unconstrained Demand (AOP + Surge)", f"${unconstrained_demand_rev:.2f}M", f"+{surge_units:,} {term_unit}")
    col_m3.metric("CTRM Hedge & Trade Benefit", f"+${ctrm_gain:.2f}M", "⚡ Active Execution" if pos_synced else "⚡ Pending Sync")
    col_m4.metric("Net Realized EBITDA", f"${net_ebitda:.2f}M", f"+${round(net_ebitda - base_aop_revenue, 2)}M vs AOP")

    st.markdown("---")
    
    # 3. LIVE DESK CROSS-TALK FEEDS
    st.subheader("📡 Live Operational Desk Feeds")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    col_f1.info(f"🔵 **NLP Commercial Sensing**: Auto-hooked signal (+{surge_units:,} {term_unit}).")
    col_f2.warning(f"🟡 **CTRM Desk**: ${ctrm_gain:.2f}M hedge gain locked in.")
    col_f3.error("🔴 **Demand/Supply Balancer**: Plant operating near capacity limits.")
    
    if pos_synced:
        col_f4.success(f"🟢 **Procurement Desk**: POs Synced (+{delay_days:.1f}d Lead-Time Offset Active).")
    else:
        col_f4.info("ℹ️ **Procurement Desk**: Standard MRP baseline active.")

    st.markdown("---")

    # 4. P&L WATERFALL & CTRM LEDGER TABLES
    col_w1, col_w2 = st.columns([1.2, 1])
    
    with col_w1:
        st.subheader("💵 Financial P&L Margin Waterfall Report")
        waterfall_data = [
            {"P&L Line Item": "1. Base AOP Revenue Target", "Amount ($)": f"${base_aop_revenue:.2f}M", "Impact": "🔴 Baseline Plan"},
            {"P&L Line Item": "2. Unconstrained Surge Realization", "Amount ($)": f"+${surge_revenue_upside:.2f}M", "Impact": "🟢 Commercial Upside"},
            {"P&L Line Item": "3. CTRM Derivative & Hedge Gain", "Amount ($)": f"+${ctrm_gain:.2f}M", "Impact": "🟡 Market Execution"},
            {"P&L Line Item": "4. COGS & Freight Cost Drag", "Amount ($)": f"-${total_freight_drag:.2f}M", "Impact": "🟢 Mitigated" if pos_synced else "⚠️ Expedited Drag"},
            {"P&L Line Item": "5. Projected Net EBITDA", "Amount ($)": f"${net_ebitda:.2f}M", "Impact": "🟢 Net Bottom-Line"}
        ]
        st.dataframe(pd.DataFrame(waterfall_data), use_container_width=True, hide_index=True)

    with col_w2:
        st.subheader("📈 CTRM Commodity Hedging Ledger")
        
        # Dynamic ledger status based on procurement ERP sync
        ledger_data = [
            {
                "Commodity": "Raw Metals & Components", 
                "Hedge Position": "100% Synced 🟢" if pos_synced else "85% Hedged", 
                "Locked Rate": "$2,210 / MT", 
                "Spot Exposure": "0% Covered" if pos_synced else "15% Unhedged ⚠️"
            },
            {
                "Commodity": "Freight Futures (FEU)", 
                "Hedge Position": "100% Synced 🟢" if pos_synced else "80% Hedged", 
                "Locked Rate": "$3,450 / FEU", 
                "Spot Exposure": "0% Covered" if pos_synced else "20% Unhedged ⚠️"
            },
            {
                "Commodity": "Power & Energy", 
                "Hedge Position": "100% Covered", 
                "Locked Rate": "$64.50 / MWh", 
                "Spot Exposure": "0% Covered"
            }
        ]
        st.dataframe(pd.DataFrame(ledger_data), use_container_width=True, hide_index=True)

# =====================================================================
# HELPER FUNCTIONS — CARRIER TELEMETRY & FALLBACK ENGINE
# =====================================================================

def get_persona_config(persona: str) -> dict:
    """Returns persona-specific terminology, facility names, and module mappings."""
    if "Industrial" in persona:
        return {
            "module_options": [
                "📊 Executive S&OP Control Tower",
                "🧠 NLP Commercial Sensing & Field Intelligence",
                "⚖️ Demand/Supply Match & Plant Load Balancer",
                "📈 Physical Procurement & Contract Desk",
                "🛡️ CTRM Event-Driven Hedging Desk",
                "🧪 Sandbox Flight Simulator & Stress Lab",
                "🌐 Global Logistics Network & GIS Control Tower",
                "🔌 Integration & Architecture Endpoints"
            ],
            "term_unit": "Units",
            "term_raw": "Raw Metals & Components",
            "plant1_name": "Detroit Main Assembly Plant",
            "plant2_name": "Munich Component Line",
            "toller_name": "3rd-Party Contract Manufacturer (CMO)"
        }
    elif "FMCG" in persona:
        return {
            "module_options": [
                "📊 Integrated Business Planning (IBP) Tower",
                "🧠 NLP Commercial Sensing & Retail Intelligence",
                "⚖️ Batch Processing & Co-Packer Load Balancer",
                "📈 Agri-Ingredients & Direct Procurement",
                "🛡️ CTRM Softs & Commodity Risk Desk",
                "🧪 Sandbox Flight Simulator & Stress Lab",
                "🌐 Cold Chain & Regional Distribution GIS Tower",
                "🔌 Integration & Architecture Endpoints"
            ],
            "term_unit": "Cases / Batches",
            "term_raw": "Agri Softs & Ingredients",
            "plant1_name": "Midwest Processing Facility",
            "plant2_name": "Rotterdam Blending Plant",
            "toller_name": "Regional Co-Packer & Cold Storage"
        }
    else:  # Merchant Trading
        return {
            "module_options": [
                "📊 Daily Trading Balance Sheet & Position Tower",
                "🧠 Global Macro & Satellite Market Intelligence",
                "📈 Physical Off-Take & Merchant Storage Desk",
                "🛡️ CTRM Derivatives & Risk Arbitrage Desk",
                "🧪 Sandbox Flight Simulator & Stress Lab",
                "🌐 Global Maritime AIS & Cargo GIS Tower",
                "🔌 Integration & Architecture Endpoints"
            ],
            "term_unit": "Lots / Contracts",
            "term_raw": "Physical Deliverable Cargoes",
            "plant1_name": "Primary Import Terminal A",
            "plant2_name": "Regional Hub Terminal B",
            "toller_name": "3rd-Party Merchant Storage Arbitrage"
        }


def render_sidebar_navigation() -> tuple[str, str, dict]:
    """Renders the sidebar controls and returns active persona, selected module, and config."""
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

    # Fetch dynamic terminology and navigation tree
    config = get_persona_config(persona)

    selected_module = st.sidebar.radio(
        "Select Operational Module",
        config["module_options"],
        key="nav_module_selection_v12"
    )

    st.session_state["selected_module"] = selected_module
    return persona, selected_module, config


def fetch_carrier_telemetry_with_fallback():
    """
    Attempts to ingest live carrier API telemetry (DHL, FedEx, UPS, AIS).
    Falls back gracefully to canned telemetry data if feeds are unreachable.
    """
    canned_telemetry = {
        "is_live": False,
        "primary_alert": "HIGH (Gulf Ports)",
        "dwell_delay_days": 4.2,
        "feed_status": "OFFLINE (Using Canned Telemetry)",
        "telemetry_rows": [
            {"Carrier Feed": "DHL Express (Air)", "Active Corridor": "Frankfurt → Detroit", "Base Lead-Time": "2 Days", "Live Delay": "0.0 Days", "Adjusted ROP Trigger": "Day T-2"},
            {"Carrier Feed": "FedEx Freight (Road)", "Active Corridor": "Houston → Detroit", "Base Lead-Time": "4 Days", "Live Delay": "+4.2 Days (Gulf Surge)", "Adjusted ROP Trigger": "Day T-8.2 ⚠️"},
            {"Carrier Feed": "UPS SCS (Rail)", "Active Corridor": "Rotterdam → Munich", "Base Lead-Time": "8 Days", "Live Delay": "+2.1 Days (Suez Transit)", "Adjusted ROP Trigger": "Day T-10.1 ⚠️"},
            {"Carrier Feed": "Maersk (Ocean AIS)", "Active Corridor": "Shanghai → Long Beach", "Base Lead-Time": "18 Days", "Live Delay": "0.0 Days", "Adjusted ROP Trigger": "Day T-18"}
        ]
    }

    # Example API endpoint check (e.g. Carrier Gateway / REST endpoint)
    try:
        # If you wire live API endpoints later, place the requests.get() here
        # response = requests.get("https://api.your-carrier-gateway.com/v1/status", timeout=1.5)
        # if response.status_code == 200:
        #     return parse_live_telemetry(response.json())
        pass
    except Exception:
        pass

    return canned_telemetry

def render_demand_supply_match(persona, term_unit="Units", plant1_name="Detroit Main Assembly", plant2_name="Munich Component Line", toller_name="3rd-Party CMO"):
    st.title(f"⚖️ Demand/Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Reconcile commercial demand signals against manufacturing footprint capacity, toller allocations, and plant loading constraints.")

    raw_surge = st.session_state.get("extracted_demand_surge", 65000)
    base_forecast = 781049
    total_horizon_demand = base_forecast + raw_surge
    st.session_state["calculated_horizon_demand"] = total_horizon_demand

    # KPI Top Row
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Baseline S&OP Forecast", f"{base_forecast:,} {term_unit}")
    col_s2.metric("Commercial Surge (NLP Signal)", f"+{raw_surge:,} {term_unit}", "Signal Ingested")
    col_s3.metric("Total Unconstrained Horizon Demand", f"{total_horizon_demand:,} {term_unit}")

    st.markdown("---")

    # TABS STRUCTURE RESTORED HERE
    tab_bau, tab_allocation = st.tabs([
        "📊 Business-As-Usual (BAU) Schedule", 
        "🏭 Multi-Facility Plant Load Allocation"
    ])

    # --- TAB 1: BAU SCHEDULE ---
    with tab_bau:
        st.subheader("📋 BAU Master Production Schedule & Baseline Loading")
        st.caption("Unconstrained demand allocation based on default primary plant assignments before what-if rebalancing.")
        
        bau_data = pd.DataFrame({
            "Facility / Line": [plant1_name, plant2_name, toller_name],
            "BAU Target Utilization": ["85%", "80%", "15%"],
            "Base Capacity": [f"500,000 {term_unit}", f"350,000 {term_unit}", f"335,000 {term_unit}"],
            "BAU Allocated Demand": [
                f"{int(500000 * 0.85):,} {term_unit}", 
                f"{int(350000 * 0.80):,} {term_unit}", 
                f"{int(total_horizon_demand * 0.15):,} {term_unit}"
            ],
            "Operational Status": ["✅ Normal", "✅ Normal", "✅ Within Quota"]
        })
        
        st.dataframe(bau_data, use_container_width=True)
        st.info(f"💡 **BAU Baseline Summary:** Primary facilities operating within standard shift guidelines.")

    # --- TAB 2: MULTI-FACILITY LOAD BALANCER ---
    with tab_allocation:
        st.subheader("🏭 Multi-Facility Plant Load Allocation")

        col_alloc1, col_alloc2 = st.columns([1, 1.1])

        with col_alloc1:
            st.markdown(f"#### **Facility Production Share ({term_unit})**")
            
            plant1_max = 500000
            plant1_alloc_pct = st.slider(f"{plant1_name} Target Utilization (%)", 50, 100, 85, key="p1_alloc_slider")
            plant1_units = int(plant1_max * (plant1_alloc_pct / 100.0))

            plant2_max = 350000
            plant2_alloc_pct = st.slider(f"{plant2_name} Target Utilization (%)", 50, 100, 80, key="p2_alloc_slider")
            plant2_units = int(plant2_max * (plant2_alloc_pct / 100.0))

            toller_alloc_pct = st.slider(f"{toller_name} Offload Share (%)", 0, 50, 15, key="toller_split_slider")
            toller_units = int(total_horizon_demand * (toller_alloc_pct / 100.0))

            allocated_total = plant1_units + plant2_units + toller_units
            unallocated_gap = total_horizon_demand - allocated_total

        with col_alloc2:
            st.markdown("#### **Capacity vs. Allocated Horizon Load**")
            
            cap_df = pd.DataFrame({
                "Facility": [plant1_name, plant2_name, toller_name],
                "Allocated Load": [plant1_units, plant2_units, toller_units],
                "Max Capacity": [plant1_max, plant2_max, int(total_horizon_demand * 0.4)]
            })
            
            fig = go.Figure(data=[
                go.Bar(name='Allocated Load', x=cap_df['Facility'], y=cap_df['Allocated Load'], marker_color='#1f77b4'),
                go.Bar(name='Max Capacity Limit', x=cap_df['Facility'], y=cap_df['Max Capacity'], marker_color='#ff7f0e', opacity=0.6)
            ])
            fig.update_layout(barmode='group', height=280, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

            if unallocated_gap > 0:
                st.warning(f"⚠️ **Capacity Deficit Detected**: Unallocated demand shortfall of **{unallocated_gap:,} {term_unit}**. Trigger CTRM Desk or increase CMO offload.")
            else:
                st.success(f"🟢 **Network Balanced**: All {total_horizon_demand:,} {term_unit} allocated across enterprise footprint.")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if st.button("📌 Commit Plant Allocation & Finalize S&OP Plan", key="btn_commit_demand_plan"):
            st.session_state["demand_plan_committed"] = True
            st.session_state["committed_horizon_demand"] = total_horizon_demand
            st.toast("S&OP Demand Plan Committed & Synced to ERP/BOM!", icon="📌")

    if st.session_state.get("demand_plan_committed", False):
        st.success(f"✅ **Demand Plan Committed**: Horizon plan locked at **{st.session_state.get('committed_horizon_demand', total_horizon_demand):,} {term_unit}**. ERP Purchase Orders and BOM Engine updated!")


def fetch_live_or_fallback(feed_url, fallback_headlines, timeout_sec=1.5):
    if not feed_url:
        return fallback_headlines, False

    try:
        response = requests.get(feed_url, timeout=timeout_sec)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            live_items = []
            for item in root.findall('.//item')[:3]:
                title = item.find('title').text if item.find('title') is not None else "Live News Event"
                live_items.append(f"🟢 [LIVE] {title} [Impact: 90,000 Units]")
            if live_items:
                return live_items, True
    except Exception:
        pass
    
    return fallback_headlines, False


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



def render_global_logistics_gis(persona="Discrete & Heavy Industrial Enterprise", term_unit="FEUs"):
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time maritime telemetry, port dwell tracking, multimodal corridor optimization, and lead-time-aware procurement bridging.")

    # Ingest carrier data (uses fallback seamlessly if feeds are offline)
    telemetry = fetch_carrier_telemetry_with_fallback()
    delay_days = telemetry["dwell_delay_days"]

    # Top Metric Banner
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Freight Volume", f"7,261 {term_unit}", "+312 in-transit")
    m2.metric("Primary Chokepoint Alert", telemetry["primary_alert"], f"Dwell Time +{delay_days} Days")
    m3.metric("Carrier API Feeds", "ONLINE" if telemetry["is_live"] else "STANDBY", telemetry["feed_status"])
    m4.metric("D/S Lead-Time Offset", "AUTOMATED", f"ROP +{delay_days} Days Adjusted")

    st.markdown("---")

    # =====================================================================
    # GIS HEADS-UP DISPLAY (HUD) MAP
    # =====================================================================
    st.subheader("🗺️ Global Multi-Modal Transit HUD & Chokepoint Telemetry")

    # Facility Nodes
    nodes_df = pd.DataFrame({
        "Name": ["Detroit Main Plant", "Munich Assembly", "Shanghai Port Hub", "Rotterdam Port Hub", "Houston Logistics Hub"],
        "Lat": [42.3314, 48.1351, 31.2304, 51.9244, 29.7604],
        "Lon": [-83.0458, 11.5820, 121.4737, 4.4777, -95.3698]
    })

    # Chokepoints
    chokepoints_df = pd.DataFrame({
        "Location": ["Suez Canal", "Panama Canal", "US Gulf Ports (Houston/Mobile)", "Strait of Malacca"],
        "Status": ["AMBER", "GREEN", "RED", "GREEN"],
        "Color": ["#fecb52", "#00cc96", "#ef553b", "#00cc96"],
        "Delay": ["+2.1 Days (Bottleneck)", "Normal Operations", f"+{delay_days} Days (NOAA Surge)", "Normal Operations"],
        "Lat": [30.5852, 9.0800, 29.3013, 1.3521],
        "Lon": [32.3432, -79.6800, -94.7977, 103.8198],
        "Size": [18, 12, 26, 12]
    })

    fig = go.Figure()

    # Corridor Arcs
    corridors = [
        {"name": "Transpacific Lane", "lats": [31.2304, 34.0522], "lons": [121.4737, -118.2437], "color": "#1f77b4"},
        {"name": "Transatlantic Lane", "lats": [51.9244, 29.7604], "lons": [4.4777, -95.3698], "color": "#ef553b"},
        {"name": "Eurasia Rail/Sea Corridor", "lats": [31.2304, 1.3521, 30.5852, 51.9244], "lons": [121.4737, 103.8198, 32.3432, 4.4777], "color": "#fecb52"}
    ]

    for line in corridors:
        fig.add_trace(go.Scattergeo(
            lat=line["lats"], lon=line["lons"],
            mode="lines", line=dict(width=2.5, color=line["color"], dash="dot"),
            name=line["name"], hoverinfo="name"
        ))

    # Plant/Warehouse Markers
    fig.add_trace(go.Scattergeo(
        lat=nodes_df["Lat"], lon=nodes_df["Lon"],
        mode="markers+text",
        marker=dict(size=10, color="#ffffff", symbol="diamond", line=dict(width=1.5, color="#000000")),
        text=nodes_df["Name"], textposition="top center",
        name="Enterprise Nodes (Plants/WH)"
    ))

    # Chokepoint Pulse Markers
    fig.add_trace(go.Scattergeo(
        lat=chokepoints_df["Lat"], lon=chokepoints_df["Lon"],
        mode="markers",
        marker=dict(size=chokepoints_df["Size"], color=chokepoints_df["Color"], opacity=0.85, line=dict(width=2, color="#ffffff")),
        text=chokepoints_df["Location"] + ": " + chokepoints_df["Delay"], hoverinfo="text",
        name="Chokepoint Telemetry"
    ))

    fig.update_layout(
        geo=dict(
            projection_type="natural earth",
            showland=True, landcolor="#1e1e1e",
            showocean=True, oceancolor="#0e1117",
            showcountries=True, countrycolor="#333333",
            bgcolor="#0e1117"
        ),
        height=480, margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================================
    # GOLDEN BRIDGE: LEAD-TIME DRIVEN PROCUREMENT
    # =====================================================================
    st.markdown("---")
    st.subheader("🌉 The Golden Bridge: Demand/Supply & Procurement Lead-Time Offset")

    col_gb1, col_gb2 = st.columns([1.2, 1])

    with col_gb1:
        st.markdown("#### **Active Carrier Telemetry & Dwell Breakdown**")
        st.dataframe(pd.DataFrame(telemetry["telemetry_rows"]), use_container_width=True)

    with col_gb2:
        st.markdown("#### **Automated Procurement Recalibration**")
        st.info(f"💡 **Dynamic MRP Integration Active:** Detected **+{delay_days} Day delay** on the Gulf Freight Corridor. Purchase Order triggers for raw materials are offset from **Day T-4 to Day T-8.2**.")
        
        if st.button("⚡ Execute Dynamic Order Offset in ERP", type="primary", key="btn_gis_execute_rop"):
            st.session_state["rop_offset_executed"] = True
            st.session_state["active_leadtime_delay_days"] = delay_days  # 👈 Dynamic handoff to Procurement Desk!
            st.toast("Reorder points synchronized with SAP S/4HANA & Logistics Engine!", icon="🚀")

    if st.session_state.get("rop_offset_executed", False):
        st.success("✅ **ERP Synchronized**: Reorder points updated across all active manufacturing plants.")
# =====================================================================
# MAIN EXECUTION FLOW
# =====================================================================

# 1. Render sidebar navigation & retrieve active configuration
persona, selected_module, config = render_sidebar_navigation()

# 2. Unpack dynamic terminology and facility variables
term_unit = config["term_unit"]
term_raw = config["term_raw"]
plant1_name = config["plant1_name"]
plant2_name = config["plant2_name"]
toller_name = config["toller_name"]


# =====================================================================
# MAIN ROUTER CONTROL LOOP (Supports All 3 Enterprise Personas)
# =====================================================================

# ROUTER 1: EXECUTIVE S&OP / IBP / DAILY TRADING BALANCE SHEET
if any(term in selected_module for term in ["Executive S&OP", "Integrated Business Planning", "Daily Trading Balance Sheet"]):
    render_executive_sop(persona=persona, term_unit=term_unit)

# ROUTER 2: NLP COMMERCIAL SENSING & MARKET INTELLIGENCE
elif any(term in selected_module for term in ["NLP Commercial Sensing", "Macro & Satellite", "Global Macro", "Retail Intelligence"]):
    render_nlp_intelligence(persona=persona, term_unit=term_unit)

# ROUTER 3: DEMAND/SUPPLY MATCH & PLANT LOAD BALANCER
elif any(term in selected_module for term in ["Demand/Supply Match", "Batch Processing", "Physical Off-Take"]):
    render_demand_supply_match(persona, term_unit, plant1_name, plant2_name, toller_name)

# ROUTER 4: PHYSICAL PROCUREMENT & DIRECT INGREDIENTS DESK
elif any(term in selected_module for term in ["Physical Procurement", "Agri-Ingredients"]):
    render_physical_procurement(persona=persona, term_unit=term_unit, term_raw=term_raw)

# ROUTER 5: CTRM DERIVATIVES & COMMODITY RISK DESK
elif "CTRM" in selected_module:
    render_ctrm_desk(persona=persona, term_unit=term_unit)

# ROUTER 6: SANDBOX FLIGHT SIMULATOR & STRESS LAB
elif any(term in selected_module for term in ["Sandbox", "Flight Simulator", "Stress Lab"]):
    render_flight_simulator(persona=persona, term_unit=term_unit)

# ROUTER 7: GLOBAL LOGISTICS NETWORK & GIS CONTROL TOWER
elif any(term in selected_module for term in ["Global Logistics", "GIS", "Cold Chain", "Maritime AIS"]):
    render_global_logistics_gis(persona=persona, term_unit=term_unit)

# ROUTER 8: INTEGRATION & ARCHITECTURE ENDPOINTS
elif "Integration" in selected_module:
    render_integration_architecture(persona=persona, selected_module=selected_module)

# FALLBACK SAFETY NET
else:
    st.warning(f"⚠️ Unmapped operational module selected: **{selected_module}**")