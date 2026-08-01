import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").strip().rstrip("/")

st.set_page_config(page_title="Integrated Business Planning Platform", layout="wide")

# --- ENTERPRISE GLOBAL STATE INITIALIZATION ---
if "active_nlp_signal" not in st.session_state:
    st.session_state["active_nlp_signal"] = {
        "event_name": "Walmart Order Surge: 50,000 Cases Teed Off Energy Drink",
        "source": "Salesforce CRM / Demand Sensing Feed",
        "surcharge_per_unit": 0.75,
        "lead_time_delay_days": 5,
        "affected_sku": "Teed Off Energy Drink",
        "lat": 36.3729,
        "lon": -94.2088,
        "risk_level": "HIGH"
    }

if "executed_decisions" not in st.session_state:
    st.session_state["executed_decisions"] = []

# Sidebar Navigation
module = st.sidebar.radio(
    "Navigate to Module:",
    [
        "D/S Match & Net Margin Solver",
        "Product & NPI Engine",
        "NLP Commercial Sensing",
        "Control Tower GIS Map",
        "Enterprise Knowledge Graph (EKG)",
        "Strategy & AOP Analysis",
        "Procurement & Trading Desk"
    ],
    key="nav_module_selection"
)

st.title("Integrated Business Planning Platform")

# Module Integration Mapping
INTEGRATION_MAP = {
    "D/S Match & Net Margin Solver": {
        "title": "Supply Chain & Manufacturing Pipeline",
        "systems": "SAP S/4HANA ERP, MES Plant Floor, WMS Storage",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-erp"
    },
    "Product & NPI Engine": {
        "title": "Product Lifecycle & Commercial Pipeline",
        "systems": "Arena PLM, Salesforce CRM, Stage-Gate Workflow",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-crm-plm"
    },
    "NLP Commercial Sensing": {
        "title": "Commercial Intelligence & Sentiment Pipeline",
        "systems": "Microsoft Outlook / Exchange API, Gmail Enterprise, Web Feeds",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-nlp-outlook"
    },
    "Control Tower GIS Map": {
        "title": "Geospatial & Logistics Visibility Pipeline",
        "systems": "FourKites TMS, project44, Mapbox API",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-gis-logistics"
    },
    "Enterprise Knowledge Graph (EKG)": {
        "title": "Knowledge Graph & Ontology Pipeline",
        "systems": "Neo4j Graph Database, NetworkX Core, Enterprise MDM",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-ekg-graph"
    },
    "Strategy & AOP Analysis": {
        "title": "FP&A Strategic & Operating Plan Pipeline",
        "systems": "Anaplan, SAP BPC, Oracle Hyperion",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-fpa-strategy"
    },
    "Procurement & Trading Desk": {
        "title": "Procurement, Spot Market & Tariff Pipeline",
        "systems": "Coupa Procurement, Bloomberg Commodity, FourKites Maritime, Descartes Tariff APIs",
        "endpoint": "" + BACKEND_URL + "/api/v1/ibp/integration/sync-procurement-trading"
    }
}

active_integration = INTEGRATION_MAP[module]

# Dynamic Integration Expander Header
with st.expander(f"Data Pipelines & API Hub ({active_integration['systems']})"):
    if st.button(f"Sync {active_integration['title']}", type="primary", key="sync_btn"):
        try:
            res = requests.post(active_integration["endpoint"])
            st.success("Sync Complete!")
            st.json(res.json())
        except Exception as e:
            st.error(f"Sync failed: {e}")

st.markdown("---")

