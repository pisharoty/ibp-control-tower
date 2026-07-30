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
