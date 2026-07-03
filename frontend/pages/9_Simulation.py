import streamlit as st
import pandas as pd
import time

from frontend.theme import apply_custom_theme, glass_card
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics import render_metrics_row
from frontend.components.charts import render_sim_performance_charts, render_health_factor_histogram
from frontend.api_client import APIClient
from frontend.ws_client import WSClient

st.set_page_config(page_title="Simulation sandbox | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[SIM] Protocol Simulation Sandbox")
st.markdown("Stress test the lending pool. Simulate thousands of active loans, adjust rates, trigger shocks, and watch liquidations happen.")

col_config, col_controls = st.columns([1, 2])

with col_config:
    st.subheader("[ADMIN] Config Sandbox")
    num_loans = st.slider("Number of Loans to Generate", min_value=10, max_value=2000, value=200, step=10)
    price_model = st.selectbox("Oracle Pricing Model", ["gbm", "random_walk", "seasonal", "economic_cycle"])
    volatility = st.slider("Oracle Base Volatility (σ)", min_value=0.0, max_value=0.2, value=0.02, step=0.005)
    speed = st.slider("Simulation Clock Speed (Ticks/sec)", min_value=1, max_value=50, value=10, step=1)
    auto_repay = st.slider("Borrower Repayment Probability", min_value=0.0, max_value=1.0, value=0.3, step=0.05)

    if st.button("Initialize & Start Simulation", use_container_width=True):
        try:
            APIClient.start_simulation({
                "num_loans": num_loans,
                "price_model": price_model,
                "volatility": volatility,
                "speed": speed,
                "auto_repay_probability": auto_repay,
            })
            st.success("Simulation sandbox started!")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start simulation: {str(e)}")

with col_controls:
    st.subheader("[CONTROL] Live Sandbox Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Pause Clock", use_container_width=True):
            APIClient.control_simulation("pause")
            st.toast("Simulation paused.")
    with col2:
        if st.button("Resume Clock", use_container_width=True):
            APIClient.control_simulation("resume")
            st.toast("Simulation resumed.")
    with col3:
        if st.button("Step Ticks", use_container_width=True):
            APIClient.control_simulation("step")
            st.toast("Advanced 1 tick.")
    with col4:
        if st.button("[RESET] Reset Protocol", use_container_width=True):
            APIClient.control_simulation("reset")
            st.success("Simulation reset.")
            time.sleep(0.5)
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    
    st.markdown("**[SHOCK] Market Scenarios (Trigger Price Volatility Shocks)**")
    col_scen1, col_scen2, col_scen3 = st.columns(3)
    with col_scen1:
        if st.button("[CRASH] Force Market Crash (-40%)", use_container_width=True):
            APIClient.control_simulation("crash")
            st.error("Market crash triggered! Prices collapsing...")
    with col_scen2:
        if st.button("[TREND] Force Market Recovery", use_container_width=True):
            APIClient.control_simulation("recover")
            st.success("Market recovery triggered! Stabilizing prices...")
    with col_scen3:
        if st.button("[HIKE] Hike Rates (+3.5%)", use_container_width=True):
            APIClient.control_simulation("rate_hike")
            st.info("Central bank hiked rates! Service costs increasing...")


@st.fragment(run_every=1)
def render_live_telemetry():
    data = WSClient.get_latest_data()
    if not data:
        st.caption("Awaiting sandbox tick events to chart telemetry...")
        return

    protocol = data.get("protocol", {})
    loans = data.get("loans", [])
    auctions = data.get("auctions", [])

    st.markdown("---")
    st.subheader("[DASH] Sandbox Live Telemetry")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Tick Count", f"#{protocol.get('sim_tick', 0)}")
    with col_m2:
        st.metric("Active Loans", f"{len(loans)}")
    with col_m3:
        st.metric("Active Auctions", f"{len(auctions)}")
    with col_m4:
        st.metric("Aggregate LTV", f"{protocol.get('avg_ltv_ratio', 0.0)*100:.2f}%")

    col_chart_left, col_chart_right = st.columns([2, 1])

    with col_chart_left:
        try:
            summary = APIClient.get_analytics_summary()
            trends = APIClient.get_oracle_trends(limit=100)
            if trends:
                df = pd.DataFrame(trends)
                import plotly.express as px
                fig = px.line(df, x="timestamp", y="price", color="asset_type", title="Live Oracle Price Feeds ($)")
                st.plotly_chart(fig, use_container_width=True, key="live_line_chart")
        except Exception:
            pass

    with col_chart_right:
        if loans:
            health_factors = [l.get("health_factor", 9.9) for l in loans]
            fig_hist = render_health_factor_histogram(health_factors)
            st.plotly_chart(fig_hist, use_container_width=True, key="live_health_hist")


render_live_telemetry()
