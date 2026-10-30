import re, py_compile

with open("main.py", "r") as f:
    code = f.read()

# 1. Initialize session_state keys for macro scenario stress
init_mc_state = """
import streamlit as st

if "active_mc_scenario" not in st.session_state:
    st.session_state["active_mc_scenario"] = None
if "mc_expected_loss" not in st.session_state:
    st.session_state["mc_expected_loss"] = 0.0
if "mc_transit_delay" not in st.session_state:
    st.session_state["mc_transit_delay"] = 0.0
"""

if "active_mc_scenario" not in code:
    code = init_mc_state + "\n" + code

# 2. Add 'Inject Scenario' button to render_flight_simulator
mc_inject_btn = """
        if st.button("🚀 Inject Selected Stress Scenario into CTRM & S&OP Engine", key="btn_inject_mc"):
            st.session_state["active_mc_scenario"] = scenario_choice
            st.session_state["mc_expected_loss"] = expected_loss_m
            st.session_state["mc_transit_delay"] = mean_delay_days
            st.success(f"✅ **Scenario Injected Platform-Wide**: '{scenario_choice}' is now live across CTRM Risk Desk and S&OP EBITDA Waterfall (-${expected_loss_m:.2f}M Stress Drag).")

        if st.session_state.get("active_mc_scenario"):
            st.info(f"⚡ **Currently Active Injected Stress**: **{st.session_state['active_mc_scenario']}** (-${st.session_state['mc_expected_loss']:.2f}M Loss Impact)")
            if st.button("🔄 Reset / Clear Active Macro Stress", key="btn_clear_mc"):
                st.session_state["active_mc_scenario"] = None
                st.session_state["mc_expected_loss"] = 0.0
                st.session_state["mc_transit_delay"] = 0.0
                st.rerun()
"""

if "btn_inject_mc" not in code:
    target_bar = "st.bar_chart(chart_df.iloc[:100])"
    if target_bar in code:
        code = code.replace(target_bar, target_bar + "\n" + mc_inject_btn)

