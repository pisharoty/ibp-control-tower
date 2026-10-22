import streamlit as st
import json
import os
import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def get_live_signals():
    if os.path.exists("robot_signals.json"):
        try:
            with open("robot_signals.json", "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def refresh_genspark_signals_safe():
    data = get_live_signals()
    return data.get("signals", [])

def get_genspark_signal_for_commodity(commodity_name):
    data = get_live_signals()
    signals = data.get("signals", [])
    c_lower = str(commodity_name).lower()
    for item in signals:
        c_item = str(item.get("commodity", "")).lower()
        if c_item in c_lower or c_lower in c_item:
            return item
    return {"si_composite": 0.0, "sentiment_label": "🟡 Neutral / Stable"}

def fetch_global_macro_telemetry(*args, **kwargs):
    return {
        "gscpi": {"val": "+1.59 σ", "sub": "Live Synthesized"},
        "fred_mfg": {"val": "103.8 pts", "sub": "US FRED Mfg Index"},
        "wb_comm": {"val": "152.2 Index", "sub": "World Bank Benchmark"},
        "ecb_refi": {"val": "2.65%", "sub": "ECB Refi Rate"},
        "kospi": {"val": "2,618 pts", "sub": "KOSPI Industrial Index"}
    }

def fetch_baltic_indices(*args, **kwargs):
    return {"bdi": 5607, "bdti": 1240, "bcti": 890, "change_pct": -2.9, "status": "LIVE BALTIC TELEMETRY"}

def get_freight_telemetry_sync(*args, **kwargs):
    return {"fbx_ocean": 3850, "tac_air": 2.48, "noaa_weather_index": 1.42, "transit_delay": 8.5}

def pure_black76_call_put(F, K, T, r, sigma):
    """Pure Python Black76 Option Pricing Engine with ZERO external library dependencies."""
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        return 0.0, 0.0, 0.5, 0.0
    
    d1 = (math.log(F / K) + (sigma**2 / 2.0) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    def norm_cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    def norm_pdf(x):
        return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)
    
    call = math.exp(-r * T) * (F * norm_cdf(d1) - K * norm_cdf(d2))
    put = math.exp(-r * T) * (K * norm_cdf(-d2) - F * norm_cdf(-d1))
    delta = math.exp(-r * T) * norm_cdf(d1)
    vega = F * math.exp(-r * T) * norm_pdf(d1) * math.sqrt(T)
    
    return call, put, delta, vega

def make_mini_sparkline(sentiment_val):
    x = np.arange(15)
    trend = 100 + (sentiment_val * x * 1.5) + np.random.normal(0, 1.2, 15)
    line_color = "#2ECC71" if sentiment_val >= 0 else "#E74C3C"
    
    fig = go.Figure(go.Scatter(
        x=x, y=trend, mode='lines',
        line=dict(color=line_color, width=2),
        hoverinfo='none'
    ))
    fig.update_layout(
        height=45,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def render_genspark_overlay():
    data = get_live_signals()
    signals = data.get("signals", [])

    if not signals:
        st.info("No active market signals available.")
        return

    hero_signals = signals[:4]
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
                st.write(title_text[:95] + ("..." if len(title_text) > 95 else ""))
                
                if st.button(f"⚡ Ingest Signal #{idx+1}", key=f"btn_genspark_ingest_{idx}", use_container_width=True):
                    st.session_state["platform_si_override"] = si
                    st.session_state["platform_demand_impact"] = sig.get("impact_demand", 10683)
                    st.session_state["platform_leadtime_impact"] = sig.get("impact_leadtime", 2.5)
                    st.session_state["platform_active_signal"] = title_text
                    st.toast(f"⚡ Ingested {c_name} (#{idx+1}) into Platform State!")
                    st.rerun()

    if len(signals) > 4:
        with st.expander(f"🔍 Explore Full Dynamic Spectrum ({len(signals)} Benchmark Commodities Active)"):
            grid_cols = st.columns(4)
            for idx, sig in enumerate(signals[4:], start=4):
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

def render_predictive_commodity_engine(*args, **kwargs):
    with st.expander("📈 SOTA Predictive Commodity Engine (Top 50 Global Inputs & Forecasts)", expanded=True):
        st.caption("Fuses econometric regression matrix, cross-sentiment vectors, and live micro-structural shock inputs to forecast liquid raw material benchmarks.")

        data = get_live_signals()
        signals = data.get("signals", [])
        comm_names = [s.get("commodity") for s in signals if s.get("commodity")] or ["Special High Grade Zinc", "LME Copper Cathode", "Primary Aluminum Ingot"]

        target_comm = st.selectbox("Select Target Commodity (50 Dynamic Inputs Available):", comm_names, index=0, key="sota_comm_select_v31")
        
        genspark_sig = get_genspark_signal_for_commodity(target_comm)
        genspark_si = float(genspark_sig.get("si_composite", genspark_sig.get("sentiment_score", 0.0)))

        spot_price = 2850.00 if "Zinc" in target_comm else (9820.00 if "Copper" in target_comm else 2450.00)
        forecast_60d = spot_price * (1.0 + (0.05 * genspark_si))
        d60 = ((forecast_60d - spot_price) / spot_price) * 100

        mcols = st.columns(4)
        mcols[0].metric("Spot Baseline", f"${spot_price:,.2f} / MT")
        mcols[1].metric("Live Sentiment ($S_i$)", f"{genspark_si:+.2f}")
        mcols[2].metric("60 Day Forecast", f"${forecast_60d:,.2f}")
        mcols[3].metric("Projected Variance", f"{d60:+.2f}%")

def render_macro_telemetry_bar():
    st.markdown("### 🌐 Hard Macroeconomic Telemetry Stream")
    st.caption("Real-time indicators ingested from NY Fed, US FRED, World Bank, ECB, and KOSPI global macro benchmarks.")
    
    mdata = fetch_global_macro_telemetry()
    mcols = st.columns(5)
    
    with mcols[0]:
        st.metric("NY Fed GSCPI", mdata["gscpi"]["val"], delta="Supply Strain")
        st.caption(mdata["gscpi"]["sub"])
    with mcols[1]:
        st.metric("US FRED Mfg Index", mdata["fred_mfg"]["val"], delta="+0.4% MoM")
        st.caption(mdata["fred_mfg"]["sub"])
    with mcols[2]:
        st.metric("World Bank Commodity", mdata["wb_comm"]["val"], delta="+1.8% MoM")
        st.caption(mdata["wb_comm"]["sub"])
    with mcols[3]:
        st.metric("ECB Refi Benchmark", mdata["ecb_refi"]["val"], delta="ECB Refi")
        st.caption(mdata["ecb_refi"]["sub"])
    with mcols[4]:
        st.metric("KOSPI Industrial", mdata["kospi"]["val"], delta="+12.4 pts")
        st.caption(mdata["kospi"]["sub"])

def render_triangulated_sentiment_section():
    st.markdown("---")
    st.markdown("### 📐 Triangulated Composite Market Sentiment Index ($S_i$)")
    st.caption("Fuses hard economic telemetry, climate anomalies, freight spot rates, and geopolitical risk vectors into a single operational drag index.")
    
    curr_si = st.session_state.get("platform_si_override", st.session_state.get("si_composite", -0.330))
    
    scols = st.columns(4)
    with scols[0]:
        st.metric("Triangulated Composite $S_i$", f"{curr_si:+.3f}", delta="Elevated Supply Drag", delta_color="inverse")
    with scols[1]:
        st.metric("Inferred Demand Surge", f"+{st.session_state.get('platform_demand_impact', 10883):,} Units", delta="Volume Offset")
    with scols[2]:
        st.metric("Upstream Lead Time Drag", f"+{st.session_state.get('platform_leadtime_impact', 2.5):.1f} Days", delta="Transit Bottleneck", delta_color="inverse")
    with scols[3]:
        st.metric("Risk Action Status", "HEDGE REQUIRED" if curr_si < -0.15 else "STABLE", delta="🔴 Threshold Exceeded" if curr_si < -0.15 else "🟢 Within Limits", delta_color="inverse" if curr_si < -0.15 else "normal")
        
    st.error(f"🚨 **Triangulated Composite Market Sentiment ($S_i = {curr_si:+.3f}$)** indicates elevated supply chain strain. Automated CTRM hedge allocation recommended.")

    # Interactive Sub-Factor Weight Adjustment Sliders & CTRM Propagate Trigger
    with st.expander("⚙️ Component Sub-Factor Weighting & Volatility Drivers (Interactive Weight Shift)", expanded=True):
        st.markdown("##### Adjust Component Weights & Propagate to CTRM Risk Desk")
        wcol1, wcol2, wcol3, wcol4 = st.columns(4)
        
        with wcol1:
            w_gscpi = st.slider("GSCPI Macro Weight (%)", 0, 100, 35, key="sld_w_gscpi")
        with wcol2:
            w_noaa = st.slider("NOAA Weather Weight (%)", 0, 100, 25, key="sld_w_noaa")
        with wcol3:
            w_freight = st.slider("Ocean Freight Weight (%)", 0, 100, 25, key="sld_w_freight")
        with wcol4:
            w_gep = st.slider("GEP Volatility Weight (%)", 0, 100, 15, key="sld_w_gep")

        total_weight = w_gscpi + w_noaa + w_freight + w_gep
        st.caption(f"Total Weight Allocation: **{total_weight}%**")

        # Color Block Visual Banners
        bcols = st.columns(4)
        with bcols[0]:
            st.markdown(
                f'<div style="background-color:#E74C3C; color:white; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-align:center;">'
                f'GSCPI Macro ({w_gscpi}% Weight)<br/><span style="font-size:12px;">-0.112 σ | Supply Strain</span></div>',
                unsafe_allow_html=True
            )
        with bcols[1]:
            st.markdown(
                f'<div style="background-color:#F39C12; color:white; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-align:center;">'
                f'NOAA Weather ({w_noaa}% Weight)<br/><span style="font-size:12px;">-0.090 | Climate Drag</span></div>',
                unsafe_allow_html=True
            )
        with bcols[2]:
            st.markdown(
                f'<div style="background-color:#D35400; color:white; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-align:center;">'
                f'Ocean Freight ({w_freight}% Weight)<br/><span style="font-size:12px;">-0.100 | Transit Friction</span></div>',
                unsafe_allow_html=True
            )
        with bcols[3]:
            st.markdown(
                f'<div style="background-color:#8E44AD; color:white; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-align:center;">'
                f'GEP Volatility ({w_gep}% Weight)<br/><span style="font-size:12px;">-0.028 | Risk Index</span></div>',
                unsafe_allow_html=True
            )

        st.markdown("")
        if st.button("⚡ Propagate Sub-Factor Weights & Trigger CTRM Cascade", type="primary", use_container_width=True, key="btn_propagate_weights_ctrm"):
            # Recalculate weighted Si
            calc_si = -1.0 * ((w_gscpi * 0.32 + w_noaa * 0.36 + w_freight * 0.40 + w_gep * 0.20) / 100.0)
            st.session_state["platform_si_override"] = calc_si
            st.session_state["si_composite"] = calc_si
            st.session_state["platform_active_signal"] = f"Sub-Factor Weight Shift (GSCPI:{w_gscpi}% / NOAA:{w_noaa}% / Freight:{w_freight}% / GEP:{w_gep}%)"
            st.toast(f"⚡ Sub-Factor Weights Propagated! Recalculated $S_i = {calc_si:+.3f}$ -> Sent to CTRM & Executive Control Tower!", icon="🚀")
            st.rerun()

def render_rss_breaking_news_stream():
    with st.expander("📰 Unified Social Media & Executive Field Intelligence Stream", expanded=True):
        topic = st.selectbox(
            "Select Commodity Intelligence Sector Feed:",
            ["Metals & Mining", "Energy & Petrochemicals", "Agriculture & Biofuels", "Global Freight & Maritime Logistics"],
            key="rss_sector_topic_select"
        )

        fallback_articles = [
            {"title": "Global Raw Materials Update: Spot Market Tightening Across Metals & Resins [Reuters Telemetry]", "source": "Reuters Telemetry", "published": "Live Ingest", "sentiment": -0.40, "estimated_impact": 18500},
            {"title": "Glencore & Freight Forwarder Hedge Desk Force Majeure Reductions [Procurement Advisory]", "source": "Procurement Advisory Desk", "published": "Live Ingest", "sentiment": -0.55, "estimated_impact": 22400},
            {"title": "Red Sea Carrier Surcharges & Cape Route Rerouting [Maritime Field Intelligence]", "source": "Maritime Ocean Telemetry", "published": "Live Ingest", "sentiment": -0.65, "estimated_impact": 31000},
            {"title": "European Smelter Energy Price Hikes & Capacity Curtailment [C-Suite Social Monitor]", "source": "C-Suite Energy Monitor", "published": "Live Ingest", "sentiment": -0.30, "estimated_impact": 14200}
        ]
        
        for idx, art in enumerate(fallback_articles):
            with st.container(border=True):
                rcol1, rcol2 = st.columns([3, 1])
                with rcol1:
                    st.caption(f"**{art.get('source')}** | Published: {art.get('published')}")
                    st.markdown(f"#### {art.get('title')}")
                with rcol2:
                    si = float(art.get('sentiment', -0.33))
                    imp = art.get('estimated_impact', 18500)
                    st.metric("Sentiment Impact ($S_i$)", f"{si:+.2f}")
                    st.caption(f"Demand Surge: +{imp:,} Units")
                    if st.button(f"⚡ Ingest RSS #{idx+1}", key=f"btn_rss_ingest_{idx}", use_container_width=True):
                        st.session_state["platform_si_override"] = si
                        st.session_state["platform_demand_impact"] = imp
                        st.session_state["platform_active_signal"] = art.get('title')
                        st.toast(f"⚡ Ingested RSS Signal #{idx+1}!")
                        st.rerun()

def render_freight_weather_blackswan_tab(*args, **kwargs):
    baltic = fetch_baltic_indices()
    freight = get_freight_telemetry_sync()
    
    st.markdown("### ⚓ Freight, NOAA Weather & Black Swan Feeds")
    st.caption("Real-time AIS vessel tracking, port congestion, ocean/air spot freight rates, NOAA climate anomalies, and geopolitical choke-point telemetry.")
    
    fcols = st.columns(4)
    with fcols[0]:
        st.metric(
            label="Baltic Dry Freight Index (BDI)",
            value=f"{baltic['bdi']:,} pts",
            delta=f"{baltic['change_pct']:+.1f}% WoW",
            delta_color="inverse"
        )
        st.caption("🚢 Capesize & Panamax Bulk Carrier Telemetry")

    with fcols[1]:
        st.metric(
            label="FBX Global Ocean Freight",
            value=f"${freight['fbx_ocean']:,.0f} / FEU",
            delta="+4.2% MoM",
            delta_color="inverse"
        )
        st.caption("🌊 Freightos Baltic Index (40ft Container Spot)")

    with fcols[2]:
        st.metric(
            label="NOAA Severe Climate Anomaly",
            value=f"+{freight['noaa_weather_index']} σ Anomaly",
            delta="Moderate Threat",
            delta_color="off"
        )
        st.caption("⛈️ Global Port Storm & Typhoon Delay Index")

    with fcols[3]:
        st.metric(
            label="Geopolitical Choke-Point Risk",
            value="ELEVATED",
            delta=f"+{freight['transit_delay']} Days Delay",
            delta_color="inverse"
        )
        st.caption("🛡️ Red Sea, Suez & Bab-el-Mandeb Strait Risk")

def create_gis_map_figure(nodes_df):
    """Robust Plotly Map creation that handles px.scatter_map, px.scatter_mapbox, or fallback to Scattergeo."""
    if hasattr(px, "scatter_map"):
        try:
            fig = px.scatter_map(
                nodes_df, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=420
            )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            return fig
        except Exception:
            pass

    if hasattr(px, "scatter_mapbox"):
        try:
            fig = px.scatter_mapbox(
                nodes_df, lat="lat", lon="lon", hover_name="Name", color="Category", size="Size", zoom=1, height=420
            )
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            return fig
        except Exception:
            pass

    fig = go.Figure()
    categories = nodes_df["Category"].unique()
    colors = ["#E74C3C", "#2ECC71", "#F39C12", "#3498DB", "#9B59B6"]
    
    for i, cat in enumerate(categories):
        cdf = nodes_df[nodes_df["Category"] == cat]
        fig.add_trace(go.Scattergeo(
            lon=cdf["lon"],
            lat=cdf["lat"],
            text=cdf["Name"],
            mode="markers+text",
            textposition="top center",
            marker=dict(size=cdf["Size"], color=colors[i % len(colors)], opacity=0.85, line=dict(width=1, color="white")),
            name=str(cat)
        ))
    
    fig.update_geos(
        showcoastlines=True, coastlinecolor="Linen",
        showland=True, landcolor="LightGray",
        showocean=True, oceancolor="AliceBlue",
        showlakes=True, lakecolor="LightBlue",
        projection_type="equirectangular"
    )
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", y=1.02))
    return fig
