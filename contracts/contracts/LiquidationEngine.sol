// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./ProtocolAccessControl.sol";
import "./PriceOracle.sol";
import "./LendingPool.sol";
import "./DutchAuction.sol";

/**
 * @title LiquidationEngine
 * @dev Integrates PriceOracle, LendingPool, and DutchAuctions to verify default states.
 */
contract LiquidationEngine {
    ProtocolAccessControl public immutable accessControl;
    PriceOracle public immutable oracle;
    LendingPool public immutable pool;
    DutchAuction public immutable auction;

    event LiquidationTriggered(uint256 indexed loanId, uint256 indexed assetId, uint256 auctionId);

    constructor(
        address _accessControl,
        address _oracle,
        address _pool,
        address _auction
    ) {
        accessControl = ProtocolAccessControl(_accessControl);
        oracle = PriceOracle(_oracle);
        pool = LendingPool(_pool);
        auction = DutchAuction(_auction);
    }

    function checkAndLiquidate(uint256 loanId) external returns (uint256) {
        require(
            accessControl.hasRole(accessControl.LIQUIDATOR_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Unauthorized liquidator role"
        );

        // Fetch loan info
        (address borrower, uint256 assetId, uint256 principal, uint256 totalRepaid, bool active) = pool.loans(loanId);
        require(active, "Loan is not active");

        uint256 currentDebt = principal - totalRepaid;
        uint256 collateralValue = oracle.getPrice(assetId);

        // Default verification: Health Factor = (Collateral * Threshold) / Debt < 1.0 => Collateral * Threshold < Debt
        // Safe math mapping for safety (liquidation threshold is e.g. 85%)
        uint256 liquidationValue = (collateralValue * 85) / 100;
        require(liquidationValue < currentDebt, "Loan health factor remains above threshold");

        // Force close loan state
        pool.forceCloseLoan(loanId);

        // Start Dutch auction
        uint256 startPrice = (collateralValue * 130) / 100; // 130% premium
        uint256 reservePrice = currentDebt; // reserve covers outstanding debt
        uint256 auctionId = auction.createAuction(
            loanId,
            assetId,
            borrower,
            startPrice,
            reservePrice,
            21600 // 6 hour duration
        );

        emit LiquidationTriggered(loanId, assetId, auctionId);
        return auctionId;
    }
}
