

import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.asset import RWAAsset, AssetStatus
from backend.models.borrower import Borrower
from backend.models.loan import Loan, LoanStatus
from backend.models.transaction import Transaction, TxType
from backend.schemas.loan import LoanCreate
from backend.engines.interest_engine import InterestEngine
from backend.engines.risk_engine import RiskEngine
from backend.config import get_settings


class LendingService:
    

    @staticmethod
    async def create_loan(db: AsyncSession, loan_in: LoanCreate) -> Loan:
        
        settings = get_settings()

        
        q_asset = select(RWAAsset).where(RWAAsset.id == loan_in.asset_id)
        res_asset = await db.execute(q_asset)
        asset = res_asset.scalars().first()
        if not asset:
            raise ValueError(f"Asset ID {loan_in.asset_id} not found.")

        if asset.status != AssetStatus.MINTED:
            raise ValueError(f"Asset cannot be collateralized. Current status: {asset.status}")

        if asset.is_locked:
            raise ValueError("Asset is already locked.")

        
        q_borrower = select(Borrower).where(Borrower.id == loan_in.borrower_id)
        res_borrower = await db.execute(q_borrower)
        borrower = res_borrower.scalars().first()
        if not borrower:
            raise ValueError(f"Borrower ID {loan_in.borrower_id} not found.")

        
        risk_eng = RiskEngine(settings.liquidation_threshold)
        ltv = risk_eng.calculate_ltv(loan_in.principal, asset.current_value)

        if ltv > settings.max_ltv_ratio:
            raise ValueError(
                f"Requested loan exceeds Max LTV of {settings.max_ltv_ratio*100}%. "
                f"Requested LTV is {ltv*100:.2f}%"
            )

        
        interest_rate = loan_in.interest_rate or settings.default_interest_rate
        maturity = datetime.now(timezone.utc) + timedelta(days=loan_in.maturity_days)

        
        asset.status = AssetStatus.COLLATERALIZED
        asset.is_locked = True
        borrower.total_borrowed += loan_in.principal
        borrower.active_loans += 1

        
        loan = Loan(
            borrower_id=borrower.id,
            asset_id=asset.id,
            principal=loan_in.principal,
            interest_rate=interest_rate,
            accrued_interest=0.0,
            total_debt=loan_in.principal,
            collateral_value=asset.current_value,
            ltv_ratio=ltv,
            health_factor=risk_eng.calculate_health_factor(asset.current_value, loan_in.principal),
            liquidation_threshold=settings.liquidation_threshold,
            status=LoanStatus.ACTIVE,
            maturity_date=maturity,
            last_interest_update=datetime.now(timezone.utc),
        )
        db.add(loan)
        await db.flush()

        
        tx_vault_hash = f"0x{hashlib.sha256(f'tx_vault_{loan.id}'.encode()).hexdigest()}"
        tx_borrow_hash = f"0x{hashlib.sha256(f'tx_borrow_{loan.id}'.encode()).hexdigest()}"

        loan.vault_tx_hash = tx_vault_hash
        loan.borrow_tx_hash = tx_borrow_hash

        tx_deposit = Transaction(
            tx_hash=tx_vault_hash,
            tx_type=TxType.DEPOSIT_COLLATERAL,
            from_address=borrower.address,
            to_address="VaultContractAddress",
            amount=asset.current_value,
            asset_id=asset.id,
            loan_id=loan.id,
            details=f"Deposited NFT token #{asset.token_id} to vault as collateral",
        )

        tx_borrow = Transaction(
            tx_hash=tx_borrow_hash,
            tx_type=TxType.BORROW,
            from_address="LendingPoolContractAddress",
            to_address=borrower.address,
            amount=loan_in.principal,
            asset_id=asset.id,
            loan_id=loan.id,
            details=f"Minted & borrowed {loan_in.principal:.2f} liqUSD stablecoin",
        )

        db.add(tx_deposit)
        db.add(tx_borrow)
        await db.commit()
        await db.refresh(loan)
        return loan

    @staticmethod
    async def get_loan(db: AsyncSession, loan_id: int) -> Optional[Loan]:
        
        q = select(Loan).where(Loan.id == loan_id)
        res = await db.execute(q)
        return res.scalars().first()

    @staticmethod
    async def get_all_loans(db: AsyncSession, status: Optional[str] = None) -> List[Loan]:
        
        q = select(Loan)
        if status:
            q = q.where(Loan.status == LoanStatus(status))
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def get_loans_for_borrower(db: AsyncSession, borrower_id: int) -> List[Loan]:
        
        q = select(Loan).where(Loan.borrower_id == borrower_id)
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def accrue_loan_interest(db: AsyncSession, loan_id: int) -> Loan:
        
        loan = await LendingService.get_loan(db, loan_id)
        if not loan or loan.status != LoanStatus.ACTIVE:
            return loan

        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - loan.last_interest_update).total_seconds()

        if elapsed_seconds > 0:
            interest = InterestEngine.accrued_interest(
                loan.total_debt, loan.interest_rate, elapsed_seconds
            )
            loan.accrued_interest += interest
            loan.total_debt += interest
            loan.last_interest_update = now

            
            risk_eng = RiskEngine(loan.liquidation_threshold)
            loan.ltv_ratio = risk_eng.calculate_ltv(loan.total_debt, loan.collateral_value)
            loan.health_factor = risk_eng.calculate_health_factor(
                loan.collateral_value, loan.total_debt, loan.liquidation_threshold
            )
            await db.flush()

        return loan

    @staticmethod
    async def accrue_all_active_interest(db: AsyncSession):
        
        q = select(Loan).where(Loan.status == LoanStatus.ACTIVE)
        res = await db.execute(q)
        loans = res.scalars().all()
        for loan in loans:
            await LendingService.accrue_loan_interest(db, loan.id)
        await db.commit()

    @staticmethod
    async def repay_loan(db: AsyncSession, loan_id: int, amount: float) -> Tuple[Loan, float]:
        
        loan = await LendingService.get_loan(db, loan_id)
        if not loan:
            raise ValueError(f"Loan ID {loan_id} not found.")

        if loan.status != LoanStatus.ACTIVE:
            raise ValueError(f"Repayment not allowed on a loan in status: {loan.status}")

        
        loan = await LendingService.accrue_loan_interest(db, loan_id)

        actual_repay = min(amount, loan.total_debt)
        surplus = amount - actual_repay

        loan.total_debt -= actual_repay
        loan.total_repaid += actual_repay
        loan.repayment_count += 1

        
        q_borrower = select(Borrower).where(Borrower.id == loan.borrower_id)
        res_borrower = await db.execute(q_borrower)
        borrower = res_borrower.scalars().first()
        if borrower:
            borrower.total_repaid += actual_repay

        
        tx_hash = f"0x{hashlib.sha256(f'repay_{loan.id}_{loan.repayment_count}_{datetime.now().timestamp()}'.encode()).hexdigest()}"
        tx = Transaction(
            tx_hash=tx_hash,
            tx_type=TxType.REPAY,
            from_address=borrower.address if borrower else "UnknownBorrower",
            to_address="LendingPoolContractAddress",
            amount=actual_repay,
            asset_id=loan.asset_id,
            loan_id=loan.id,
            details=f"Repaid {actual_repay:.2f} liqUSD to lending pool",
        )
        db.add(tx)

        if loan.total_debt <= 0.01:
            
            loan.total_debt = 0.0
            loan.status = LoanStatus.REPAID

            
            q_asset = select(RWAAsset).where(RWAAsset.id == loan.asset_id)
            res_asset = await db.execute(q_asset)
            asset = res_asset.scalars().first()
            if asset:
                asset.status = AssetStatus.MINTED
                asset.is_locked = False

            if borrower:
                borrower.active_loans = max(0, borrower.active_loans - 1)

            
            tx_withdraw_hash = f"0x{hashlib.sha256(f'withdraw_{loan.id}'.encode()).hexdigest()}"
            tx_withdraw = Transaction(
                tx_hash=tx_withdraw_hash,
                tx_type=TxType.WITHDRAW_COLLATERAL,
                from_address="VaultContractAddress",
                to_address=borrower.address if borrower else "UnknownBorrower",
                amount=asset.current_value if asset else 0.0,
                asset_id=loan.asset_id,
                loan_id=loan.id,
                details=f"Withdrew NFT token #{asset.token_id if asset else ''} from vault (loan settled)",
            )
            db.add(tx_withdraw)

        else:
            
            risk_eng = RiskEngine(loan.liquidation_threshold)
            loan.ltv_ratio = risk_eng.calculate_ltv(loan.total_debt, loan.collateral_value)
            loan.health_factor = risk_eng.calculate_health_factor(
                loan.collateral_value, loan.total_debt, loan.liquidation_threshold
            )

        await db.commit()
        await db.refresh(loan)
        return loan, surplus
