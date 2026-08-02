import streamlit as st
import pandas as pd
import numpy as np
import math
import re
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="IBP Control Tower", layout="wide", page_icon="⚡")

# --- Session State Initialization ---
if 'extracted_demand_surge' not in st.session_state:
    st.session_state['extracted_demand_surge'] = 50000
if 'unconstrained_demand' not in st.session_state:
    st.session_state['unconstrained_demand'] = 150000
if 'active_signal_name' not in st.session_state:
    st.session_state['active_signal_name'] = "Costco Demand Signal (+50,000 units)"
if 'ledger_data' not in st.session_state:
    st.session_state['ledger_data'] = {
        "trades": [],
        "total_hedging_revenue": 0.0,
        "total_cogs_savings": 0.0,
        "trade_count": 0
    }

# Sidebar Navigation
st.sidebar.title("⚡ IBP Control Tower")
module = st.sidebar.radio(
    "Select Module",
    [
        "📊 Executive S&OP Dashboard",
        "💬 NLP Commercial Sensing",
        "⚖️ D/S Match & Net Margin Solver",
        "🏭 Procurement & Trading Desk",
        "🌐 Global Network & Logistics Map"
    ]
)

# Helper function to check if overflow was outsourced
def get_outsourced_info():
    trades = st.session_state['ledger_data'].get('trades', [])
    outsourced_vol = 0
    outsourced_cost_weighted = 0.0
    for t in trades:
        if t.get('category') == 'Physical Make/Buy':
            vol = t.get('volume', 0)
            outsourced_vol += vol
            outsourced_cost_weighted += t.get('strike', 12.01) * vol
    if outsourced_vol > 0:
        avg_cost = outsourced_cost_weighted / outsourced_vol
        return outsourced_vol, avg_cost
    return 0, 0.0

# =============================================================================
# MODULE 0: EXECUTIVE S&OP DASHBOARD
# =============================================================================
if module == "📊 Executive S&OP Dashboard":
    st.header("📊 Executive S&OP & Financial Control Tower")
    st.caption("Master Enterprise View: Synthesizing commercial demand signals, plant capacities, procurement arbitrage, and CTRM hedges.")
    
    total_demand = st.session_state['unconstrained_demand']
    outsourced_vol, avg_outsource_cost = get_outsourced_info()
    
    selling_price = 50.00
    trade_spend_pct = 0.12
    
    gross_rev = total_demand * selling_price
    trade_spend = gross_rev * trade_spend_pct
    net_rev = gross_rev - trade_spend
    
    cap_a, cost_a = 40000, 14.50
    cap_b, cost_b = 45000, 17.00
    alloc_a = min(total_demand, cap_a)
    rem_1 = total_demand - alloc_a
    alloc_b = min(rem_1, cap_b)
    overflow = rem_1 - alloc_b
    
    actual_outsourced = min(overflow, outsourced_vol)
    expedited_vol = overflow - actual_outsourced
    
    cost_a_tot = alloc_a * cost_a
    cost_b_tot = alloc_b * cost_b
    cost_outsource_tot = actual_outsourced * (avg_outsource_cost if avg_outsource_cost > 0 else 12.01)
    cost_expedited_tot = expedited_vol * 24.50
    
    total_supply_chain_cost = cost_a_tot + cost_b_tot + cost_outsource_tot + cost_expedited_tot
    net_operating_margin = net_rev - total_supply_chain_cost
    margin_pct = (net_operating_margin / gross_rev) * 100.0 if gross_rev > 0 else 0.0

    cogs_sav = st.session_state['ledger_data'].get("total_cogs_savings", 0.0)
    hedge_rev = st.session_state['ledger_data'].get("total_hedging_revenue", 0.0)

    # Key Metrics
    st.subheader("💡 Enterprise Performance Summary")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Unconstrained Demand", f"{total_demand:,.0f} units")
    kpi2.metric("Gross Revenue", f"${gross_rev:,.2f}")
    kpi3.metric("Net Revenue", f"${net_rev:,.2f}")
    kpi4.metric("Net Operating Margin", f"${net_operating_margin:,.2f}", f"{margin_pct:.1f}% Margin")
    kpi5.metric("Procurement & Hedging Value", f"${(cogs_sav + hedge_rev):,.2f}")

    st.markdown("---")
    
    col_dash1, col_dash2 = st.columns(2)
    with col_dash1:
        st.markdown("### 📊 Financial Waterfall & Operational Margin")
        waterfall_df = pd.DataFrame({
            "Financial Line Item": ["Gross Revenue", "Trade Spend (-12%)", "Net Revenue", "Base Plant Production Cost", "Outsourced / Expedited Fulfillment", "NET OPERATING MARGIN"],
            "Amount ($)": [f"${gross_rev:,.2f}", f"-${trade_spend:,.2f}", f"${net_rev:,.2f}", f"-${(cost_a_tot + cost_b_tot):,.2f}", f"-${(cost_outsource_tot + cost_expedited_tot):,.2f}", f"${net_operating_margin:,.2f}"]
        })
        st.table(waterfall_df)

    with col_dash2:
        st.markdown("### 🏭 Physical Fulfillment Breakdown")
        fulfillment_df = pd.DataFrame({
            "Channel": ["Plant A (In-House)", "Plant B (In-House)", "Tier-1 Outsource Partner", "Expedited Air Freight"],
            "Volume Allocated": [f"{alloc_a:,.0f} units", f"{alloc_b:,.0f} units", f"{actual_outsourced:,.0f} units", f"{expedited_vol:,.0f} units"],
            "Unit Cost": ["$14.50", "$17.00", f"${(avg_outsource_cost if avg_outsource_cost > 0 else 12.01):.2f}", "$24.50"]
        })
        st.table(fulfillment_df)

    st.markdown("---")
    st.subheader("📋 Active Corporate General Ledger & Sourcing Book")
    trades_list = st.session_state['ledger_data'].get('trades', [])
    if isinstance(trades_list, list) and len(trades_list) > 0:
        st.dataframe(trades_list, use_container_width=True)
    else:
        st.info("ℹ️ No physical or financial trades committed to the ledger yet. Execute decisions in **Procurement & Trading Desk** to populate the ledger.")

