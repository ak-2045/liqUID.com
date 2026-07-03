

import streamlit as st
from typing import Dict


def render_alert_notifications(events: list[Dict]):
    
    if not events:
        return

    st.subheader("[WARN] System Alerts")
    for ev in events[-5:]:  
        ev_type = ev.get("type", "generic")
        tick = ev.get("tick", 0)
        
        if ev_type == "liquidation":
            st.error(
                f"[ALERT] **Tick {tick}** — **LIQUIDATION TRIGGERED** on Loan #{ev.get('loan_id')}. "
                f"Debt outstanding: ${ev.get('debt'):,.2f}. Collateral moved to Dutch Auction."
            )
        elif ev_type == "market_crash":
            st.warning(
                f"[CRASH] **Tick {tick}** — **MARKET SHOCK EVENT**! "
                f"Oracle valuations crashed by {ev.get('magnitude', 0)*100:.0f}%."
            )
        elif ev_type == "auction_sold":
            st.success(
                f"[AUCTION] **Tick {tick}** — **AUCTION SETTLED**! "
                f"Dutch Auction #{ev.get('auction_id')} bought for ${ev.get('price'):,.2f} liqUSD."
            )
        elif ev_type == "rate_hike":
            st.info(
                f"[TREND] **Tick {tick}** — **INTEREST RATE ADJUSTMENT**! "
                f"All active loans hiked by {ev.get('increase', 0)*10000:.0f} bps."
            )
