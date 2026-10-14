import numpy as np
import pandas as pd
import streamlit as st

# =========================================================================
# TOP 50 GLOBAL COMMODITY REFERENCE REGISTRY
# =========================================================================
TOP_50_COMMODITIES_REGISTRY = {
    # Industrial & Base Metals (1-10)
    "LME Copper Cathode": {"category": "Base Metals", "unit": "MT", "default_cost": 9820.00},
    "Primary Aluminum Ingot": {"category": "Base Metals", "unit": "MT", "default_cost": 2450.00},
    "LME Primary Nickel": {"category": "Base Metals", "unit": "MT", "default_cost": 16800.00},
    "Special High Grade Zinc": {"category": "Base Metals", "unit": "MT", "default_cost": 2850.00},
    "Refined Lead Ingot": {"category": "Base Metals", "unit": "MT", "default_cost": 2100.00},
    "LME Refined Tin": {"category": "Base Metals", "unit": "MT", "default_cost": 31500.00},
    "Iron Ore Fines (62% Fe CFR China)": {"category": "Bulks & Steel", "unit": "dmt", "default_cost": 108.50},
    "Hot Rolled Coil Steel (US Midwest)": {"category": "Bulks & Steel", "unit": "ST", "default_cost": 820.00},
    "Coking / Metallurgical Coal": {"category": "Bulks & Steel", "unit": "MT", "default_cost": 240.00},
    "Ferro-Chrome (High Carbon)": {"category": "Minor Metals", "unit": "lb", "default_cost": 1.45},
    
    # Battery & Energy Transition Metals (11-15)
    "Battery-Grade Lithium Carbonate": {"category": "Battery Metals", "unit": "MT", "default_cost": 14200.00},
    "Cobalt Metal 99.8%": {"category": "Battery Metals", "unit": "MT", "default_cost": 28500.00},
    "Neodymium-Praseodymium Oxide (NdPr)": {"category": "Rare Earths", "unit": "kg", "default_cost": 58.00},
    "Class 1 Nickel Sulfate": {"category": "Battery Metals", "unit": "MT", "default_cost": 18200.00},
    "Polysilicon (Solar Grade)": {"category": "Energy Transition", "unit": "kg", "default_cost": 9.80},
    
    # Energy & Fuel Inputs (16-23)
    "Henry Hub Natural Gas": {"category": "Energy", "unit": "MMBtu", "default_cost": 3.16},
    "Brent Crude Oil": {"category": "Energy", "unit": "Bbl", "default_cost": 78.50},
    "WTI Crude Oil": {"category": "Energy", "unit": "Bbl", "default_cost": 74.20},
    "TTF Natural Gas (Europe Benchmark)": {"category": "Energy", "unit": "MWh", "default_cost": 38.50},
    "Ultra-Low Sulfur Diesel (ULSD)": {"category": "Energy", "unit": "Gal", "default_cost": 2.45},
    "Jet Fuel A-1": {"category": "Energy", "unit": "Bbl", "default_cost": 92.00},
    "API2 Rotterdam Coal": {"category": "Energy", "unit": "MT", "default_cost": 112.00},
    "EUA Carbon Allowances (ETS)": {"category": "Energy & Carbon", "unit": "MT", "default_cost": 68.40},
    
    # Precious Metals (24-27)
    "Gold Bullion (9999)": {"category": "Precious Metals", "unit": "oz t", "default_cost": 2650.00},
    "Silver Bullion": {"category": "Precious Metals", "unit": "oz t", "default_cost": 31.80},
    "Platinum Sponge": {"category": "Precious Metals", "unit": "oz t", "default_cost": 980.00},
    "Palladium Sponge": {"category": "Precious Metals", "unit": "oz t", "default_cost": 1050.00},

    # Agricultural Softs & Grains (28-37)
    "CBOT Milling Wheat": {"category": "Agriculture", "unit": "Bu", "default_cost": 5.85},
    "CBOT Yellow Corn": {"category": "Agriculture", "unit": "Bu", "default_cost": 4.25},
    "CBOT Soybeans": {"category": "Agriculture", "unit": "Bu", "default_cost": 10.12},
    "Crude Palm Oil (FCPO)": {"category": "Agriculture", "unit": "MT", "default_cost": 920.00},
    "ICE Arabica Coffee": {"category": "Agriculture", "unit": "lb", "default_cost": 2.45},
    "ICE Raw Sugar No. 11": {"category": "Agriculture", "unit": "lb", "default_cost": 0.22},
    "ICE Cotton No. 2": {"category": "Agriculture", "unit": "lb", "default_cost": 0.74},
    "Cocoa Bean (ICE London)": {"category": "Agriculture", "unit": "MT", "default_cost": 7400.00},
    "Natural Rubber (TSR20)": {"category": "Agriculture", "unit": "kg", "default_cost": 1.72},
    "Pulp (NBSK Northern Bleached Softwood)": {"category": "Forestry", "unit": "MT", "default_cost": 810.00},

    # Petrochemicals & Polymers (38-45)
    "High-Density Polyethylene (HDPE)": {"category": "Petrochemicals", "unit": "MT", "default_cost": 1150.00},
    "Polypropylene (PP Raffia)": {"category": "Petrochemicals", "unit": "MT", "default_cost": 1080.00},
    "Polyvinyl Chloride (PVC)": {"category": "Petrochemicals", "unit": "MT", "default_cost": 890.00},
    "Purified Terephthalic Acid (PTA)": {"category": "Petrochemicals", "unit": "MT", "default_cost": 760.00},
    "Methanol CFR China": {"category": "Petrochemicals", "unit": "MT", "default_cost": 310.00},
    "Ethylene Monomer": {"category": "Petrochemicals", "unit": "MT", "default_cost": 880.00},
    "Sulfuric Acid 98%": {"category": "Chemicals", "unit": "MT", "default_cost": 145.00},
    "Caustic Soda Flakes": {"category": "Chemicals", "unit": "MT", "default_cost": 420.00},

    # Logistics & Freight Surcharges (46-50)
    "FBX Ocean Freight Container Index": {"category": "Logistics", "unit": "FEU", "default_cost": 3380.00},
    "Baltic Dry Index (BDI)": {"category": "Logistics", "unit": "pts", "default_cost": 1850.00},
    "Air Freight Rate (Hong Kong - US West)": {"category": "Logistics", "unit": "kg", "default_cost": 5.20},
    "US Truckload Spot Rate": {"category": "Logistics", "unit": "Mile", "default_cost": 2.15},
    "Bunker Fuel 0.5% VLSFO": {"category": "Logistics", "unit": "MT", "default_cost": 610.00},
}


