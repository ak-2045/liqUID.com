

import streamlit as st
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.components.forms import render_asset_mint_wizard
from frontend.api_client import APIClient


st.set_page_config(page_title="Mint RWA NFT | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[TOKEN] Tokenize Real World Assets")
st.markdown("Convert certified physical appraisals, invoices, and titles into ERC-721 security tokens.")

col_form, col_preview = st.columns([3, 2])


def on_register_submit(form_data: dict):
    try:
        with st.spinner("Uploading metadata details to database..."):
            asset = APIClient.register_asset(form_data)
            st.session_state["last_registered_asset"] = asset
            st.success(f"Asset '{asset['name']}' registered successfully! Ready for on-chain tokenization.")
    except Exception as e:
        st.error(f"Failed to register asset: {str(e)}")


with col_form:
    st.subheader("Step 1: Specification Specifications")
    render_asset_mint_wizard(on_submit=on_register_submit)

with col_preview:
    st.subheader("Step 2: Tokenization & Minting")
    
    asset = st.session_state.get("last_registered_asset")
    
    if asset:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <img src="{asset.get('image_url')}" style="width: 100%; border-radius: 12px; max-height: 250px; object-fit: cover; margin-bottom: 16px;" />
                <h4 style="margin: 0;">{asset['name']}</h4>
                <p style="color: #6366f1; font-weight: bold; font-size: 1.2rem; margin: 8px 0;">
                    Value: ${asset['valuation']:,.2f}
                </p>
                <div style="text-align: left; font-size: 0.9rem; margin-top: 12px;">
                    <strong>Type:</strong> {asset['asset_type'].upper()} <br/>
                    <strong>Serial:</strong> {asset['serial_number']} <br/>
                    <strong>Location:</strong> {asset['location']} <br/>
                    <strong>Status:</strong> {asset['status'].upper()} <br/>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if asset["status"] == "pending":
            if st.button("2. Execute On-chain Tokenization (Mint NFT)", use_container_width=True):
                try:
                    with st.spinner("Uploading to IPFS & executing mint transaction on-chain..."):
                        tokenized = APIClient.tokenize_asset(asset["id"])
                        st.session_state["last_registered_asset"] = tokenized
                        st.success("[SUCCESS] NFT successfully minted! Token ID registered on-chain.")
                        st.balloons()
                        
                        st.session_state["last_registered_asset"] = None
                except Exception as e:
                    st.error(f"Minting failed: {str(e)}")
        else:
            st.info("This asset has already been minted to your connected wallet.")
            
    else:
        st.info("Complete the specifications wizard on the left to review the NFT preview card.")
