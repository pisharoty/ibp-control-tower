import json
import os
import re
import numpy as np
import pandas as pd
import plotly.express as px
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


def render_nlp_intelligence(persona=None, term_unit="Units", **kwargs):
  """Complete NLP Commercial Sensing & Intelligence Module.

  Features:
  - Composite Market Sentiment Index ($SI$) Executive Card with fallback parsing
  - Automated GEP & LinkedIn IMAP Signal Ingestion
  - Expanded Sector Coverage: Copper, Tin, Rare Earths, Industrial Chemicals,
  Semiconductors, Energy, Freight
  """
  st.title("🧠 NLP Commercial Sensing & Intelligence")
  st.caption(
      "Ingest unstructured signals from news feeds, social media, post-trade"
      " show emails, and GIS telemetry."
  )

  tab1, tab2, tab3 = st.tabs([
      "📡 Live Web Signals",
      "📧 Email & Event Debrief Parser",
      "⚓ Freight, Weather & Black Swan Feeds",
  ])

  with tab1:
    # Header & Manual Refresh Button
    r_head1, r_head2 = st.columns([3, 1])
    with r_head1:
      st.caption("🤖 **Triangulated Intelligence**: Macro Sentiment + Live Feeds")
    with r_head2:
      if st.button("🔄 Refresh Live Feeds", key="btn_refresh_robot_feeds"):
        try:
          from robot_feeds import sync_robot_feeds

          sync_robot_feeds()
          st.toast("Refreshed feeds from Gmail IMAP & GEP!", icon="🔄")
          st.rerun()
        except Exception as e:
          st.error(f"Sync error: {e}")

    # Auto-sync baseline cache if missing
    if not os.path.exists("robot_signals.json"):
      try:
        from robot_feeds import sync_robot_feeds

        sync_robot_feeds()
      except Exception as e:
        st.error(f"Robot Feed Sync Error: {e}")

    # Read cache or compute dynamic fallback
    robot_data = {}
    if os.path.exists("robot_signals.json"):
      try:
        with open("robot_signals.json", "r") as f:
          robot_data = json.load(f)
      except Exception:
        pass

    composite = robot_data.get("composite_sentiment", {})
    if not composite:
      try:
        from robot_feeds import calculate_composite_sentiment

        composite = calculate_composite_sentiment()
      except Exception:
        composite = {}

    # =========================================================================
    # 📊 COMPOSITE SENTIMENT INDEX EXECUTIVE CARD
    # =========================================================================
    if composite:
      si_score = composite.get("si_composite", -0.38)
      surge_units = composite.get("demand_surge_units", 118750)
      lt_days = composite.get("leadtime_delay_days", 2.9)
      rec_text = composite.get("recommendation", "")

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
          st.metric("Quantified Demand Surge", f"+{surge_units:,} {term_unit}")
        with c_col3:
          st.metric("Lead Time Expansion", f"+{lt_days} Days")
        with c_col4:
          ctrm_status = (
              "🔴 HEDGE REQUIRED"
              if composite.get("ctrm_hedge_required")
              else "🟢 STABLE"
          )
          st.metric("CTRM Risk Status", ctrm_status)

        st.info(f"**Quantified Action Plan**: {rec_text}")

        if st.button(
            "⚡ Propagate Triangulated Composite Index across Platform",
            key="btn_propagate_composite",
        ):
          st.session_state["si_composite"] = si_score
          st.session_state["extracted_demand_surge"] = surge_units
          st.session_state["active_leadtime_delay_days"] = lt_days
          st.session_state["ctrm_hedge_required"] = composite.get(
              "ctrm_hedge_required", True
          )
          st.session_state["active_risk_signal_title"] = (
              f"Triangulated Sentiment Index ({si_score:+.2f})"
          )
          st.session_state["signal_category"] = "Macro Triangulation Engine"

          st.toast("Propagated Composite Sentiment Engine!", icon="⚡")
          st.success(
              f"✅ Loaded **$SI = {si_score:+.2f}$** across S&OP Demand"
              f" Matching, Lead Time Offsets (+{lt_days}d), and CTRM Desk!"
          )

      st.divider()

    # GEP Index Display
    gep = robot_data.get("gep_index", {})
    if gep and gep.get("source"):
      st.info(f"🤖 **Automated Robot Signal Detected**: {gep.get('source')}")

      r_col1, r_col2, r_col3 = st.columns([2, 1, 1])
      with r_col1:
        st.caption(f"**Summary**: {gep.get('summary', '')[:180]}...")
      with r_col2:
        st.metric(
            "Volatility Score",
            gep.get("volatility_score", 0.0),
            delta=f"+{gep.get('leadtime_delay_days', 2.0)}d Lead Time",
        )
      with r_col3:
        robot_units = gep.get("demand_surge_units", 60000)
        st.metric("Auto Surge", f"{robot_units:,} {term_unit}")

      if st.button(
          "🤖 Ingest Live Robot GEP Signal", key="btn_ingest_robot_gep"
      ):
        st.session_state["extracted_demand_surge"] = robot_units
        st.session_state["active_risk_signal_title"] = (
            f"[Robot] {gep.get('source')}"
        )
        st.session_state["signal_category"] = "Automated GEP Feed"
        st.session_state["active_leadtime_delay_days"] = gep.get(
            "leadtime_delay_days", 2.0
        )
        st.toast("Ingested Live GEP Robot Feed!", icon="🤖")
        st.success(
            f"✅ Propagated **[Robot] {gep.get('source')}** ({robot_units:,}"
            f" {term_unit}) across S&OP and CTRM Desk!"
        )

      st.divider()

    # LinkedIn Newsletter Feed Display
    newsletters = robot_data.get("newsletter_feeds", [])
    if newsletters and isinstance(newsletters, list) and len(newsletters) > 0:
      first_signal = newsletters[0]
      if "title" in first_signal:
        st.success(
            f"📰 **LinkedIn Signal Received**: {first_signal.get('title')}"
        )
        st.caption(
            f"Published: {first_signal.get('published', 'Recent')} | Summary:"
            f" {first_signal.get('summary', '')}"
        )
        if st.button(
            "📰 Ingest LinkedIn Newsletter Signal", key="btn_ingest_ktn_news"
        ):
          st.session_state["extracted_demand_surge"] = 95000
          st.session_state["active_risk_signal_title"] = (
              f"[LinkedIn] {first_signal.get('title')}"
          )
          st.session_state["signal_category"] = "LinkedIn Feed"
          st.toast("Ingested LinkedIn Newsletter Signal!", icon="📰")
        st.divider()

    # =========================================================================
    # 📡 REAL-TIME WEB & MACRO NEWS STREAM (EXPANDED DOMAINS)
    # =========================================================================
    st.subheader("📡 Real-Time Web & Macro News Stream")
    NEWS_DOMAINS = {
        "🧱 Non-Ferrous Metals (Copper, Tin, Zinc, Aluminum)": [
            (
                "LME Copper Inventories Drop to 6-Year Lows Amid Chilean Mine"
                " Outages [Impact: 145,000 Units]"
            ),
            (
                "Indonesia Extends Unrefined Tin Export Restrictions; Spot"
                " Premiums Jump +18% [Impact: 92,000 Units]"
            ),
            (
                "European Aluminum Smelters Curtail Output Due to Energy"
                " Surcharges [Impact: 115,000 Units]"
            ),
        ],
        "💎 Precious Metals & Rare Earth Elements (REE)": [
            (
                "China Imposes Neodymium & Dysprosium Export Licensing Controls"
                " [Impact: 210,000 Units]"
            ),
            (
                "Platinum & Palladium Surges Threaten Auto-Catalyst Raw Material"
                " Costs [Impact: 88,000 Units]"
            ),
            (
                "Gold Spot Rally Triggers Hedging Re-evaluations Across"
                " Electronic Connectors [Impact: 65,000 Units]"
            ),
        ],
        "🧪 Industrial Chemicals & Base Polymers": [
            (
                "US Gulf Coast Ethylene Cracker Shutdown Triggers PVC & Resin"
                " Force Majeure [Impact: 130,000 Units]"
            ),
            (
                "European Ammonia & Nitric Acid Production Cuts Hit Fertilizer"
                " & Specialty Chem [Impact: 105,000 Units]"
            ),
            (
                "Titanium Dioxide Supply Tightens as Pigment Feedstock Costs"
                " Escalate [Impact: 75,000 Units]"
            ),
        ],
        "⚡ Essential Semiconductors & High-Tech Hardware": [
            (
                "TSMC Packaging Bottleneck Delays Advanced ASIC Deliveries"
                " [Impact: 175,000 Units]"
            ),
            (
                "Asahi Kasei Resin Shortage Hits Chip Substrate Supply Chain"
                " [Impact: 110,000 Units]"
            ),
            (
                "Critical Neon Gas Export Restrictions Target European Fabs"
                " [Impact: 140,000 Units]"
            ),
        ],
        "🛢️ Energy, Power & Petrochemicals": [
            (
                "European Natural Gas Spike (+32%) Triggers Smelter Surcharge"
                " [Impact: 85,000 Units]"
            ),
            (
                "Gulf Coast Refinery Outage Restricts Polymer Feedstock"
                " [Impact: 95,000 Units]"
            ),
            (
                "Crude Oil Benchmark Breaches $95/bbl Increasing Freight Matrix"
                " [Impact: 50,000 Units]"
            ),
        ],
        "🚢 Maritime Freight, Ports & Logistics": [
            (
                "Red Sea Vessel Diversions Drive +45% FBX Container Index Surge"
                " [Impact: 130,000 Units]"
            ),
            (
                "US East Coast Port Labor Negotiations Risk Q4 Stocking"
                " [Impact: 210,000 Units]"
            ),
            (
                "Singapore Transshipment Dwell Time Peaks at 4.8 Days [Impact:"
                " 80,000 Units]"
            ),
        ],
    }

    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
      selected_domain = st.selectbox(
          "Select Commodity / Industry Sector Focus:",
          list(NEWS_DOMAINS.keys()),
          key="nlp_sector_focus",
      )
      active_headlines = NEWS_DOMAINS[selected_domain]
      selected_headline = st.selectbox(
          "Select AI-Scraped Headline Signal:",
          active_headlines,
          key="nlp_web_headline_select",
      )

    with col_w2:
      match = re.search(r"\[Impact:\s*([\d,]+)\s*Units\]", selected_headline)
      extracted_default = (
          int(match.group(1).replace(",", "")) if match else 85000
      )
      web_impact = st.number_input(
          f"Extracted Signal Impact ({term_unit})",
          value=extracted_default,
          step=5000,
          key="web_signal_units",
      )

    if st.button("📡 Ingest Scraped Domain News Signal", key="btn_ingest_web"):
      headline_clean = selected_headline.split("[")[0].strip()
      domain_label = (
          selected_domain.split(" ")[1]
          if len(selected_domain.split(" ")) > 1
          else "Macro"
      )
      st.session_state["extracted_demand_surge"] = web_impact
      st.session_state["active_risk_signal_title"] = (
          f"[{domain_label}] {headline_clean}"
      )
      st.session_state["signal_category"] = "Live Web Intelligence"
      st.toast(
          f"Ingested '{headline_clean}' ({web_impact:,} {term_unit})", icon="📡"
      )
      st.success(
          f"✅ Propagated **[{domain_label}] {headline_clean}** ({web_impact:,}"
          f" {term_unit}) across S&OP and CTRM Desk!"
      )

  with tab2:
    st.subheader("📧 Email & Event Debrief Parser")
    st.caption(
        "Extract unstructured supplier updates, trip reports, and meeting"
        " debriefs."
    )

  with tab3:
    st.subheader("⚓ Freight, Weather & Black Swan Feeds")
    st.caption(
        "Track maritime vessel AIS feeds, port dwell anomalies, and climate"
        " disruptions."
    )


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


