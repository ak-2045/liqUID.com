from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.future import select
import asyncio
import json

from backend.database import get_session_factory
from backend.models.protocol import ProtocolState
from backend.models.asset import RWAAsset
from backend.models.loan import Loan, LoanStatus
from backend.models.auction import DutchAuction, AuctionStatus
from backend.models.transaction import Transaction

router = APIRouter(prefix="/ws", tags=["WebSockets"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/live")
async def websocket_live_feed(websocket: WebSocket):
    await manager.connect(websocket)
    session_factory = get_session_factory()

    try:
        while True:
            async with session_factory() as db:
                q_state = select(ProtocolState)
                res_state = await db.execute(q_state)
                state = res_state.scalars().first()
                state_data = state.to_dict() if state else {}

                q_assets = select(RWAAsset.id, RWAAsset.name, RWAAsset.current_value, RWAAsset.asset_type)
                res_assets = await db.execute(q_assets)
                asset_list = [
                    {"id": r[0], "name": r[1], "price": r[2], "asset_type": r[3].value}
                    for r in res_assets.all()
                ]

                q_loans = select(Loan.id, Loan.principal, Loan.total_debt, Loan.health_factor, Loan.ltv_ratio, Loan.status).where(Loan.status == LoanStatus.ACTIVE)
                res_loans = await db.execute(q_loans)
                loan_list = [
                    {"id": r[0], "principal": r[1], "debt": r[2], "health_factor": min(r[3], 99.0), "ltv": r[4]}
                    for r in res_loans.all()
                ]

                q_aucs = select(
                    DutchAuction.id, DutchAuction.current_price, DutchAuction.reserve_price,
                    DutchAuction.start_price, DutchAuction.decay_rate, DutchAuction.started_at, DutchAuction.duration_seconds
                ).where(DutchAuction.status == AuctionStatus.ACTIVE)
                res_aucs = await db.execute(q_aucs)
                auction_list = []
                from datetime import datetime, timezone
                for r in res_aucs.all():
                    elapsed = (datetime.now(timezone.utc) - r[5]).total_seconds() if r[5] else 0.0
                    progress = (elapsed / r[6]) * 100 if r[6] > 0 else 0.0
                    auction_list.append({
                        "id": r[0],
                        "current_price": r[1],
                        "reserve_price": r[2],
                        "start_price": r[3],
                        "decay_rate": r[4],
                        "progress": min(100.0, progress),
                    })

                q_txs = select(Transaction).order_by(Transaction.timestamp.desc()).limit(10)
                res_txs = await db.execute(q_txs)
                tx_list = [t.to_dict() for t in res_txs.scalars().all()]

            payload = {
                "protocol": state_data,
                "prices": asset_list,
                "loans": loan_list,
                "auctions": auction_list,
                "transactions": tx_list,
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