# =============================================================================
# MODULE 1: NLP COMMERCIAL SENSING
# =============================================================================
elif module == "💬 NLP Commercial Sensing":
    st.header("💬 NLP Commercial Sensing & Demand Extraction")
    st.caption("Converts unstructured market intelligence (customer communications, CRM notes, retailer updates) into structured demand signals for the S&OP network.")

    st.markdown("#### 🎯 Select Commercial Scenario or Input Custom Signal")
    scenario_choice = st.selectbox(
        "Pre-configured Commercial Intelligence Signals",
        [
            "Costco Promo Surge (+50,000 cases Teed Off Energy)",
            "Walmart Summer Heat Wave Demand (+75,000 cases)",
            "Target Back-to-School Flash Sale (+30,000 cases)",
            "✏️ Custom Free-Text Communication Input"
        ]
    )

    if scenario_choice == "Costco Promo Surge (+50,000 cases Teed Off Energy)":
        default_text = "Costco wants 50,000 extra cases of Teed off energy drink for an upcoming promo campaign."
    elif scenario_choice == "Walmart Summer Heat Wave Demand (+75,000 cases)":
        default_text = "Walmart issued an urgent request for 75,000 additional units of Teed Off drink to cover summer heatwave stockouts."
    elif scenario_choice == "Target Back-to-School Flash Sale (+30,000 cases)":
        default_text = "Target back-to-school flash promotion requires an additional 30,000 cases next month."
    else:
        default_text = "Customer requested 40,000 additional cases for immediate delivery."

    raw_text = st.text_area("Raw Commercial Communication Log", value=default_text, height=100)

    if st.button("🚀 Parse & Route Commercial Signal", key="parse_nlp_btn"):
        text_lower = raw_text.lower()
        customer = "Costco" if "costco" in text_lower else "Walmart" if "walmart" in text_lower else "Target" if "target" in text_lower else "Retail Partner"
        product = "Teed Off Energy Drink" if "teed off" in text_lower or "energy" in text_lower else "General SKU"
        
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', raw_text)
        extracted_vol = 50000
        if numbers:
            extracted_vol = int(numbers[0].replace(',', ''))

        new_demand = 100000 + extracted_vol
        st.session_state['extracted_demand_surge'] = extracted_vol
        st.session_state['unconstrained_demand'] = new_demand
        st.session_state['active_signal_name'] = f"{customer} Demand Signal (+{extracted_vol:,.0f} units)"
        st.session_state['ind_qty'] = max(0, new_demand - 85000)

        st.success("🎉 Signal Extracted & Routed Across S&OP Network!")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("Customer Account", customer)
        col_e2.metric("Product Family", product)
        col_e3.metric("Incremental Volume Surge", f"{extracted_vol:,.0f} cases")

        st.info(f"**Pulse Tag:** `COMMERCIAL_DEMAND_SURGE_{customer.upper()}` | **Routed To:** `Demand Planner - {customer} Retail`")
        st.balloons()

