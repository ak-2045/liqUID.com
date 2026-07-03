

import streamlit as st
import pandas as pd
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.api_client import APIClient


st.set_page_config(page_title="Admin Panel | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[ADMIN] Protocol Admin Panel")
st.markdown("Administrative configurations. Change interest parameters and override liquidation systems.")

try:
    summary = APIClient.get_analytics_summary()
    auctions = APIClient.list_auctions(status="active")
except Exception:
    summary = {}
    auctions = []

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("️ Global Protocol parameters")
    
    with st.form("parameters_form"):
        st.caption("Change active protocol parameters globally")
        
        default_rate = st.number_input(
            ,
            min_value=0.0,
            max_value=0.50,
            value=0.08,
            step=0.005,
            format="%.3f"
        )
        
        max_ltv = st.number_input(
            ,
            min_value=0.10,
            max_value=0.90,
            value=0.75,
            step=0.01,
            format="%.2f"
        )
        
        liq_threshold = st.number_input(
            ,
            min_value=0.20,
            max_value=0.95,
            value=0.85,
            step=0.01,
            format="%.2f"
        )
        
        submit = st.form_submit_button("Publish Parameter Adjustments")
        
        if submit:
            try:
                APIClient.update_protocol_parameters(default_rate, max_ltv, liq_threshold)
                st.success("Global parameters updated successfully!")
                time.sleep(1.0)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to publish parameters: {str(e)}")

with col_right:
    st.subheader("[HALT] Cancel Active Dutch Auctions")
    st.caption("Interrupt liquidations in emergency settings (releases collateral NFT back to borrowers).")
    
    if auctions:
        
        auc_map = {}
        for a in auctions:
            try:
                asset = APIClient.get_asset(a["asset_id"])
                asset_name = asset["name"]
            except Exception:
                asset_name = f"Asset ID {a['asset_id']}"
            auc_map[f"Auction #{a['id']} - {asset_name} (Price: ${a['current_price']:,.2f})"] = a

        selected_key = st.selectbox("Select Active Auction to Stop", list(auc_map.keys()))
        auction = auc_map[selected_key]

        if st.button("Halt & Cancel Auction", type="secondary", use_container_width=True):
            try:
                with st.spinner("Executing override cancellation..."):
                    APIClient.cancel_auction(auction["id"])
                    st.warning(f"Auction #{auction['id']} successfully halted. Collateral returned.")
                    time.sleep(1.0)
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to cancel auction: {str(e)}")
    else:
        st.info("No active Dutch auctions found to cancel.")
