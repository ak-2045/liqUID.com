// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./ProtocolAccessControl.sol";
import "./LiqUSD.sol";
import "./CollateralVault.sol";

/**
 * @title LendingPool
 * @dev Coordinates loan creation events and on-chain repayments.
 */
contract LendingPool is ReentrancyGuard {
    ProtocolAccessControl public immutable accessControl;
    LiqUSD public immutable stablecoin;
    CollateralVault public immutable vault;

    struct LoanInfo {
        address borrower;
        uint256 assetId;
        uint256 principal;
        uint256 totalRepaid;
        bool active;
    }

    mapping(uint256 => LoanInfo) public loans;
    uint256 private _nextLoanId;

    event LoanCreated(uint256 indexed loanId, address indexed borrower, uint256 indexed assetId, uint256 principal);
    event LoanRepaid(uint256 indexed loanId, address indexed borrower, uint256 amountRepaid, uint256 remainingDebt);
    event LoanSettled(uint256 indexed loanId);

    constructor(
        address _accessControl,
        address payable _stablecoin,
        address payable _vault
    ) {
        require(_accessControl != address(0), "Invalid access control");
        accessControl = ProtocolAccessControl(_accessControl);
        stablecoin = LiqUSD(_stablecoin);
        vault = CollateralVault(_vault);
    }

    function borrow(uint256 assetId, uint256 principal) external nonReentrant returns (uint256) {
        require(vault.deposits(assetId) == msg.sender, "Caller is not asset depositor");
        require(vault.lockedAssets(assetId), "Collateral asset must be locked in vault");

        uint256 loanId = _nextLoanId++;
        loans[loanId] = LoanInfo({
            borrower: msg.sender,
            assetId: assetId,
            principal: principal,
            totalRepaid: 0,
            active: true
        });

        // Mint credit stablecoins to borrower
        stablecoin.mint(msg.sender, principal);

        emit LoanCreated(loanId, msg.sender, assetId, principal);
        return loanId;
    }

    function repay(uint256 loanId, uint256 amount) external nonReentrant {
        LoanInfo storage loan = loans[loanId];
        require(loan.active, "Loan is not active");
        require(amount > 0, "Repay amount must be greater than zero");

        // Burn paid stablecoins from borrower
        stablecoin.burnFrom(msg.sender, amount);
        loan.totalRepaid += amount;

        emit LoanRepaid(loanId, msg.sender, amount, loan.principal - loan.totalRepaid);

        if (loan.totalRepaid >= loan.principal) {
            loan.active = false;
            emit LoanSettled(loanId);
        }
    }

    function forceCloseLoan(uint256 loanId) external {
        require(
            accessControl.hasRole(accessControl.LIQUIDATOR_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Unauthorized liquidator access"
        );
        LoanInfo storage loan = loans[loanId];
        require(loan.active, "Loan is already closed");
        loan.active = false;
        emit LoanSettled(loanId);
    }
}
