import streamlit as st
import time

from frontend.theme import apply_custom_theme, glass_card
from frontend.components.sidebar import render_sidebar
from frontend.ws_client import WSClient

st.set_page_config(
    page_title="liqUID.com — Liquid-Centric Lending Protocol for RWAs",
    page_icon="liqUID",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()
WSClient.start()
render_sidebar()

st.markdown(
    """
    <div style="padding: 20px 0; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.08);">
        <h1 style="font-size: 2.8rem; margin: 0; background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            liqUID.com Lending Protocol
        </h1>
        <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 8px; max-width: 800px;">
            Institutional-grade, liquid-centric lending marketplace for Real World Assets. 
            Tokenize yield-bearing physical inventory, land, bonds, invoices, or gold into liquid on-chain credit lines.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

data = WSClient.get_latest_data()
protocol_stats = data.get("protocol", {})

cols = st.columns(4)
with cols[0]:
    tvl = protocol_stats.get("total_value_locked", 0.0)
    st.metric("Total Value Locked (TVL)", f"${tvl:,.2f}", "+2.4%")
with cols[1]:
    borrowed = protocol_stats.get("total_borrowed", 0.0)
    st.metric("Outstanding Debt", f"${borrowed:,.2f}", "+5.1%")
with cols[2]:
    fees = protocol_stats.get("total_protocol_fees", 0.0)
    st.metric("Accumulated Protocol Fees", f"${fees:,.2f}")
with cols[3]:
    score = protocol_stats.get("protocol_health_score", 100.0)
    st.metric("Protocol Safety Score", f"{score:.1f}%", "-0.2%")

st.markdown("---")

col_main, col_features = st.columns([2, 1])

with col_main:
    st.subheader("[IDEA] The Liquidity Paradigm for RWA")
    st.markdown(
        """
        Conventional asset lending is slow, fragmented, and burdened by high appraisal delays. 
        liqUID.com solves this through an integrated five-stage protocol framework:
        
        1. Tokenization (Phase 1): Upload appraisals, titles, and specifications to generate ERC-721 NFTs backed by legal trusts.
        2. Instant Borrowing (Phase 2): Open credit lines against NFTs immediately. Amortization and interest schedules are powered by high-performance Python engines.
        3. Dynamic Valuations (Phase 3): A multi-model machine learning oracle monitors collateral values in real-time, recalculating Loan-to-Value (LTV) and health scores every second.
        4. Automatic Dutch Liquidation (Phase 4): If an asset health factor dips below 1.0, the contract launches a public Dutch auction, declining prices linearly to settle outstanding debt.
        5. Simulation & Analytics (Phase 5): Run market stress tests, simulate crashes, analyze concentration risks, and track recovery speeds.
        """
    )
    
    st.image("https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&q=80&w=1200", caption="liqUID RWA Vault Ecosystem", use_container_width=True)

with col_features:
    st.subheader("Quick Start Actions")
    
    with st.container():
        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                <h4 style="margin-top:0; color:#00d4ff;">[SIM] Simulation Sandbox</h4>
                <p style="font-size:0.9rem; color:#94a3b8;">
                    Jump directly into the Simulation Engine. Generate up to 1,000 active credit lines and trigger a market-wide liquidity event to see the oracle and liquidation engines react live.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Configure Simulation"):
            st.switch_page("pages/9_Simulation.py")

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;">
                <h4 style="margin-top:0; color:#00ff88;">[TOKEN] Asset Registration</h4>
                <p style="font-size:0.9rem; color:#94a3b8;">
                    Tokenize a mock real estate deed or invoice. Instantly mint an ERC-721 representation to your simulated address.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Mint RWA NFT"):
            st.switch_page("pages/3_Mint_NFT.py")