def init_session_state_inventory():
    """Initializes default commodity and finished goods inventory tables in st.session_state."""
    if "raw_materials_inventory" not in st.session_state:
        initial_raw = [
            {
                "Commodity Name": "LME Copper Cathode",
                "Category": "Base Metals",
                "On-Hand Stock": 125000.0,
                "Safety Stock": 45000.0,
                "Lead Time (Days)": 14.0,
                "Unit Cost ($)": 9820.00,
                "Primary Hub / Location": "Rotterdam Warehouse A",
            },
            {
                "Commodity Name": "Primary Aluminum Ingot",
                "Category": "Base Metals",
                "On-Hand Stock": 85000.0,
                "Safety Stock": 30000.0,
                "Lead Time (Days)": 10.0,
                "Unit Cost ($)": 2450.00,
                "Primary Hub / Location": "Singapore Freezone",
            },
            {
                "Commodity Name": "Henry Hub Natural Gas",
                "Category": "Energy",
                "On-Hand Stock": 500000.0,
                "Safety Stock": 150000.0,
                "Lead Time (Days)": 5.0,
                "Unit Cost ($)": 3.16,
                "Primary Hub / Location": "Henry Hub Terminal",
            },
        ]
        st.session_state["raw_materials_inventory"] = pd.DataFrame(initial_raw)

    if "finished_goods_inventory" not in st.session_state:
        initial_fg = [
            {
                "SKU Code": "FG-TR-1000",
                "Finished Product Name": "500 kVA Industrial Transformer",
                "Linked Primary Commodity": "LME Copper Cathode",
                "BOM Ratio (Units Raw / FG)": 12.5,
                "On-Hand Stock": 1200.0,
                "Safety Stock": 400.0,
                "Lead Time (Days)": 21.0,
                "Unit Build Cost ($)": 18500.00,
                "Assembly Plant": "Houston Plant #2",
            },
            {
                "SKU Code": "FG-HV-5000",
                "Finished Product Name": "Commercial HVAC Heat Exchanger",
                "Linked Primary Commodity": "Primary Aluminum Ingot",
                "BOM Ratio (Units Raw / FG)": 8.0,
                "On-Hand Stock": 3400.0,
                "Safety Stock": 1000.0,
                "Lead Time (Days)": 15.0,
                "Unit Build Cost ($)": 4200.00,
                "Assembly Plant": "Monterrey Assembly",
            },
        ]
        st.session_state["finished_goods_inventory"] = pd.DataFrame(initial_fg)