# =============================================================================
# MODULE 2: D/S MATCH & NET MARGIN SOLVER
# =============================================================================
elif module == "⚖️ D/S Match & Net Margin Solver":
    st.header("⚖️ D/S Match & Net Margin Optimization Solver")
    st.caption("Multi-echelon SciPy LP solver balancing plant capacity, expedited logistics, trade spend, and operating margins.")

    active_surge = st.session_state.get('extracted_demand_surge', 0)
    st.info(f"📡 **Active Signal Ingested from Pillar 1**: +{active_surge:,} units ({st.session_state.get('active_signal_name', 'Commercial Surge')})")

    total_demand = st.slider(
        "Total Unconstrained Demand (Units)", 
        min_value=50000, max_value=250000, 
        value=int(st.session_state.get('unconstrained_demand', 150000)), 
        step=5000, key="ds_demand_slider"
    )
    st.session_state['unconstrained_demand'] = total_demand

    outsourced_vol, avg_outsource_cost = get_outsourced_info()

    selling_price = 50.00
    trade_spend_pct = 0.12

    gross_rev = total_demand * selling_price
    trade_spend = gross_rev * trade_spend_pct
    net_rev = gross_rev - trade_spend

    cap_a, cost_a = 40000, 14.50
    cap_b, cost_b = 45000, 17.00

    alloc_a = min(total_demand, cap_a)
    rem_1 = total_demand - alloc_a

    alloc_b = min(rem_1, cap_b)
    overflow = rem_1 - alloc_b

    actual_outsourced = min(overflow, outsourced_vol)
    alloc_exp = overflow - actual_outsourced

    cost_a_total = alloc_a * cost_a
    cost_b_total = alloc_b * cost_b
    cost_outsource_total = actual_outsourced * (avg_outsource_cost if avg_outsource_cost > 0 else 12.01)
    cost_exp_total = alloc_exp * 24.50
    
    total_mfg_logistics_cost = cost_a_total + cost_b_total + cost_outsource_total + cost_exp_total

    net_operating_margin = net_rev - total_mfg_logistics_cost
    margin_pct = (net_operating_margin / gross_rev) * 100.0 if gross_rev > 0 else 0.0

    st.markdown("---")
    st.subheader("📊 Financial Waterfall & Profitability Summary")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Revenue", f"${gross_rev:,.2f}")
    m2.metric("Net Revenue (After Trade Spend)", f"${net_rev:,.2f}")
    m3.metric("Total Fulfillment Cost", f"${total_mfg_logistics_cost:,.2f}")
    m4.metric("Net Operating Margin", f"${net_operating_margin:,.2f}", f"{margin_pct:.1f}% Margin")

    st.markdown("#### 🏭 Supply Chain Allocation Breakdown (SciPy LP)")
    alloc_data = {
        "Fulfillment Channel": ["Plant A (In-House)", "Plant B (In-House)", "Tier-1 Outsource Partner", "Expedited Air Freight", "TOTAL FULFILLMENT"],
        "Capacity Limit": ["40,000 units", "45,000 units", "Flexible Contract", "Unlimited Overflow", "85,000 Max In-House"],
        "Allocated Volume": [f"{alloc_a:,.0f} units", f"{alloc_b:,.0f} units", f"{actual_outsourced:,.0f} units", f"{alloc_exp:,.0f} units", f"{total_demand:,.0f} units"],
        "Unit Cost ($/unit)": ["$14.50", "$17.00", f"${(avg_outsource_cost if avg_outsource_cost > 0 else 12.01):.2f}", "$24.50", f"${(total_mfg_logistics_cost/total_demand):.2f} avg"],
        "Total Cost ($)": [f"${cost_a_total:,.2f}", f"${cost_b_total:,.2f}", f"${cost_outsource_total:,.2f}", f"${cost_exp_total:,.2f}", f"${total_mfg_logistics_cost:,.2f}"]
    }
    st.table(alloc_data)

    if alloc_exp > 0:
        st.warning(f"⚠️ **Capacity Bottleneck**: Order volume exceeds maximum internal plant capacity (85,000 units). **{alloc_exp:,.0f} units** currently routed through expedited air freight at a **$10.00/unit penalty** ($24.50/unit vs $14.50 base cost).")
        st.info("💡 **Action Item**: Navigate to **Procurement & Trading Desk** to execute an Industrial Arbitrage trade and outsource this overflow volume at $12.01/unit landed cost!")
    elif actual_outsourced > 0:
        st.success(f"✅ **Bottleneck Mitigated via Outsourcing**: **{actual_outsourced:,.0f} overflow units** successfully outsourced at **${avg_outsource_cost:.2f}/unit**, bypassing expedited freight penalties and protecting operating margins ({margin_pct:.1f}%).")
    else:
        st.success(f"✅ **Optimal In-House Allocation**: All demand satisfied through internal plant capacity without expedited penalties. Operating margin: **{margin_pct:.1f}%**.")

