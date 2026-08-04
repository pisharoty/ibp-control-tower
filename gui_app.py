import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Digital Brain — Enterprise IBP Control Tower", layout="wide")

st.title("Digital Brain — Enterprise IBP Control Tower")
st.caption("Real-Time Autonomous Integrated Business Planning & Financial Trade-off Platform")

# --- TOP HEADER 1: ENTERPRISE DATA INGESTION HUB ---
with st.expander("Enterprise Data Pipelines & API Hub (SAP S/4HANA, Salesforce, FourKites, Coupa)"):
    col_sync, col_info = st.columns([1, 3])
    with col_sync:
        if st.button("Sync Enterprise Data", type="primary"):
            try:
                res = requests.post(f"{API_BASE}/api/v1/ibp/ingestion/sync-all").json()
                st.success("Sync Complete!")
                st.json(res["ingestion_summary"])
            except Exception as e:
                st.error(f"Backend Connection Error: {e}")

# --- TOP HEADER 2: DIGITALIZED 5-STEP S&OP WORKFLOW STEPPER ---
st.subheader("Digitalized 5-Step S&OP Workflow Execution")

sop_steps = [
    "Step 1: Data Reconciliation & Reporting",
    "Step 2: Commercial & Demand Review",
    "Step 3: Supply & Operations Review",
    "Step 4: Pre-S&OP Financial Alignment",
    "Step 5: Executive S&OP Approval"
]

current_step = st.select_slider(
    "Active S&OP Planning Cycle Phase:",
    options=sop_steps,
    value="Step 4: Pre-S&OP Financial Alignment"
)

step_num = sop_steps.index(current_step) + 1
st.progress(step_num / 5)
st.info(f"**Current Active Phase:** {current_step} — Automated cross-functional decision support live across all modules.")

st.markdown("---")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("IBP Modules")
module = st.sidebar.radio(
    "Navigate to Module:",
    [
        "D/S Match & Net Margin Solver",
        "Product & NPI Engine",
        "NLP Commercial Sensing",
        "Control Tower GIS Map",
        "Enterprise Knowledge Graph (EKG)",
        "Strategy & AOP Analysis"
    ]
)

