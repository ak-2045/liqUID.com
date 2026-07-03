import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="font-size: 2.2rem; margin: 0; background: linear-gradient(135deg, #00d4ff 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    liqUID
                </h1>
                <p style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;">
                    RWA Liquidity Protocol
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### [KEY] Wallet Connection")
        
        if "wallet_address" not in st.session_state:
            st.session_state["wallet_address"] = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        
        address = st.text_input(
            "Account Address",
            value=st.session_state["wallet_address"],
            key="input_wallet_address"
        )
        st.session_state["wallet_address"] = address

        short_addr = f"{address[:6]}...{address[-4:]}" if len(address) == 42 else "Invalid Address"
        
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); padding: 12px; border-radius: 8px; font-family: monospace; text-align: center;">
                [OK] Connected: <span style="color: #00ff88; font-weight: bold;">{short_addr}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")
        
        st.markdown("### [SYS] Protocol Info")
        st.caption("Network: Hardhat Localhost")
        st.caption("Chain ID: 31337")
        st.caption("Stablecoin: liqUSD")
        st.caption("Valuation Feed: Multi-model Oracle")
