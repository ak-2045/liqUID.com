import os
import sys
import json
import subprocess
import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import init_db, get_session_factory
from backend.models.asset import RWAAsset, AssetType, AssetStatus
from backend.models.protocol import ProtocolState


async def preseed_database():
    print("--------------------------------------------------")
    print("[SYSTEM] liqUID.com — Initializing Database Setup...")
    print("--------------------------------------------------")
    
    await init_db()
    
    session_factory = get_session_factory()
    async with session_factory() as db:
        q_count = select(RWAAsset)
        res = await db.execute(q_count)
        existing = res.scalars().all()
        
        if len(existing) > 0:
            print("[INFO] Database already seeded. Skipping asset imports.")
            return

        print("[LOAD] Seeding database with sample assets...")
        sample_path = os.path.join("data", "sample_assets.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r") as f:
                assets_data = json.load(f)
                
            for index, item in enumerate(assets_data):
                asset = RWAAsset(
                    token_id=1000 + index,
                    name=item["name"],
                    asset_type=AssetType(item["asset_type"]),
                    description=f"Pre-seeded RWA portfolio collateral: {item['name']}",
                    valuation=item["valuation"],
                    current_value=item["valuation"],
                    owner_address="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
                    status=AssetStatus.MINTED,
                    image_url=item["image_url"],
                    location=item["location"],
                    serial_number=item["serial_number"],
                    is_locked=False
                )
                db.add(asset)
            
            state = ProtocolState(
                sim_tick=0,
                sim_running=False,
            )
            db.add(state)
            
            await db.commit()
            print(f"[SUCCESS] Successfully seeded {len(assets_data)} default assets.")
        else:
            print("[WARN] sample_assets.json not found. Database started clean.")


def launch_services():
    print("--------------------------------------------------")
    print("[START] Starting liqUID.com Services...")
    print("--------------------------------------------------")
    
    os.makedirs("logs", exist_ok=True)
    
    print("[RUN] Booting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "backend.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("[RUN] Booting Streamlit Interface on http://127.0.0.1:8501 ...")
    frontend_proc = subprocess.Popen(
        ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("\n[ACTIVE] Both services are starting. Press Ctrl+C to terminate both servers.")
    print("--------------------------------------------------\n")
    
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Shutting down protocol services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("[EXIT] Services shut down clean.")


if __name__ == "__main__":
    asyncio.run(preseed_database())
    launch_services()
