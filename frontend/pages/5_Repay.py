import streamlit as st
import time

from frontend.theme import apply_custom_theme
from frontend.components.sidebar import render_sidebar
from frontend.api_client import APIClient

st.set_page_config(page_title="Repay Debt | liqUID.com", layout="wide")
apply_custom_theme()
render_sidebar()

st.title("[REPAY] Repay Loan Positions")
st.markdown("Service outstanding loan balances to reclaim tokenized collateral NFTs.")

try:
    loans = APIClient.list_loans(status="active")
except Exception as e:
    loans = []
    st.error(f"Failed to load active loans: {str(e)}")

if not loans:
    st.info("You have no active loan positions. Borrow capital to open positions.")
else:
    loan_map = {}
    for l in loans:
        try:
            asset = APIClient.get_asset(l["asset_id"])
            asset_name = asset["name"]
        except Exception:
            asset_name = f"Asset ID {l['asset_id']}"
        
        loan_map[f"Loan #{l['id']} - collateral: {asset_name} (debt: ${l['total_debt']:,.2f})"] = l

    selected_key = st.selectbox("Select Active Loan Position", list(loan_map.keys()))
    loan = loan_map[selected_key]

    col_stats, col_action = st.columns([1, 1])

    with col_stats:
        st.subheader("Position Analysis")
        try:
            health_info = APIClient.get_loan_health(loan["id"])
        except Exception:
            health_info = loan

        st.markdown(
            f"""
            <div class="glass-card">
                <strong>Current Debt Balance:</strong> ${health_info.get('total_debt', 0.0):,.2f} <br/>
                <strong>Collateral Valuation:</strong> ${health_info.get('collateral_value', 0.0):,.2f} <br/>
                <strong>Current LTV Ratio:</strong> {health_info.get('ltv_ratio', 0.0)*100:.2f}% <br/>
                <strong>Liquidation Threshold:</strong> 85.00% <br/>
                <strong>Loan Health Factor:</strong> <span style="color: {'#00ff88' if health_info.get('health_factor', 0.0) >= 1.2 else '#ff4466'}; font-weight: bold;">{health_info.get('health_factor', 0.0):.2f}</span> <br/>
                <strong>Estimated Liquidation Price:</strong> ${health_info.get('liquidation_price', 0.0):,.2f} <br/>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_action:
        st.subheader("Process Repayment")
        
        with st.form("repay_form"):
            repay_amount = st.number_input(
                "Payment Amount (liqUSD)",
                min_value=1.0,
                max_value=health_info.get('total_debt', 1.0),
                value=health_info.get('total_debt', 1.0),
                step=10.0
            )
            
            is_full = repay_amount >= health_info.get('total_debt', 0.0)
            
            submit = st.form_submit_button("Repay & Settle" if is_full else "Process Partial Repayment")
            
            if submit:
                try:
                    with st.spinner("Processing payment transaction..."):
                        updated = APIClient.repay_loan(loan["id"], repay_amount)
                        
                        if is_full:
                            st.success("[SUCCESS] Loan fully paid! Collateral NFT has been returned to your wallet.")
                            st.balloons()
                        else:
                            st.success(f"Repaid ${repay_amount:,.2f} liqUSD. Outstanding debt is now ${updated['total_debt']:,.2f}")
                        
                        time.sleep(1.2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Repayment execution failed: {str(e)}")
