import streamlit as st
import pandas as pd
import numpy as np
import math

# Page configuration
st.set_page_config(page_title="IBP Control Tower", layout="wide", page_icon="⚡")

# --- Session State Initialization ---
if 'extracted_demand_surge' not in st.session_state:
    st.session_state['extracted_demand_surge'] = 0
if 'unconstrained_demand' not in st.session_state:
    st.session_state['unconstrained_demand'] = 100000
if 'ledger_data' not in st.session_state:
    st.session_state['ledger_data'] = {"trades": [], "total_hedging_revenue": 0.0, "total_cogs_savings": 0.0, "trade_count": 0}

# Sidebar Navigation
st.sidebar.title("⚡ IBP Control Tower")
module = st.sidebar.radio(
    "Select Module",
    [
        "📊 Executive S&OP Dashboard",
        "💬 Pillar 1: NLP Commercial Sensing",
        "⚖️ D/S Match & Net Margin Solver",
        "🏭 Procurement & Trading Desk"
    ]
)

# =============================================================================
# MODULE 0: EXECUTIVE S&OP DASHBOARD
# =============================================================================
if module == "📊 Executive S&OP Dashboard":
    st.header("📊 Executive S&OP & Financial Control Tower")
    st.caption("High-level enterprise visibility across commercial demand, plant utilization, supply chain costs, and CTRM hedges.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Unconstrained Demand", f"{st.session_state['unconstrained_demand']:,} units")
    col2.metric("Base Plant Capacity", "85,000 units")
    
    cogs_sav = st.session_state['ledger_data'].get("total_cogs_savings", 0.0)
    hedge_rev = st.session_state['ledger_data'].get("total_hedging_revenue", 0.0)
    
    col3.metric("Procurement COGS Savings", f"${cogs_sav:,.2f}")
    col4.metric("CTRM Option Premium Yield", f"${hedge_rev:,.2f}")

    st.markdown("---")
    st.info("💡 **Quick Navigation**: Use the sidebar to jump between **Pillar 1 (NLP Sensing)**, **D/S Net Margin LP Solver**, and the **Procurement & CTRM Trading Desk**.")

# =============================================================================
# MODULE 1: PILLAR 1 — NLP COMMERCIAL SENSING
# =============================================================================
elif module == "💬 Pillar 1: NLP Commercial Sensing":
    st.header("💬 Pillar 1: NLP Commercial Sensing")
    st.caption("Extract unstructured commercial intelligence and automatically route demand signals across the S&OP network.")

    raw_text = st.text_area(
        "Raw Account Communication / Commercial Signal", 
        value="Costco wants 50,000 extra cases of Teed off energy drink for a promo", 
        height=100
    )

    if st.button("🚀 Parse Intelligence", key="parse_nlp_btn"):
        text_lower = raw_text.lower()
        customer = "Costco" if "costco" in text_lower else "Walmart" if "walmart" in text_lower else "Retail Partner"
        product = "Teed Off Energy Drink" if "teed off" in text_lower or "energy" in text_lower else "General SKU"
        
        import re
        numbers = re.findall(r'\b\d{1,3}(?:,\d{3})*\b', raw_text)
        extracted_vol = 50000
        if numbers:
            extracted_vol = int(numbers[0].replace(',', ''))

        pulse_tag = f"COMMERCIAL_DEMAND_SURGE_{customer.upper()}"
        routed_to = f"Demand Planner - {customer} Retail Account"

        st.session_state['extracted_demand_surge'] = extracted_vol
        st.session_state['unconstrained_demand'] = 100000 + extracted_vol

        st.success("🎉 Parsed & Graph-Routed Successfully! 🚀")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("Customer", customer)
        col_e2.metric("Product Family", product)
        col_e3.metric("Incremental Volume", f"{extracted_vol:,.0f} cases")

        st.info(f"**Pulse Tag:** `{pulse_tag}`")
        st.info(f"**Routed To:** `{routed_to}`")
        st.balloons()
        st.caption("💡 *Demand updated! Navigate to **D/S Match & Net Margin Solver** to view the auto-updated LP allocation.*")