# 3. Update render_executive_sop to incorporate active MC scenario loss into Waterfall & Desk Feeds
sop_mc_updated = """def render_executive_sop(persona=None):
    st.header("📊 Global Trade Flows & S&OP Engine")
    st.caption("Integrated Business Planning, P&L EBITDA Margin Waterfall, and Live Desk Signal Synchronization.")

    rerouted = st.session_state.get("rerouted_vessels", [])
    hedges = st.session_state.get("executed_hedges", [])
    mc_scenario = st.session_state.get("active_mc_scenario", None)
    mc_loss = st.session_state.get("mc_expected_loss", 0.0)

    twin_data = get_digital_twin_telemetry_feed()
    total_transit_drag = 0.0
    for v in twin_data:
        v_name = v["vessel_name"]
        c_cost = v["carrying_cost_usd"]
        d_cost = v["demurrage_penalty_usd"]
        
        if any(r in v_name for r in rerouted):
            total_transit_drag += c_cost + 56958.90
        else:
            total_transit_drag += c_cost + d_cost

    drag_m = total_transit_drag / 1000000.0
    hedge_benefit = 3.25 + len(hedges) * 2.15
    base_aop = 120.0
    cogs = -70.0
    surge_rev = 10.0
    net_ebitda = base_aop + cogs + surge_rev - drag_m - mc_loss + hedge_benefit

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Annual Operating Plan (AOP)", f"${base_aop:.1f}M", "+4.2% YoY")
    col_m2.metric("Unconstrained Demand", "$125.94M", "+23,750 Units")
    col_m3.metric("CTRM Hedge Benefit", f"+${hedge_benefit:.2f}M", f"{len(hedges)} Digital Twin Hedges Locked")
    col_m4.metric("Available Treasury Cash", f"${15.29 + (1.14 - drag_m) - mc_loss:.2f}M", f"-${drag_m + mc_loss:.2f}M Total Drag")

    col_w1, col_w2 = st.columns([2, 1])

    with col_w1:
        st.subheader("📊 Financial P&L Margin Waterfall")
        import plotly.graph_objects as go
        
        x_bars = ["Base AOP Rev", "Base COGS", "Surge Rev", "Freight Drag"]
        measures = ["relative", "relative", "relative", "relative"]
        y_vals = [base_aop, cogs, surge_rev, -drag_m]
        text_vals = [f"+${base_aop:.1f}M", f"-${abs(cogs):.1f}M", f"+${surge_rev:.1f}M", f"-${drag_m:.2f}M"]

        if mc_loss > 0:
            x_bars.append("Macro Stress Shock")
            measures.append("relative")
            y_vals.append(-mc_loss)
            text_vals.append(f"-${mc_loss:.2f}M")

        x_bars.extend(["Hedge Benefit", "Net EBITDA"])
        measures.extend(["relative", "total"])
        y_vals.extend([hedge_benefit, None])
        text_vals.extend([f"+${hedge_benefit:.2f}M", f"${net_ebitda:.2f}M"])

        fig = go.Figure(go.Waterfall(
            name="P&L Waterfall",
            orientation="v",
            measure=measures,
            x=x_bars,
            textposition="outside",
            text=text_vals,
            y=y_vals,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#ef553b"}},
            increasing={"marker": {"color": "#00cc96"}},
            totals={"marker": {"color": "#1d70b8"}}
        ))
        fig.update_layout(
            title="Dynamic EBITDA Margin Waterfall ($M USD)",
            showlegend=False,
            height=340,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_w2:
        st.subheader("► Live Operational Desk Feeds")
        
        if mc_scenario:
            st.error(f"🔥 **Macro Stress Active**: **{mc_scenario}** injected (-${mc_loss:.2f}M P&L Drag).")
        else:
            st.markdown("• **Active Signal**: Sub-Factor Weight Shift (GSCPI:35% / NOAA:25% / Freight:25% / GEP:15%)")
        
        if rerouted:
            r_str = ", ".join(rerouted)
            st.success(f"• **Logistics Desk**: 🚢 Digital Twin Reroute Executed for **{r_str}** via Cape of Good Hope.")
        else:
            st.warning("• **Logistics Desk**: Lead time delay drag set at +3.5 days (Panama/Suez queues active).")

        if hedges:
            st.success(f"• **CTRM Risk Desk**: ⚡ {len(hedges)} Digital Twin FIX 4.4 Short Futures Position(s) Locked.")
        else:
            st.info("• **CTRM Risk Desk**: 0 Digital Twin Hedges Executed.")

    st.markdown("---")
    st.subheader("💰 Digital Twin Carrying Cost Drag on P&L Waterfall")
    col_pnl1, col_pnl2, col_pnl3 = st.columns(3)
    col_pnl1.metric("Gross EBITDA Target", "$120.00M")
    col_pnl2.metric("In-Transit Carrying & Demurrage Drag", f"-${drag_m + mc_loss:.2f}M", delta=f"Injected Macro Loss: -${mc_loss:.2f}M" if mc_loss > 0 else f"Saved ${1.14 - drag_m:.2f}M via Rerouting", delta_color="inverse")
    col_pnl3.metric("Net Adjusted EBITDA", f"${net_ebitda:.2f}M")
"""

pos_sop = code.find("def render_executive_sop")
if pos_sop != -1:
    next_def_sop = code.find("\ndef ", pos_sop + 10)
    if next_def_sop != -1:
        code = code[:pos_sop] + sop_mc_updated + "\n" + code[next_def_sop:]

# 4. Inject macro scenario banner into CTRM view
ctrm_macro_banner = """
    mc_scenario_ctrm = st.session_state.get("active_mc_scenario", None)
    mc_loss_ctrm = st.session_state.get("mc_expected_loss", 0.0)
    if mc_scenario_ctrm:
        st.warning(f"🚨 **ENTERPRISE MACRO STRESS INJECTED**: **{mc_scenario_ctrm}** | Systemic VaR Baseline Elevated by **+${mc_loss_ctrm:.2f}M**. Recommended Action: Execute FIX 4.4 derivatives hedges to protect gross margin.")
"""

if "mc_scenario_ctrm" not in code:
    pos_ctrm = code.find("def render_ctrm_desk")
    if pos_ctrm != -1:
        code = code[:pos_ctrm + 25] + "\n" + ctrm_macro_banner + "\n" + code[pos_ctrm + 25:]

with open("main.py", "w") as f:
    f.write(code)

py_compile.compile("main.py", doraise=True)
print("✓ Cross-module scenario injection logic compiled cleanly!")
