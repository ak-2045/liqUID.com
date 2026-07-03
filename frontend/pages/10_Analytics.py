

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.api_client import APIClient


st.set_page_config(page_title="Protocol Analytics | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[TREND] Protocol Analytics & Risk Dashboards")
st.markdown("Inspect collateral allocation matrices, credit quality tiers, and overall solvency metrics.")

try:
    
    summary = APIClient.get_analytics_summary()
    collateral = APIClient.get_collateral_distribution()
    borrowers = APIClient.get_borrower_segmentation()
    risk = APIClient.get_risk_breakdown()
except Exception as e:
    st.error(f"Failed to load analytics datasets: {str(e)}")
    summary, collateral, borrowers, risk = {}, [], [], {}

if not collateral and not borrowers:
    st.info("No active protocol data available to chart. Open simulation page and seed positions.")
else:
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Solvency Value Locked", f"${summary.get('total_value_locked', 0.0):,.2f}")
    with cols[1]:
        st.metric("Total Debt Outstanding", f"${summary.get('total_borrowed', 0.0):,.2f}")
    with cols[2]:
        st.metric("LTV Safety Buffer", f"{(1 - summary.get('avg_ltv_ratio', 0.0))*100:.1f}%")
    with cols[3]:
        st.metric("Auction Liquidation Rate", f"{summary.get('auction_success_rate', 1.0)*100:.1f}%")

    st.markdown("---")

    
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("[PORTFOLIO] Collateral Value Allocation")
        if collateral:
            df_col = pd.DataFrame(collateral)
            
            fig_tree = px.treemap(
                df_col,
                path=["asset_type"],
                values="value",
                title="Valuation Concentration by Asset Type ($)",
                template="plotly_dark",
                color="value",
                color_continuous_scale="Purples"
            )
            fig_tree.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.caption("No collateral active.")

        
        st.subheader("[WARN] Loan Position Health Tiers")
        if risk:
            
            fig_risk = px.bar(
                x=list(risk.keys()),
                y=list(risk.values()),
                title="Loans Sorted by Health Zones",
                labels={"x": "Health Zones", "y": "Loan Count"},
                color=list(risk.keys()),
                color_discrete_map={
                    : "#00ff88",
                    : "#00d4ff",
                    : "#ffaa00",
                    : "#ff4466",
                    : "#ff1122"
                },
                template="plotly_dark"
            )
            fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_risk, use_container_width=True)

    with col_right:
        st.subheader(" Borrower Credit Segments")
        if borrowers:
            df_bor = pd.DataFrame(borrowers)
            fig_pie = px.pie(
                df_bor,
                names="segment",
                values="count",
                title="Borrower Risk Tier Segmentations",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.caption("No borrowers registered.")

        
        st.subheader("️ Asset Class Risk Correlations")
        asset_classes = ["real_estate", "gold", "vehicle", "invoice", "land", "machinery"]
        corr_matrix = np.array([
            [1.00, 0.12, 0.35, 0.20, 0.85, 0.40],
            [0.12, 1.00, -0.05, 0.10, 0.15, 0.05],
            [0.35, -0.05, 1.00, 0.45, 0.28, 0.60],
            [0.20, 0.10, 0.45, 1.00, 0.15, 0.38],
            [0.85, 0.15, 0.28, 0.15, 1.00, 0.30],
            [0.40, 0.05, 0.60, 0.38, 0.30, 1.00]
        ])
        fig_heat = px.imshow(
            corr_matrix,
            x=asset_classes,
            y=asset_classes,
            title="Asset Correlation Volatility Matrix",
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_heat, use_container_width=True)
