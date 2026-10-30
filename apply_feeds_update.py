import re

# Load target file (supports robot_feeds.py or robot_feeds.txt)
target_file = "robot_feeds.py" if __import__("os").path.exists("robot_feeds.py") else "robot_feeds.txt"

with open(target_file, "r") as f:
    code = f.read()

# Categorization function definition
sector_helper = '''
def categorize_commodity_sector(commodity_name):
    c = str(commodity_name).lower()
    if any(k in c for k in ["wheat", "corn", "coffee", "sugar", "palm", "soybean", "biodiesel", "ethanol"]):
        return "Agriculture & Biofuels"
    elif any(k in c for k in ["crude", "oil", "gas", "ethylene", "propylene", "methanol", "benzene", "toluene", "xylene", "coal", "brent"]):
        return "Energy & Petrochemicals"
    elif any(k in c for k in ["soda", "chlorine", "acid", "potassium", "mop", "urea", "ammonia"]):
        return "Fertilizers & Industrial Chemicals"
    elif any(k in c for k in ["logistics", "freight", "canal", "ocean", "air", "barge"]):
        return "Global Freight & Maritime Logistics"
    else:
        return "Metals & Mining"
'''

# Replacement for render_genspark_overlay
new_render_genspark = '''
def render_genspark_overlay():
    data = get_live_signals()
    signals = data.get("signals", [])

    if not signals:
        st.info("No active market signals available.")
        return

    if "selected_sector" not in st.session_state:
        st.session_state["selected_sector"] = "Metals & Mining"

    sectors = [
        "Metals & Mining",
        "Energy & Petrochemicals",
        "Agriculture & Biofuels",
        "Fertilizers & Industrial Chemicals",
        "Global Freight & Maritime Logistics"
    ]
    
    current_idx = sectors.index(st.session_state["selected_sector"]) if st.session_state["selected_sector"] in sectors else 0
    
    selected_sector = st.selectbox(
        "⚡ Filter Tactical Signals by Sector Focus:",
        sectors,
        index=current_idx,
        key="genspark_overlay_sector_select"
    )
    st.session_state["selected_sector"] = selected_sector

    matching_signals = [s for s in signals if categorize_commodity_sector(s.get("commodity", s.get("metal", ""))) == selected_sector]
    if not matching_signals:
        matching_signals = signals[:4]

    hero_signals = matching_signals[:4]
    cols = st.columns(4)
    for idx, sig in enumerate(hero_signals):
        with cols[idx]:
            with st.container(border=True):
                si = float(sig.get('sentiment_score', sig.get('si_composite', -0.20)))
                c_name = sig.get('metal') or sig.get('commodity') or 'Commodity'
                
                st.caption(f"**{c_name}**")
                st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                st.plotly_chart(make_mini_sparkline(si), use_container_width=True, config={'displayModeBar': False})
                
                badge_label = sig.get('sentiment_label') or ("🟢 Bullish Surge" if si > 0.15 else ("🔴 Bearish Drag" if si < -0.15 else "🟡 Neutral / Mixed"))
                st.caption(badge_label)
                
                title_text = sig.get('title') or sig.get('headline_summary') or 'Market signal update.'
                st.write(title_text[:90] + ("..." if len(title_text) > 90 else ""))
                
                if st.button(f"⚡ Ingest Signal #{idx+1}", key=f"btn_genspark_ingest_{idx}", use_container_width=True):
                    st.session_state["platform_si_override"] = si
                    st.session_state["platform_demand_impact"] = sig.get("impact_demand", 10683)
                    st.session_state["platform_leadtime_impact"] = sig.get("impact_leadtime", 2.5)
                    st.session_state["platform_active_signal"] = title_text
                    st.toast(f"⚡ Ingested {c_name} (#{idx+1}) into Platform State!")
                    st.rerun()

    if len(matching_signals) > 4:
        with st.expander(f"🔍 Explore Full {selected_sector} Spectrum ({len(matching_signals)} Benchmarks Active)"):
            grid_cols = st.columns(4)
            for idx, sig in enumerate(matching_signals[4:], start=4):
                with grid_cols[idx % 4]:
                    with st.container(border=True):
                        si = float(sig.get('sentiment_score', sig.get('si_composite', 0.0)))
                        c_name = sig.get('metal') or sig.get('commodity')
                        st.caption(f"**{c_name}**")
                        st.metric("Sentiment ($S_i$)", f"{si:+.2f}")
                        st.write(sig.get('title', '')[:80] + "...")
                        if st.button(f"⚡ Ingest #{idx+1}", key=f"btn_exp_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_demand_impact"] = sig.get("impact_demand", 10000)
                            st.session_state["platform_leadtime_impact"] = sig.get("impact_leadtime", 2.0)
                            st.session_state["platform_active_signal"] = sig.get('title', '')
                            st.toast(f"⚡ Ingested {c_name} (#{idx+1})!")
                            st.rerun()

    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        active_sig = st.session_state.get("platform_active_signal", "Baseline Operations (No Active Signal Ingested)")
        st.info(f"**Active Ingested Signal**: {active_sig}")
    with c2:
        if st.button("🔄 Refresh Live Feeds & APIs", key="btn_refresh_feeds_genspark", use_container_width=True):
            st.toast("🔄 Fetching latest market telemetry from feeds...")
            st.rerun()
'''

# Inject sector helper if missing
if "def categorize_commodity_sector" not in code:
    code = sector_helper + "\n\n" + code

# Replace render_genspark_overlay implementation
pattern = r"def render_genspark_overlay\(\):[\s\S]*?(?=\ndef |\Z)"
updated_code = re.sub(pattern, new_render_genspark.strip(), code)

with open(target_file, "w") as f:
    f.write(updated_code)

print(f"✅ Successfully updated {target_file}.")
