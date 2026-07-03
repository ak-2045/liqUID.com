import streamlit as st
from typing import Callable, List, Dict


def render_asset_mint_wizard(on_submit: Callable):
    with st.form("mint_asset_form", clear_on_submit=True):
        st.subheader("Asset Specifications")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Asset Name", placeholder="e.g. SF SOMA Commercial Real Estate")
            asset_type = st.selectbox(
                "Asset Classification Type",
                ["real_estate", "gold", "vehicle", "invoice", "land", "machinery", "artwork", "warehouse_receipt", "bond"]
            )
            valuation = st.number_input("Current Appraised Valuation ($)", min_value=100.0, step=1000.0, value=100000.0)
            
        with col2:
            location = st.text_input("Physical Storage Location", placeholder="e.g. Vault 7, London, UK")
            serial_number = st.text_input("Serial / Asset Registry ID", placeholder="e.g. RE-SF-94103")
            appraiser = st.text_input("Appraisal Organization", value="liqUID Audit Services")
            
        description = st.text_area("Asset Details & Verification Parameters")
        image_url = st.text_input("Asset Image URL (Optional)", value="https://picsum.photos/400/300")
        
        submit = st.form_submit_button("1. Register Asset In Database")
        
        if submit:
            if not name:
                st.error("Please supply a valid asset name.")
                return
                
            on_submit({
                "name": name,
                "asset_type": asset_type,
                "valuation": valuation,
                "location": location,
                "serial_number": serial_number,
                "appraiser": appraiser,
                "description": description,
                "image_url": image_url,
                "owner_address": st.session_state.get("wallet_address", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
            })


def render_borrow_form(assets: List[Dict], on_submit: Callable):
    if not assets:
        st.warning("You must register and mint/tokenize an asset before initiating a borrow position.")
        return

    asset_map = {f"NFT #{a['token_id']} - {a['name']} (${a['current_value']:,.2f})": a for a in assets}

    with st.form("borrow_form"):
        st.subheader("Debt Position Configurations")
        selected_key = st.selectbox("Select Collateral NFT", list(asset_map.keys()))
        asset = asset_map[selected_key]
        
        max_borrow = asset["current_value"] * 0.75  
        
        principal = st.number_input(
            f"Requested Debt Amount ($) (Max: ${max_borrow:,.2f})",
            min_value=10.0,
            max_value=max_borrow,
            value=max_borrow * 0.5,
            step=100.0
        )
        
        maturity_days = st.selectbox("Maturity Term Duration", [90, 180, 365, 730], index=2)
        
        st.info(f"Target Loan-to-Value: {(principal/asset['current_value'])*100:.2f}% | Oracle Volatility Tier: Low")
        
        submit = st.form_submit_button("Initiate Collateralized Borrow")
        
        if submit:
            on_submit({
                "borrower_id": 1,
                "asset_id": asset["id"],
                "principal": principal,
                "maturity_days": maturity_days
            })