# =============================================================================
# MODULE 2: D/S MATCH & NET MARGIN SOLVER
# =============================================================================
elif module == "⚖️ D/S Match & Net Margin Solver":
    st.header("⚖️ D/S Match & Net Margin Optimization Solver")
    st.caption("Multi-echelon SciPy LP solver balancing plant capacity, expedited logistics, trade spend, and operating margins.")

    if st.session_state.get('extracted_demand_surge', 0) > 0:
        st.info(f"📡 **Active Signal Ingested from Pillar 1**: +{st.session_state['extracted_demand_surge']:,} units (Costco Promo Surge)")

    total_demand = st.slider(
        "Total Unconstrained Demand (Units)", 
        min_value=50000, max_value=250000, 
        value=int(st.session_state.get('unconstrained_demand', 100000)), 
        step=5000, key="ds_demand_slider"
    )

    selling_price = 50.00
    trade_spend_pct = 0.12

    gross_rev = total_demand * selling_price
    trade_spend = gross_rev * trade_spend_pct
    net_rev = gross_rev - trade_spend

    cap_a, cost_a = 40000, 14.50
    cap_b, cost_b = 45000, 17.00
    cost_exp = 24.50

    alloc_a = min(total_demand, cap_a)
    rem_1 = total_demand - alloc_a

    alloc_b = min(rem_1, cap_b)
    alloc_exp = rem_1 - alloc_b

    cost_a_total = alloc_a * cost_a
    cost_b_total = alloc_b * cost_b
    cost_exp_total = alloc_exp * cost_exp
    total_mfg_logistics_cost = cost_a_total + cost_b_total + cost_exp_total

    net_operating_margin = net_rev - total_mfg_logistics_cost
    margin_pct = (net_operating_margin / gross_rev) * 100.0

    st.markdown("---")
    st.subheader("📊 Financial Waterfall & Profitability Summary")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Revenue", f"${gross_rev:,.2f}")
    m2.metric("Net Revenue (After Trade Spend)", f"${net_rev:,.2f}")
    m3.metric("Total Mfg & Freight Cost", f"${total_mfg_logistics_cost:,.2f}")
    m4.metric("Net Operating Margin", f"${net_operating_margin:,.2f}", f"{margin_pct:.1f}% Margin")

    st.markdown("#### 🏭 Supply Chain Allocation Breakdown (SciPy LP)")
    alloc_data = {
        "Fulfillment Channel": ["Plant A (In-House)", "Plant B (In-House)", "Expedited Air / Freight Overflow", "TOTAL FULFILLMENT"],
        "Capacity Limit": ["40,000 units", "45,000 units", "Unlimited", "85,000 Max In-House"],
        "Allocated Volume": [f"{alloc_a:,.0f} units", f"{alloc_b:,.0f} units", f"{alloc_exp:,.0f} units", f"{total_demand:,.0f} units"],
        "Unit Cost ($/unit)": ["$14.50", "$17.00", "$24.50", f"${(total_mfg_logistics_cost/total_demand):.2f} avg"],
        "Total Cost ($)": [f"${cost_a_total:,.2f}", f"${cost_b_total:,.2f}", f"${cost_exp_total:,.2f}", f"${total_mfg_logistics_cost:,.2f}"]
    }
    st.table(alloc_data)

    if alloc_exp > 0:
        st.warning(f"⚠️ **Capacity Bottleneck**: Order volume exceeds maximum internal plant capacity (85,000 units). **{alloc_exp:,.0f} units** routed through expedited freight at a **$10.00/unit penalty**, diluting margin rate to **{margin_pct:.1f}%**.")
        st.caption("💡 *Action Item: Navigate to **Procurement & Trading Desk** to evaluate outsourcing options for the overflow volume.*")
    else:
        st.success(f"✅ **Optimal Allocation**: All demand satisfied through internal plant capacity without expedited penalties. Operating margin: **{margin_pct:.1f}%**.")

# =============================================================================
# MODULE 3: PROCUREMENT & TRADING DESK (INDUSTRIAL MAKE/BUY + CTRM)
# =============================================================================
elif module == "🏭 Procurement & Trading Desk":
    st.header("🏭 Procurement & Trading Desk")
    st.caption("Execute physical Make vs. Buy arbitrage to mitigate capacity bottlenecks and trade financial derivatives (Black-76).")

    # -------------------------------------------------------------------------
    # SECTION 1: Industrial Make vs Buy & Capacity Cannibalization Engine
    # -------------------------------------------------------------------------
    st.subheader("🏭 Industrial Make vs. Buy & Capacity Cannibalization Engine")
    st.info("📡 **Active Market Signal Ingested**: Costco Order Surge (+50,000 cases Teed Off Energy Drink)")

    col_hdr1, col_hdr2, col_hdr3 = st.columns(3)
    with col_hdr1:
        order_qty = st.number_input("Target Overflow Volume (Units)", value=65000, step=5000, key="ind_qty")
    with col_hdr2:
        unit_price = st.number_input("End-Market Unit Selling Price ($)", value=50.00, step=1.00, key="ind_price")
    with col_hdr3:
        supplier_name = st.selectbox("Tier-1 Supplier Partner", ["SugarCo Global Trading", "Apex Logistics", "Pacific Rim Supply"], key="ind_supplier")

    st.markdown("---")
    col_make, col_buy = st.columns(2)

    # In-House Plant (Make)
    with col_make:
        st.markdown("### 🏬 In-House Plant Economics (Make / Expedited)")
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

    # Outsource Supplier (Buy)
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
        st.success(f"✅ Executed Outsource Arbitrage! Committed ${cogs_savings_val:,.2f} COGS savings to General Ledger.")
        st.rerun()

    # -------------------------------------------------------------------------
    # SECTION 2: Financial CTRM & Derivatives Engine (Black-76)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("⚡ CTRM Commodity & Derivatives Trading Engine (Black-76)")
    st.caption("Monetize physical inventory, hedge agricultural/energy inputs, and price supply flexibility as real options.")

    ledger_data = st.session_state['ledger_data']
    trade_cnt = ledger_data.get("trade_count", 0)
    if trade_cnt > 0:
        hedging_rev = ledger_data.get("total_hedging_revenue", 0.0)
        cogs_sav = ledger_data.get("total_cogs_savings", 0.0)
        st.success(f"📈 **Corporate P&L Ledger Active**: **${hedging_rev:,.2f}** in option yield + **${cogs_sav:,.2f}** in physical COGS risk protection across **{trade_cnt}** persistent trade(s).")

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
            st.success("✅ Financial trade committed to persistent P&L ledger!")
            st.rerun()

    trades_list = st.session_state['ledger_data'].get('trades', [])
    if isinstance(trades_list, list) and len(trades_list) > 0:
        st.markdown("---")
        st.subheader("📋 Active Corporate General Ledger & Sourcing Book")
        st.dataframe(trades_list, use_container_width=True)