# PAGE 1: SOLVER
if module == "D/S Match & Net Margin Solver":
    st.header("Demand / Supply Match & Financial Waterfall Solver")
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.subheader("Scenario & Commercial Inputs")
        demand = st.slider("Total Unconstrained Demand (Units)", 50000, 200000, 150000, 5000)
        list_price = st.number_input("Base List Price ($/Unit)", value=50.0)
        trade_spend_pct = st.slider("Trade Spend Off-Invoice (%)", 0.0, 0.30, 0.12, 0.01)
        
        st.subheader("Plant Capacities & Freight Costs")
        cap_a = st.number_input("Plant A Max Capacity", value=40000)
        cap_b = st.number_input("Plant B Max Capacity", value=45000)
        cost_a_mfg = st.number_input("Plant A Mfg Cost ($)", value=12.0)
        cost_b_mfg = st.number_input("Plant B Mfg Cost ($)", value=14.0)
        freight_a = st.number_input("Plant A Freight ($)", value=2.5)
        freight_b = st.number_input("Plant B Freight ($)", value=3.0)
        expedite_prem = st.number_input("Air/Expedite Premium ($)", value=10.0)

    payload = {
        "demand_units": demand,
        "base_list_price": list_price,
        "trade_spend_pct": trade_spend_pct,
        "plant_capacities": [cap_a, cap_b],
        "mfg_unit_costs": [cost_a_mfg, cost_b_mfg],
        "logistics_unit_costs": [freight_a, freight_b],
        "expedite_premium_unit": expedite_prem
    }

    try:
        res = requests.post(f"{API_BASE}/api/v1/ibp/scenarios/run-ds-solver", json=payload).json()
        waterfall = res["waterfall"]
        alloc = res["allocation"]
        
        with col_out:
            st.subheader("Live Financial KPI Cards")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Gross Revenue", f"${waterfall['gross_revenue']:,.0f}")
            kpi2.metric("Trade Spend", f"-${waterfall['trade_spend']:,.0f}")
            kpi3.metric("Net Revenue", f"${waterfall['net_revenue']:,.0f}")
            margin_pct = (waterfall['net_margin'] / waterfall['gross_revenue']) * 100
            kpi4.metric("Net Operating Margin", f"${waterfall['net_margin']:,.0f}", f"{margin_pct:.1f}% Margin")

            fig = go.Figure(go.Waterfall(
                name = "P&L", orientation = "v",
                measure = ["relative", "relative", "total", "relative", "total"],
                x = ["Gross Revenue", "Trade Spend", "Net Revenue", "Mfg & Freight Costs", "Net Operating Margin"],
                textposition = "outside",
                text = [f"${waterfall['gross_revenue']:,.0f}", f"-${waterfall['trade_spend']:,.0f}", f"${waterfall['net_revenue']:,.0f}", f"-${waterfall['total_cogs_logistics']:,.0f}", f"${waterfall['net_margin']:,.0f}"],
                y = [waterfall['gross_revenue'], -waterfall['trade_spend'], waterfall['net_revenue'], -waterfall['total_cogs_logistics'], waterfall['net_margin']],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            fig.update_layout(title="Financial P&L Waterfall Breakdown ($)", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Optimal Multi-Echelon Supply Allocation")
            alloc_df = pd.DataFrame([{
                "Plant A Standard Units": alloc["plant_a_std_units"],
                "Plant B Standard Units": alloc["plant_b_std_units"],
                "Expedited / Air Freight Units": alloc["expedited_units"],
                "Total Demand Fulfilled": demand
            }])
            st.dataframe(alloc_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error connecting to FastAPI backend: {e}")

# PAGE 2: NPI ENGINE
elif module == "Product & NPI Engine":
    st.header("Product Launch & NPI Cannibalization Engine")
    col1, col2 = st.columns([1, 1])
    with col1:
        prod_name = st.text_input("New Product Launch Name", "Teed Off Energy Drink Zero")
        target_units = st.number_input("Target Launch Volume (Units)", value=50000)
        cann_pct = st.slider("Estimated Legacy Cannibalization Rate (%)", 0, 50, 20) / 100.0
        price = st.number_input("Unit Retail Price ($)", value=4.50)
        
        if st.button("Run NPI Cannibalization Simulation", type="primary"):
            npi_payload = {
                "new_product_name": prod_name,
                "target_launch_units": target_units,
                "estimated_cannibalization_pct": cann_pct,
                "base_price": price
            }
            try:
                res = requests.post(f"{API_BASE}/api/v1/ibp/npi/cannibalization-analysis", json=npi_payload).json()
                st.session_state['npi_res'] = res
            except Exception as e:
                st.error(f"Error: {e}")
                
    with col2:
        if 'npi_res' in st.session_state:
            res = st.session_state['npi_res']
            st.success(f"Stage Gate Status: {res['stage_gate_status']}")
            st.subheader("Financial & Cannibalization Analysis")
            st.write(f"**Gross New Launch Revenue:** ${res['financial_impact']['gross_new_revenue']:,.2f}")
            st.write(f"**Legacy Cannibalization Revenue Loss:** -${res['financial_impact']['cannibalized_revenue_loss']:,.2f}")
            st.metric("Net Incremental Revenue Contribution", f"${res['financial_impact']['net_incremental_revenue']:,.2f}")

# PAGE 3: NLP COMMERCIAL SENSING
elif module == "NLP Commercial Sensing":
    st.header("Unstructured Commercial Intelligence Ingestion")
    text_input = st.text_area("Account Field Update / Email Thread:", "Costco wants 50,000 extra cases of Teed off energy drink for a promo", height=100)
    
    if st.button("Extract Entities & Route Intelligence", type="primary"):
        try:
            res = requests.post(f"{API_BASE}/api/v1/ibp/nlp/parse-intelligence", json={"raw_text": text_input}).json()
            st.success("Parsed & Graph-Routed Successfully!")
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Extracted Knowledge Graph Entities")
                st.json(res["parsed_entities"])
            with col_b:
                st.subheader("Automated Workflow Routing")
                st.info(f"**Assigned Planner Role:** {res['routed_target_planner_role']}")
                st.code(f"Auto-Tag: {res['auto_generated_pulse_tag']}")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# PAGE 4: GIS MAP
elif module == "Control Tower GIS Map":
    st.header("Geospatial Control Tower & Node Health")
    try:
        nodes = requests.get(f"{API_BASE}/api/v1/ibp/geospatial/nodes").json()
        df = pd.DataFrame(nodes)
        
        st.subheader("Interactive Geographic Node Status Map")
        fig = px.scatter_mapbox(
            df, lat="lat", lon="lon", hover_name="name", hover_data=["type", "status", "otif_risk"],
            color="status", size_max=15, zoom=3, height=450
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Node Operational Status Summary")
        st.dataframe(df[["name", "type", "status", "capacity_util", "stockout_risk", "otif_risk"]], use_container_width=True)
    except Exception as e:
        st.error(f"Error loading map data: {e}")

# PAGE 5: ENTERPRISE KNOWLEDGE GRAPH
elif module == "Enterprise Knowledge Graph (EKG)":
    st.header("Enterprise Knowledge Graph (EKG) Explorer")
    try:
        ekg_data = requests.get(f"{API_BASE}/api/v1/ibp/ekg/graph").json()
        st.subheader("Connected Value Chain Knowledge Topology")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Graph Entities (Nodes):**")
            st.dataframe(pd.DataFrame(ekg_data["nodes"]), use_container_width=True)
        with col2:
            st.write("**Graph Relationships (Edges):**")
            st.dataframe(pd.DataFrame(ekg_data["edges"]), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading EKG data: {e}")

# PAGE 6: STRATEGY & AOP ANALYSIS
elif module == "Strategy & AOP Analysis":
    st.header("Strategic Target vs. Operational Execution Analysis")
    col_gap_in, col_gap_out = st.columns([1, 1])
    with col_gap_in:
        target_rev = st.number_input("Long Range Strategic Revenue Target ($)", value=10000000.0)
        aop_budget = st.number_input("Annual Operating Plan (AOP) Budget ($)", value=8500000.0)
        stat_base = st.number_input("Statistical Baseline Demand Forecast ($)", value=7500000.0)
        constrained_ibp = st.number_input("Constrained IBP Operational Output ($)", value=6600000.0)
        
        calc_btn = st.button("Calculate Strategic Gaps", type="primary")

    gap_payload = {
        "period_id": "FY2027_Q1",
        "long_range_target_revenue": target_rev,
        "aop_budget_revenue": aop_budget,
        "stat_baseline_forecast_revenue": stat_base,
        "constrained_ibp_forecast_revenue": constrained_ibp
    }

    try:
        res = requests.post(f"{API_BASE}/api/v1/ibp/strategy/aop-gap-analysis", json=gap_payload).json()
        
        st.subheader("Quantified Strategic & Execution Gaps")
        g1, g2, g3 = st.columns(3)
        g1.metric("Strategic Gap (Target vs Constrained)", f"${res['strategic_gap']:,.0f}", "↓ High Gap", delta_color="inverse")
        g2.metric("AOP Execution Gap", f"${res['aop_execution_gap']:,.0f}", "↓ Risk", delta_color="inverse")
        g3.metric("Supply Unconstrained Risk", f"${res['unconstrained_to_constrained_risk']:,.0f}")

        df_chart = pd.DataFrame({
            "Stage": ["Strategic Target", "AOP Budget", "Unconstrained Forecast", "Constrained IBP Commitment"],
            "Revenue ($)": [target_rev, aop_budget, stat_base, constrained_ibp]
        })
        fig_gap = px.bar(df_chart, x="Stage", y="Revenue ($)", color="Stage", title="Revenue Target Comparison")
        st.plotly_chart(fig_gap, use_container_width=True)

    except Exception as e:
        st.error(f"Backend Connection Error: {e}")


# >>> UNIQUE_CTRM_RISK_ENGINE_DESK_v2 <<<
from ctrm_engine import CTRMExtensionEngine, DSSolverOutput, RiskEventType

# Initialize Session State
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "custom_scenarios" not in st.session_state:
    st.session_state["custom_scenarios"] = {}

# Sidebar Risk Scenario Injector
st.sidebar.markdown("---")
st.sidebar.subheader("🌋 Risk Scenario Injector")
st.sidebar.caption("⚡ Auto-Ingest Telemetry Alerts:")

col_nlp1, col_nlp2 = st.sidebar.columns(2)
if col_nlp1.button("🌋 Iceland Ash", use_container_width=True):
    st.session_state["active_disruption"] = "Icelandic Volcanic Ash (North Atlantic Freight Corridor)"
    st.toast("⚡ Ingested: Eyjafjallajökull Volcanic Ash Cloud Alert!", icon="🌋")

if col_nlp2.button("🌊 El Niño AIS", use_container_width=True):
    st.session_state["active_disruption"] = "El Niño Climate Shock (Pacific Ocean Warm Current)"
    st.toast("⚡ Ingested: Sea surface anomaly confirmed in Pacific!", icon="🌊")

if st.sidebar.button("💥 Seismic Earthquake Feed", use_container_width=True):
    st.session_state["active_disruption"] = "Seismic Earthquake Shock (Port Facilities Damage)"
    st.toast("⚡ Ingested: Port Infrastructure Impaired!", icon="💥")

with st.sidebar.expander("🎨 Custom Disruption Model Builder (CME/ICE)"):
    with st.form("custom_disruption_form"):
        c_name = st.text_input("Disruption Title", "Panama Canal Drought Bottleneck")
        c_comm = st.selectbox("Target Commodity (CME/ICE)", [
            "CME Freight Futures (FBX)",
            "ICE Arabica Coffee (KC)",
            "NYMEX WTI Crude Oil (CL)",
            "CBOT Corn Futures (ZC)",
            "LME Primary Copper (HG)",
            "Custom Ticker / Asset"
        ])
        if c_comm == "Custom Ticker / Asset":
            c_comm = st.text_input("Custom Asset Ticker", "CME Random Length Lumber")
            
        c_type_str = st.selectbox("Pricing Engine Routing", [
            "Volcanic / Air Corridor Shock (Hawkes Jump)",
            "Climate / Weather Anomaly (Hawkes Jump)",
            "Seismic / Facility Loss (Parametric CAT)",
            "Standard / Geopolitical Volatility (Black-76)"
        ])
        
        col_p1, col_p2 = st.columns(2)
        c_base = col_p1.number_input("Base Price ($)", value=120.0)
        c_spot = col_p2.number_input("Spot Price ($)", value=195.0)
        c_vol = st.slider("Implied Volatility (σ)", 0.05, 1.50, 0.45, 0.05)
        c_thru = st.slider("Throughput Ratio (θ)", 0.05, 1.00, 0.30, 0.05)
        
        submit_custom = st.form_submit_button("🚀 Inject Custom Scenario", type="primary")
        if submit_custom:
            type_map = {
                "Volcanic / Air Corridor Shock (Hawkes Jump)": RiskEventType.VOLCANIC_ASH_DISRUPTION,
                "Climate / Weather Anomaly (Hawkes Jump)": RiskEventType.CLIMATE_SHOCK_EL_NINO,
                "Seismic / Facility Loss (Parametric CAT)": RiskEventType.SEISMIC_EARTHQUAKE_SHOCK,
                "Standard / Geopolitical Volatility (Black-76)": RiskEventType.STANDARD_VOLATILITY
            }
            st.session_state["custom_scenarios"][c_name] = {
                "commodity": c_comm,
                "event_type": type_map[c_type_str],
                "baseline_price": float(c_base),
                "spot_price": float(c_spot),
                "volatility": float(c_vol),
                "throughput": float(c_thru)
            }
            st.session_state["active_disruption"] = c_name
            st.toast(f"Custom Scenario Injected: {c_name}!", icon="🎯")

COMMODITY_SHOCK_MATRIX = {
    "El Niño Climate Shock (Pacific Ocean Warm Current)": {
        "commodity": "ICE Arabica Coffee & Softs",
        "event_type": RiskEventType.CLIMATE_SHOCK_EL_NINO,
        "baseline_price": 22.50,
        "spot_price": 28.40,
        "volatility": 0.32,
        "throughput": 0.70
    },
    "Icelandic Volcanic Ash (North Atlantic Freight Corridor)": {
        "commodity": "CME Freight Futures (FBX Air/Sea)",
        "event_type": RiskEventType.VOLCANIC_ASH_DISRUPTION,
        "baseline_price": 85.00,
        "spot_price": 135.00,
        "volatility": 0.55,
        "throughput": 0.40
    },
    "Seismic Earthquake Shock (Port Facilities Damage)": {
        "commodity": "Semiconductor Wafers & Rare Metals",
        "event_type": RiskEventType.SEISMIC_EARTHQUAKE_SHOCK,
        "baseline_price": 450.00,
        "spot_price": 720.00,
        "volatility": 0.65,
        "throughput": 0.20
    },
    "Standard Market Price Volatility": {
        "commodity": "LME Primary Aluminum",
        "event_type": RiskEventType.STANDARD_VOLATILITY,
        "baseline_price": 2200.00,
        "spot_price": 2350.00,
        "volatility": 0.18,
        "throughput": 1.00
    }
}
COMMODITY_SHOCK_MATRIX.update(st.session_state["custom_scenarios"])

disruption_options = list(COMMODITY_SHOCK_MATRIX.keys())
current_selection = st.session_state.get("active_disruption", "Standard Market Price Volatility")
default_idx = disruption_options.index(current_selection) if current_selection in disruption_options else 0

selected_event_label = st.sidebar.selectbox(
    "Select Physical Supply Chain Shock:",
    options=disruption_options,
    index=default_idx
)

if st.sidebar.button("🚨 Inject Selected Shock to CTRM Desk", type="primary", use_container_width=True):
    st.session_state["active_disruption"] = selected_event_label
    st.sidebar.success(f"Injected: {selected_event_label}")

active_label = st.session_state["active_disruption"]
st.sidebar.info(f"📡 **Active Signal Ingested:** {active_label}")

shock_data = COMMODITY_SHOCK_MATRIX.get(active_label, COMMODITY_SHOCK_MATRIX["Standard Market Price Volatility"])

ds_run = DSSolverOutput(
    scenario_name=active_label,
    commodity_name=shock_data["commodity"],
    incremental_gross_profit=7137631.0,
    flex_capacity_cost=930194.0,
    volume_shortfall_units=float(st.session_state.get("extracted_demand_surge", 50000)),
    baseline_price=shock_data["baseline_price"],
    spot_price=shock_data["spot_price"],
    implied_volatility=shock_data["volatility"],
    risk_event_type=shock_data["event_type"],
    network_throughput_ratio=shock_data["throughput"]
)

# Render CTRM Desk ONLY on active trading/margin modules
active_module = locals().get("selected_module", globals().get("selected_module", st.session_state.get("selected_module", None)))

if active_module in ["D/S Match & Net Margin Solver", "Procurement & Trading Desk"]:
    st.markdown("---")
    st.header("🛡️ CTRM Event-Driven Hedging & Arbitrage Desk")
    st.caption(f"Active Commodity Exposure: **{shock_data['commodity']}**")

    ctrm_bridge = CTRMExtensionEngine()
    arbitrage_info = ctrm_bridge.detect_arbitrage_risk(ds_run)
    staged_ticket = ctrm_bridge.select_model_and_structure_hedge(ds_run)

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Unhedged Margin Risk", f"${arbitrage_info['unhedged_margin_risk_usd']:,.2f}")
    col_b.metric("Pricing Model", staged_ticket.selected_model.value.replace("_", " "))
    col_c.metric("Notional Volume", f"{staged_ticket.notional_volume:,.0f} units")
    col_d.metric("Option Premium", f"${staged_ticket.estimated_premium:,.2f}")

    st.info(f"💡 **Recommendation**: Activate **{staged_ticket.selected_model.value}** to cap price volatility at **${staged_ticket.strike_price:.2f}/unit**.")

    if st.button("⚡ Approve & Execute CTRM Option Trade", type="primary"):
        approved_ticket = ctrm_bridge.approve_hedge_order(staged_ticket)
        results = ctrm_bridge.execute_and_close_loop(ds_run, approved_ticket, market_price_at_expiry=shock_data["spot_price"] * 1.1)
        
        if "ledger_data" in st.session_state:
            st.session_state["ledger_data"]["trades"].append(results)
            st.session_state["ledger_data"]["trade_count"] += 1
            st.session_state["ledger_data"]["total_hedging_revenue"] += results["financial_waterfall"]["hedge_payout_received_usd"]
            st.session_state["ledger_data"]["total_cogs_savings"] += (
                results["financial_waterfall"]["hedge_payout_received_usd"] - results["financial_waterfall"]["hedge_premium_paid_usd"]
            )
        
        st.balloons()
        st.success(f"Trade **{approved_ticket.order_id}** EXECUTED on Exchange for **{shock_data['commodity']}**!")
        st.subheader("📊 Closed-Loop Financial Waterfall")
        st.json(results["financial_waterfall"])