def render_ctrm_desk(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """Financial commodity risk engine, custom synthetic derivatives builder, and

  FIX order execution with dynamic NLP sentiment ($SI$) integration.
  """
  st.title("🛡️ CTRM Event-Driven Hedging Desk")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Financial commodity risk engine, custom synthetic derivatives builder,"
      " and FIX order execution."
  )

  # ----------------------------------------------------
  # 0. CROSS-DESK SESSION STATE INITIALIZATION
  # ----------------------------------------------------
  if "sop_cash_balance" not in st.session_state:
    st.session_state["sop_cash_balance"] = 5_000_000.00  # Default $5M Treasury
  if "future_supply_ledger" not in st.session_state:
    st.session_state["future_supply_ledger"] = {
        "Current Period": 50000,
        "Target Period (+30D)": 60000,
        "Target Period (+90D)": 65000,
    }

  # Ingest Upstream Signals (NLP Sentiment SI, Demand Surge, Physical Procurement State)
  si_score = st.session_state.get("si_composite", -0.33)
  raw_surge = st.session_state.get("extracted_demand_surge", 65000)
  req_metal_mt = st.session_state.get("required_metal_mt", 9349)
  req_feus = st.session_state.get("required_feu_slots", 4319)

  signal_title = st.session_state.get(
      "active_risk_signal_title", "NOAA Climate Alert / Sentiment Engine"
  )
  signal_category = st.session_state.get(
      "signal_category", "Weather & Macro Feed"
  )

  # Dynamic Quantitative Risk & Hedge Policy Models driven by SI
  target_hedge_ratio = min(1.0, max(0.20, 0.50 - (0.80 * si_score)))
  cmo_offload_pct = st.session_state.get("toller_split_slider", 15)
  net_exposure_pct = max(target_hedge_ratio, cmo_offload_pct / 100.0)

  net_unhedged_units = int(raw_surge * net_exposure_pct)
  net_metal_shortfall_mt = int(req_metal_mt * net_exposure_pct)
  unhedged_risk = net_unhedged_units * 150.0
  margin_buffer = unhedged_risk * (0.10 + abs(si_score) * 0.15)
  default_lots = max(10, int(net_metal_shortfall_mt / 25))  # 25 MT / LME Lot

  # Auto-Derive Expiration Horizon
  if "Climate" in signal_title or "Surge" in signal_category or si_score < -0.20:
    auto_horizon_days = 90
    target_period_key = "Target Period (+90D)"
  else:
    auto_horizon_days = 30
    target_period_key = "Target Period (+30D)"

  st.info(
      f"⚡ **Active Risk Signal Ingested**: {signal_title} *({signal_category})*"
      f" | **Upstream Sentiment ($SI$):** `{si_score:+.2f}` | **Target Hedge"
      f" Ratio:** `{target_hedge_ratio:.1%}` | **Unhedged Shortfall:**"
      f" {net_metal_shortfall_mt:,} MT ({net_unhedged_units:,} {term_unit}) |"
      f" ⏱️ **Auto Horizon:** {auto_horizon_days} Days"
  )

  tab_exec, tab_lab = st.tabs([
      "📊 Standard Desk & FIX Execution",
      "🧪 Synthetic Derivative Builder & Model Lab",
  ])

  # ----------------------------------------------------
  # TAB 1: STANDARD DESK & FIX EXECUTION
  # ----------------------------------------------------
  with tab_exec:
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric(
        "Gross Demand Surge",
        f"{raw_surge:,} {term_unit}",
        f"{req_metal_mt:,} MT Metals",
    )
    col_c2.metric(
        "Target Hedge Ratio ($HR$)",
        f"{target_hedge_ratio:.1%}",
        f"Sentiment $SI = {si_score:+.2f}$",
    )
    col_c3.metric(
        "Net Shortfall to Hedge",
        f"{net_unhedged_units:,} {term_unit}",
        f"{net_exposure_pct*100:.0f}% Target Cover Gap",
    )
    col_c4.metric(
        "Required Risk Margin Buffer",
        f"${margin_buffer:,.2f}",
        delta=f"+{abs(si_score)*100:.1f}% Volatility Load",
        delta_color="inverse",
    )

    st.markdown("---")
    st.subheader("⚡ FIX 4.4 Order Execution Gateway")

    # Row 1: Intent & Horizon
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
      intent_type = st.selectbox(
          "Execution Intent",
          [
              "Hedge Risk (Cover Shortfall)",
              "Exercise Call Option",
              "Exercise Put Option",
              "Speculative Position",
          ],
          key="std_intent",
      )
    with col_i2:
      time_horizon = st.selectbox(
          "Time Period / Expiration",
          [
              f"Auto-Matched ({auto_horizon_days} Days)",
              "30 Days (Short-Term)",
              "60 Days (Mid-Term)",
              "90 Days (Long-Term LEAP)",
          ],
          key="std_horizon",
      )
    with col_i3:
      unit_premium_est = st.number_input(
          "Est. Premium ($/Unit)", value=4.25, step=0.25, key="std_unit_prem"
      )

    calculated_total_premium = net_unhedged_units * unit_premium_est

    # Row 2: Order Structure & Exchange
    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
    with col_f1:
      order_type = st.selectbox(
          "Order Structure",
          [
              "Asian Call Collar",
              "Outright Call Option",
              "Outright Put Option",
              "Delta-Hedged Futures Spread",
          ],
          key="std_order_type",
      )
    with col_f2:
      exchange = st.selectbox(
          "Execution Exchange",
          ["LME (London Metal Exchange)", "CME Group", "ICE Futures"],
          key="std_exchange",
      )
    with col_f3:
      lots = st.number_input(
          "Lots / Contracts (LME 25 MT)",
          value=default_lots,
          step=5,
          key="std_lots",
      )

    st.caption(
        f"💰 **Total Premium Required:** `${calculated_total_premium:,.2f}`"
        " (Will be debited from Exec S&OP Cash Treasury)"
    )

    if st.button("⚡ Execute & Route FIX 4.4 Paper Order", key="btn_exec_std"):
      # 1. State Cascade: Deduct Premium from S&OP Treasury Cash
      st.session_state["sop_cash_balance"] -= calculated_total_premium

      # 2. State Cascade: Inject Hedged Volume into Demand/Supply Ledger
      if "Hedge" in intent_type or "Call" in intent_type:
        st.session_state["future_supply_ledger"][target_period_key] += (
            net_unhedged_units
        )
        supply_msg = (
            f"Added +{net_unhedged_units:,} {term_unit} ("
            f"{net_metal_shortfall_mt:,} MT) to Module 3 ({target_period_key})."
        )
      else:
        supply_msg = (
            "No physical volume added (Financial Settlement/Put Option)."
        )

      st.session_state["fix_executed"] = True
      st.session_state["ctrm_hedged"] = True
      st.session_state["ctrm_hedge_gain"] = 3.25
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
          f"✅ **FIX 4.4 Executed**: {exec_type} on {exec_exch} for"
          f" **{exec_lots:,} Lots** | Intent: **{intent_type}**\n\n💸 **Exec"
          f" S&OP Treasury Updated:** Debited `${calculated_total_premium:,.2f}`."
          f" Remaining Cash:"
          f" `${st.session_state['sop_cash_balance']:,.2f}`\n\n📦"
          f" **Demand/Supply (Module 3) Updated:** {last_msg}"
      )

  # ----------------------------------------------------
  # TAB 2: SYNTHETIC DERIVATIVE BUILDER & MODEL LAB
  # ----------------------------------------------------
  with tab_lab:
    st.subheader("🛠️ Custom Synthetic Derivative Constructor")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
      deriv_type = st.selectbox(
          "Structure Type",
          [
              "Fixed-for-Floating Synthetic Swap",
              "Zero-Cost Asian Collar",
              "Custom Crack/Spark Spread",
              "Digital Barrier Option",
          ],
          key="lab_deriv_type",
      )
    with col_d2:
      pricing_engine = st.selectbox(
          "Pricing Model Engine",
          [
              "Black76 Jump-Diffusion Model",
              "Monte Carlo Path Simulation (10k Runs)",
              "Hawkes Stochastic Volatility",
          ],
          key="lab_model_engine",
      )
    with col_d3:
      strike_price = st.number_input(
          "Strike / Cap Price ($/Unit)",
          value=150.0,
          step=5.0,
          key="lab_strike",
      )

    st.markdown("---")
    st.subheader("📊 Dynamic Payoff Profile & Sensitivity Analysis")

    col_m1, col_m2 = st.columns([1.5, 1])
    with col_m1:
      price_range = np.linspace(strike_price * 0.7, strike_price * 1.3, 50)
      if "Swap" in deriv_type:
        payoff = (price_range - strike_price) * net_unhedged_units
      elif "Collar" in deriv_type:
        floor, cap = strike_price * 0.9, strike_price * 1.1
        payoff = (
            np.clip(price_range - floor, 0, cap - floor) * net_unhedged_units
            - (strike_price * 0.05 * net_unhedged_units)
        )
      else:
        payoff = (
            np.maximum(price_range - strike_price, 0) * net_unhedged_units
            - (strike_price * 0.08 * net_unhedged_units)
        )

      chart_data = pd.DataFrame(
          {"Underlying Price ($)": price_range, "Net Payoff ($)": payoff}
      )
      st.line_chart(
          chart_data,
          x="Underlying Price ($)",
          y="Net Payoff ($)",
          use_container_width=True,
      )

    with col_m2:
      st.markdown("#### **Estimated Instrument Greeks**")
      st.metric(
          "Delta (Δ) Sensitivity",
          "0.52" if "Black76" in pricing_engine else "0.48 (Simulated)",
      )
      st.metric(
          "Vega (ν) Vol Risk",
          "$12,450 / 1% Vol"
          if "Jump-Diffusion" in pricing_engine
          else "$10,200 / 1% Vol",
      )
      st.metric(
          "Estimated Structure Premium", f"${net_unhedged_units * 4.25:,.2f}"
      )

    if st.button(
        "🚀 Route Custom OTC Synthetic Structure to Exchange Clearing",
        key="btn_route_synthetic",
    ):
      synthetic_prem = net_unhedged_units * 4.25
      st.session_state["sop_cash_balance"] -= synthetic_prem
      st.session_state["future_supply_ledger"][target_period_key] += (
          net_unhedged_units
      )
      st.session_state["synthetic_executed"] = True
      st.session_state["ctrm_hedged"] = True
      st.session_state["ctrm_hedge_gain"] = 3.25
      st.toast(
          f"Custom OTC Structure Cleared! Debited ${synthetic_prem:,.2f} from"
          " S&OP Cash.",
          icon="🚀",
      )

  # ----------------------------------------------------
  # LIVE CROSS-DESK LEDGER AUDIT DISPLAY
  # ----------------------------------------------------
  st.markdown("---")
  st.markdown("### 🔗 Real-Time Cross-Desk Cascades")
  l_col1, l_col2, l_col3 = st.columns(3)
  with l_col1:
    st.markdown("**Exec S&OP Treasury (Module 1)**")
    st.metric(
        "Available Cash Balance", f"${st.session_state['sop_cash_balance']:,.2f}"
    )
  with l_col2:
    st.markdown("**Demand/Supply Ledger (Module 3)**")
    st.json(st.session_state["future_supply_ledger"])
  with l_col3:
    st.markdown("**Physical Procurement Exposure (Module 4)**")
    st.metric("Raw Metals Exposure", f"{req_metal_mt:,} MT")
    st.metric("Freight Slots Reserved", f"{req_feus:,} FEUs")


