

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any


def get_chart_theme_overrides() -> Dict[str, Any]:
    
    return {
        : "rgba(0, 0, 0, 0)",
        : "rgba(0, 0, 0, 0)",
        : "#94a3b8",
        : {
            : "rgba(255, 255, 255, 0.05)",
            : "rgba(255, 255, 255, 0.1)",
            : "rgba(255, 255, 255, 0.05)",
        },
        : {
            : "rgba(255, 255, 255, 0.05)",
            : "rgba(255, 255, 255, 0.1)",
            : "rgba(255, 255, 255, 0.05)",
        }
    }


def render_price_history_chart(df: pd.DataFrame) -> go.Figure:
    
    fig = px.line(
        df,
        x="timestamp",
        y="price",
        color="asset_name",
        title="Oracle Real-time Valuations ($)",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(**get_chart_theme_overrides())
    return fig


def render_collateral_treemap(df: pd.DataFrame) -> go.Figure:
    
    fig = px.treemap(
        df,
        path=["asset_type", "asset_name"],
        values="collateral_value",
        title="Locked Collateral Concentration Allocation",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Muted
    )
    fig.update_layout(**get_chart_theme_overrides())
    return fig


def render_health_factor_histogram(health_factors: List[float]) -> go.Figure:
    
    fig = px.histogram(
        x=health_factors,
        nbins=25,
        title="Protocol Health Factor Distribution",
        labels={"x": "Health Factor"},
        color_discrete_sequence=["#6366f1"],
        template="plotly_dark"
    )
    
    fig.add_vline(x=1.0, line_dash="dash", line_color="#ff4466", annotation_text="Liquidation Threshold")
    fig.update_layout(**get_chart_theme_overrides())
    return fig


def render_sim_performance_charts(df: pd.DataFrame) -> go.Figure:
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["tick"], y=df["tvl"], name="Total Value Locked",
        line=dict(color="#00ff88", width=2.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=df["tick"], y=df["borrowed"], name="Outstanding Debt",
        line=dict(color="#00d4ff", width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["tick"], y=df["fees"], name="Protocol Fees",
        line=dict(color="#ffaa00", width=1.5, dash="dot")
    ))

    fig.update_layout(
        title="Protocol Historical TVL & Borrow Activity",
        template="plotly_dark",
        **get_chart_theme_overrides()
    )
    return fig


def render_auction_price_decay_chart(start_price: float, current_price: float, reserve_price: float, elapsed: float, total_duration: float) -> go.Figure:
    
    time_series = [t for t in range(int(total_duration) + 1)]
    decay_rate = (start_price - reserve_price) / total_duration
    prices = [max(start_price - (decay_rate * t), reserve_price) for t in time_series]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_series, y=prices, name="Auction Decay Curve",
        line=dict(color="#94a3b8", width=2, dash="dash")
    ))

    
    fig.add_trace(go.Scatter(
        x=[elapsed], y=[current_price], name="Current Price Spot",
        mode="markers", marker=dict(color="#ff4466", size=12)
    ))

    fig.update_layout(
        title="Dutch Auction Price Decay Tracking ($)",
        xaxis_title="Elapsed Seconds",
        yaxis_title="Asset Purchase Price",
        template="plotly_dark",
        **get_chart_theme_overrides()
    )
    return fig
