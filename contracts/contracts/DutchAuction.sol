// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./ProtocolAccessControl.sol";
import "./LiqUSD.sol";
import "./CollateralVault.sol";

/**
 * @title DutchAuction
 * @dev Dynamic price decay auction for liquidating defaulted RWA collateral.
 */
contract DutchAuction is ReentrancyGuard {
    ProtocolAccessControl public immutable accessControl;
    LiqUSD public immutable stablecoin;
    CollateralVault public immutable vault;

    struct Auction {
        uint256 loanId;
        uint256 assetId;
        address borrower;
        uint256 startPrice;
        uint256 reservePrice;
        uint256 decayRate;
        uint256 startedAt;
        uint256 duration;
        bool active;
    }

    mapping(uint256 => Auction) public auctions;
    uint256 private _nextAuctionId;

    event AuctionCreated(uint256 indexed auctionId, uint256 indexed loanId, uint256 assetId, uint256 startPrice, uint256 reservePrice);
    event AuctionSettled(uint256 indexed auctionId, address indexed buyer, uint256 purchasePrice);
    event AuctionCancelled(uint256 indexed auctionId);

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

    function createAuction(
        uint256 loanId,
        uint256 assetId,
        address borrower,
        uint256 startPrice,
        uint256 reservePrice,
        uint256 duration
    ) external returns (uint256) {
        require(
            accessControl.hasRole(accessControl.LIQUIDATOR_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Unauthorized liquidator role"
        );
        require(startPrice > reservePrice, "Start price must exceed reserve price");
        require(duration > 0, "Duration must exceed zero");

        uint256 decayRate = (startPrice - reservePrice) / duration;
        uint256 auctionId = _nextAuctionId++;

        auctions[auctionId] = Auction({
            loanId: loanId,
            assetId: assetId,
            borrower: borrower,
            startPrice: startPrice,
            reservePrice: reservePrice,
            decayRate: decayRate,
            startedAt: block.timestamp,
            duration: duration,
            active: true
        });

        emit AuctionCreated(auctionId, loanId, assetId, startPrice, reservePrice);
        return auctionId;
    }

    function getPrice(uint256 auctionId) public view returns (uint256) {
        Auction memory auction = auctions[auctionId];
        require(auction.active, "Auction is not active");

        uint256 elapsed = block.timestamp - auction.startedAt;
        if (elapsed >= auction.duration) {
            return auction.reservePrice;
        }

        uint256 priceDecay = auction.decayRate * elapsed;
        return auction.startPrice - priceDecay;
    }

    function buy(uint256 auctionId, uint256 maxPrice) external nonReentrant {
        Auction storage auction = auctions[auctionId];
        require(auction.active, "Auction is not active");

        uint256 currentPrice = getPrice(auctionId);
        require(currentPrice <= maxPrice, "Current price exceeds buyer limit");

        auction.active = false;

        // Collect purchase payment in stablecoins from buyer
        stablecoin.transferFrom(msg.sender, address(this), currentPrice);

        // Distribute funds (split with fee & debt payback)
        uint256 protocolFee = (currentPrice * 2) / 100; // 2% protocol fee
        uint256 repayAmount = currentPrice - protocolFee;

        // Transfer fee to treasury or admin
        stablecoin.transfer(owner(), protocolFee);

        // Repay debt
        stablecoin.transfer(address(vault), repayAmount);

        // Release RWA NFT to buyer
        vault.releaseCollateral(address(this), auction.assetId, msg.sender);

        emit AuctionSettled(auctionId, msg.sender, currentPrice);
    }

    function cancelAuction(uint256 auctionId) external {
        require(
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Admin required"
        );
        Auction storage auction = auctions[auctionId];
        require(auction.active, "Auction is not active");
        auction.active = false;
        
        emit AuctionCancelled(auctionId);
    }

    function owner() public view returns (address) {
        return accessControl.owner();
    }
}
// Note: Solidity contract matches standard patterns with linear price decay calculations.
