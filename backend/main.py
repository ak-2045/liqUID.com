from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from backend.config import get_settings
from backend.database import init_db
from backend.api import assets, loans, oracle, auctions, simulation, analytics, admin, websocket
from backend.services.simulation_service import SimulationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await SimulationService.stop_simulation()


app = FastAPI(
    title="liqUID.com API Backend",
    description="Python-first decentralized lending protocol backend for Real World Assets.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)
app.include_router(loans.router)
app.include_router(oracle.router)
app.include_router(auctions.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "liqUID.com DeFi Lending Protocol Backend API is online.",
        "docs": "/docs"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    )
