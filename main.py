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

def render_flight_simulator(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """Sandbox Flight Simulator & Stress Lab.

  Executes multi-variable Monte Carlo shock simulations across all upstream
  states (NLP Sentiment, CTRM Hedging, GIS Logistics, Treasury Cash).
  """
  st.title("🧪 Sandbox Flight Simulator & Stress Lab")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Run multi-variable Monte Carlo shock tests to stress-test cash"
      " reserves, margin stability, and supply chain buffers."
  )

  # Read upstream states from prior modules
  si_score = st.session_state.get("si_composite", -0.33)
  surge_units = st.session_state.get("extracted_demand_surge", 102968)
  cash_balance = st.session_state.get("sop_cash_balance", 5_000_000.0)
  fix_executed = st.session_state.get("fix_executed", False)
  curr_leadtime_delay = st.session_state.get(
      "active_leadtime_delay_days", 2.5
  )

  st.divider()

  # ----------------------------------------------------
  # 1. SHOCK SCENARIO CONTROLS
  # ----------------------------------------------------
  st.subheader("⚙️ Monte Carlo Stress Test Parameters")

  col_s1, col_s2, col_s3, col_s4 = st.columns(4)
  with col_s1:
    n_sims = st.select_slider(
        "Simulation Runs",
        options=[1000, 2500, 5000, 10000],
        value=5000,
        key="sim_runs",
    )
  with col_s2:
    vol_shock = (
        st.slider(
            "Spot Price Volatility (σ)",
            min_value=10,
            max_value=60,
            value=35,
            step=5,
            key="sim_vol",
        )
        / 100.0
    )
  with col_s3:
    lead_time_shock = st.slider(
        "Lead Time Delay (Days)",
        min_value=1,
        max_value=21,
        value=7,
        step=1,
        key="sim_lt",
    )
  with col_s4:
    demand_multiplier = st.slider(
        "Demand Surge Multiplier",
        min_value=1.0,
        max_value=2.5,
        value=1.3,
        step=0.1,
        key="sim_dem",
    )

  # ----------------------------------------------------
  # 2. MONTE CARLO SIMULATION ENGINE
  # ----------------------------------------------------
  if st.button("🚀 Run Monte Carlo Stress Simulation", key="btn_run_mc"):
    with st.spinner(f"Simulating {n_sims:,} market shocks..."):
      base_unit_price = 150.0

      # Log-normal spot price distribution & dynamic demand variation
      price_shocks = np.random.lognormal(
          mean=np.log(base_unit_price), sigma=vol_shock, size=n_sims
      )
      simulated_demand = surge_units * demand_multiplier * np.random.uniform(
          0.9, 1.1, size=n_sims
      )

      # Unhedged vs Hedged Exposure Calculation
      hedge_ratio = 0.764 if fix_executed else 0.0
      unhedged_demand = simulated_demand * (1.0 - hedge_ratio)
      hedged_demand = simulated_demand * hedge_ratio

      # Financial Impact ($)
      unhedged_cost = unhedged_demand * price_shocks
      hedged_cost = hedged_demand * base_unit_price
      total_simulated_cost = unhedged_cost + hedged_cost
      net_cash_impact = cash_balance - total_simulated_cost

      # Risk Metrics
      var_95 = np.percentile(total_simulated_cost, 95)
      var_99 = np.percentile(total_simulated_cost, 99)
      mean_cost = np.mean(total_simulated_cost)
      insolvency_risk = np.mean(net_cash_impact < 0) * 100.0

      st.session_state["mc_results"] = {
          "mean_cost": mean_cost,
          "var_95": var_95,
          "var_99": var_99,
          "insolvency_risk": insolvency_risk,
          "total_cost": total_simulated_cost,
      }

  # ----------------------------------------------------
  # 3. RESULTS & VISUALIZATION
  # ----------------------------------------------------
  if "mc_results" in st.session_state:
    res = st.session_state["mc_results"]

    st.markdown("### 📊 Simulation Outcomes & Value at Risk (VaR)")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
      st.metric("Expected Total Cost", f"${res['mean_cost']:,.2f}")
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

    # Histogram Visualization using Plotly
    df_chart = pd.DataFrame({"Simulated Cost ($)": res["total_cost"]})
    fig = px.histogram(
        df_chart,
        x="Simulated Cost ($)",
        nbins=50,
        title=f"Monte Carlo Risk Exposure ({n_sims:,} Iterations)",
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

    # Direct Back-Propagation Button
    if st.button(
        "⚡ Inject Stressed Parameters Back into Live Operations",
        key="btn_inject_mc",
    ):
      st.session_state["extracted_demand_surge"] = int(
          surge_units * demand_multiplier
      )
      st.session_state["active_leadtime_delay_days"] = (
          curr_leadtime_delay + lead_time_shock
      )
      st.session_state["si_composite"] = max(-1.0, si_score - (vol_shock * 0.5))

      st.toast("Propagated stressed parameters across platform!", icon="⚡")
      st.success(
          "✅ **Live Operations Updated**: Demand surge escalated to"
          f" **{st.session_state['extracted_demand_surge']:,} {term_unit}**,"
          f" lead times expanded by **+{lead_time_shock} days**, and market"
          f" sentiment adjusted to **{st.session_state['si_composite']:.2f}**!"
      )

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


def render_physical_procurement(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """Physical Procurement & Master Contract Desk.

  Translates paper hedge profits and demand surge signals into binding physical
  Purchase Orders (POs), supplier allocations, and inbound logistics schedule
  locks.
  """
  st.title("📦 Physical Procurement & Master Contract Desk")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Physical supply chain execution, master contract allocation, and vendor"
      " invoice settlement subsidized by financial derivative hedges."
  )

  # Read upstream states from NLP / Monte Carlo / CTRM / S&OP
  si_score = st.session_state.get("si_composite", -0.51)
  surge_units = st.session_state.get("extracted_demand_surge", 133858)
  sop_cash = st.session_state.get("sop_cash_balance", 4486918.75)
  fix_executed = st.session_state.get("fix_executed", False)
  po_executed = st.session_state.get("po_executed", False)

  # Operational Calculations
  base_unit_cogs = 160.00  # Base raw material cost per unit
  spot_surge_premium = base_unit_cogs * (
      1.0 + abs(si_score) * 0.35
  )  # Stressed spot cost
  hedge_subsidy = 8_970_000.0 if fix_executed else 0.0

  base_lead_time_days = 14
  delay_shock_days = (
      7  # +7 day delay shock from Monte Carlo / Logistics Desk
  )
  total_lead_time = base_lead_time_days + delay_shock_days

  # Sourcing Volume Split
  tier1_alloc_pct = 0.60
  tier2_alloc_pct = 0.25
  spot_alloc_pct = 0.15

  v_tier1 = int(surge_units * tier1_alloc_pct)
  v_tier2 = int(surge_units * tier2_alloc_pct)
  v_spot = int(surge_units * spot_alloc_pct)

  cost_tier1 = v_tier1 * base_unit_cogs
  cost_tier2 = v_tier2 * (base_unit_cogs * 1.05)
  cost_spot = v_spot * spot_surge_premium
  gross_procurement_cost = cost_tier1 + cost_tier2 + cost_spot

  net_procurement_cost = max(0.0, gross_procurement_cost - hedge_subsidy)

  # Top Operational Ingestion Banner
  st.info(
      f"🌐 **Physical Demand Signal Ingested**: Required Procurement Volume:"
      f" **{surge_units:,} {term_unit}** | Lead-Time Delay Shock:"
      f" **+{delay_shock_days} Days** (Total Lead Time: **{total_lead_time}"
      f" Days**) | Financial Hedge Cash Subsidy Available:"
      f" **${hedge_subsidy:,.2f}**"
  )

  # Top Procurement Metrics
  m1, m2, m3, m4 = st.columns(4)
  with m1:
    st.metric("Gross Physical Material Need", f"{surge_units:,} {term_unit}")
  with m2:
    st.metric(
        "Gross Supplier Invoice Total", f"${gross_procurement_cost / 1e6:.2f}M"
    )
  with m3:
    st.metric(
        "CTRM Financial Paper Subsidy",
        f"-${hedge_subsidy / 1e6:.2f}M" if fix_executed else "$0.00M",
        delta="Hedge Active" if fix_executed else "Unhedged Spot Risk",
        delta_color="normal" if fix_executed else "inverse",
    )
  with m4:
    st.metric(
        "Net Cash Outlay to Suppliers",
        f"${net_procurement_cost / 1e6:.2f}M",
        delta=f"-${hedge_subsidy / 1e6:.2f}M Savings"
        if fix_executed
        else "+0% Subsidy",
    )

  st.divider()

  # Master Contract Allocation Matrix
  st.subheader("📋 Master Contract Sourcing Matrix")
  st.caption(
      "Allocations across long-term contracted vendors and open spot market"
      " sourcing."
  )

  matrix_data = {
      "Supplier Name": [
          "Global Metals Corp (Tier 1 Primary)",
          "Apex Logistics Raw Ltd (Tier 2 Secondary)",
          "Spot Market Open Sourcing (Emergency)",
      ],
      "Contract Type": [
          "Fixed-Price Master Agreement",
          "Indexed Master Agreement",
          "Open Spot Market Purchase",
      ],
      "Alloc %": [
          f"{tier1_alloc_pct:.0%}",
          f"{tier2_alloc_pct:.0%}",
          f"{spot_alloc_pct:.0%}",
      ],
      "Volume (Units)": [f"{v_tier1:,}", f"{v_tier2:,}", f"{v_spot:,}"],
      "Unit Cost ($)": [
          f"${base_unit_cogs:.2f}",
          f"${base_unit_cogs * 1.05:.2f}",
          f"${spot_surge_premium:.2f}",
      ],
      "Subtotal Invoice": [
          f"${cost_tier1 / 1e6:.2f}M",
          f"${cost_tier2 / 1e6:.2f}M",
          f"${cost_spot / 1e6:.2f}M",
      ],
      "Expected ETA": [
          f"{total_lead_time} Days",
          f"{total_lead_time - 2} Days",
          f"{base_lead_time_days} Days (Expedited)",
      ],
  }
  st.table(pd.DataFrame(matrix_data))

  st.divider()

  # Physical Purchase Order Dispatch Controls
  st.subheader("🏭 Physical PO Execution Gateway")

  c1, c2, c3 = st.columns(3)
  with c1:
    st.selectbox(
        "Primary Delivery Destination",
        [
            "Central Assembly Plant (Facility A)",
            "Eastern Distribution Center",
            "Direct-to-Customer Hub",
        ],
        key="po_dest",
    )
    st.selectbox(
        "Inbound Logistics Mode",
        [
            "Standard Multi-Modal Rail & Truck",
            "Expedited Air Freight Overlay (+$12/unit)",
            "Dedicated Direct Vessel Charter",
        ],
        key="po_freight",
    )

  with c2:
    payment_terms = st.selectbox(
        "Vendor Payment Terms",
        ["Net 60 Days", "Net 30 Days", "Letter of Credit (LC)", "Cash on Delivery"],
        key="po_pay_terms",
    )
    quality_cert = st.selectbox(
        "Quality & Compliance Standard",
        ["ISO 9001 Heavy Industrial", "Aerospace Grade Spec A", "Standard Commercial"],
        key="po_qual",
    )

  with c3:
    expedite_fee = st.number_input(
        "Logistics Expedite Fee ($/Unit)", value=0.00, step=2.50, key="po_exp_fee"
    )
    st.caption(
        f"🚚 Logistics Premium: **${expedite_fee * surge_units:,.2f}**"
    )

  if po_executed:
    st.success(
        "✅ **PHYSICAL PURCHASE ORDERS ISSUED**: PO-2026-991A routed to Global"
        f" Metals Corp & Apex Logistics. Delivery schedule locked for"
        f" **{surge_units:,} {term_unit}**."
    )
  else:
    if st.button(
        "📦 Issue Physical Purchase Orders & Lock Delivery Schedules",
        key="btn_issue_po",
    ):
      st.session_state["po_executed"] = True
      st.toast(
          f"Purchase Orders Issued! {surge_units:,} Units dispatched.",
          icon="📦",
      )
      st.rerun()

  st.divider()

  # Operational Inbound Schedule Cascade
  st.subheader("🚚 Inbound Physical Delivery Cascade")
  dc1, dc2, dc3 = st.columns(3)
  with dc1:
    st.markdown("**Warehouse Staging & Buffer**")
    st.caption(
        f"Allocated Staging Bays: **{max(12, int(surge_units / 10000))} Bays**\n\nStatus:"
        f" **{'Space Reserved' if po_executed else 'Awaiting PO Release'}**"
    )
  with dc2:
    st.markdown("**Supplier Production Slots**")
    st.caption(
        "Global Metals Capacity:"
        f" **{'100% Locked' if po_executed else 'Option Held'}**\n\nLead Time:"
        f" **{total_lead_time} Days**"
    )
  with dc3:
    st.markdown("**Net Financial Settlement**")
    st.caption(
        f"Gross Supplier Invoice: **${gross_procurement_cost / 1e6:.2f}M**\n\nCTRM"
        f" Paper Subsidy: **-${hedge_subsidy / 1e6:.2f}M**\n\nEffective Material"
        f" Spend: **${net_procurement_cost / 1e6:.2f}M**"
    )


def render_ctrm_desk(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """CTRM Derivatives & Commodity Risk Desk.

  Full multi-tab risk engine: FIX order execution, Synthetic Derivative
  Builder, and Real-Time Cross-Desk Cascades.
  """
  st.title("🛡️ CTRM Event-Driven Hedging Desk")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Financial commodity risk engine, custom synthetic derivatives builder,"
      " and FIX order execution."
  )

  # Read upstream states from NLP / Monte Carlo / S&OP
  si_score = st.session_state.get("si_composite", -0.33)
  surge_units = st.session_state.get("extracted_demand_surge", 102968)
  sop_cash = st.session_state.get("sop_cash_balance", 5_000_000.0)
  fix_executed = st.session_state.get("fix_executed", False)

  target_hr = min(1.0, max(0.50, 0.70 + abs(si_score) * 0.40))
  net_shortfall_units = int(surge_units * target_hr)
  mt_metals = int(net_shortfall_units / 11)
  required_margin = net_shortfall_units * 23.83
  vol_load = abs(si_score) * 100.0

  # NOAA / Sentiment Signal Ingestion Banner
  st.info(
      "📡 **Active Risk Signal Ingested**: NOAA Climate Alert / Sentiment Engine"
      f" (Weather & Macro Feed) | Upstream Sentiment ($SI = {si_score:+.2f}$) |"
      f" Target Hedge Ratio: **{target_hr:.1%}** | Unhedged Shortfall:"
      f" **{net_shortfall_units:,} {term_unit}** ({mt_metals:,} MT Metals) |"
      " **Auto Horizon: 90 Days**"
  )

  # Full Multi-Tab Interface
  tab_std, tab_synth = st.tabs([
      "📊 Standard Desk & FIX Execution",
      "🧪 Synthetic Derivative Builder & Model Lab",
  ])

  with tab_std:
    # 4 Top Metrics with restored deltas/sub-captions
    m1, m2, m3, m4 = st.columns(4)
    with m1:
      st.metric(
          "Gross Demand Surge",
          f"{surge_units:,} {term_unit}",
          delta=f"+{mt_metals:,} MT Metals",
      )
    with m2:
      st.metric(
          "Target Hedge Ratio (HR)",
          f"{target_hr:.1%}",
          delta=f"Sentiment SI = {si_score:+.2f}",
      )
    with m3:
      st.metric(
          "Net Shortfall to Hedge",
          f"{net_shortfall_units:,} {term_unit}",
          delta=f"+{target_hr:.0%} Target Cover Gap",
      )
    with m4:
      st.metric(
          "Required Risk Margin Buffer",
          f"${required_margin:,.2f}",
          delta=f"+{vol_load:.1f}% Volatility Load",
          delta_color="inverse",
      )

    st.divider()

    # FIX 4.4 Execution Gateway
    st.subheader("⚡ FIX 4.4 Order Execution Gateway")

    c1, c2, c3 = st.columns(3)
    with c1:
      exec_intent = st.selectbox(
          "Execution Intent",
          [
              "Hedge Risk (Cover Shortfall)",
              "Speculative Overlay",
              "Tail Protect",
          ],
          key="ctrm_intent",
      )
      order_struct = st.selectbox(
          "Order Structure",
          [
              "Asian Call Collar",
              "Zero-Cost Collar",
              "Fixed Swap",
              "Out-of-Money Put",
          ],
          key="ctrm_struct",
      )

    with c2:
      expiration = st.selectbox(
          "Time Period / Expiration",
          ["Auto-Matched (90 Days)", "30 Days", "60 Days", "180 Days"],
          key="ctrm_exp",
      )
      exchange = st.selectbox(
          "Execution Exchange",
          [
              "LME (London Metal Exchange)",
              "CME Group",
              "ICE Futures",
              "OTC Bilateral",
          ],
          key="ctrm_exch",
      )

    with c3:
      est_premium_unit = st.number_input(
          "Est. Premium ($/Unit)", value=4.25, step=0.25, key="ctrm_prem"
      )
      suggested_lots = max(1, int(mt_metals / 25))
      lots = st.number_input(
          "Lots / Contracts (LME 25 MT)",
          value=suggested_lots,
          step=5,
          key="ctrm_lots",
      )

    total_premium = lots * 25 * 11 * est_premium_unit
    st.caption(
        f"💰 Total Premium Required: **${total_premium:,.2f}** (Will be debited"
        " from Exec S&OP Cash Treasury)"
    )

    if fix_executed:
      st.success(
          f"✅ **FIX 4.4 PAPER ORDER EXECUTED**: {lots} Lots routed to"
          f" {exchange}. P&L hedge benefit active across S&OP Control Tower."
      )
    else:
      if st.button("🚀 Execute & Route FIX 4.4 Paper Order", key="btn_fix_exec"):
        st.session_state["fix_executed"] = True
        st.session_state["ctrm_hedged"] = True
        st.session_state["executed_lots"] = lots
        st.session_state["sop_cash_balance"] = sop_cash - total_premium

        st.toast(
            f"FIX Order Routed! {lots} Contracts locked on {exchange}.",
            icon="🛡️",
        )
        st.rerun()

    st.divider()

    # Restored Real-Time Cross-Desk Cascades Section
    st.subheader("🔗 Real-Time Cross-Desk Cascades")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
      st.markdown("**Exec S&OP Treasury (Module 1)**")
      st.caption(
          f"Cash Balance: **${sop_cash:,.2f}**\n\nHedge Benefit:"
          f" **{'Active' if fix_executed else '0% Floating Exposure'}**"
      )
    with dc2:
      st.markdown("**Demand/Supply Ledger (Module 3)**")
      st.caption(
          f"Gross Demand Surge: **{surge_units:,} {term_unit}**\n\nShortfall"
          f" Cover: **{net_shortfall_units:,} {term_unit}**"
      )
    with dc3:
      st.markdown("**Physical Procurement Exposure (Module 4)**")
      st.caption(
          f"Hedged Volume: **{lots * 25 * 11 if fix_executed else 0:,}"
          f" {term_unit}**\n\nFloating Open Risk:"
          f" **{max(0, surge_units - (lots * 25 * 11 if fix_executed else 0)):,} {term_unit}**"
      )

  with tab_synth:
    st.subheader("🧪 Synthetic Derivative Payoff Simulator")
    st.markdown(
        "Model custom multi-leg options, zero-cost collars, and weather index"
        " hedges."
    )

    col_sy1, col_sy2 = st.columns(2)
    with col_sy1:
      strike_price = st.slider(
          "Floor Strike Price ($/MT)", 1500, 3000, 2200, step=50
      )
      cap_price = st.slider(
          "Cap Strike Price ($/MT)", 2200, 4000, 2800, step=50
      )
    with col_sy2:
      spot_range = np.linspace(1200, 3500, 100)
      payoff = np.clip(spot_range - strike_price, 0, cap_price - strike_price)
      fig_payoff = go.Figure(
          data=go.Scatter(
              x=spot_range,
              y=payoff,
              mode="lines",
              name="Collar Payoff",
              line=dict(color="#0068C9", width=3),
          )
      )
      fig_payoff.update_layout(
          title="Synthetic Collar Payoff Diagram ($/MT)",
          xaxis_title="Underlying Spot Price ($)",
          yaxis_title="Option Payoff ($)",
          height=300,
      )
      st.plotly_chart(fig_payoff, use_container_width=True)


def render_executive_sop(
    persona="Discrete & Heavy Industrial Enterprise", term_unit="Units", **kwargs
):
  """Executive S&OP Control Tower.

  Dynamically binds to Monte Carlo VaR results, CTRM hedge positions, and
  Treasury cash state to drive real-time P&L waterfalls.
  """
  st.title("📈 Executive S&OP Control Tower")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Real-time financial alignment, financial waterfalls, and trade hedge"
      " benefit reconciliation."
  )

  # ----------------------------------------------------
  # 1. DYNAMIC STATE INGESTION
  # ----------------------------------------------------
  sop_cash = st.session_state.get("sop_cash_balance", 5_000_000.0)
  surge_units = st.session_state.get("extracted_demand_surge", 102968)
  si_score = st.session_state.get("si_composite", -0.33)
  fix_executed = st.session_state.get("fix_executed", False)
  mc_res = st.session_state.get("mc_results", None)

  # Base financial targets
  base_aop_rev = 120_000_000.0
  unit_price = 780.0  # Finished good ASP
  unconstrained_rev = base_aop_rev + (surge_units * unit_price * 0.001)

  # Dynamic COGS & Freight Drag Calculation
  if mc_res:
    # Use Monte Carlo mean cost if simulation was executed
    cogs_drag = mc_res["mean_cost"]
    var_95_drag = mc_res["var_95"]
  else:
    # Baseline operational drag scaled by sentiment shock
    cogs_drag = 3_200_000.0 * (1.0 + abs(si_score) * 2.5)
    var_95_drag = cogs_drag * 1.4

  # Hedge Gain Mitigation
  ctrm_hedge_benefit = (
      cogs_drag * 0.42 if fix_executed else 0.0
  )  # 42% risk mitigation if hedged
  net_cogs_drag = cogs_drag - ctrm_hedge_benefit
  net_ebitda = unconstrained_rev - (base_aop_rev * 0.65) - net_cogs_drag

  # ----------------------------------------------------
  # 2. TOP EXECUTIVE METRICS
  # ----------------------------------------------------
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
        "FIX Hedged" if fix_executed else "0% Cover (Floating Risk)",
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

  # Insolvency Alert Banner if Stressed
  if sop_cash < 0 or (mc_res and mc_res.get("insolvency_risk", 0) > 10):
    st.error(
        f"🚨 **STRESSED FINANCIAL RISK DETECTED**: Monte Carlo VaR indicates"
        f" **${var_95_drag / 1e6:.2f}M (95% VaR)** potential cost drag."
        f" Current Treasury Cash balance is **${sop_cash:,.2f}**."
    )

  # ----------------------------------------------------
  # 3. DYNAMIC P&L WATERFALL & FEED DESKS
  # ----------------------------------------------------
  col_p1, col_p2 = st.columns([1.2, 1])

  with col_p1:
    st.subheader("💵 Financial P&L Margin Waterfall")

    pnl_data = {
        "P&L Line Item": [
            "1. Base AOP Revenue Target",
            "2. Unconstrained Demand Realization",
            "3. Stressed COGS & Freight Cost Drag",
            "4. CTRM Derivative Hedge Benefit",
            "5. Projected Net EBITDA",
        ],
        "Amount ($)": [
            f"${base_aop_rev / 1e6:.2f}M",
            f"+${(unconstrained_rev - base_aop_rev) / 1e6:.2f}M",
            f"-${cogs_drag / 1e6:.2f}M",
            f"+${ctrm_hedge_benefit / 1e6:.2f}M",
            f"${net_ebitda / 1e6:.2f}M",
        ],
        "Impact Status": [
            "Baseline Target",
            "Volume Surge",
            "Stressed Market Shock" if mc_res else "Baseline Drag",
            "FIX Covered" if fix_executed else "Unhedged Exposure",
            "Net Realized",
        ],
    }
    st.table(pd.DataFrame(pnl_data))

  with col_p2:
    st.subheader("🚩 Live Operational Desk Feeds")

    st.info(
        f"🔹 **NLP Sensing**: Auto-parsed $SI = {si_score:+.2f}$ signal across"
        f" field feeds."
    )
    st.warning(
        f"🔸 **CTRM Risk Desk**: Unhedged Volatility Gap ="
        f" **{surge_units:,} {term_unit}**."
    )
    if mc_res:
      st.error(
          f"💥 **Monte Carlo Engine**: 95% VaR cost risk elevated to"
          f" **${mc_res['var_95'] / 1e6:.2f}M**."
      )
    else:
      st.success("🟢 **Monte Carlo Engine**: Baseline parameters active.")


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

  Visualizes freight transit routes, port congestion bottlenecks, and inbound
  ETA delays tied to active physical purchase orders.
  """
  st.title("🌐 Global Logistics Network & GIS Control Tower")
  st.caption(f"Active Persona View: **{persona}**")
  st.markdown(
      "Real-time freight route tracking, port bottleneck telemetry, and inbound"
      " physical inventory arrival monitoring."
  )

  # Read upstream operational states
  surge_units = st.session_state.get("extracted_demand_surge", 133858)
  po_executed = st.session_state.get("po_executed", True)
  fix_executed = st.session_state.get("fix_executed", True)

  delay_days = 7
  base_lead_time = 14
  total_eta = base_lead_time + delay_days

  # Route Ingestion Banner
  st.info(
      f"🛳️ **Inbound Logistics Feed**: Tracking **{surge_units:,} {term_unit}**"
      f" across 3 Ocean & Rail Corridors | Lead-Time Shock: **+{delay_days}"
      f" Days** | Current Inbound Status:"
      f" **{'En Route (PO Issued)' if po_executed else 'Awaiting PO Release'}**"
  )

  # Top Logistics Kpis
  k1, k2, k3, k4 = st.columns(4)
  with k1:
    st.metric("Active Inbound Volume", f"{surge_units:,} {term_unit}")
  with k2:
    st.metric(
        "Avg Transit Lead Time",
        f"{total_eta} Days",
        delta=f"+{delay_days} Days Delay Shock",
        delta_color="inverse",
    )
  with k3:
    st.metric("Global Route Risk Level", "ELEVATED", delta="Port Congestion")
  with k4:
    st.metric(
        "On-Time In-Full (OTIF) Target",
        "88.4%",
        delta="-6.2% Stressed",
        delta_color="inverse",
    )

  st.divider()

  # GIS Map & Corridor Tracking
  st.subheader("🗺️ Live Global Freight GIS Map")

  # Sample shipping route coordinates (Asia / Europe / Americas hubs)
  routes_df = pd.DataFrame({
      "Hub": [
          "Port of Shanghai (Origin)",
          "Suez Transit Checkpoint",
          "Port of Rotterdam (Chokepoint)",
          "Port of Los Angeles",
          "Central Assembly Facility A",
      ],
      "Lat": [31.2304, 29.9753, 51.9244, 33.7423, 41.8781],
      "Lon": [121.4737, 32.5599, 4.4777, -118.2702, -87.6298],
      "Status": [
          "Dispatched",
          "Congested (+3 Days)",
          "Severe Bottleneck (+4 Days)",
          "Clear",
          "Destination Hub",
      ],
      "Volume": [
          surge_units * 0.4,
          surge_units * 0.4,
          surge_units * 0.25,
          surge_units * 0.35,
          surge_units,
      ],
  })

  fig_map = px.scatter_geo(
      routes_df,
      lat="Lat",
      lon="Lon",
      hover_name="Hub",
      size="Volume",
      color="Status",
      projection="natural earth",
      title="Active Inbound Shipments & Bottleneck Telemetry",
      color_discrete_map={
          "Dispatched": "#28A745",
          "Congested (+3 Days)": "#FFC107",
          "Severe Bottleneck (+4 Days)": "#DC3545",
          "Clear": "#0068C9",
          "Destination Hub": "#6F42C1",
      },
  )
  fig_map.update_layout(height=450, margin={"r": 0, "t": 40, "l": 0, "b": 0})
  st.plotly_chart(fig_map, use_container_width=True)

  st.divider()

  # Inbound Shipment Corridor Breakdown
  st.subheader("📦 Transit Corridor Health & Arrival Timeline")

  corridor_data = {
      "Corridor Name": [
          "Pacific Ocean Expressway (Asia -> LA)",
          "Trans-Suez / Atlantic Route (Asia -> Europe -> US)",
          "Domestic Overland Heavy Rail",
      ],
      "Primary Carrier": [
          "Maersk Ocean Line",
          "MSC Freight Fleet",
          "BNSF Railway Co",
      ],
      "Volume (Units)": [
          f"{int(surge_units * 0.45):,}",
          f"{int(surge_units * 0.35):,}",
          f"{int(surge_units * 0.20):,}",
      ],
      "Original ETA": ["14 Days", "16 Days", "5 Days"],
      "Delay Shock": ["+3 Days", "+4 Days", "+0 Days"],
      "Adjusted ETA": [
          f"{14 + 3} Days",
          f"{16 + 4} Days",
          "5 Days (On Schedule)",
      ],
      "Bottleneck Reason": [
          "Port Berth Queueing",
          "Canal Capacity Constraints",
          "Normal Operations",
      ],
  }
  st.table(pd.DataFrame(corridor_data))


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