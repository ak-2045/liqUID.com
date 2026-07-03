

import streamlit as st
import pandas as pd
import time

from frontend.theme import apply_custom_theme, glowing_badge
from frontend.components.sidebar import render_sidebar
from frontend.api_client import APIClient


st.set_page_config(page_title="Portfolio | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[PORTFOLIO] Collateral Vault Portfolio")
st.markdown("Inspect registered real world assets and locked lending vault collateral NFTs.")

try:
    assets = APIClient.list_assets()
except Exception as e:
    assets = []
    st.error(f"Failed to fetch portfolio: {str(e)}")

if not assets:
    st.info("No assets registered to your wallet. Head to 'Mint NFT' to begin tokenizing.")
else:
    
    asset_types = list(set([a["asset_type"] for a in assets]))
    selected_type = st.multiselect("Filter Asset Category", asset_types, default=asset_types)

    
    filtered = [a for a in assets if a["asset_type"] in selected_type]

    
    st.subheader(f"Total Assets: {len(filtered)}")
    
    
    rows = [filtered[i:i + 3] for i in range(0, len(filtered), 3)]
    
    for r in rows:
        cols = st.columns(3)
        for idx, asset in enumerate(r):
            with cols[idx]:
                badge_html = glowing_badge(asset["status"])
                st.markdown(
                    f"""
                    <div class="glass-card" style="height: 100%;">
                        <img src="{asset.get('image_url')}" style="width: 100%; border-radius: 8px; max-height: 180px; object-fit: cover; margin-bottom: 12px;" />
                        <h4 style="margin: 0;">{asset['name']}</h4>
                        <p style="color: #00d4ff; font-weight: bold; margin: 4px 0;">Valuation: ${asset['current_value']:,.2f}</p>
                        <div style="font-size: 0.85rem; margin-top: 8px; color:#94a3b8;">
                            <strong>Token ID:</strong> {asset.get('token_id', 'Unminted')} <br/>
                            <strong>Type:</strong> {asset['asset_type'].upper()} <br/>
                            <strong>Serial:</strong> {asset['serial_number']} <br/>
                            <strong>Location:</strong> {asset['location']} <br/>
                            <strong>Locked:</strong> {'Yes ' if asset['is_locked'] else 'No '} <br/>
                            <div style="margin-top: 10px;">{badge_html}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
