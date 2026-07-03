import streamlit as st
import pandas as pd
import time
from datetime import datetime, timezone

from frontend.theme import apply_custom_theme, glowing_badge
from frontend.components.sidebar import render_sidebar
from frontend.components.charts import render_auction_price_decay_chart
from frontend.api_client import APIClient
from frontend.ws_client import WSClient

st.set_page_config(page_title="Liquidation Auctions | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[AUCTION] Live Dutch Liquidation Auctions")
st.markdown("Acquire premium real-world assets at discount valuations. Prices decay linearly until reserve thresholds are met.")


@st.fragment(run_every=1)
def update_auction_page():
    data = WSClient.get_latest_data()
    
    try:
        raw_aucs = APIClient.list_auctions(status="active")
    except Exception:
        raw_aucs = []

    if not raw_aucs:
        st.info("No live liquidation auctions currently active. Keep monitoring the dashboard risk levels.")
        return

    auc_map = {}
    for a in raw_aucs:
        try:
            asset = APIClient.get_asset(a["asset_id"])
            asset_name = asset["name"]
            img_url = asset["image_url"]
        except Exception:
            asset_name = f"Asset ID {a['asset_id']}"
            img_url = "https://picsum.photos/400/300"
            
        auc_map[f"Auction #{a['id']} - collateral: {asset_name} (price: ${a['current_price']:,.2f})"] = {
            "auc": a,
            "name": asset_name,
            "img": img_url
        }

    col_list, col_bid = st.columns([1, 1])

    with col_list:
        st.subheader("[AUCTION] Active Liquidations List")
        for key, info in auc_map.items():
            auc = info["auc"]
            
            duration = auc["duration_seconds"]
            elapsed = 0
            if auc["started_at"]:
                try:
                    start_dt = datetime.fromisoformat(auc["started_at"].replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
                except Exception:
                    elapsed = 0.0

            progress = min(100.0, (elapsed / duration) * 100) if duration > 0 else 0.0

            st.markdown(
                f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;">{info['name']}</h4>
                        {glowing_badge("AUCTION")}
                    </div>
                    <div style="margin-top: 10px; font-size: 0.9rem;">
                        <strong>Starting Price:</strong> ${auc['start_price']:,.2f} <br/>
                        <strong style="color: #ffff88;">Current Decayed Spot:</strong> ${auc['current_price']:,.2f} <br/>
                        <strong>Reserve Price:</strong> ${auc['reserve_price']:,.2f} <br/>
                        <strong>Outstanding Debt Repaid:</strong> ${auc['outstanding_debt']:,.2f} <br/>
                    </div>
                    <div class="auction-progress-container">
                        <div class="auction-progress-bar" style="width: {progress}%;"></div>
                    </div>
                    <small style="color: #64748b;">Progress to Reserve Price: {progress:.1f}%</small>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col_bid:
        st.subheader("[BID] Auction Purchase bidding")
        selected_key = st.selectbox("Select Active Auction", list(auc_map.keys()))
        selected_info = auc_map[selected_key]
        s_auc = selected_info["auc"]

        st.image(selected_info["img"], use_container_width=True, caption=selected_info["name"])

        try:
            duration = s_auc["duration_seconds"]
            elapsed = 0
            if s_auc["started_at"]:
                try:
                    start_dt = datetime.fromisoformat(s_auc["started_at"].replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
                except Exception:
                    elapsed = 0.0
            
            fig = render_auction_price_decay_chart(
                s_auc["start_price"],
                s_auc["current_price"],
                s_auc["reserve_price"],
                elapsed,
                duration
            )
            st.plotly_chart(fig, use_container_width=True, key=f"decay_{s_auc['id']}")
        except Exception as e:
            st.caption("Rendering auction price curve chart...")

        buyer_addr = st.session_state.get("wallet_address", "0x3C44Cd3B2a14643306b028E9c3C16c1B97529339")
        
        if st.button(f"Acquire Asset at Spot ${s_auc['current_price']:,.2f}", use_container_width=True):
            try:
                with st.spinner("Executing auction buy settlement..."):
                    APIClient.buy_auction(s_auc["id"], buyer_addr, s_auc["current_price"] * 1.05)
                    st.success("[SUCCESS] Purchase successful! NFT transferred to your wallet.")
                    st.balloons()
                    time.sleep(1.2)
                    st.rerun()
            except Exception as e:
                st.error(f"Purchase failed: {str(e)}")


update_auction_page()
