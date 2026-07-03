import streamlit as st
import os


def apply_custom_theme():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0b0f2a !important;
                color: #e2e8f0 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


def glass_card(title: str = "", content: str = ""):
    return st.markdown(
        f"""
        <div class="glass-card">
            {f'<h3>{title}</h3>' if title else ''}
            <div>{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def glowing_badge(status: str) -> str:
    status_lower = status.lower()
    
    if status_lower in ("minted", "active"):
        cls = "badge-active"
    elif status_lower in ("defaulted", "liquidated", "expired", "cancelled", "burned"):
        cls = "badge-defaulted"
    elif status_lower in ("in_auction", "auction"):
        cls = "badge-auction"
    else:
        cls = "badge-minted"
        
    return f'<span class="glowing-badge {cls}">{status}</span>'