# =============================================================================
# MODULE 3: PROCUREMENT & TRADING DESK
# =============================================================================
elif module == "🏭 Procurement & Trading Desk":
    st.header("🏭 Procurement & Trading Desk")
    st.caption("Execute physical Make vs. Buy arbitrage to mitigate capacity bottlenecks and trade financial derivatives (Black-76).")

    st.subheader("🏭 Industrial Make vs. Buy & Capacity Cannibalization Engine")
    
    total_dem = st.session_state.get('unconstrained_demand', 150000)
    sig_name = st.session_state.get('active_signal_name', 'Commercial Surge')
    suggested_overflow = max(0, total_dem - 85000)
    
    st.info(f"📡 **Active Commercial Signal Ingested**: `{sig_name}` | Total Demand = **{total_dem:,} units** | Calculated Unmet Internal Capacity = **{suggested_overflow:,} units**")

    if 'ind_qty' not in st.session_state:
        st.session_state['ind_qty'] = int(suggested_overflow)

    col_hdr1, col_hdr2, col_hdr3 = st.columns(3)
    with col_hdr1:
        order_qty = st.number_input("Target Overflow Volume (Units)", min_value=0, max_value=200000, step=5000, key="ind_qty")
    with col_hdr2:
        unit_price = st.number_input("End-Market Unit Selling Price ($)", value=50.00, step=1.00, key="ind_price")
    with col_hdr3:
        supplier_name = st.selectbox("Tier-1 Supplier Partner", ["SugarCo Global Trading", "Apex Logistics", "Pacific Rim Supply"], key="ind_supplier")

    st.markdown("---")
    col_make, col_buy = st.columns(2)

    with col_make:
        st.markdown("### 🏬 In-House Expedited Economics (Make)")
        dm_cost = st.number_input("Direct Materials ($/unit)", value=7.20, step=0.10, key="h_dm")
        dl_cost = st.number_input("Direct Labor ($/unit)", value=4.10, step=0.10, key="h_dl")
        voh_cost = st.number_input("Variable & Expedited Overhead ($/unit)", value=11.50, step=0.50, key="h_voh")
        foh_cost = st.number_input("Fixed Overhead Allocation ($/unit)", value=1.70, step=0.10, key="h_foh")

        make_defect_rate = st.slider("In-House Scrap / Defect Rate (%)", 0.0, 10.0, 1.5, step=0.1, key="h_make_defect") / 100.0
        plant_utilization = st.slider("Current Plant Utilization Rate (%)", 50, 110, 100, step=5, key="h_util")
        
        opp_cost_per_unit = 1.25 if plant_utilization > 90 else 0.0
        if opp_cost_per_unit > 0:
            st.caption(f"⚠️ Plant operating at **{plant_utilization}%** capacity. $1.25/unit cannibalization penalty applied.")

        variable_cogs_make = dm_cost + dl_cost + voh_cost
        base_unit_make = variable_cogs_make + foh_cost
        defect_penalty_make = base_unit_make * make_defect_rate
        total_unit_make_cost = base_unit_make + defect_penalty_make + opp_cost_per_unit
        
        st.metric("Total In-House / Expedited Unit Cost", f"${total_unit_make_cost:.2f}")

    with col_buy:
        st.markdown("### 🌍 Outsource Supplier Landed Cost (Buy)")
        buy_base_quote = st.number_input("Supplier Base Quote ($/unit)", value=9.80, step=0.25, key="h_buy_quote")
        tariff_rate = st.slider("Import Tariff / Duty Rate (%)", 0.0, 35.0, 7.5, step=0.5, key="h_tariff") / 100.0
        freight_cost = st.number_input("Logistics & Freight ($/unit)", value=0.85, step=0.05, key="h_freight")
        buy_defect_rate = st.slider("Supplier Non-Conformance Rate (%)", 0.0, 10.0, 3.0, step=0.1, key="h_buy_defect") / 100.0
        buy_lead_time = st.number_input("Supplier Delivery Lead Time (Days)", value=18, step=1, key="h_buy_lt")
        
        tariff_cost_per_unit = buy_base_quote * tariff_rate
        quality_risk_penalty = buy_base_quote * buy_defect_rate
        lt_risk_penalty = max(0, buy_lead_time - 7) * 0.03
        
        landed_buy_unit = buy_base_quote + tariff_cost_per_unit + freight_cost + quality_risk_penalty + lt_risk_penalty
        st.metric("Total Outsource Landed Unit Cost", f"${landed_buy_unit:.2f}")

    st.markdown("#### 📊 Economic & Cost Element Comparison")
    breakdown_data = {
        "Cost Element": [
            "Base Production / Quote", "Tariffs & Import Duties", "Freight & Freight Penalties", 
            "Quality / Scrap Risk Penalty", "Capacity Cannibalization Penalty", "TOTAL ECONOMIC COST / UNIT"
        ],
        "In-House / Expedited (Make)": [
            f"${base_unit_make:.2f}", "$0.00", f"${voh_cost:.2f}", 
            f"${defect_penalty_make:.2f}", f"${opp_cost_per_unit:.2f}", f"${total_unit_make_cost:.2f}"
        ],
        f"Outsource ({supplier_name})": [
            f"${buy_base_quote:.2f}", f"${tariff_cost_per_unit:.2f}", f"${freight_cost:.2f}", 
            f"${quality_risk_penalty:.2f}", "$0.00", f"${landed_buy_unit:.2f}"
        ]
    }
    st.table(breakdown_data)

    unit_arbitrage_delta = total_unit_make_cost - landed_buy_unit
    total_net_savings = unit_arbitrage_delta * order_qty

    if unit_arbitrage_delta > 0:
        st.success(f"💡 **Industrial Arbitrage Opportunity**: Outsourcing overflow to **{supplier_name}** saves **${unit_arbitrage_delta:.2f}/unit** over internal plant expansion & expedited freight! (Net P&L Benefit: **${total_net_savings:,.2f}**).")
    else:
        st.warning(f"⚠️ **In-House Manufacturing Preferred**: Internal production is cheaper by **${abs(unit_arbitrage_delta):.2f}/unit**.")

    if st.button("🚀 Execute Industrial Arbitrage Decision", key="exec_industrial_mb_btn"):
        cogs_savings_val = max(0.0, total_net_savings)
        new_trade = {
            "id": f"PHYS-{len(st.session_state['ledger_data']['trades']) + 1001}",
            "symbol": "Teed Off Energy Drink",
            "category": "Physical Make/Buy",
            "option_type": "BUY (Outsource)",
            "volume": int(order_qty),
            "premium_income": 0.0,
            "cogs_savings": round(cogs_savings_val, 2),
            "strike": round(landed_buy_unit, 2),
            "forward": round(total_unit_make_cost, 2),
            "strategy": f"Outsourced Bottleneck via {supplier_name} (Saved ${unit_arbitrage_delta:.2f}/unit)"
        }
        st.session_state['ledger_data']['trades'].append(new_trade)
        st.session_state['ledger_data']['total_cogs_savings'] += cogs_savings_val
        st.session_state['ledger_data']['trade_count'] += 1
        st.balloons()
        st.success(f"✅ Executed Outsource Arbitrage! Saved ${cogs_savings_val:,.2f} in COGS. Flowed to General Ledger & D/S Solver!")
        st.rerun()

    # SECTION 2: Financial CTRM
    st.markdown("---")
    st.subheader("⚡ CTRM Commodity & Derivatives Trading Engine (Black-76)")
    st.caption("Monetize physical inventory, hedge agricultural/energy inputs, and price supply flexibility as real options.")

    col_cat, col_sym = st.columns(2)
    with col_cat:
        comm_cat = st.selectbox("Commodity Sector", [
            "Agriculture & Livestock", "Energy", "Rare Earths & Battery Metals", "Industrial Metals"
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

        if st.button("💰 Commit Trade Yield to Corporate P&L Ledger", key="commit_pnl_btn_proc"):
            cogs_sav = (f_price - k_price) * contract_qty if opt_type == "call" and f_price > k_price else 0.0
            new_trade = {
                "id": f"TRD-{len(st.session_state['ledger_data']['trades']) + 1001}",
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
            st.success("✅ Financial trade committed to persistent General Ledger!")
            st.rerun()

    trades_list = st.session_state['ledger_data'].get('trades', [])
    if isinstance(trades_list, list) and len(trades_list) > 0:
        st.markdown("---")
        st.subheader("📋 Active Corporate General Ledger & Sourcing Book")
        st.dataframe(trades_list, use_container_width=True)

# =============================================================================
# MODULE 4: GLOBAL NETWORK & LOGISTICS MAP (RESTORED)
# =============================================================================
elif module == "🌐 Global Network & Logistics Map":
    st.header("🌐 Global Supply Chain & Logistics Control Map")
    st.caption("Real-time geographic visibility into manufacturing plants, supplier hubs, transit choke points, and active ocean/air shipments.")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Active Ocean Shipments", "14 Vessels", "+2 In-Transit")
    g2.metric("Chokepoint Bottlenecks", "1 Critical", "Suez Canal Disruptions")
    g3.metric("Plant Capacity Utilized", "100%", "Maxed Out (85k units)")
    g4.metric("Average Transit Delay", "+3.8 Days", "Suez Circumvent Route")

    # Plotly Geographic Map Creation
    nodes_df = pd.DataFrame([
        {"name": "Plant A (In-House Mfg)", "lat": 32.7767, "lon": -96.7970, "type": "Plant", "status": "100% Utilized (40,000 units)", "color": "blue", "size": 14},
        {"name": "Plant B (In-House Mfg)", "lat": 41.8781, "lon": -87.6298, "type": "Plant", "status": "100% Utilized (45,000 units)", "color": "blue", "size": 14},
        {"name": "SugarCo Tier-1 Partner", "lat": 10.8231, "lon": 106.6297, "type": "Supplier Hub", "status": "Active Arbitrage Outsource Partner", "color": "green", "size": 16},
        {"name": "Suez Canal Chokepoint", "lat": 30.5852, "lon": 32.2654, "type": "Bottleneck", "status": "⚠️ Critical Blockage / +5 Day Delay", "color": "red", "size": 18},
        {"name": "Port of Long Beach", "lat": 33.7701, "lon": -118.1937, "type": "Port Hub", "status": "Moderate Berth Congestion", "color": "orange", "size": 12},
        {"name": "Rotterdam Gateway", "lat": 51.9244, "lon": 4.4777, "type": "Distribution Hub", "status": "Normal Operations", "color": "blue", "size": 12}
    ])

    fig = go.Figure()

    for _, row in nodes_df.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[row['lon']],
            lat=[row['lat']],
            text=f"<b>{row['name']}</b><br>Type: {row['type']}<br>Status: {row['status']}",
            mode='markers+text',
            textposition="top center",
            marker=dict(size=row['size'], color=row['color'], symbol='circle'),
            name=row['name']
        ))

    # Transpacific Route (SugarCo Vietnam -> Long Beach USA)
    fig.add_trace(go.Scattergeo(
        lon=[106.6297, -118.1937],
        lat=[10.8231, 33.7701],
        mode='lines',
        line=dict(width=2.5, color='green', dash='dot'),
        name='Transpacific Route (SugarCo Outsource Shipping Lane)'
    ))

    # Eurasia Chokepoint Route (Asia -> Suez -> Europe)
    fig.add_trace(go.Scattergeo(
        lon=[106.6297, 32.2654, 4.4777],
        lat=[10.8231, 30.5852, 51.9244],
        mode='lines',
        line=dict(width=2.5, color='red', dash='dash'),
        name='Red Sea / Suez Route (Suez Canal Blockage Warning Zone)'
    ))

    fig.update_layout(
        title='📍 Global Network Telemetry & Freight Corridors',
        geo=dict(
            projection_type='equirectangular',
            showland=True,
            landcolor="rgb(240, 243, 246)",
            countrycolor="rgb(200, 200, 200)",
            coastlinecolor="rgb(180, 180, 180)",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🚢 Live Shipment Telemetry & Risk Matrix")
    shipment_df = pd.DataFrame({
        "Shipment ID": ["SHP-8841", "SHP-9012", "SHP-7734", "SHP-3310"],
        "Origin": ["Ho Chi Minh (SugarCo)", "Rotterdam Hub", "Dallas (Plant A)", "Chicago (Plant B)"],
        "Destination": ["Port of Long Beach", "Port of Newark", "Costco Distribution DC", "Walmart Regional DC"],
        "Carrier / Freight Mode": ["Maersk Ocean Line", "Hapag-Lloyd Ocean", "FedEx Freight (Ground)", "Expedited Air Freight"],
        "SKU Volume": ["65,000 units", "20,000 units", "40,000 units", "25,000 units"],
        "ETA": ["Aug 14, 2026", "Aug 19, 2026", "Aug 05, 2026", "Aug 04, 2026"],
        "Risk Status": ["🟢 On-Time", "🔴 +5 Days (Suez Re-route)", "🟢 On-Time", "🟡 Expedited ($24.50/unit)"]
    })
    st.table(shipment_df)

# =============================================================================
# FOOTER ARCHITECTURE SCHEMA EXPANDER
# =============================================================================
st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ System Architecture & API Schema"):
    st.markdown("""
    **API Endpoints & Integration Mapping:**
    * **NLP Sensing**: `POST /api/v1/nlp/commercial-signal` (Salesforce CRM / EDI 850)
    * **D/S Solver**: `POST /api/v1/ds/scipy-solve` (SAP IBP / Kinaxis Orchestrator)
    * **Make/Buy**: `POST /api/v1/procurement/arbitrage-commit` (ERP SAP MM Purchase Orders)
    * **CTRM Pricing**: `GET /api/v1/ctrm/black76-greeks` (CME Futures & Options Data Feed)
    * **Logistics Telemetry**: `GET /api/v1/logistics/ais-tracking` (Project44 / FourKites AIS)
    """)
