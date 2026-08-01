# global_init_marker_v1
ledger_data = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}
# =======================================================
# Global CTRM Ledger State Initializer
# =======================================================
ledger_data = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}
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

    # --- Enterprise Knowledge Graph (EKG) Module ---
    st.subheader("Enterprise Knowledge Graph (EKG) Dependency Tree")
    st.markdown("##### Dynamic Risk Correlation & Node Impact")

    ledger = st.session_state.get('ledger_data', {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0})
    trade_cnt = len(ledger.get("trades", []))

    ekg_json = {
        "Root Commodity Affected": "Teed Off Energy Drink",
        "Active Disruption Trigger": "Walmart Order Surge: 50,000 Cases Teed Off Energy Drink",
        "Sensed Surcharge Exposure": "+$0.75/unit",
        "Lead Time Vulnerability Delta": "+5 Days",
        "Tier-1 Supplier Status": "SugarCo Global Trading (High Exposure)",
        "Executed Arbitrage Decisions Count": trade_cnt
    }
    st.json(ekg_json)


# 6. STRATEGY & AOP ANALYSIS
elif module == "Strategy & AOP Analysis":

    # --- Strategy & AOP Analysis Module ---
    st.subheader("Strategic Planning & Annual Operating Plan (AOP)")
    st.caption("Reconcile live NLP risks and executed trading arbitrage decisions against corporate AOP targets.")

    ledger = st.session_state.get('ledger_data', {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0})
    trades = ledger.get("trades", [])
    trade_cnt = len(trades)
    total_benefit = ledger.get("total_hedging_revenue", 0.0) + ledger.get("total_cogs_savings", 0.0)

    col1, col2, col3 = st.columns(3)
    col1.metric("AOP Operating Margin Target", "$12.4M", "↑ 2.1% vs LY")
    col2.metric("Committed Arbitrage P&L Benefit", f"${total_benefit:,.2f}", f"↑ {trade_cnt} Trades Executed")
    col3.metric("Active Risk Surcharge Exposure", "$0.75/unit")

    st.markdown("##### Executed Trade Log (Flowing into General Ledger)")
    if trade_cnt > 0:
        st.dataframe(trades, use_container_width=True)
    else:
        st.info("No trade decisions executed yet. Use the Procurement & Trading Desk to execute Make/Buy orders.")


    st.subheader("Executed Trade Log (Flowing into General Ledger)")
    if st.session_state["executed_decisions"]:
        st.table(st.session_state["executed_decisions"])
    else:
        st.info("No trade decisions executed yet. Use the Procurement & Trading Desk to execute Make/Buy orders.")