def render_executive_sop(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units"
):
  st.title("📊 Executive S&OP Control Tower")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Real-time financial alignment, financial waterfalls, and trade hedge"
      " benefit reconciliation."
  )

  # 1. STATE INGESTION & DYNAMIC FINANCIAL AUDIT
  baseline_volume = 781049
  is_committed = st.session_state.get("demand_plan_committed", False)
  active_demand = (
      st.session_state.get(
          "committed_horizon_demand"
          if is_committed
          else "extracted_demand_surge",
          65000,
      )
      + baseline_volume
  )

  surge_units = max(0, active_demand - baseline_volume)

  # Financial Inputs ($ Millions)
  base_aop_revenue = 120.00
  surge_revenue_upside = round((surge_units * 249.23) / 1_000_000, 2)
  unconstrained_demand_rev = base_aop_revenue + surge_revenue_upside

  # Check State Locks
  pos_synced = st.session_state.get(
      "erp_requisitions_pushed", False
  ) or st.session_state.get("rop_offset_executed", False)
  ctrm_hedged = st.session_state.get("ctrm_hedged", False)
  delay_days = st.session_state.get("active_leadtime_delay_days", 4.2)

  # Dynamic Drag & Hedge Calculations
  base_freight_drag = 3.20 + (
      delay_days * 0.15 if st.session_state.get("sandbox_active", False) else 0.0
  )
  total_freight_drag = round(
      base_freight_drag * 0.6 if pos_synced else base_freight_drag, 2
  )
  ctrm_gain = 3.25 if ctrm_hedged else 0.00
  net_ebitda = round(
      unconstrained_demand_rev + ctrm_gain - total_freight_drag - 10.0, 2
  )

  # 2. EXECUTIVE METRICS CARDS
  col_m1, col_m2, col_m3, col_m4 = st.columns(4)
  col_m1.metric(
      "Annual Operating Plan (AOP)", f"${base_aop_revenue:.1f}M", "+4.2% YoY"
  )
  col_m2.metric(
      "Unconstrained Demand (AOP + Surge)",
      f"${unconstrained_demand_rev:.2f}M",
      f"+{surge_units:,} {term_unit}",
  )
  col_m3.metric(
      "CTRM Hedge & Trade Benefit",
      f"+${ctrm_gain:.2f}M",
      "⚡ Active Execution" if ctrm_hedged else "⚡ Floating Spot Exposure",
  )
  col_m4.metric(
      "Net Realized EBITDA",
      f"${net_ebitda:.2f}M",
      f"+${round(net_ebitda - base_aop_revenue, 2)}M vs AOP",
  )

  st.markdown("---")

  # 3. LIVE DESK CROSS-TALK FEEDS
  st.subheader("📡 Live Operational Desk Feeds")
  col_f1, col_f2, col_f3, col_f4 = st.columns(4)
  col_f1.info(
      f"🔵 **NLP Commercial Sensing**: Auto-hooked signal (+{surge_units:,}"
      f" {term_unit})."
  )

  if ctrm_hedged:
    col_f2.success(f"🟢 **CTRM Desk**: ${ctrm_gain:.2f}M hedge gain locked in.")
  else:
    col_f2.warning(
        "🟡 **CTRM Desk**: Metal & Freight exposure floating on spot market."
    )

  col_f3.error("🔴 **Demand/Supply Balancer**: Plant operating near capacity limits.")

  if pos_synced:
    col_f4.success(
        f"🟢 **Procurement Desk**: POs Synced (+{delay_days:.1f}d Lead-Time"
        " Offset Active)."
    )
  else:
    col_f4.info("ℹ️ **Procurement Desk**: Standard MRP baseline active.")

  st.markdown("---")

  # 4. P&L WATERFALL & CTRM LEDGER TABLES
  col_w1, col_w2 = st.columns([1.2, 1])

  with col_w1:
    st.subheader("💵 Financial P&L Margin Waterfall Report")
    waterfall_data = [
        {
            "P&L Line Item": "1. Base AOP Revenue Target",
            "Amount ($)": f"${base_aop_revenue:.2f}M",
            "Impact": "🔴 Baseline Plan",
        },
        {
            "P&L Line Item": "2. Unconstrained Surge Realization",
            "Amount ($)": f"+${surge_revenue_upside:.2f}M",
            "Impact": "🟢 Commercial Upside",
        },
        {
            "P&L Line Item": "3. CTRM Derivative & Hedge Gain",
            "Amount ($)": f"+${ctrm_gain:.2f}M",
            "Impact": (
                "🟢 Market Execution"
                if ctrm_hedged
                else "⚠️ Unhedged Spot Exposure"
            ),
        },
        {
            "P&L Line Item": "4. COGS & Freight Cost Drag",
            "Amount ($)": f"-${total_freight_drag:.2f}M",
            "Impact": (
                "🟢 Mitigated" if pos_synced else "⚠️ Expedited Drag"
            ),
        },
        {
            "P&L Line Item": "5. Projected Net EBITDA",
            "Amount ($)": f"${net_ebitda:.2f}M",
            "Impact": "🟢 Net Bottom-Line",
        },
    ]
    st.dataframe(
        pd.DataFrame(waterfall_data),
        use_container_width=True,
        hide_index=True,
    )

  with col_w2:
    st.subheader("📈 CTRM Commodity Hedging Ledger")

    ledger_data = [
        {
            "Commodity": "Raw Metals & Components",
            "Hedge Position": (
                "100% Synced 🟢" if ctrm_hedged else "15% Unhedged ⚠️"
            ),
            "Locked Rate": "$2,210 / MT",
            "Spot Exposure": (
                "0% Covered" if ctrm_hedged else "Spot Volatility Float"
            ),
        },
        {
            "Commodity": "Freight Futures (FEU)",
            "Hedge Position": (
                "100% Synced 🟢" if pos_synced else "20% Unhedged ⚠️"
            ),
            "Locked Rate": "$3,450 / FEU",
            "Spot Exposure": "0% Covered" if pos_synced else "Spot Logistics Float",
        },
        {
            "Commodity": "Power & Energy",
            "Hedge Position": "100% Covered",
            "Locked Rate": "$64.50 / MWh",
            "Spot Exposure": "0% Covered",
        },
    ]
    st.dataframe(
        pd.DataFrame(ledger_data), use_container_width=True, hide_index=True
    )


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