# 1. D/S MATCH & NET MARGIN SOLVER
if module == "D/S Match & Net Margin Solver":
    st.header("Demand / Supply Match & Financial Waterfall Solver")
    
    active_nlp = st.session_state["active_nlp_signal"]
    st.info(f"🌐 **Active Signal Ingested:** {active_nlp['event_name']} (+${active_nlp['surcharge_per_unit']:.2f}/unit surcharge applied to COGS for {active_nlp['affected_sku']})")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Scenario & Commercial Inputs")
        demand = st.slider("Total Unconstrained Demand (Units)", 50000, 300000, 150000, step=10000, key="ds_demand")
        list_price = st.number_input("Base List Price ($/Unit)", value=50.00, step=1.0, key="ds_price")
        trade_spend = st.slider("Trade Spend Off-Invoice (%)", 0.0, 0.30, 0.12, step=0.01, key="ds_spend")
        
    with col2:
        st.subheader("Plant Capacities & Costs")
        cap_a = st.number_input("Plant A Max Capacity", value=40000, step=5000, key="cap_a")
        cap_b = st.number_input("Plant B Max Capacity", value=45000, step=5000, key="cap_b")
        cost_a = st.number_input("Plant A Mfg Cost ($)", value=12.00, step=0.5, key="cost_a")
        cost_b = st.number_input("Plant B Mfg Cost ($)", value=14.00, step=0.5, key="cost_b")

    if st.button("Run Financial Net Margin Optimization", type="primary", key="ds_solve_btn"):
        payload = {
            "unconstrained_demand": demand,
            "base_price": list_price,
            "trade_spend_pct": trade_spend,
            "plant_a_cap": cap_a,
            "plant_b_cap": cap_b,
            "plant_a_cost": cost_a,
            "plant_b_cost": cost_b,
            "nlp_surcharge_per_unit": active_nlp["surcharge_per_unit"]
        }
        try:
            res = requests.post("" + BACKEND_URL + "/api/v1/ibp/solver/ds-match", json=payload).json()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fulfilled Demand", f"{res['fulfilled_demand']:,} units")
            m2.metric("Gross Revenue", f"${res['gross_revenue']:,.2f}")
            m3.metric("Net Revenue", f"${res['net_revenue']:,.2f}")
            m4.metric("Net Margin P&L (incl. risk)", f"${res['net_margin']:,.2f}")
        except Exception as e:
            st.error(f"Solver connection error: {e}")

