import re, os

# Target file paths
feeds_file = "robot_feeds.py" if os.path.exists("robot_feeds.py") else "robot_feeds.txt"
main_file = "main.py" if os.path.exists("main.py") else "main-Oct 30th_2.txt"

# --- 1. UPDATE ROBOT_FEEDS.PY ---
with open(feeds_file, "r") as f:
    feeds_code = f.read()

new_feeds_helpers = '''
COMMODITY_BOOLEAN_TEMPLATES = {
    "metals": '("copper cathode" OR "aluminum" OR "zinc" OR "lithium" OR "nickel") AND ("smelter shutdown" OR "TC/RC" OR "warehouse stock" OR strike)',
    "energy": '("brent crude" OR "WTI" OR "natural gas" OR "LNG" OR "petrochemical") AND ("OPEC" OR "refinery outage" OR "feedgas" OR "inventory draw")',
    "agriculture": '("milling wheat" OR "corn" OR "arabica coffee" OR "palm oil" OR "soybean") AND ("frost" OR "drought" OR "crop yield" OR "export quota")',
    "fertilizer": '("urea" OR "ammonia" OR "caustic soda" OR "sulfuric acid" OR "potash") AND ("gas feedstock" OR "plant outage" OR "tender")',
    "freight": '("Red Sea" OR "Suez Canal" OR "Panama Canal" OR "Baltic Dry") AND (rerouting OR "spot rate" OR "congestion" OR "demurrage")'
}

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

def render_rss_breaking_news_stream():
    with st.expander("📰 Unified Social Media & Executive Field Intelligence Stream", expanded=True):
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

        topic = st.selectbox(
            "Select Commodity Intelligence Sector Feed:",
            sectors,
            index=current_idx,
            key="rss_sector_topic_select"
        )
        st.session_state["selected_sector"] = topic

        articles = fetch_live_genspark_multi_channel(topic=topic, commodity_name=topic)
        
        if not articles:
            st.info(f"No live breaking news feeds available for {topic}.")
            return

        for idx, art in enumerate(articles):
            with st.container(border=True):
                rcol1, rcol2 = st.columns([3, 1])
                with rcol1:
                    st.caption(f"**{art.get('source', 'Intelligence Stream')}** | Sector: **{topic}** | Published: {art.get('published', 'Recent')}")
                    st.markdown(f"#### {art.get('title')}")
                with rcol2:
                    si = float(art.get('sentiment', art.get('sentiment_score', -0.33)))
                    imp = art.get('estimated_impact', art.get('impact_demand', 18500))
                    st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                    st.caption(f"Demand Surge: +{imp:,} Units")
                    
                    if st.button(f"⚡ Ingest RSS #{idx+1}", key=f"btn_rss_ingest_{idx}", use_container_width=True):
                        st.session_state["platform_si_override"] = si
                        st.session_state["platform_demand_impact"] = imp
                        st.session_state["platform_active_signal"] = art.get('title', '')
                        st.toast(f"⚡ Ingested RSS News Item #{idx+1} into Platform State!")
                        st.rerun()
'''

pattern_genspark = r"def render_genspark_overlay\(\):[\s\S]*?(?=\ndef |\Z)"
pattern_rss = r"def render_rss_breaking_news_stream\(\):[\s\S]*?(?=\ndef |\Z)"

if "categorize_commodity_sector" not in feeds_code:
    feeds_code = new_feeds_helpers + "\n\n" + feeds_code
else:
    feeds_code = re.sub(pattern_genspark, "", feeds_code)
    feeds_code = re.sub(pattern_rss, "", feeds_code)
    feeds_code += "\n\n" + new_feeds_helpers

with open(feeds_file, "w") as f:
    f.write(feeds_code)
print(f"✅ Successfully updated {feeds_file} (Tab 1 Top & Bottom sector stream synchronized).")

# --- 2. UPDATE MAIN.PY ---
with open(main_file, "r") as f:
    main_code = f.read()