# 7. PROCUREMENT & TRADING DESK
elif module == "Procurement & Trading Desk":

    # --- Procurement & Trading Desk Module ---
    st.subheader("⚡ CTRM Commodity & Derivatives Trading Engine (Black-76)")
    st.caption("Monetize physical inventory, hedge agricultural/energy inputs, and price supply flexibility as real options.")

    if 'ledger_data' not in st.session_state:
        st.session_state['ledger_data'] = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}

    ledger_data = st.session_state['ledger_data']

    try:
        ledger_res = requests.get(f"{BACKEND_URL}/api/v1/ibp/trading/ledger", timeout=2)
        if ledger_res.status_code == 200:
            fetched = ledger_res.json()
            if isinstance(fetched, dict):
                st.session_state['ledger_data'] = fetched
                ledger_data = fetched
    except Exception:
        pass

    trade_cnt = ledger_data.get("trade_count", 0)
    if trade_cnt > 0:
        hedging_rev = ledger_data.get("total_hedging_revenue", 0.0)
        cogs_sav = ledger_data.get("total_cogs_savings", 0.0)
        st.success(f"📈 **Corporate P&L Ledger Active**: **${hedging_rev:,.2f}** in option yield + **${cogs_sav:,.2f}** in COGS risk protection across **{trade_cnt}** persistent trade(s).")

    col_cat, col_sym = st.columns(2)
    with col_cat:
        comm_cat = st.selectbox("Commodity Sector", [
            "Agriculture & Livestock", 
            "Energy", 
            "Rare Earths & Battery Metals", 
            "Industrial Metals"
        ], key="ctrm_cat_proc")
    with col_sym:
        if comm_cat == "Agriculture & Livestock":
            comm_sym = st.selectbox("Asset", ["CME Lean Hogs (lbs)", "CME Corn (Bushels)", "CME Live Cattle (lbs)", "Soybean Meal (Tons)"], key="ctrm_asset_a_proc")
            default_f, default_vol = 88.50, 0.28
        elif comm_cat == "Energy":
            comm_sym = st.selectbox("Asset", ["WTI Crude Oil (bbl)", "Henry Hub Natural Gas (MMBtu)", "Electricity (MWh)"], key="ctrm_asset_e_proc")
            default_f, default_vol = 78.50, 0.38
        elif comm_cat == "Rare Earths & Battery Metals":
            comm_sym = st.selectbox("Asset", ["Neodymium NdFeB (kg)", "Lithium Carbonate (MT)", "Dysprosium Oxide (kg)"], key="ctrm_asset_r_proc")
            default_f, default_vol = 145.00, 0.45
        else:
            comm_sym = st.selectbox("Asset", ["LME Copper (MT)", "LME Aluminum (MT)", "Nickel (MT)"], key="ctrm_asset_m_proc")
            default_f, default_vol = 9200.00, 0.22

    col_inputs1, col_inputs2 = st.columns(2)
    with col_inputs1:
        f_price = st.slider("Forward / Futures Price ($/unit)", min_value=1.0, max_value=15000.0, value=float(default_f), step=1.0, key="ctrm_f_proc")
        k_price = st.slider("Strike Price ($/unit)", min_value=1.0, max_value=15000.0, value=float(default_f * 1.05), step=1.0, key="ctrm_k_proc")
        opt_type = st.radio("Option Type", ["call", "put"], horizontal=True, key="ctrm_type_proc")

    with col_inputs2:
        exp_months = st.slider("Contract Expiration (Months)", min_value=1, max_value=24, value=6, key="ctrm_exp_proc")
        imp_vol = st.slider("Implied Volatility (σ)", min_value=0.05, max_value=1.00, value=float(default_vol), step=0.01, key="ctrm_vol_proc")
        contract_qty = st.number_input("Contract Volume (Units)", value=10000, step=1000, key="ctrm_qty_proc")

    if st.button("Run Black-76 Option Valuation & Arbitrage Solver", key="ctrm_btn_proc"):
        import math
        def local_norm_cdf(x: float) -> float:
            return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
        def local_norm_pdf(x: float) -> float:
            return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

        F, K, T, r, sigma = f_price, k_price, exp_months / 12.0, 0.045, imp_vol
        d1 = (math.log(F / K) + (0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        discount = math.exp(-r * T)

        if opt_type.lower() == "call":
            price = discount * (F * local_norm_cdf(d1) - K * local_norm_cdf(d2))
            delta = discount * local_norm_cdf(d1)
            strategy = "Upside Price Protection / Call Overlay"
            rec = f"Call Option on {comm_sym}: Locks maximum purchasing price ceiling at ${K:,.2f}."
        else:
            price = discount * (K * local_norm_cdf(-d2) - F * local_norm_cdf(-d1))
            delta = -discount * local_norm_cdf(-d1)
            strategy = "Inventory Floor Protection / Put Hedge"
            rec = f"Put Option on {comm_sym}: Provides downside price floor at ${K:,.2f} for physical volume."

        vega = discount * F * local_norm_pdf(d1) * math.sqrt(T) * 0.01

        st.session_state['last_ctrm_res'] = {
            "status": "SUCCESS",
            "premium_per_unit": round(price, 4),
            "total_premium_income": round(price * contract_qty, 2),
            "greeks": {"delta": round(delta, 4), "vega_1pct_vol": round(vega * contract_qty, 2)},
            "strategy": strategy,
            "trading_desk_recommendation": rec
        }

    if 'last_ctrm_res' in st.session_state and st.session_state['last_ctrm_res']:
        data = st.session_state['last_ctrm_res']
        st.success(f"Strategy: {data.get('strategy', 'N/A')}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Option Premium / Unit", f"${data.get('premium_per_unit', 0.0)}")
        m2.metric("Total Premium Revenue", f"${data.get('total_premium_income', 0.0):,.2f}")
        m3.metric("Delta (Δ)", data.get('greeks', {}).get('delta', 0.0))
        m4.metric("1% Vol Vega Impact", f"${data.get('greeks', {}).get('vega_1pct_vol', 0.0):,.2f}")
        
        st.info(f"**Trading Desk Action Plan:** {data.get('trading_desk_recommendation', 'N/A')}")

        st.markdown("##### 💼 Corporate Financial Ledger Sync")
        if st.button("💰 Commit Trade Yield to Corporate P&L Ledger", key="commit_pnl_btn_proc"):
            cogs_sav = (f_price - k_price) * contract_qty if opt_type == "call" and f_price > k_price else 0.0
            new_trade = {
                "id": f"TRD-{len(ledger_data['trades']) + 1001}",
                "symbol": comm_sym,
                "category": comm_cat,
                "option_type": opt_type.upper(),
                "volume": int(contract_qty),
                "premium_income": float(data.get('total_premium_income', 0.0)),
                "cogs_savings": round(cogs_sav, 2),
                "strike": k_price,
                "forward": f_price,
                "strategy": data.get('strategy', 'N/A')
            }
            st.session_state['ledger_data']['trades'].append(new_trade)
            st.session_state['ledger_data']['total_hedging_revenue'] += float(data.get('total_premium_income', 0.0))
            st.session_state['ledger_data']['total_cogs_savings'] += cogs_sav
            st.session_state['ledger_data']['trade_count'] += 1
            st.balloons()
            st.success("✅ Trade committed to persistent P&L ledger!")
            st.rerun()

    trades_list = ledger_data.get('trades', [])
    if isinstance(trades_list, list) and len(trades_list) > 0:
        st.markdown("---")
        st.subheader("📋 Active Corporate Trade & Derivatives Book")
        st.dataframe(trades_list, use_container_width=True)