def get_commodity_inventory_position(commodity_name: str) -> dict:
    """Safe lookup helper to query user inventory levels without breaking downstream code."""
    init_session_state_inventory()
    df = st.session_state.get("raw_materials_inventory", pd.DataFrame())
    
    if not df.empty:
        match = df[df["Commodity Name"].str.contains(commodity_name, case=False, na=False)]
        if not match.empty:
            row = match.iloc[0]
            return {
                "on_hand": float(row["On-Hand Stock"]),
                "safety_stock": float(row["Safety Stock"]),
                "lead_time": float(row["Lead Time (Days)"]),
                "unit_cost": float(row["Unit Cost ($)"]),
                "location": str(row["Primary Hub / Location"]),
            }
    
    return {
        "on_hand": 100000.0,
        "safety_stock": 30000.0,
        "lead_time": 14.0,
        "unit_cost": TOP_50_COMMODITIES_REGISTRY.get(commodity_name, {}).get("default_cost", 5000.0),
        "location": "Primary Regional Vault (Auto-Fallback)",
    }


def render_inventory_position_manager():
    """Enterprise Inventory & Position Manager UI Panel."""
    init_session_state_inventory()

    st.subheader("📦 Enterprise Inventory & Position Manager")
    st.caption(
        "Configure baseline stock levels across the Top 50 Global Commodities or add custom client Finished Product SKUs. "
        "Provides $Q$ (Quantity) exposure parameters to the S&OP Control Tower."
    )

    c_demo1, c_demo2 = st.columns([3, 1])
    with c_demo1:
        st.info("💡 **Client Demo Mode**: Populate baseline inventory positions across all 50 global commodity benchmarks?")
    with c_demo2:
        if st.button("⚡ Load 50-Commodity Preset", type="primary", use_container_width=True):
            demo_list = []
            for name, details in TOP_50_COMMODITIES_REGISTRY.items():
                demo_list.append({
                    "Commodity Name": name,
                    "Category": details["category"],
                    "On-Hand Stock": float(np.random.randint(40000, 200000)),
                    "Safety Stock": float(np.random.randint(10000, 45000)),
                    "Lead Time (Days)": float(np.random.choice([7.0, 10.0, 14.0, 21.0])),
                    "Unit Cost ($)": details["default_cost"],
                    "Primary Hub / Location": "Global Logistics Hub",
                })
            st.session_state["raw_materials_inventory"] = pd.DataFrame(demo_list)
            st.toast("Populated baseline inventory across all 50 Global Commodities!", icon="🚀")
            st.rerun()

    st.divider()

    tab_raw, tab_fg, tab_import = st.tabs([
        "⛏️ Raw Materials & Top 50 Commodities",
        "🏭 Custom Client Finished Products & BOM",
        "📤 Bulk ERP Import / Export",
    ])

    with tab_raw:
        st.markdown("#### 🌐 Top 50 Commodity Drop-Down Selection")
        all_commodity_names = list(TOP_50_COMMODITIES_REGISTRY.keys())
        current_df_raw = st.session_state["raw_materials_inventory"]
        active_commodities = current_df_raw["Commodity Name"].tolist() if not current_df_raw.empty else []

        col_select, col_add = st.columns([3, 1])
        with col_select:
            selected_commodity_to_add = st.selectbox(
                "Select Commodity from Global Top 50 Registry:",
                options=[c for c in all_commodity_names if c not in active_commodities],
                index=0 if len([c for c in all_commodity_names if c not in active_commodities]) > 0 else None,
                key="select_top50_commodity",
            )
        with col_add:
            st.write(" ")
            st.write(" ")
            if st.button("➕ Add Commodity", type="secondary", use_container_width=True):
                if selected_commodity_to_add:
                    details = TOP_50_COMMODITIES_REGISTRY[selected_commodity_to_add]
                    new_row = {
                        "Commodity Name": selected_commodity_to_add,
                        "Category": details["category"],
                        "On-Hand Stock": 10000.0,
                        "Safety Stock": 2500.0,
                        "Lead Time (Days)": 14.0,
                        "Unit Cost ($)": details["default_cost"],
                        "Primary Hub / Location": "Primary Regional Vault",
                    }
                    updated_df = pd.concat([current_df_raw, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state["raw_materials_inventory"] = updated_df
                    st.toast(f"Added {selected_commodity_to_add}!", icon="✅")
                    st.rerun()

        st.markdown("##### 📝 Active Commodity Stock Positions (In-Line Editable)")
        edited_raw_df = st.data_editor(
            st.session_state["raw_materials_inventory"],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Commodity Name": st.column_config.TextColumn("Commodity Benchmark", disabled=True),
                "Category": st.column_config.TextColumn("Category", disabled=True),
                "On-Hand Stock": st.column_config.NumberColumn("On-Hand Balance", min_value=0.0, format="%,.1f"),
                "Safety Stock": st.column_config.NumberColumn("Safety Target", min_value=0.0, format="%,.1f"),
                "Lead Time (Days)": st.column_config.NumberColumn("Lead Time (Days)", min_value=0.5, format="%.1f"),
                "Unit Cost ($)": st.column_config.NumberColumn("Unit Cost ($)", min_value=0.0, format="$%,.2f"),
                "Primary Hub / Location": st.column_config.TextColumn("Hub / Location"),
            },
            key="raw_materials_editor",
        )

        if st.button("💾 Save Commodity Stock Balances", type="primary"):
            st.session_state["raw_materials_inventory"] = edited_raw_df
            st.toast("Saved raw material inventory positions!", icon="💾")
            st.rerun()

    with tab_fg:
        st.markdown("#### 🏭 Client Custom Finished Goods (FG) Builder")
        with st.expander("➕ Add New Custom Client SKU", expanded=False):
            with st.form("form_add_finished_product", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    fg_sku = st.text_input("SKU Code", value="FG-CUSTOM-001")
                    fg_name = st.text_input("Product Name", value="Industrial Motor 50HP")
                with col2:
                    fg_commodity = st.selectbox("Linked Raw Commodity (BOM)", options=all_commodity_names, index=0)
                    fg_bom_ratio = st.number_input("BOM Ratio (Units Raw / FG)", min_value=0.1, value=5.0, step=0.5)
                with col3:
                    fg_onhand = st.number_input("On-Hand Stock Units", min_value=0.0, value=500.0, step=50.0)
                    fg_safety = st.number_input("Safety Stock Target", min_value=0.0, value=150.0, step=25.0)

                fg_cost = st.number_input("Unit Build Cost ($)", min_value=0.0, value=2500.00, step=100.0)
                plant_loc = st.text_input("Assembly Plant", value="Main Assembly Facility")

                if st.form_submit_button("Submit Custom Product SKU"):
                    new_fg = {
                        "SKU Code": fg_sku,
                        "Finished Product Name": fg_name,
                        "Linked Primary Commodity": fg_commodity,
                        "BOM Ratio (Units Raw / FG)": fg_bom_ratio,
                        "On-Hand Stock": fg_onhand,
                        "Safety Stock": fg_safety,
                        "Lead Time (Days)": 14.0,
                        "Unit Build Cost ($)": fg_cost,
                        "Assembly Plant": plant_loc,
                    }
                    st.session_state["finished_goods_inventory"] = pd.concat(
                        [st.session_state["finished_goods_inventory"], pd.DataFrame([new_fg])],
                        ignore_index=True,
                    )
                    st.toast(f"Added SKU {fg_sku}!", icon="🏭")
                    st.rerun()

        st.markdown("##### 📝 Active Client Finished Goods Balances")
        edited_fg_df = st.data_editor(
            st.session_state["finished_goods_inventory"],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "SKU Code": st.column_config.TextColumn("SKU Code"),
                "Finished Product Name": st.column_config.TextColumn("Product Name"),
                "Linked Primary Commodity": st.column_config.SelectboxColumn("Linked Commodity", options=all_commodity_names),
                "BOM Ratio (Units Raw / FG)": st.column_config.NumberColumn("BOM Ratio", min_value=0.01, format="%.2f"),
                "On-Hand Stock": st.column_config.NumberColumn("On-Hand Units", min_value=0.0, format="%,.0f"),
                "Safety Stock": st.column_config.NumberColumn("Safety Target", min_value=0.0, format="%,.0f"),
                "Lead Time (Days)": st.column_config.NumberColumn("Lead Time (Days)", min_value=1.0, format="%.1f"),
                "Unit Build Cost ($)": st.column_config.NumberColumn("Build Cost ($)", min_value=0.0, format="$%,.2f"),
                "Assembly Plant": st.column_config.TextColumn("Plant Location"),
            },
            key="finished_goods_editor",
        )

        if st.button("💾 Save Finished Goods Balances", type="primary"):
            st.session_state["finished_goods_inventory"] = edited_fg_df
            st.toast("Saved finished goods positions!", icon="💾")
            st.rerun()

    with tab_import:
        st.markdown("#### 📤 Bulk ERP Import & Data Export")
        col_imp1, col_imp2 = st.columns(2)
        with col_imp1:
            st.markdown("##### 📥 Import CSV/Excel")
            target_table = st.radio("Target Stream:", ["Raw Materials / Commodities", "Finished Goods SKUs"])
            uploaded_file = st.file_uploader("Upload Inventory File", type=["csv", "xlsx"], key="file_uploader_inv")
            if uploaded_file is not None:
                try:
                    df_up = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    if target_table == "Raw Materials / Commodities":
                        st.session_state["raw_materials_inventory"] = df_up
                    else:
                        st.session_state["finished_goods_inventory"] = df_up
                    st.success(f"Imported {len(df_up)} records into {target_table}!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error reading file: {ex}")

        with col_imp2:
            st.markdown("##### 📊 Download Current Snapshot")
            raw_csv = st.session_state["raw_materials_inventory"].to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Commodities (CSV)", data=raw_csv, file_name="commodities_inventory.csv", mime="text/csv", use_container_width=True)
            fg_csv = st.session_state["finished_goods_inventory"].to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Finished Goods (CSV)", data=fg_csv, file_name="finished_goods_inventory.csv", mime="text/csv", use_container_width=True)