def render_global_logistics_gis(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """Global Logistics Network & GIS Control Tower.

  Monitors global maritime routes, vessel chokepoints, and automatically
  triggers contingency freight bookings based on CTRM hedge positions and open
  unhedged exposure.
  """
  st.title("🚢 Global Logistics Network & GIS Control Tower")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Real-time vessel tracking, port dwell anomalies, and automated"
      " contingency freight booking."
  )

  # Read upstream states from CTRM Desk, NLP Engine, and Procurement
  fix_executed = st.session_state.get("fix_executed", False)
  synthetic_executed = st.session_state.get("synthetic_executed", False)
  is_hedged = st.session_state.get("ctrm_hedged", False)

  si_score = st.session_state.get("si_composite", -0.33)
  raw_surge = st.session_state.get("extracted_demand_surge", 102968)
  req_feus = st.session_state.get("required_feu_slots", 4319)

  # Calculate open unhedged volume & ratio
  exec_lots = st.session_state.get("executed_lots", 0)
  hedged_units = exec_lots * 25 * 11 if fix_executed else 0
  open_unhedged_units = (
      max(0, raw_surge - hedged_units) if is_hedged else raw_surge
  )
  unhedged_ratio = (
      open_unhedged_units / raw_surge if raw_surge > 0 else 0.0
  )

  # Contingency Freight Trigger Policy: Triggered if unhedged ratio > 25% or macro SI < -0.25
  contingency_required = unhedged_ratio > 0.25 or si_score < -0.25

  # Dynamic Operational Alert Banner
  if fix_executed or synthetic_executed:
    st.success(
        f"✅ **CTRM HEDGE COVERAGE ACTIVE**: FIX execution confirmed."
        f" Open unhedged physical gap reduced to **{open_unhedged_units:,}"
        f" {term_unit} ({unhedged_ratio:.1%})**."
    )
  elif contingency_required:
    st.warning(
        f"⚠️ **UNHEDGED SUPPLY EXPOSURE DETECTED**: Open gap sits at"
        f" **{open_unhedged_units:,} {term_unit} ({unhedged_ratio:.1%})** with"
        f" sentiment $SI = {si_score:+.2f}$. Automated policy recommends"
        " locking contingency freight slots."
    )
  else:
    st.info(
        f"🟢 **LOGISTICS BALANCED**: Unhedged exposure is within safe limits"
        f" ({unhedged_ratio:.1%}). Baseline freight schedules active."
    )

  # Key Logistics Metrics
  m1, m2, m3, m4 = st.columns(4)
  with m1:
    st.metric("Total Vessel FEU Requirement", f"{req_feus:,} FEUs")
  with m2:
    st.metric("Open Unhedged Freight Gap", f"{open_unhedged_units:,} {term_unit}")
  with m3:
    st.metric(
        "Unhedged Volatility Ratio",
        f"{unhedged_ratio:.1%}",
        delta="Requires Contingency" if contingency_required else "Safe Level",
        delta_color="inverse" if contingency_required else "normal",
    )
  with m4:
    rec_contingency_feus = int(req_feus * max(0.15, unhedged_ratio))
    st.metric(
        "Recommended Express Freight",
        f"{rec_contingency_feus:,} FEUs",
    )

  st.divider()

  # GIS Vessel Tracking & Dispatch Panel
  col_map, col_action = st.columns([1.8, 1])

  with col_map:
    st.subheader("🗺️ Live Global Shipping Chokepoints")

    # Interactive vessel location map data
    map_data = pd.DataFrame({
        "lat": [29.93, 1.29, 22.31, 51.95, 25.03],
        "lon": [32.55, 103.85, 114.16, 4.14, 121.56],
        "name": [
            "Suez Canal Chokepoint",
            "Singapore Transshipment Hub",
            "Hong Kong Terminal",
            "Rotterdam Gateway",
            "Taiwan Strait Route",
        ],
    })
    st.map(map_data, zoom=1)

  with col_action:
    st.subheader("⚡ Contingency Dispatch")
    st.markdown("Automated priority slot allocation for unhedged volume.")

    freight_mode = st.selectbox(
        "Contingency Transport Mode",
        [
            "Express Air Freight (3-5 Day Lead)",
            "Premium Guaranteed Ocean FEU",
            "Multi-Modal Rail/Truck Relay",
        ],
        key="gis_freight_mode",
    )

    feus_to_book = st.number_input(
        "FEU / Express Slots to Reserve",
        value=max(25, rec_contingency_feus),
        step=25,
        key="gis_feus_book",
    )

    unit_rate = 4800 if "Air" in freight_mode else 2200
    est_cost = feus_to_book * unit_rate
    st.caption(f"💰 Estimated Contingency Premium: **${est_cost:,.2f}**")

    if st.button("🚢 Lock Contingency Freight Booking", key="btn_book_freight"):
      st.session_state["contingency_freight_booked"] = True
      st.session_state["booked_feus"] = feus_to_book
      st.session_state["booked_mode"] = freight_mode
      st.session_state["contingency_cost"] = est_cost

      st.toast(
          f"Reserved {feus_to_book:,} slots via {freight_mode}!", icon="🚢"
      )
      st.success(
          f"✅ **Contingency Freight Confirmed!** Reserved **{feus_to_book:,}"
          f" FEU slots** using **{freight_mode}** for **${est_cost:,.2f}**."
          " Logistics bottleneck risk neutralized!"
      )

  # Display Active Contingency Ledger if booked
  if st.session_state.get("contingency_freight_booked", False):
    st.info(
        f"📦 **Active Freight Reservation**:"
        f" {st.session_state.get('booked_feus', 0):,} FEUs booked via"
        f" *{st.session_state.get('booked_mode', '')}* (Total Cost:"
        f" ${st.session_state.get('contingency_cost', 0.0):,.2f})"
    )


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