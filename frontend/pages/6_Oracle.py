

import streamlit as st
import pandas as pd
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.components.charts import render_price_history_chart
from frontend.api_client import APIClient
from frontend.ws_client import WSClient


st.set_page_config(page_title="Oracle Telemetry | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[ORACLE] Oracle Price Monitoring")
st.markdown("Real-time decentralized pricing node feeds. Manage price configurations and manual overrides.")

col_left, col_right = st.columns([1, 1])


@st.fragment(run_every=2)
def update_oracle_section():
    data = WSClient.get_latest_data()
    if not data:
        st.warning("Connecting to Live Oracle stream...")
        return

    prices = data.get("prices", [])
    
    with col_left:
        st.subheader("[ORACLE] Real-time Price Feeds")
        if prices:
            df = pd.DataFrame(prices)
            display_df = df[["id", "name", "asset_type", "price"]].copy()
            display_df.columns = ["Asset ID", "Asset Name", "Type", "Live Valuation ($)"]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Awaiting asset initialization. Launch simulations to populate feeds.")

    with col_right:
        st.subheader("️ Price Feeds Override Node")
        if prices:
            
            asset_map = {f"ID #{p['id']} - {p['name']} (${p['price']:,.2f})": p for p in prices}
            selected_key = st.selectbox("Select Asset to Adjust", list(asset_map.keys()))
            asset = asset_map[selected_key]

            new_val = st.number_input("Override Target Price ($)", min_value=1.0, value=asset["price"], step=1000.0)
            
            if st.button("Publish Price Override to Oracle Network", use_container_width=True):
                try:
                    APIClient.update_oracle_price(asset["id"], new_val, "manual")
                    st.success(f"Overrode Asset #{asset['id']} price to ${new_val:,.2f}")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to submit oracle override: {str(e)}")
        else:
            st.info("Valuation overrides disabled. No assets active.")


update_oracle_section()

st.markdown("---")


st.subheader("[TREND] Valuation Historical Analysis")
try:
    history = APIClient.get_oracle_trends(limit=300)
    if history:
        df_hist = pd.DataFrame(history)
        fig = render_price_history_chart(df_hist)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical trends generated yet. Advance simulation clock ticks to chart prices.")
except Exception as e:
    st.caption("Awaiting chart analytics updates...")
