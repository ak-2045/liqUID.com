

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from backend.database import get_db
from backend.schemas.protocol import SimulationConfig, SimulationCommand
from backend.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_sim_loop(config: SimulationConfig, db: AsyncSession = Depends(get_db)):
    
    try:
        
        await SimulationService.generate_mock_portfolio(db, config.num_loans)
        
        
        await SimulationService.start_simulation(
            num_loans=config.num_loans,
            price_model=config.price_model,
            volatility=config.volatility,
            drift=config.drift,
            speed=config.speed,
            auto_repay_prob=config.auto_repay_probability,
        )
        return {"status": "success", "message": f"Simulation started with {config.num_loans} active loans."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )


@router.post("/control", status_code=status.HTTP_200_OK)
async def control_sim_loop(cmd: SimulationCommand, db: AsyncSession = Depends(get_db)):
    
    try:
        action = cmd.action.lower()
        
        if action == "start":
            await SimulationService.start_simulation(100, "gbm", 0.02, 0.0001, 10, 0.3)
            return {"status": "success", "message": "Simulation loop started."}
            
        elif action == "pause" or action == "stop":
            await SimulationService.stop_simulation()
            return {"status": "success", "message": "Simulation loop paused."}
            
        elif action == "resume":
            
            await SimulationService.start_simulation(
                100, SimulationService._price_model, SimulationService._volatility,
                SimulationService._drift, SimulationService._speed, SimulationService._auto_repay_prob
            )
            return {"status": "success", "message": "Simulation loop resumed."}
            
        elif action == "step":
            
            from backend.services.oracle_service import OracleService
            from backend.services.lending_service import LendingService
            from backend.services.liquidation_service import LiquidationService
            from backend.services.auction_service import AuctionService
            await OracleService.run_batch_oracle_tick(db)
            await LendingService.accrue_all_active_interest(db)
            await SimulationService._simulate_repayment_activity(db)
            await LiquidationService.scan_and_trigger_liquidations(db)
            await AuctionService.tick_active_auctions(db)
            await SimulationService._simulate_auction_purchases(db)
            await SimulationService.recalculate_protocol_state(db)
            return {"status": "success", "message": "Simulation advanced one tick."}
            
        elif action == "reset":
            await SimulationService.stop_simulation()
            
            await SimulationService.generate_mock_portfolio(db, 0)
            return {"status": "success", "message": "Simulation reset successfully."}
            
        elif action == "crash":
            from backend.services.admin_service import AdminService
            msg = await AdminService.trigger_market_scenario(db, "crash")
            return {"status": "success", "message": msg}
            
        elif action == "recover":
            from backend.services.admin_service import AdminService
            msg = await AdminService.trigger_market_scenario(db, "recovery")
            return {"status": "success", "message": msg}
            
        elif action == "rate_hike":
            from backend.services.admin_service import AdminService
            msg = await AdminService.trigger_market_scenario(db, "rate_hike")
            return {"status": "success", "message": msg}
            
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {action}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
