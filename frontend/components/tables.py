

# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
from typing import List, Dict
from frontend.theme import glowing_badge


def render_assets_table(assets: List[Dict]):
    
    if not assets:
        st.info("No tokenized assets found.")
        return

    df = pd.DataFrame(assets)
    
    display_df = df[["id", "token_id", "name", "asset_type", "current_value", "status", "is_locked"]].copy()
    display_df.columns = ["Asset ID", "Token ID", "Name", "Type", "Valuation ($)", "Status", "Locked"]
    
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_loans_table(loans: List[Dict]):
    
    if not loans:
        st.info("No active protocol loans found.")
        return

    df = pd.DataFrame(loans)
    display_df = df[["loan_id", "borrower", "asset", "principal", "total_debt", "health_factor", "ltv_ratio", "status"]].copy()
    display_df.columns = ["Loan ID", "Borrower", "Asset", "Principal ($)", "Outstanding Debt ($)", "Health Factor", "LTV Ratio", "Status"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
