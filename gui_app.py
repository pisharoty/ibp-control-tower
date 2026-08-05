import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import json

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================
if "active_disruption" not in st.session_state:
    st.session_state["active_disruption"] = "Standard Market Price Volatility"
if "extracted_demand_surge" not in st.session_state:
    st.session_state["extracted_demand_surge"] = 65000
if "physical_contracts" not in st.session_state:
    st.session_state["physical_contracts"] = [
        {"Contract ID": "CTR-2026-A1", "Commodity": "Primary Aluminum / Heavy Metals", "Supplier": "Rio Tinto", "Volume": "15,000 MT", "Fixed Price": "$2,200 / MT", "Status": "Active"},
        {"Contract ID": "CTR-2026-B4", "Commodity": "Freight Futures (FBX)", "Supplier": "Maersk Line", "Volume": "2,500 FEU", "Fixed Price": "$1,450 / FEU", "Status": "Under Review"},
        {"Contract ID": "CTR-2026-C9", "Commodity": "Semiconductor Wafers / Components", "Supplier": "TSMC", "Volume": "100,000 Wafers", "Fixed Price": "$450 / Wafer", "Status": "Executing"}
    ]
if "ctrm_ledger" not in st.session_state:
    st.session_state["ctrm_ledger"] = []

st.set_page_config(page_title="IBP Enterprise Control Tower", layout="wide")

try:
    from ctrm_engine import CTRMExtensionEngine, DSSolverOutput, RiskEventType
    CTRM_AVAILABLE = True
except ImportError:
    CTRM_AVAILABLE = False

# =====================================================================
# SIDEBAR: DYNAMIC PERSONA ARCHITECTURE & NAVIGATION
# =====================================================================
st.sidebar.title("⚡ IBP Control Tower")

persona = st.sidebar.selectbox(
    "🏢 Enterprise Platform Persona",
    [
        "🏭 Discrete & Heavy Industrial Enterprise",
        "📦 Process Goods & FMCG Enterprise",
        "📈 Merchant Trading & Commodity Risk Desk"
    ],
    key="platform_persona_v11"
)

