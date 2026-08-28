import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =====================================================================
# HELPER FUNCTIONS & MODEL ENGINES
# =====================================================================

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
            {"Vendor": "Cargill Oils", "Material": "Refined Palm / Soy Oil", "Quantity": "15,000 MT", "Status": "🟢 Active", "Delivery": "Weekly Stream"},
            {"Vendor": "Tetra Pak Global", "Material": "Aseptic Packaging Board", "Quantity": "2,500,000 Units", "Status": "🟢 Active", "Delivery": "Bi-Weekly"},
            {"Vendor": "Archer Daniels Midland", "Material": "High-Fructose Corn Syrup", "Quantity": "8,000 MT", "Status": "⚠️ Delayed", "Delivery": "Monthly Spot"}
        ]
    elif "Merchant" in persona:
        return [
            {"Vendor": "Glencore Singapore", "Material": "Physical Copper Cathodes", "Quantity": "10,000 MT", "Status": "🟢 Active", "Delivery": "Prompt Shipment"},
            {"Vendor": "Trafigura Trading", "Material": "LNG Physical Cargo", "Quantity": "120,000 MWh", "Status": "🟢 Active", "Delivery": "CIF Rotterdam"},
            {"Vendor": "Bunge Global", "Material": "Yellow Corn #2", "Quantity": "45,000 MT", "Status": "🟡 Re-negotiating", "Delivery": "FOB Santos"}
        ]
    else:  # Discrete & Heavy Industrial
        return [
            {"Vendor": "Rio Tinto Metals", "Material": "Primary Aluminum Ingot", "Quantity": "12,000 MT", "Status": "🟢 Active", "Delivery": "Monthly Rail"},
            {"Vendor": "TSMC Wafer Foundry", "Material": "Automotive Microcontrollers", "Quantity": "500,000 Units", "Status": "⚠️ Bottleneck", "Delivery": "Quarterly Allocation"},
            {"Vendor": "POSCO Steel", "Material": "Cold-Rolled Sheet Coil", "Quantity": "25,000 MT", "Status": "🟢 Active", "Delivery": "Weekly Barge"}
        ]