updated_render_nlp = '''
def render_nlp_commercial_sensing(persona="Commercial Commodities & Trading Enterprise"):
    st.title("🧠 Alternative Data & Sentiment Vector Matrix")
    st.caption("A data-driven commodity intelligence and machine-learning forecasting platform providing real-time cargo tracking, supply/demand projections, and backtested analytics across 50+ commodities.")
    
    if "selected_sector" not in st.session_state:
        st.session_state["selected_sector"] = "Metals & Mining"

    tab1, tab2, tab3 = st.tabs([
        "📡 Live Web, Macro & Social Signals", 
        "📧 Email & Event Debrief Parser", 
        "⚓ Freight, Weather & Black Swan Feeds"
    ])
    
    with tab1:
        st.subheader("📡 Live Genspark Tactical Market Signals")
        rf.render_genspark_overlay()

        rf.render_predictive_commodity_engine()

        rf.render_macro_telemetry_bar()

        rf.render_triangulated_sentiment_section()

        rf.render_rss_breaking_news_stream()

    with tab2:
        st.subheader("📧 Executive Email & Field Intelligence Debrief Stream")
        st.caption("Parsing post-trade show debriefs, executive LinkedIn disclosures, and CFO field updates before ERP entry.")
        
        active_sector = st.session_state.get("selected_sector", "Metals & Mining")
        st.info(f"🏢 Active Sector Filter: **{active_sector}**")
        
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            raw_debriefs = sig_data.get("email_debriefs", sig_data.get("field_intelligence", []))
        except Exception:
            raw_debriefs = []
        
        debrief_list = [d for d in raw_debriefs if d.get("sector") == active_sector]
        if not debrief_list:
            debrief_list = [d for d in raw_debriefs if any(w in d.get("title", "").lower() or w in d.get("author", "").lower() or w in d.get("commodity", "").lower() for w in active_sector.lower().split())]
        if not debrief_list:
            debrief_list = raw_debriefs[:4]
        
        if not debrief_list:
            st.info("No active executive event debriefs available.")
        else:
            cols_t2 = st.columns(2)
            for idx, item in enumerate(debrief_list):
                with cols_t2[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Executive Briefing')}** | **{item.get('author', 'Field Sourcing')}** | Sector: **{item.get('sector', active_sector)}**")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Debrief'))}")
                        st.write(item.get('content', 'Executive field intelligence report regarding spot supply constraints.'))
                        si = float(item.get('sentiment_score', -0.33))
                        st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                        
                        if st.button(f"⚡ Ingest Debrief #{idx+1}", key=f"btn_tab2_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 15400)
                            st.session_state["platform_leadtime_impact"] = item.get("impact_leadtime", 4.2)
                            st.session_state["platform_active_signal"] = item.get("headline", item.get("title", ""))
                            st.toast(f"⚡ Executive Debrief #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()

    with tab3:
        st.subheader("⚓ Live Maritime Freight, Weather & Black Swan Feeds")
        st.caption("Real-time ocean/air spot freight indices, NOAA severe weather tracking, and geopolitical chokepoints.")
        
        rf.render_freight_weather_blackswan_tab()

        st.markdown("---")
        st.markdown("#### 📡 Real-time Telemetry Incident Stream")
        
        try:
            with open("robot_signals.json", "r") as f:
                sig_data = json.load(f)
            freight_list = sig_data.get("freight_telemetry_feeds", sig_data.get("freight_weather_feeds", []))
        except Exception:
            freight_list = []
        
        if freight_list:
            cols_t3 = st.columns(2)
            for idx, item in enumerate(freight_list):
                with cols_t3[idx % 2]:
                    with st.container(border=True):
                        st.caption(f"**{item.get('source', 'Telemetry Feed')}** | Corridor: **{item.get('commodity', 'Logistics')}**")
                        st.markdown(f"#### {item.get('headline', item.get('title', 'Freight Disruption'))}")
                        si = float(item.get('sentiment_score', -0.42))
                        lt = float(item.get('impact_leadtime', 4.5))
                        st.metric("Lead Time Drag", f"+{lt:.1f} Days", delta=f"SI: {si:+.2f}")
                        
                        if st.button(f"⚡ Ingest Freight Signal #{idx+1}", key=f"btn_tab3_ingest_{idx}", use_container_width=True):
                            st.session_state["platform_si_override"] = si
                            st.session_state["platform_leadtime_impact"] = lt
                            st.session_state["platform_demand_impact"] = item.get("impact_demand", 16500)
                            st.session_state["platform_active_signal"] = item.get("headline", "")
                            st.toast(f"⚡ Freight Disruption Signal #{idx+1} Ingested into S&OP Platform!")
                            st.rerun()
'''

pattern_nlp = r"def render_nlp_commercial_sensing\([\s\S]*?(?=\n# MODULE 4|\ndef render_demand_supply_match|\Z)"
main_code = re.sub(pattern_nlp, updated_render_nlp.strip() + "\n\n", main_code)

with open(main_file, "w") as f:
    f.write(main_code)
print(f"✅ Successfully updated {main_file} (Tab 2 debriefs & Tab 3 telemetry preserved).")