# Dynamic Module Navigation Mapping per Persona
if "Industrial" in persona:
    term_unit = "Units"
    term_raw = "Raw Metals & Components"
    plant1_name = "Detroit Main Assembly Plant"
    plant2_name = "Munich Component Line"
    toller_name = "3rd-Party Contract Manufacturer (CMO)"
    available_modules = [
        "📊 Executive S&OP Control Tower",
        "🧠 NLP Commercial Sensing & Field Intelligence",
        "⚖️ Demand/Supply Match & Plant Load Balancer",
        "📈 Physical Procurement & Contract Desk",
        "🛡️ CTRM Event-Driven Hedging Desk",
        "🌐 Global Logistics Network & GIS Control Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
elif "FMCG" in persona:
    term_unit = "Cases / Batches"
    term_raw = "Agri Softs & Packaging Ingredients"
    plant1_name = "Midwest Processing Facility"
    plant2_name = "Rotterdam Blending Plant"
    toller_name = "Regional Cold-Storage Co-Packer"
    available_modules = [
        "📊 Integrated Business Planning (IBP) Tower",
        "🧠 NLP Commercial Sensing & Retail Intelligence",
        "⚖️ Batch Processing & Co-Packer Load Balancer",
        "📈 Agri-Ingredients & Direct Procurement",
        "🛡️ CTRM Softs & Commodity Risk Desk",
        "🌐 Cold Chain & Regional Distribution GIS Tower",
        "🔌 Integration & Architecture Endpoints"
    ]
else:  # Merchant Trading & PE Desk
    term_unit = "Lots / Contracts"
    term_raw = "Physical Deliverable Cargoes"
    plant1_name = "Primary Import Terminal A"
    plant2_name = "Regional Hub Terminal B"
    toller_name = "3rd-Party Merchant Storage Arbitrage"
    # D/S Solver OMITTED FOR MERCHANT TRADERS
    available_modules = [
        "🏛️ Daily Trading Balance Sheet & Position Tower",
        "🧠 Global Macro & Satellite Market Intelligence",
        "📈 Physical Off-Take & Merchant Storage Desk",
        "🛡️ CTRM Derivatives & Risk Arbitrage Desk",
        "🌐 Global Maritime AIS & Cargo GIS Tower",
        "🔌 Integration & Architecture Endpoints"
    ]

selected_module = st.sidebar.radio(
    "Select Operational Module",
    available_modules,
    key="nav_module_selection_v11"
)

def parse_demand_from_text(text):
    patterns = [
        r'(?:spike|surge|demand|units|cases|batches|lots)\s*(?:of|by)?\s*~?\s*(\d+[\d,]*)',
        r'(\d+[\d,]*)\s*(?:additional|extra)?\s*(?:units|cases|batches|lots|MT)'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val_str = m.group(1).replace(',', '')
            if val_str.isdigit() and int(val_str) > 100:
                return int(val_str)
    return 65000

# =====================================================================
# MODULE 1: S&OP / DAILY TRADING BALANCE SHEET
# =====================================================================
if "S&OP" in selected_module or "IBP" in selected_module or "Trading Balance Sheet" in selected_module:
    surge = st.session_state.get("extracted_demand_surge", 65000)

    if "Merchant Trading" in persona:
        st.title("🏛️ Daily Trading Balance Sheet & Position Tower")
        st.caption(f"Active Persona View: **{persona}** (Hedge Fund / Private Equity Commodities Desk)")
        st.markdown("Daily Marked-to-Market (MtM) financial reconciliation, net delta position exposure, and trading liquidity.")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Marked-to-Market (MtM) Daily P&L", "+$4.85M", "+3.1% Today")
        col2.metric("Gross Portfolio Exposure", "$412.5M", "82% Capacity")
        col3.metric("Net Delta Position Exposure", f"+{surge:,} Lots", "Long Position")
        col4.metric("Value at Risk (95% 1-Day VaR)", "$1.82M", "-0.14%", delta_color="inverse")
        
        st.markdown("---")
        st.subheader("📋 Daily Reconciled Trading Positions & Cash Liquidity Bridge")
        
        trading_ledger = pd.DataFrame({
            "Commodity Desk / Book": ["LME Metals & Rare Earths", "CME Freight Futures (FBX)", "ICE Agri & Softs", "Physical Gold Bullion Storage"],
            "Physical Asset Holding": ["15,000 MT (Warehouse A)", "2,500 Containers (In-Transit)", "85,000 Lots (Off-Take)", "4,500 oz (Vault Secure)"],
            "Paper Derivative Hedge": ["Long 12,000 MT Put Options", "Short 2,500 FEU Swaps", "Long 50,000 Calls", "Unhedged Spot"],
            "Net Delta Exposure": ["+3,000 MT Net Long", "Delta Neutral (0.00)", "+35,000 Lots Net Long", "+4,500 oz Physical"],
            "Daily MtM P&L ($)": ["+$1,250,000", "+$420,000", "+$2,850,000", "+$330,000"],
            "Reconciliation Status": ["🟢 Cleared Daily", "🟢 Cleared Daily", "🟡 Pending OTC Settlement", "🟢 Vault Verified"]
        })
        st.dataframe(trading_ledger, use_container_width=True)

    else:
        st.title("📊 Executive S&OP Control Tower" if "Industrial" in persona else "📊 Integrated Business Planning (IBP) Tower")
        st.caption(f"Active Persona View: **{persona}**")
        st.markdown("Real-time financial alignment, financial waterfalls, and trade hedge benefit reconciliation.")
        
        unconstrained_val = 120.0 + (surge * 0.00025)
        trade_offset = 3.25
        cogs_drag = -12.4
        net_ebitda = round(120.0 + (surge * 0.00025) + cogs_drag + trade_offset, 2)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Annual Operating Plan (AOP)", "$120.0M", "+4.2%")
        col2.metric("Unconstrained Demand (AOP + Surge)", f"${unconstrained_val:.1f}M", f"+{surge:,} {term_unit}")
        col3.metric("CTRM Hedge & Trade Benefit", f"+${trade_offset:.2f}M", "Derivative Gain")
        col4.metric("Net Realized EBITDA", f"${net_ebitda:.2f}M", "+6.4%", delta_color="normal")
        
        st.markdown("---")
        st.subheader("📊 Executive Financial Waterfall (Volume-to-Value Bridge)")
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="S&OP Bridge",
            orientation="v",
            measure=["relative", "relative", "relative", "relative", "total"],
            x=["Base AOP Revenue", f"Trade Promo Surge (+{surge:,})", "Raw Material COGS Volatility", "CTRM Derivative Hedge Offset", "Net Realized EBITDA"],
            textposition="outside",
            text=[f"$120.0M", f"+${(surge * 0.00025):.2f}M", f"-${abs(cogs_drag):.2f}M", f"+${trade_offset:.2f}M", f"${net_ebitda:.2f}M"],
            y=[120.0, surge * 0.00025, cogs_drag, trade_offset, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#EF553B"}},
            increasing={"marker": {"color": "#00CC96"}},
            totals={"marker": {"color": "#636EFA"}}
        ))
        fig_waterfall.update_layout(title="Volume-to-Value S&OP Financial Bridge ($M)", showlegend=False, height=450)
        st.plotly_chart(fig_waterfall, use_container_width=True)

# =====================================================================
# MODULE 2: NLP COMMERCIAL SENSING
# =====================================================================
elif "NLP Commercial" in selected_module or "Global Macro" in selected_module:
    st.title("🧠 Global Macro & Satellite Intelligence" if "Merchant" in persona else "🧠 NLP Commercial Sensing & Email Intelligence")
    st.caption(f"Active Persona View: **{persona}**")
    
    if "Merchant" in persona:
        st.markdown("Ingest unstructured global macro feeds, satellite imagery alerts, vessel tracking news, and commodity policy changes.")
        
        signals = pd.DataFrame({
            "Signal Feed": ["Satellite Synthetic Aperture Radar", "Bloomberg Macro Intelligence", "Global Maritime News", "Central Bank Reserve Monitor"],
            "Event Detected": ["Tank Farm Fill Rate +14% (Rotterdam)", "China Export Duty Revision on Metals", "Malacca Strait Naval Transit Slowdown", "PBOC Gold Reserve Accumulation"],
            "Market Impact": ["Crude Storage Arbitrage Spread Opening", "Rare Earth Spot Spike (+12%)", "Maritime Freight Rate Inversion", "Spot Bullion Price Support"],
            "Confidence": ["98%", "94%", "89%", "96%"]
        })
        st.dataframe(signals, use_container_width=True)
    else:
        st.markdown("Ingest unstructured signals from news feeds, social media, post-trade show emails, and marketing promo debriefs.")
        default_email = """From: vpsales@enterprise.com
Date: Aug 3, 2026
Subject: CES 2026 Recap - Demand Surge Alert

We experienced overwhelming interest. Major retail distributors gave verbal commitments. 
We estimate an unconstrained demand surge of ~85,000 additional units over baseline."""
        user_email = st.text_area("Email / Field Debrief Content:", value=default_email, height=150)
        if st.button("🧠 Extract NLP Demand Intent", type="primary"):
            val = parse_demand_from_text(user_email)
            st.session_state["extracted_demand_surge"] = val
            st.success(f"Parsed {val:,} {term_unit} demand surge!")

    current_surge = st.session_state.get("extracted_demand_surge", 65000)
    demand_surge = st.slider(f"Active Demand Shock Volume ({term_unit})", 10000, 200000, int(current_surge), step=5000)
    st.session_state["extracted_demand_surge"] = demand_surge

# =====================================================================
# MODULE 3: DEMAND/SUPPLY MATCH (ONLY FOR INDUSTRIAL & FMCG)
# =====================================================================
elif "Demand/Supply" in selected_module or "Batch Processing" in selected_module:
    st.title("⚖️ Demand/Supply Match & Plant Load Balancer")
    st.caption(f"Active Persona View: **{persona}**")
    st.markdown("Linear programming optimization for global plant load balancing, make vs. buy arbitrage, and profit maximization.")
    
    surge_vol = st.session_state.get("extracted_demand_surge", 65000)
    primary_cap = 450000
    flex_alloc = min(surge_vol, 100000)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Primary Internal Facility Capacity", f"{primary_cap:,} {term_unit}")
        st.metric(f"Flex Allocation to {toller_name}", f"{flex_alloc:,} {term_unit}")
    with col2:
        st.metric("Maximized Gross Profit", "$68.53M")
        
    st.markdown("---")
    plant_df = pd.DataFrame({
        "Production Facility / Source": [plant1_name, plant2_name, toller_name],
        "Facility Type": ["Primary Facility A", "Primary Facility B", "3rd-Party CMO / Co-Packer"],
        "Max Capacity": [300000, 150000, 100000],
        "Allocated Volume": [300000, 150000, flex_alloc],
        "Utilization Rate (%)": ["100%", "100%", f"{(flex_alloc/100000)*100:.1f}%"]
    })
    st.dataframe(plant_df, use_container_width=True)

# =====================================================================
# MODULE 4: PHYSICAL PROCUREMENT / MERCHANT STORAGE DESK
# =====================================================================
elif "Procurement" in selected_module or "Off-Take" in selected_module:
    if "Merchant" in persona:
        st.title("📈 Physical Off-Take & Merchant Storage Desk")
        st.caption(f"Active Persona View: **{persona}** (Goldman / PE / Hedge Fund Merchant Assets)")
        st.markdown("Physical commodity off-take contracts, vault/tank storage holdings, and warehouse inventory management.")
        
        st.info("💡 **Merchant Strategy Note**: Tracking physical gold bullion vaults, metal storage warehouses, and oil tank farm allocations to capture physical/paper contango arbitrage.")
        
        proc_contracts = pd.DataFrame([
            {"Contract ID": "OFF-2026-G1", "Asset Class": "Physical Gold Bullion", "Vault / Warehouse": "Zurich Bullion Storage", "Holding Volume": "4,500 oz", "Carrying Cost": "$12.50 / oz / yr", "Status": "Vault Verified"},
            {"Contract ID": "OFF-2026-M8", "Asset Class": "Rare Earth Metals (Neodymium)", "Vault / Warehouse": "Rotterdam Metal Depot", "Holding Volume": "12,000 MT", "Carrying Cost": "$110 / MT / yr", "Status": "Off-Take Active"},
            {"Contract ID": "OFF-2026-E4", "Asset Class": "Light Sweet Crude Oil", "Vault / Warehouse": "Cushing Tank Farm", "Holding Volume": "500,000 Barrels", "Carrying Cost": "$0.45 / Bbl / mo", "Status": "Tank Lease Active"}
        ])
        st.dataframe(proc_contracts, use_container_width=True)
    else:
        st.title("📈 Physical Procurement & Contract Desk")
        st.caption(f"Active Persona View: **{persona}**")
        surge = st.session_state.get("extracted_demand_surge", 65000)
        
        # FIXED: FEU Divisor changed to / 100 so numbers don't collide
        raw_mt = (450000 + surge) * 0.02
        freight_feu = (450000 + surge) / 100
        
        st.info(f"📦 **Active BOM Requisitions Ingested from D/S Solver**: Requesting **{raw_mt:,.0f} MT** of raw materials and **{freight_feu:,.0f} FEUs** of maritime freight.")
        st.dataframe(pd.DataFrame(st.session_state["physical_contracts"]), use_container_width=True)

# =====================================================================
# MODULE 5: CTRM HEDGING & ARBITRAGE DESK
# =====================================================================
elif "CTRM" in selected_module:
    st.title("🛡️ CTRM Derivatives & Risk Arbitrage Desk" if "Merchant" in persona else "🛡️ CTRM Event-Driven Hedging Desk")
    st.caption(f"Active Persona View: **{persona}**")
    
    surge = st.session_state.get("extracted_demand_surge", 65000)
    active_label = st.session_state.get("active_disruption", "Standard Market Price Volatility")
    st.info(f"📡 **Active Risk Signal**: {active_label} | **Notional Portfolio Exposure**: {surge:,} {term_unit}")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Unhedged Margin / Price Risk", f"${(surge * 150):,.2f}")
    col_b.metric("Pricing Engine", "Black76 Jump-Diffusion")
    col_c.metric("Recommended Derivative Structure", "Asian Call Option Collar")

# =====================================================================
# MODULE 6: LOGISTICS & GIS CONTROL TOWER
# =====================================================================
elif "Logistics" in selected_module or "AIS" in selected_module:
    if "Merchant" in persona:
        st.title("🌐 Global Maritime AIS & Cargo GIS Tower")
        st.caption(f"Active Persona View: **{persona}** (Global AIS Vessel Tracking & Commodity Flow)")
        st.markdown("Geospatial tracking of oil tankers, dry bulk carriers, port queue bottlenecks, and global tank farm storage.")
        
        gis_nodes = pd.DataFrame({
            "Name": ["Suez Canal Maritime Chokepoint", "Panama Canal Transit Queue", "Rotterdam Tank Farm Depot", "Singapore Anchorage Queue", "Cushing Tank Terminal"],
            "lat": [30.5852, 9.0800, 51.9244, 1.3521, 35.9856],
            "lon": [32.5656, -79.6800, 4.4777, 103.8198, -96.7681],
            "Category": ["Maritime Chokepoint", "Maritime Chokepoint", "Tank Farm Storage", "Anchorage Queue", "Tank Farm Storage"],
            "Status": ["24 Vessels Waiting", "18 Days Delay", "88% Capacity (Full)", "Normal Transit", "62% Capacity"],
            "Size": [25, 25, 20, 18, 20]
        })
        
        fig_map = px.scatter_mapbox(gis_nodes, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=450)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
        st.subheader("🚢 Live AIS Vessel & Cargo Telemetry Stream")
        ais_vessels = pd.DataFrame({
            "Vessel Name / IMO": ["M/T Nordic Trader (IMO 98213)", "M/V Atlantic Bullion (IMO 91124)", "M/T Pacific Energy (IMO 94511)"],
            "Cargo Type": ["Light Sweet Crude (1.2M Bbls)", "Physical Rare Earths (25,000 MT)", "LNG Liquefied Gas (170k m³)"],
            "Destination Port": ["Rotterdam Depot", "Baltimore Metal Vault", "Tokyo Gas Terminal"],
            "AIS Status": ["🟢 In Transit (14.2 knots)", "🟡 Anchored / Queue (+3 Days)", "🟢 In Transit (16.0 knots)"],
            "Contango Arbitrage Status": ["In the Money (+$1.80/Bbl)", "Spread Secured", "In the Money"]
        })
        st.dataframe(ais_vessels, use_container_width=True)
        
    else:
        st.title("🌐 Global Logistics Network & GIS Control Tower")
        st.caption(f"Active Persona View: **{persona}**")
        
        gis_nodes = pd.DataFrame({
            "Name": [plant1_name, plant2_name, toller_name, "Chicago Logistics Hub", "Frankfurt Regional DC"],
            "lat": [42.3314, 48.1351, 32.7767, 41.8781, 50.1109],
            "lon": [-83.0458, 11.5820, -96.7970, -87.6298, 8.6821],
            "Category": ["Manufacturing Plant", "Manufacturing Plant", "3rd-Party CMO", "Warehouse DC", "Warehouse DC"],
            "Size": [20, 20, 15, 18, 18]
        })
        fig_map = px.scatter_mapbox(gis_nodes, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=450)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

# =====================================================================
# MODULE 7: INTEGRATION ENDPOINTS
# =====================================================================
elif "Integration" in selected_module:
    st.title("🔌 Integration & Architecture Endpoints")
    st.caption("Live system integration waypoints, REST/GraphQL endpoints, and enterprise API connections.")
    
    endpoints = [
        {"Tab / Module": "Executive / Balance Sheet", "Protocol": "REST / FIX", "Endpoint URL": "/api/v1/finance/position-ledger", "Status": "🟢 ACTIVE 200 OK"},
        {"Tab / Module": "NLP / Satellite Intelligence", "Protocol": "Webhook / RSS", "Endpoint URL": "/api/v1/macro/satellite-feed", "Status": "🟢 ACTIVE 200 OK"},
        {"Tab / Module": "Physical Procurement / Off-Take", "Protocol": "REST / OData", "Endpoint URL": "/api/v1/procurement/offtake-bridge", "Status": "🟢 ACTIVE 200 OK"},
        {"Tab / Module": "CTRM Hedging Desk", "Protocol": "FIX 4.4", "Endpoint URL": "/api/v1/ctrm/fix-order-execution", "Status": "🟢 ACTIVE 200 OK"},
        {"Tab / Module": "GIS / Maritime AIS Tower", "Protocol": "WebSocket / AIS", "Endpoint URL": "/api/v1/gis/vessel-ais-telemetry", "Status": "🟢 ACTIVE 200 OK"}
    ]
    st.dataframe(pd.DataFrame(endpoints), use_container_width=True)

# SIDEBAR RISK INJECTOR
st.sidebar.markdown("---")
st.sidebar.subheader("🌋 Risk Scenario Injector")
st.sidebar.info(f"📡 Active Disruption: **{st.session_state['active_disruption']}**")
