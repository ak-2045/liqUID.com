

# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics import render_metrics_row
from frontend.components.tables import render_loans_table
from frontend.ws_client import WSClient


st.set_page_config(page_title="Dashboard | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[DASH] Protocol Live Dashboard")
st.markdown("Real-time telemetry and risk index monitoring for the liquid-centric lending pool.")


@st.fragment(run_every=2)
def update_dashboard():
    
    data = WSClient.get_latest_data()
    
    if not data:
        st.warning("Connecting to API WebSocket stream...")
        st.spinner("Awaiting live data packets...")
        return

    
    protocol_stats = data.get("protocol", {})
    loans = data.get("loans", [])
    auctions = data.get("auctions", [])
    txs = data.get("transactions", [])

    
    metrics = [
        {"title": "Total Value Locked (TVL)", "value": f"${protocol_stats.get('total_value_locked', 0.0):,.2f}"},
        {"title": "Active Debt Issue", "value": f"${protocol_stats.get('total_borrowed', 0.0):,.2f}"},
        {"title": "Active Auctions Count", "value": f"{len(auctions)} Live", "direction": "down" if auctions else "up"},
        {"title": "Liquidation Recovered Value", "value": f"${protocol_stats.get('recovered_capital', 0.0):,.2f}"}
    ]
    render_metrics_row(metrics)
    
    st.markdown("---")

    
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader(" Active Lending Positions")
        if loans:
            render_loans_table(loans)
        else:
            st.info("No active loan positions to display. Generate mock assets in the simulation page.")

    with col_right:
        st.subheader(" Protocol Telemetry Events")
        if txs:
            for tx in txs[:8]:  
                tx_type = tx.get("tx_type", "generic").upper()
                amt = tx.get("amount", 0.0)
                hsh = tx.get("tx_hash", "0x")[:10]
                
                
                bullet = "[INFO]"
                if tx_type == "LIQUIDATION":
                    bullet = "[ALERT]"
                elif tx_type == "AUCTION_BUY":
                    bullet = "[AUCTION]"
                elif tx_type == "REPAY":
                    bullet = "[OK]"

                st.markdown(
                    f"{bullet} **{tx_type}** | ${amt:,.2f} | Hash: `{hsh}`  \n"
                    f"<small style='color: #64748b;'>{tx.get('details', '')}</small>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Awaiting on-chain transaction events...")


update_dashboard()
