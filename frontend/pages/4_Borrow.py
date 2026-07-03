import streamlit as st
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.components.forms import render_borrow_form
from frontend.api_client import APIClient

st.set_page_config(page_title="Borrow Against Assets | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[BORROW] Open Credit Line (Borrow)")
st.markdown("Unlock capital against your tokenized Real World Assets by depositing them into the secure protocol vault.")

try:
    assets = APIClient.list_assets(status="minted")
except Exception as e:
    assets = []
    st.error(f"Failed to load assets: {str(e)}")

def on_borrow_submit(borrow_payload: dict):
    try:
        with st.spinner("Locking collateral in vault and issuing stablecoin credit..."):
            loan = APIClient.borrow(borrow_payload)
            st.success(f"[SUCCESS] Loan #{loan['id']} successfully created! {loan['principal']:,.2f} liqUSD has been issued.")
            st.balloons()
            time.sleep(1.0)
            st.rerun()
    except Exception as e:
        st.error(f"Borrow transaction failed: {str(e)}")

col_form, col_info = st.columns([2, 1])

with col_form:
    render_borrow_form(assets, on_submit=on_borrow_submit)

with col_info:
    st.subheader("[INFO] Borrowing Rules")
    st.markdown(
        """
        * Max Loan-to-Value (LTV): 75% of asset valuation.
        * Liquidation Threshold: 85%. If your LTV reaches this point due to price drops or interest accruals, the asset will trigger liquidation.
        * Stablecoin Issued: liqUSD (simulated credit stablecoin soft-pegged to $1 USD).
        * Custody vault: Your NFT is held in our smart contract vault and cannot be transferred until the debt is repaid.
        """
    )