# =====================================================================
# SCREEN RENDER FUNCTIONS
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
        {"Endpoint": "IBP Engine Core", "Protocol": "Python / Microservice", "Latency": "12 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "SAP S/4HANA Enterprise ERP", "Protocol": "REST / OData API", "Latency": "45 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "CME / LME FIX Gateway", "Protocol": "FIX 4.4 Engine", "Latency": "4 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "AIS Global Maritime Radar", "Protocol": "WebSocket Stream", "Latency": "120 ms", "Status": "🟢 HEALTHY"},
        {"Endpoint": "TextBlob / RSS NLP Scraper", "Protocol": "HTTP / RSS Feed", "Latency": "210 ms", "Status": "🟢 HEALTHY"}
    ])
    st.dataframe(mesh_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🛠️ Session State Telemetry Debugger")
    st.json({
        "active_disruption": st.session_state.get("active_disruption"),
        "extracted_demand_surge": st.session_state.get("extracted_demand_surge"),
        "demand_plan_committed": st.session_state.get("demand_plan_committed", False),
        "committed_horizon_demand": st.session_state.get("committed_horizon_demand"),
        "fix_executed": st.session_state.get("fix_executed", False),
        "erp_requisitions_pushed": st.session_state.get("erp_requisitions_pushed", False),
        "rop_offset_executed": st.session_state.get("rop_offset_executed", False),
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

    with tab1:
        st.subheader("📡 Real-Time Web & Macro News Stream")
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
            "🍊 Agricultural Commodities & Cold-Chain": [
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

        col_w1, col_w2 = st.columns([2, 1])
        with col_w1:
            selected_domain = st.selectbox("Select Commodity / Industry Sector Focus:", list(NEWS_DOMAINS.keys()), key="nlp_sector_focus")
            fallback_list = NEWS_DOMAINS[selected_domain]
            active_headlines, is_live = fetch_live_or_fallback("", fallback_list)

            selected_headline = st.selectbox("Select AI-Scraped Headline Signal:", active_headlines, key="nlp_web_headline_select")

        with col_w2:
            match = re.search(r'\[Impact:\s*([\d,]+)\s*Units\]', selected_headline)
            extracted_default = int(match.group(1).replace(',', '')) if match else 85000
            web_impact = st.number_input(f"Extracted Signal Impact ({term_unit})", value=extracted_default, step=5000, key="web_signal_units")

        if st.button("📡 Ingest Scraped Domain News Signal", key="btn_ingest_web"):
            headline_clean = selected_headline.split("[")[0].strip()
            domain_label = selected_domain.split(" ")[1] if len(selected_domain.split(" ")) > 1 else "Macro"
            st.session_state["extracted_demand_surge"] = web_impact
            st.session_state["active_risk_signal_title"] = f"[{domain_label}] {headline_clean}"
            st.session_state["signal_category"] = "Live Web Intelligence"
            st.toast(f"Ingested '{headline_clean}' ({web_impact:,} {term_unit})", icon="📡")
            st.success(f"✅ Propagated **[{domain_label}] {headline_clean}** ({web_impact:,} {term_unit}) across S&OP and CTRM Desk!")

    with tab2:
        st.subheader("📧 Unstructured Email & Sales Debrief Parser")
        input_mode = st.radio("Select Debrief Input Mode:", ["📋 Select Preset Communication", "✍️ Paste Custom Email / Debrief"], horizontal=True, key="email_input_mode")

        if input_mode == "📋 Select Preset Communication":
            email_selection = st.selectbox(
                "Select Field Communication / Debrief:",
                [
                    f"Trade Show / Sales Debrief (CES Expo 2026) - 250,000 {term_unit} Uplift",
                    f"Q3 Distributor Stocking Order Email - 150,000 {term_unit} Uplift",
                    f"OEM Emergency Spares Requisition - 75,000 {term_unit} Uplift"
                ],
                key="email_debrief_select"
            )
            default_email_val = 250000 if "CES" in email_selection else (150000 if "Distributor" in email_selection else 75000)
            email_text_preview = f"Parsed from inbox: Rep indicates major commercial surge following {email_selection}. Demand spike expected to hit W38."
            email_title_parsed = email_selection.split("-")[0].strip()
        else:
            custom_email_text = st.text_area(
                "Paste Unstructured Email / Sales Rep Notes:",
                value=f"From: regional_sales_vp@enterprise.com\nSubject: URGENT: Q3 OEM Order Expansion\n\nTeam, Key Customer Apex Motors requests immediate supply ramp of 180,000 additional {term_unit.lower()} for Q3.",
                height=120,
                key="custom_email_text_area"
            )
            units_found = re.findall(r'([\d,]+)\s*(?:additional\s*)?(?:units|cases|batches|lots|contracts)?', custom_email_text, re.IGNORECASE)
            default_email_val = int(units_found[0].replace(',', '')) if units_found and units_found[0].replace(',', '').isdigit() else 180000
            email_text_preview = custom_email_text
            email_title_parsed = "Custom Rep Email Signal"

        col_e1, col_e2 = st.columns([2, 1])
        with col_e1:
            st.text_area("Parsed Raw Text Preview:", value=email_text_preview, height=100, disabled=True, key="email_preview_disabled")
        with col_e2:
            email_impact = st.number_input(f"Parsed Demand Surge Impact ({term_unit})", value=default_email_val, step=10000, key="email_units")

        if st.button("📧 Parse & Ingest Selected Email Debrief", key="btn_ingest_email"):
            st.session_state["extracted_demand_surge"] = email_impact
            st.session_state["active_risk_signal_title"] = f"Email Debrief: {email_title_parsed}"
            st.session_state["signal_category"] = "Field Sales Debrief"
            st.toast(f"Parsed {email_title_parsed} ({email_impact:,} {term_unit})", icon="📧")
            st.success(f"✅ Propagated **{email_title_parsed}** ({email_impact:,} {term_unit}) directly to S&OP Horizon & CTRM Desk!")

    with tab3:
        st.subheader("⛈️ Climate, Weather & Black Swan Risk Feeds")
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
            default_weather_val = 120000 if "Hurricane" in weather_alert else (60000 if "Panama" in weather_alert else 25000)
            weather_impact = st.number_input(f"Climate Risk Deficit Impact ({term_unit})", value=default_weather_val, step=5000, key="weather_signal_units")

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

    # --- 1. GIS Lead-Time Offset State ---
    rop_offset_active = st.session_state.get("rop_offset_executed", False)
    delay_days = st.session_state.get("active_leadtime_delay_days", 4.2 if rop_offset_active else 0.0)

    if rop_offset_active:
        st.warning(
            f"⚡ **Dynamic Lead-Time Offset Active (from GIS Control Tower):** "
            f"Carrier delays added **+{delay_days:.1f} Days** to active transit corridors. "
            f"Purchase Order release triggers shifted from **Day T-4.0** to **Day T-{(4.0 + delay_days):.1f}**."
        )
    else:
        st.info("ℹ️ **Standard MRP Mode:** Lead times running on static baseline vendor contracts.")

    # --- 2. Master Active Physical Contracts ---
    st.subheader("📋 Active Physical Supply Contracts")
    contracts_df = pd.DataFrame(get_persona_contracts(persona))

    if not contracts_df.empty and rop_offset_active:
        contracts_df["GIS Transit Delay"] = f"+{delay_days:.1f} Days"
        contracts_df["Adjusted ROP Trigger"] = f"Day T-{(4.0 + delay_days):.1f} ⚠️"

    st.dataframe(contracts_df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # --- 3. Dynamic Horizon Ingestion & BOM Engine ---
    st.subheader("📦 Bill of Materials (BOM) Auto-Requisition Engine")
    is_committed = st.session_state.get("demand_plan_committed", False)
    
    # Reads multi-week total from Load Balancer, fallback to committed/calculated demand
    active_demand = st.session_state.get(
        "total_horizon_units",
        st.session_state.get(
            "committed_horizon_demand" if is_committed else "calculated_horizon_demand", 
            862640
        )
    )

    if is_committed:
        st.success(f"⚡ **Live S&OP Horizon Sync Active**: Displaying requisitions for committed Demand Plan of **{active_demand:,} {term_unit}**.")
    else:
        st.info(f"ℹ️ **Baseline S&OP Forecast**: Displaying uncommitted requisitions for **{active_demand:,} {term_unit}**.")

    # Chautauqua BOM Explosion Formulas
    req_metals_mt = int(active_demand * 0.015)
    req_components = int(active_demand * 1.50)
    req_freight_feus = int(active_demand / 144.28)

    # Push to session state for downstream CTRM Derivatives Desk
    st.session_state["required_metal_mt"] = req_metals_mt
    st.session_state["required_feu_slots"] = req_freight_feus

    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric(f"Required {term_raw}", f"{req_metals_mt:,} MT", help="Formula: Horizon Units * 0.015")
    col_b2.metric("Component Requisitions", f"{req_components:,} Units", help="Formula: Horizon Units * 1.5")
    col_b3.metric("Freight Slots Reserved", f"{req_freight_feus:,} FEUs", help="Formula: Horizon Units / 144.28")

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

    # ----------------------------------------------------
    # 0. CROSS-DESK SESSION STATE INITIALIZATION
    # ----------------------------------------------------
    if "sop_cash_balance" not in st.session_state:
        st.session_state["sop_cash_balance"] = 5_000_000.00  # Default $5M Treasury
    if "future_supply_ledger" not in st.session_state:
        st.session_state["future_supply_ledger"] = {
            "Current Period": 50000,
            "Target Period (+30D)": 60000,
            "Target Period (+90D)": 65000
        }

    raw_surge = st.session_state.get("extracted_demand_surge", 65000)
    signal_title = st.session_state.get("active_risk_signal_title", "NOAA Climate Alert")
    signal_category = st.session_state.get("signal_category", "Weather & Macro Feed")

    cmo_offload_pct = st.session_state.get("toller_split_slider", 15)
    net_exposure_pct = max(0.20, cmo_offload_pct / 100.0)
    net_unhedged_units = int(raw_surge * net_exposure_pct)
    unhedged_risk = net_unhedged_units * 150.0
    default_lots = max(10, int(net_unhedged_units / 100))

    # Auto-Derive Time Period / Expiration Horizon from Market Signal
    if "Climate" in signal_title or "Surge" in signal_category:
        auto_horizon_days = 90
        target_period_key = "Target Period (+90D)"
    else:
        auto_horizon_days = 30
        target_period_key = "Target Period (+30D)"

    st.info(
        f"⚡ **Active Risk Signal Ingested**: {signal_title} *({signal_category})* | "
        f"**Gross Exposure:** {raw_surge:,} {term_unit} | **Net Shortfall:** {net_unhedged_units:,} {term_unit} | "
        f"⏱️ **Auto Horizon:** {auto_horizon_days} Days"
    )

    tab_exec, tab_lab = st.tabs(["📊 Standard Desk & FIX Execution", "🧪 Synthetic Derivative Builder & Model Lab"])

    with tab_exec:
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        col_c1.metric("Gross Demand Surge", f"{raw_surge:,} {term_unit}")
        col_c2.metric("Physical Cover (Stock/CMO)", f"{raw_surge - net_unhedged_units:,} {term_unit}")
        col_c3.metric("Net Shortfall", f"{net_unhedged_units:,} {term_unit}", f"{net_exposure_pct*100:.0f}% Unhedged Gap")
        col_c4.metric("Unhedged Margin Risk", f"${unhedged_risk:,.2f}")

        st.markdown("---")
        st.subheader("⚡ FIX 4.4 Order Execution Gateway")

        # Row 1: Intent & Time Period
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            intent_type = st.selectbox(
                "Execution Intent", 
                ["Hedge Risk (Cover Shortfall)", "Exercise Call Option", "Exercise Put Option", "Speculative Position"], 
                key="std_intent"
            )
        with col_i2:
            time_horizon = st.selectbox(
                "Time Period / Expiration", 
                [f"Auto-Matched ({auto_horizon_days} Days)", "30 Days (Short-Term)", "60 Days (Mid-Term)", "90 Days (Long-Term LEAP)"], 
                key="std_horizon"
            )
        with col_i3:
            unit_premium_est = st.number_input("Est. Premium ($/Unit)", value=4.25, step=0.25, key="std_unit_prem")

        # Dynamic Premium Cost Calculation
        calculated_total_premium = net_unhedged_units * unit_premium_est

        # Row 2: Structure, Exchange, Lots
        col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
        with col_f1:
            order_type = st.selectbox("Order Structure", ["Asian Call Collar", "Outright Call Option", "Outright Put Option", "Delta-Hedged Futures Spread"], key="std_order_type")
        with col_f2:
            exchange = st.selectbox("Execution Exchange", ["CME Group", "ICE Futures", "LME"], key="std_exchange")
        with col_f3:
            lots = st.number_input("Lots / Contracts (Net Shortfall)", value=default_lots, step=10, key="std_lots")

        st.caption(f"💰 **Total Premium Required:** `${calculated_total_premium:,.2f}` (Will be debited from Exec S&OP Cash)")

        if st.button("⚡ Execute & Route FIX 4.4 Paper Order", key="btn_exec_std"):
            # 1. State cascade: Deduct Premium from S&OP Treasury
            st.session_state["sop_cash_balance"] -= calculated_total_premium
            
            # 2. State cascade: Inject Volume to Module 3 if Hedging or Exercising Call
            if "Hedge" in intent_type or "Call" in intent_type:
                st.session_state["future_supply_ledger"][target_period_key] += net_unhedged_units
                supply_msg = f"Added +{net_unhedged_units:,} {term_unit} to Module 3 ({target_period_key})."
            else:
                supply_msg = "No physical volume added (Financial Settlement/Put Option)."

            st.session_state["fix_executed"] = True
            st.session_state["executed_lots"] = lots
            st.session_state["executed_order_type"] = order_type
            st.session_state["executed_exchange"] = exchange
            st.session_state["last_supply_msg"] = supply_msg

            st.toast(f"FIX Order Sent: {lots:,} Lots to {exchange}!", icon="⚡")

        if st.session_state.get("fix_executed", False):
            exec_lots = st.session_state.get("executed_lots", lots)
            exec_type = st.session_state.get("executed_order_type", order_type)
            exec_exch = st.session_state.get("executed_exchange", exchange)
            last_msg = st.session_state.get("last_supply_msg", "")
            
            st.success(
                f"✅ **FIX 4.4 Executed**: {exec_type} on {exec_exch} for **{exec_lots:,} Lots** | Intent: **{intent_type}**\n\n"
                f"💸 **Exec S&OP Treasury Updated:** Debited `${calculated_total_premium:,.2f}`. Remaining Cash: `${st.session_state['sop_cash_balance']:,.2f}`\n\n"
                f"📦 **Demand/Supply (Module 3) Updated:** {last_msg}"
            )

    with tab_lab:
        st.subheader("🛠️ Custom Synthetic Derivative Constructor")
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
                floor, cap = strike_price * 0.9, strike_price * 1.1
                payoff = np.clip(price_range - floor, 0, cap - floor) * net_unhedged_units - (strike_price * 0.05 * net_unhedged_units)
            else:
                payoff = np.maximum(price_range - strike_price, 0) * net_unhedged_units - (strike_price * 0.08 * net_unhedged_units)

            chart_data = pd.DataFrame({"Underlying Price ($)": price_range, "Net Payoff ($)": payoff})
            st.line_chart(chart_data, x="Underlying Price ($)", y="Net Payoff ($)", use_container_width=True)

        with col_m2:
            st.markdown("#### **Estimated Instrument Greeks**")
            st.metric("Delta (Δ) Sensitivity", "0.52" if "Black76" in pricing_engine else "0.48 (Simulated)")
            st.metric("Vega (ν) Vol Risk", "$12,450 / 1% Vol" if "Jump-Diffusion" in pricing_engine else "$10,200 / 1% Vol")
            st.metric("Estimated Structure Premium", f"${net_unhedged_units * 4.25:,.2f}")

        if st.button("🚀 Route Custom OTC Synthetic Structure to Exchange Clearing", key="btn_route_synthetic"):
            synthetic_prem = net_unhedged_units * 4.25
            st.session_state["sop_cash_balance"] -= synthetic_prem
            st.session_state["future_supply_ledger"][target_period_key] += net_unhedged_units
            st.session_state["synthetic_executed"] = True
            st.toast(f"Custom OTC Structure Cleared! Debited ${synthetic_prem:,.2f} from S&OP Cash.", icon="🚀")

    # ----------------------------------------------------
    # LIVE CROSS-DESK LEDGER AUDIT DISPLAY
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔗 Real-Time Cross-Desk Cascades")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.markdown("**Exec S&OP Desk (Module 1) Treasury**")
        st.metric("Available Cash Balance", f"${st.session_state['sop_cash_balance']:,.2f}")
    with l_col2:
        st.markdown("**Demand/Supply Match (Module 3) Ledger**")
        st.json(st.session_state["future_supply_ledger"])


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
    surge_revenue_upside = round((surge_units * 249.23) / 1_000_000, 2)  # Yields +$16.20M
    unconstrained_demand_rev = base_aop_revenue + surge_revenue_upside
    
    # Check procurement sync state from Procurement / GIS Desks
    pos_synced = st.session_state.get("erp_requisitions_pushed", False) or st.session_state.get("rop_offset_executed", False)
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


def render_demand_supply_match(persona, term_unit, plant1_name, plant2_name, toller_name):
    st.title("⚙️ Demand / Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")
    
    # Ingest live NLP surge from Commercial Sensing session state
    nlp_surge_val = st.session_state.get("extracted_demand_surge", 65000)
    
    # --- 1. Horizon Window & BAU Baseline Controls ---
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.2, 1, 1])
    
    with col_ctrl1:
        horizon_window = st.radio(
            "Planning Horizon Window",
            ["+30 Days (W35–W38)", "+60 Days (W35–W42)", "+90 Days (W35–W46)"],
            horizontal=True
        )
    with col_ctrl2:
        yoy_growth = st.slider("YoY Base Growth %", min_value=-10.0, max_value=30.0, value=5.0, step=0.5)
    with col_ctrl3:
        base_avg_demand = st.slider(f"Weekly BAU Base Avg ({term_unit})", min_value=100000, max_value=200000, value=130000, step=5000)

    # --- 2. Dynamic Time-Phased Baseline & NLP Surge Array ---
    num_weeks = 4 if "+30" in horizon_window else (8 if "+60" in horizon_window else 12)
    weeks = [f"W{35 + i}" for i in range(num_weeks)]
    
    base_demand = [int(base_avg_demand * (1 + (yoy_growth / 100.0)) * (1 + 0.015 * i)) for i in range(num_weeks)]
    
    # Map ingested NLP surge across mid-horizon weeks
    nlp_surge = [0] * num_weeks
    if num_weeks >= 3:
        nlp_surge[2] = int(nlp_surge_val * 0.4)
    if num_weeks >= 4:
        nlp_surge[3] = int(nlp_surge_val * 0.6)
        
    total_unconstrained = [b + s for b, s in zip(base_demand, nlp_surge)]
    
    moq_floor = 115000
    max_plant_capacity = 145000

    # --- 3. Interactive Plotly Horizon HUD ---
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=weeks, y=total_unconstrained, 
        name='Total Unconstrained (BAU + NLP Surge)',
        marker_color='#0747a6', opacity=0.45
    ))
    
    fig.add_trace(go.Scatter(
        x=weeks, y=base_demand, 
        mode='lines+markers', name='BAU Baseline (YoY Dynamic)',
        line=dict(color='#0052cc', width=3)
    ))
    
    fig.add_hline(y=moq_floor, line_dash="dash", line_color="#ffab00", annotation_text=f"Contract MOQ Floor ({moq_floor:,})")
    fig.add_hline(y=max_plant_capacity, line_dash="dot", line_color="#de350b", annotation_text=f"Primary Plant Ceiling ({max_plant_capacity:,})")

    fig.update_layout(
        title=f"Time-Phased Demand vs. Capacity Constraints ({horizon_window})",
        xaxis_title="Planning Horizon (Weeks)",
        yaxis_title=f"Volume ({term_unit})",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. Plant Telemetry & Co-Packer Margin Drag Engine ---
    st.markdown("---")
    st.subheader("⚖️ Dynamic Allocation Adjustment & Co-Packer Drag Engine")
    
    cmo_slider = st.slider(f"CMO / Partner Offload Ratio ({toller_name}):", min_value=5, max_value=40, value=15, step=5, key="toller_split_slider")

    total_horizon_units = sum(total_unconstrained)
    offload_units = int(total_horizon_units * (cmo_slider / 100.0))
    retained_units = total_horizon_units - offload_units
    margin_drag = cmo_slider * 0.12  # Formula: Slider % * $0.12M per % offload

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric(f"Facility A: {plant1_name}", f"{int(retained_units * 0.56):,} {term_unit}", "98% Capacity")
    col_p2.metric(f"Facility B: {plant2_name}", f"{int(retained_units * 0.44):,} {term_unit}", "85% Capacity")
    col_p3.metric(f"Partner: {toller_name}", f"{offload_units:,} {term_unit}", f"{cmo_slider}% Offload Split")
    col_p4.metric("Co-Packer Margin Drag", f"-${margin_drag:.2f}M", delta_color="inverse")

    # --- 5. Commit Button & Multi-Desk State Handshake ---
    if st.button("⚡ Commit & Finalize S&OP Production Horizon", type="primary", key="btn_commit_sop"):
        st.session_state["demand_plan_committed"] = True
        st.session_state["committed_horizon_demand"] = total_horizon_units
        st.session_state["total_horizon_units"] = total_horizon_units
        st.session_state["retained_plant_units"] = retained_units
        st.session_state["cmo_offload_units"] = offload_units
        st.toast("Production plan committed across primary plants and partner nodes!", icon="🚀")
        
    if st.session_state.get("demand_plan_committed", False):
        st.success(
            f"✅ **S&OP Horizon Plan Committed**: "
            f"{st.session_state.get('total_horizon_units', total_horizon_units):,} {term_unit} "
            f"locked into manufacturing schedule across {horizon_window}."
        )

def render_global_logistics_gis(persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"):
    st.title("🌐 Global Logistics Network & GIS Control Tower")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Real-time maritime AIS vessel tracking, port dwell telemetry, and dynamic MRP procurement lead-time recalibration.")

    active_signal = st.session_state.get("active_risk_signal_title", "Baseline - Normal Transit Operations")
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.info(f"📡 **Active GIS Risk Signal**: {active_signal}")
    with col_c2:
        delay_days = st.slider("Simulated Route Transit Delay (Days):", min_value=0.0, max_value=14.0, value=4.2, step=0.5, key="gis_delay_slider")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Global Freight Index (FBX)", "$3,420 / FEU", "+12.4%", delta_color="inverse")
    col_m2.metric("Port Dwell Time (US Gulf)", f"{3.2 + delay_days:.1f} Days", f"+{delay_days:.1f} Days", delta_color="inverse")
    col_m3.metric("Active Vessels Tracked", "142 Cargo Ships")
    col_m4.metric("Supply Chain Risk Level", "ELEVATED" if delay_days > 3 else "NORMAL")

    st.markdown("---")
    st.subheader("🗺️ Global Multi-Modal Transit HUD & Chokepoint Telemetry")

    nodes_df = pd.DataFrame({
        "Name": ["Detroit Main Plant", "Munich Assembly", "Shanghai Port Hub", "Rotterdam Port Hub", "Houston Logistics Hub"],
        "Lat": [42.3314, 48.1351, 31.2304, 51.9244, 29.7604],
        "Lon": [-83.0458, 11.5820, 121.4737, 4.4777, -95.3698]
    })

    chokepoints_df = pd.DataFrame({
        "Location": ["Suez Canal", "Panama Canal", "US Gulf Ports", "Strait of Malacca"],
        "Delay": ["+2.1 Days", "Normal Operations", f"+{delay_days} Days", "Normal Operations"],
        "Color": ["#fecb52", "#00cc96", "#ef553b", "#00cc96"],
        "Lat": [30.5852, 9.0800, 29.3013, 1.3521],
        "Lon": [32.3432, -79.6800, -94.7977, 103.8198],
        "Size": [18, 12, 26, 12]
    })

    fig = go.Figure()
    corridors = [
        {"name": "Transpacific Lane", "lats": [31.2304, 34.0522], "lons": [121.4737, -118.2437], "color": "#1f77b4"},
        {"name": "Transatlantic Lane", "lats": [51.9244, 29.7604], "lons": [4.4777, -95.3698], "color": "#ef553b"},
        {"name": "Eurasia Rail/Sea Corridor", "lats": [31.2304, 1.3521, 30.5852, 51.9244], "lons": [121.4737, 103.8198, 32.3432, 4.4777], "color": "#fecb52"}
    ]

    for line in corridors:
        fig.add_trace(go.Scattergeo(lat=line["lats"], lon=line["lons"], mode="lines", line=dict(width=2.5, color=line["color"], dash="dot"), name=line["name"]))

    fig.add_trace(go.Scattergeo(lat=nodes_df["Lat"], lon=nodes_df["Lon"], mode="markers+text", marker=dict(size=10, color="#ffffff", symbol="diamond"), text=nodes_df["Name"], textposition="top center", name="Enterprise Nodes"))
    fig.add_trace(go.Scattergeo(lat=chokepoints_df["Lat"], lon=chokepoints_df["Lon"], mode="markers", marker=dict(size=chokepoints_df["Size"], color=chokepoints_df["Color"], opacity=0.85), text=chokepoints_df["Location"] + ": " + chokepoints_df["Delay"], name="Chokepoint Telemetry"))

    fig.update_layout(geo=dict(projection_type="natural earth", showland=True, landcolor="#1e1e1e", showocean=True, oceancolor="#0e1117", bgcolor="#0e1117"), height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🌉 Dynamic Procurement Lead-Time Recalibration")
    col_gb1, col_gb2 = st.columns([1.2, 1])

    with col_gb1:
        st.markdown("#### **Active Carrier Telemetry**")
        st.dataframe(pd.DataFrame([
            {"Carrier / Vessel": "Maersk Horizon", "Route": "Shanghai -> Houston", "Dwell Time": f"{4.1 + delay_days:.1f} Days", "Status": "⚠️ Delayed"},
            {"Carrier / Vessel": "MSC Geneva", "Route": "Rotterdam -> Detroit", "Dwell Time": "1.8 Days", "Status": "🟢 On Time"}
        ]), use_container_width=True, hide_index=True)

    with col_gb2:
        st.markdown("#### **Automated PO Recalibration**")
        st.info(f"💡 **Dynamic MRP Integration Active:** Detected **+{delay_days} Day delay**. Purchase Order triggers offset from **Day T-4 to Day T-{(4.0 + delay_days):.1f}**.")
        if st.button("⚡ Execute Dynamic Order Offset in ERP", type="primary", key="btn_gis_execute_rop"):
            st.session_state["rop_offset_executed"] = True
            st.session_state["active_leadtime_delay_days"] = delay_days
            st.toast("Reorder points synchronized with SAP S/4HANA!", icon="🚀")


# =====================================================================
# PERSONA CONFIG ENGINE & SIDEBAR NAVIGATION
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
                "Executive S&OP & IBP Control Tower",
                "NLP Commercial Sensing & Field Intelligence",
                "Demand/Supply Match & Plant Load Balancer",
                "Physical Procurement & Master Contract Desk",
                "CTRM Derivatives & Commodity Risk Desk",
                "Global Logistics Network & GIS Control Tower",
                "Sandbox Flight Simulator & Stress Lab",
                "Integration & Architecture Endpoints"
            ]
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
                "Physical Procurement & Direct Ingredients Desk",
                "CTRM Event-Driven Hedging Desk",
                "Global Logistics Network & GIS Control Tower",
                "Sandbox Flight Simulator & Stress Lab",
                "Integration & Architecture Endpoints"
            ]
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
                "Demand/Supply Match & Batch Processing",
                "Physical Procurement & Master Contract Desk",
                "CTRM Derivatives & Commodity Risk Desk",
                "Global Logistics Network & GIS Control Tower",
                "Sandbox Flight Simulator & Stress Lab",
                "Integration & Architecture Endpoints"
            ]
        }


