

import streamlit as st


def render_metric_card(title: str, value: str, delta: str = "", delta_direction: str = "up"):
    
    delta_class = "delta-up" if delta_direction == "up" else "delta-down"
    delta_indicator = "▲" if delta_direction == "up" else "▼"
    
    delta_html = ""
    if delta:
        delta_html = f'<div class="metric-delta {delta_class}">{delta_indicator} {delta}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metrics_row(metrics: list[dict]):
    
    cols = st.columns(len(metrics))
    for idx, metric in enumerate(metrics):
        with cols[idx]:
            render_metric_card(
                title=metric.get("title", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta", ""),
                delta_direction=metric.get("direction", "up")
            )