# 2. PRODUCT & NPI ENGINE
elif module == "Product & NPI Engine":
    st.header("Product Lifecycle & New Product Introduction (NPI) Engine")
    st.subheader("Active NPI Gate Review Pipeline")
    
    active_sku = st.session_state["active_nlp_signal"]["affected_sku"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Projected Launch SKU", active_sku)
        st.write("**Stage-Gate Status:** Gate 3 (Manufacturing Pilot)")
    with col2:
        st.metric("Target Commercial Launch", "Q4 2026")
        st.write("**Target Margin:** 42.5%")
    with col3:
        st.metric("R&D Budget Consumption", "$340,000 / $500,000")
        st.progress(0.68)

# 3. NLP COMMERCIAL SENSING (DYNAMICALLY REFLECTS LIVE STATE)
elif module == "NLP Commercial Sensing":
    st.header("NLP Commercial Sensing & Market Risk Generator")
    st.caption("Simulate, sense, or ingest real-time market disruptions and broadcast them across all IBP solvers.")
    
    # Live Scenario Card
    active_nlp = st.session_state["active_nlp_signal"]
    
    st.subheader("📡 Live Broadcast Signal (Active Enterprise Scenario)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Event Signal", active_nlp["event_name"])
    c2.metric("Impacted SKU", active_nlp["affected_sku"])
    c3.metric("Sensed Surcharge", f"+${active_nlp['surcharge_per_unit']:.2f} / unit")
    c4.metric("Schedule Delay", f"+{active_nlp['lead_time_delay_days']} Days")
    
    st.markdown("---")
    st.subheader("🔄 Ingest, Override, or Switch Market Signals")
    
    preset_option = st.selectbox(
        "Select Preset or Custom Market Signal:",
        [
            "Walmart Order Surge: 50,000 Cases Teed Off Energy Drink",
            "Suez Canal Maritime Congestion",
            "Panama Canal Drought & Slot Restrictions",
            "Brazilian Sugar Mill Strike (Raw Material Bottleneck)",
            "European Energy Tariff Spike",
            "Custom User Defined Market Signal"
        ],
        key="nlp_preset_choice"
    )
    
    if preset_option == "Walmart Order Surge: 50,000 Cases Teed Off Energy Drink":
        ev_name = "Walmart Order Surge: 50,000 Cases Teed Off Energy Drink"
        ev_src = "Salesforce CRM / Demand Sensing Feed"
        ev_sur = 0.75
        ev_lead = 5
        ev_sku = "Teed Off Energy Drink"
        ev_lat, ev_lon = 36.3729, -94.2088
    elif preset_option == "Suez Canal Maritime Congestion":
        ev_name = "Suez Canal Maritime Congestion"
        ev_src = "Outlook Exchange API / Maritime Feeds"
        ev_sur = 0.50
        ev_lead = 7
        ev_sku = "Cosmo Cola 20oz Packaging"
        ev_lat, ev_lon = 29.9753, 32.5599
    elif preset_option == "Panama Canal Drought & Slot Restrictions":
        ev_name = "Panama Canal Drought & Delay"
        ev_src = "project44 Telematics / News Feeds"
        ev_sur = 0.85
        ev_lead = 10
        ev_sku = "Citric Acid Raw Material"
        ev_lat, ev_lon = 9.0800, -79.6800
    elif preset_option == "Brazilian Sugar Mill Strike (Raw Material Bottleneck)":
        ev_name = "Brazilian Sugar Mill Strike"
        ev_src = "Bloomberg Commodity Feed"
        ev_sur = 1.25
        ev_lead = 14
        ev_sku = "Liquid Cane Sugar"
        ev_lat, ev_lon = -23.5505, -46.6333
    elif preset_option == "European Energy Tariff Spike":
        ev_name = "European Industrial Energy Surcharge"
        ev_src = "Descartes Customs & Tariff API"
        ev_sur = 0.40
        ev_lead = 3
        ev_sku = "Aluminum Can Stocks"
        ev_lat, ev_lon = 50.8503, 4.3517
    else:
        ev_name = st.text_input("Custom Event Name", active_nlp["event_name"])
        ev_src = "Manual Market Intelligence"
        ev_sur = st.number_input("Freight / Risk Surcharge ($/Unit)", value=float(active_nlp["surcharge_per_unit"]), step=0.10)
        ev_lead = st.number_input("Lead Time Delay (Days)", value=int(active_nlp["lead_time_delay_days"]), step=1)
        ev_sku = st.text_input("Affected Commodity SKU", active_nlp["affected_sku"])
        ev_lat, ev_lon = 12.0000, 43.0000

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Selected Event:** {ev_name}")
        st.write(f"**Data Source:** {ev_src}")
        st.write(f"**Target Commodity SKU:** {ev_sku}")
    with col2:
        st.write(f"**Landed Surcharge Impact:** +${ev_sur:.2f} / unit")
        st.write(f"**Schedule Delay Impact:** +{ev_lead} days")

    if st.button("🚨 Broadcast Selected Market Signal Across Platform", type="primary", key="activate_signal"):
        st.session_state["active_nlp_signal"] = {
            "event_name": ev_name,
            "source": ev_src,
            "surcharge_per_unit": ev_sur,
            "lead_time_delay_days": ev_lead,
            "affected_sku": ev_sku,
            "lat": ev_lat,
            "lon": ev_lon,
            "risk_level": "HIGH"
        }
        st.rerun()

# 4. CONTROL TOWER GIS MAP
elif module == "Control Tower GIS Map":
    st.header("Global Logistics Control Tower & Geospatial Map")
    active_nlp = st.session_state["active_nlp_signal"]
    
    st.subheader(f"Live Disruption Marker: {active_nlp['event_name']}")
    
    map_points = [
        {"lat": active_nlp["lat"], "lon": active_nlp["lon"]},
        {"lat": 31.2304, "lon": 121.4737},
        {"lat": 33.7490, "lon": -84.3880}
    ]
    st.map(data=map_points)
    
    st.caption(f"Active Node: Lat {active_nlp['lat']}, Lon {active_nlp['lon']} | Impacting SKU: {active_nlp['affected_sku']}")

# 5. ENTERPRISE KNOWLEDGE GRAPH
elif module == "Enterprise Knowledge Graph (EKG)":
    st.header("Enterprise Knowledge Graph (EKG) Dependency Tree")
    active_nlp = st.session_state["active_nlp_signal"]
    
    st.subheader("Dynamic Risk Correlation & Node Impact")
    
    st.json({
        "Root Commodity Affected": active_nlp["affected_sku"],
        "Active Disruption Trigger": active_nlp["event_name"],
        "Sensed Surcharge Exposure": f"+${active_nlp['surcharge_per_unit']:.2f}/unit",
        "Lead Time Vulnerability Delta": f"+{active_nlp['lead_time_delay_days']} Days",
        "Tier-1 Supplier Status": "SugarCo Global Trading (High Exposure)",
        "Executed Arbitrage Decisons Count": len(st.session_state["executed_decisions"])
    })

# 6. STRATEGY & AOP ANALYSIS
elif module == "Strategy & AOP Analysis":
    st.header("Strategic Planning & Annual Operating Plan (AOP)")
    st.caption("Reconcile live NLP risks and executed trading arbitrage decisions against corporate AOP targets.")
    
    total_trade_savings = sum(d.get("pnl_impact", 0) for d in st.session_state["executed_decisions"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("AOP Operating Margin Target", "$12.4M", "2.1% vs Ly")
    c2.metric("Committed Arbitrage P&L Benefit", f"${total_trade_savings:,.2f}", f"{len(st.session_state['executed_decisions'])} Trades Executed")
    c3.metric("Active Risk Surcharge Exposure", f"${st.session_state['active_nlp_signal']['surcharge_per_unit']:.2f}/unit")

    st.subheader("Executed Trade Log (Flowing into General Ledger)")
    if st.session_state["executed_decisions"]:
        st.table(st.session_state["executed_decisions"])
    else:
        st.info("No trade decisions executed yet. Use the Procurement & Trading Desk to execute Make/Buy orders.")

# 7. PROCUREMENT & TRADING DESK
elif module == "Procurement & Trading Desk":
    st.header("Procurement Trading Desk & Physical Arbitrage Engine")
    
    active_nlp = st.session_state["active_nlp_signal"]
    st.info(f"💡 **Auto-Ingested Market Risk Signal:** {active_nlp['event_name']} (+${active_nlp['surcharge_per_unit']:.2f}/unit surcharge | +{active_nlp['lead_time_delay_days']} days delay)")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Internal Manufacturing Inputs")
        sku_name = st.text_input("Product SKU / Commodity", active_nlp["affected_sku"], key="proc_sku")
        volume_req = st.number_input("Required Volume (Units)", value=50000, step=5000, key="proc_vol")
        internal_mfg = st.number_input("Internal Mfg Cost ($/Unit)", value=12.50, step=0.50, key="proc_mfg")
        internal_freight = st.number_input("Internal Outbound Freight ($/Unit)", value=2.00, step=0.25, key="proc_freight")
        internal_lead_time = st.number_input("Internal Lead Time (Days)", value=5, step=1, key="proc_ilt")

    with col2:
        st.subheader("External Supplier & Real-Time Risk Inputs")
        supplier_name = st.text_input("Supplier Name", "SugarCo Global Trading", key="proc_supp")
        spot_price = st.number_input("Spot Offer Price ($/Unit)", value=9.80, step=0.50, key="proc_spot")
        inbound_freight = st.number_input("Inbound Freight ($/Unit)", value=1.20, step=0.10, key="proc_inbound")
        tariff_duty = st.number_input("Tariff & Customs Duty ($/Unit)", value=0.60, step=0.10, key="proc_duty")
        warehousing = st.number_input("Warehousing ($/Unit)", value=0.20, step=0.05, key="proc_wh")
        supplier_lead_time = st.number_input("Supplier Lead Time (Days)", value=12 + active_nlp["lead_time_delay_days"], step=1, key="proc_slt")
        defect_rate = st.number_input("Defect / Scrap Rate (%)", value=2.5, step=0.5, key="proc_defect")
        disruption_surcharge = st.number_input("NLP Sensed Surcharge ($/Unit)", value=float(active_nlp["surcharge_per_unit"]), step=0.10, key="proc_surcharge")

    st.markdown("---")

    if st.button("Run Arbitrage & Trade Decision Solver", type="primary", key="proc_solve_btn"):
        payload = {
            "product_sku": sku_name,
            "target_volume": volume_req,
            "internal_mfg_cost_per_unit": internal_mfg,
            "internal_freight_per_unit": internal_freight,
            "internal_lead_time_days": internal_lead_time,
            "holding_cost_per_day": 0.15,
            "supplier_offers": [{
                "supplier_name": supplier_name,
                "spot_price_per_unit": spot_price,
                "inbound_freight_per_unit": inbound_freight,
                "tariff_and_duty_per_unit": tariff_duty,
                "warehousing_per_unit": warehousing,
                "lead_time_days": supplier_lead_time,
                "defect_rate_pct": defect_rate,
                "disruption_surcharge_per_unit": disruption_surcharge,
                "max_available_units": volume_req
            }]
        }
        try:
            res = requests.post("" + BACKEND_URL + "/api/v1/ibp/trading/make-vs-buy", json=payload).json()
            st.session_state["arbitrage_data"] = res
        except Exception as e:
            st.error(f"Solver connection error: {e}")

    if "arbitrage_data" in st.session_state:
        data = st.session_state["arbitrage_data"]
        
        if data["arbitrage_opportunity_found"]:
            st.success(f"⚠️ Arbitrage Opportunity Identified! Recommended Action: {data['recommended_action']}")
        else:
            st.warning(f"✅ Internal Production Optimal. Recommended Action: {data['recommended_action']}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Internal Landed Cost", f"${data['internal_landed_unit_cost']:.2f}/unit")
        m2.metric("Supplier Effective TCO Cost", f"${data['supplier_effective_unit_cost']:.2f}/unit")
        m3.metric("Net Unit Savings Delta", f"${data['unit_savings']:.2f}/unit")
        m4.metric("Net P&L Operating Benefit", f"${data['total_pnl_impact']:,.2f}")

        st.markdown("### 🛒 Execute Decision & Lock Financial Arbitrage")
        if st.button("Execute Order & Commit Decision to Enterprise State", key="proc_po_btn"):
            po_payload = {
                "sku": data["sku"],
                "supplier_name": data["best_supplier"],
                "volume": data["target_volume"],
                "agreed_unit_cost": data["supplier_effective_unit_cost"],
                "total_cost": data["supplier_effective_unit_cost"] * data["target_volume"],
                "action_type": data["recommended_action"]
            }
            try:
                po_res = requests.post("" + BACKEND_URL + "/api/v1/ibp/trading/execute-po", json=po_payload).json()
                
                st.session_state["executed_decisions"].append({
                    "po_number": po_res["po_number"],
                    "sku": data["sku"],
                    "action": data["recommended_action"],
                    "volume": data["target_volume"],
                    "unit_cost": f"${data['supplier_effective_unit_cost']:.2f}",
                    "pnl_impact": data["total_pnl_impact"]
                })
                
                st.balloons()
                st.success(f"🎉 {po_res['message']} Action committed to Global IBP State.")
            except Exception as e:
                st.error(f"PO Execution error: {e}")


    # --- CTRM Energy & Rare Earths Engine ---
    if 'hedging_revenue' not in st.session_state:
        st.session_state['hedging_revenue'] = 0.0
    if 'committed_trades' not in st.session_state:
        st.session_state['committed_trades'] = []
    if 'last_ctrm_res' not in st.session_state:
        st.session_state['last_ctrm_res'] = None

    st.markdown("---")
    st.subheader("⚡ CTRM Energy & Rare Earths Derivatives Engine (Black-76)")
    st.caption("Monetize physical inventory, write covered options, and price supply flexibility as real options.")

    # Ledger Active Banner
    if st.session_state['hedging_revenue'] > 0:
        st.success(f"📈 **Corporate P&L Ledger Active**: **${st.session_state['hedging_revenue']:,.2f}** accrued in hedging yield across {len(st.session_state['committed_trades'])} committed trade(s).")

    col_cat, col_sym = st.columns(2)
    with col_cat:
        comm_cat = st.selectbox("Commodity Sector", ["Energy", "Rare Earths"], key="ctrm_cat")
    with col_sym:
        if comm_cat == "Energy":
            comm_sym = st.selectbox("Asset", ["WTI Crude Oil (bbl)", "Henry Hub Natural Gas (MMBtu)", "Electricity (MWh)"], key="ctrm_asset_e")
            default_f, default_vol = 78.50, 0.38
        else:
            comm_sym = st.selectbox("Asset", ["Neodymium NdFeB (kg)", "Lithium Carbonate (MT)", "Dysprosium Oxide (kg)"], key="ctrm_asset_r")
            default_f, default_vol = 145.00, 0.45

    col_inputs1, col_inputs2 = st.columns(2)
    with col_inputs1:
        f_price = st.slider("Forward / Futures Price ($/unit)", min_value=10.0, max_value=500.0, value=float(default_f), step=0.5, key="ctrm_f")
        k_price = st.slider("Strike Price ($/unit)", min_value=10.0, max_value=500.0, value=float(default_f * 1.05), step=0.5, key="ctrm_k")
        opt_type = st.radio("Option Type", ["call", "put"], horizontal=True, key="ctrm_type")

    with col_inputs2:
        exp_months = st.slider("Contract Expiration (Months)", min_value=1, max_value=24, value=6, key="ctrm_exp")
        imp_vol = st.slider("Implied Volatility (σ)", min_value=0.05, max_value=1.00, value=float(default_vol), step=0.01, key="ctrm_vol")
        contract_qty = st.number_input("Contract Volume (Units)", value=10000, step=1000, key="ctrm_qty")

    if st.button("Run Black-76 Option Valuation & Arbitrage Solver", key="ctrm_btn"):
        payload = {
            "commodity_category": comm_cat,
            "commodity_symbol": comm_sym,
            "forward_price": f_price,
            "strike_price": k_price,
            "time_to_expiration": exp_months / 12.0,
            "risk_free_rate": 0.045,
            "implied_volatility": imp_vol,
            "contract_volume": int(contract_qty),
            "option_type": opt_type
        }
        try:
            res = requests.post(f"{BACKEND_URL}/api/v1/ibp/trading/black-scholes", json=payload)
            if res.status_code == 200:
                st.session_state['last_ctrm_res'] = res.json()
            else:
                st.error(f"Server Error: {res.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    if st.session_state['last_ctrm_res']:
        data = st.session_state['last_ctrm_res']
        st.success(f"Calculated Strategy: {data['strategy']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Option Premium / Unit", f"${data['premium_per_unit']}")
        m2.metric("Total Premium Revenue", f"${data['total_premium_income']:,.2f}")
        m3.metric("Delta (Δ)", data['greeks']['delta'])
        m4.metric("1% Vol Vega Impact", f"${data['greeks']['vega_1pct_vol']:,.2f}")
        
        st.info(f"**Trading Desk Action Plan:** {data['trading_desk_recommendation']}")

        st.markdown("##### 💼 Corporate Financial Ledger Sync")
        if st.button("💰 Commit Trade Yield to Corporate P&L Ledger", key="commit_pnl_btn"):
            income = data['total_premium_income']
            st.session_state['hedging_revenue'] += income
            st.session_state['committed_trades'].append({
                'commodity': data['commodity'],
                'income': income,
                'strategy': data['strategy']
            })
            st.balloons()
            st.success(f"✅ Committed **${income:,.2f}** in derivative yield to Corporate P&L! Total Accrued Hedging Revenue: **${st.session_state['hedging_revenue']:,.2f}**")