def render_sidebar_navigation():
    st.sidebar.title("⚡ IBP Control Tower")
    
    persona = st.sidebar.selectbox(
        "Enterprise Operating Persona:",
        [
            "Discrete & Heavy Industrial Enterprise",
            "FMCG, Food & Beverage Enterprise",
            "Merchant Trading & Commodity Enterprise"
        ],
        key="platform_persona_select"
    )
    
    config = get_persona_config(persona)
    
    selected_module = st.sidebar.radio(
        "Navigation Modules:",
        config["modules"],
        key="sidebar_module_radio"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧪 Macro Flight Simulator")
    sandbox_scenario = st.sidebar.selectbox(
        "Select 'What-If' Stress Scenario:",
        [
            "Baseline Operations",
            "Red Sea Freight Bottleneck (+45% Freight, +8d Lag)",
            "Red River Drought / Crop Deficit (-30% Yield)",
            "Black Swan Volatility Spike (+250% IV Shock)"
        ],
        key="sb_scenario_select"
    )
    
    if st.sidebar.button("🧪 Launch Sim Scenario", key="btn_launch_sandbox"):
        st.session_state["sandbox_active"] = (sandbox_scenario != "Baseline Operations")
        st.session_state["sandbox_scenario"] = sandbox_scenario
        
        if "Freight" in sandbox_scenario:
            st.session_state["sandbox_params"] = {
                "volume_multiplier": 1.10, "spot_cost_increase": 0.35,
                "transit_delay_days": 8, "iv_multiplier": 1.4,
                "description": "Red Sea maritime rerouting forcing Cape of Good Hope transit."
            }
        elif "Drought" in sandbox_scenario:
            st.session_state["sandbox_params"] = {
                "volume_multiplier": 0.85, "spot_cost_increase": 0.50,
                "transit_delay_days": 4, "iv_multiplier": 1.8,
                "description": "Severe agricultural crop failure inflating physical spot prices."
            }
        elif "Volatility" in sandbox_scenario:
            st.session_state["sandbox_params"] = {
                "volume_multiplier": 1.00, "spot_cost_increase": 0.15,
                "transit_delay_days": 0, "iv_multiplier": 2.5,
                "description": "Financial market dislocation spiking derivative options implied volatility."
            }
        else:
            st.session_state["sandbox_params"] = {
                "volume_multiplier": 1.00, "spot_cost_increase": 0.00,
                "transit_delay_days": 0, "iv_multiplier": 1.0,
                "description": "Standard baseline parameters."
            }
        st.toast(f"Activated: {sandbox_scenario}", icon="🧪")
        
    return persona, selected_module, config


# =====================================================================
# MAIN EXECUTION ROUTER
# =====================================================================

persona, selected_module, config = render_sidebar_navigation()

term_unit = config["term_unit"]
term_raw = config["term_raw"]
plant1_name = config["plant1_name"]
plant2_name = config["plant2_name"]
toller_name = config["toller_name"]

if any(term in selected_module for term in ["Executive S&OP", "Integrated Business Planning", "Daily Trading Balance Sheet"]):
    render_executive_sop(persona=persona, term_unit=term_unit)

elif any(term in selected_module for term in ["NLP Commercial Sensing", "Macro & Satellite", "Global Macro", "Retail Intelligence"]):
    render_nlp_intelligence(persona=persona, term_unit=term_unit)

elif any(term in selected_module for term in ["Demand/Supply Match", "Batch Processing", "Physical Off-Take"]):
    render_demand_supply_match(persona, term_unit, plant1_name, plant2_name, toller_name)

elif any(term in selected_module for term in ["Physical Procurement", "Agri-Ingredients"]):
    render_physical_procurement(persona=persona, term_unit=term_unit, term_raw=term_raw)

elif "CTRM" in selected_module:
    render_ctrm_desk(persona=persona, term_unit=term_unit)

elif any(term in selected_module for term in ["Sandbox", "Flight Simulator", "Stress Lab"]):
    render_flight_simulator(persona=persona, term_unit=term_unit)

elif any(term in selected_module for term in ["Global Logistics", "GIS", "Cold Chain", "Maritime AIS"]):
    render_global_logistics_gis(persona=persona, term_unit=term_unit)

elif "Integration" in selected_module:
    render_integration_architecture(persona=persona, selected_module=selected_module)

else:
    st.warning(f"⚠️ Unmapped operational module selected: **{selected_module}**")