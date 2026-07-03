// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./ProtocolAccessControl.sol";

/**
 * @title PriceOracle
 * @dev Stores asset valuation feed records for liquidations and loan updates.
 */
contract PriceOracle {
    ProtocolAccessControl public immutable accessControl;

    struct PriceData {
        uint256 price;
        uint256 timestamp;
    }

    // Mapping: assetTokenId => price
    mapping(uint256 => PriceData) public assetPrices;

    event PriceUpdated(uint256 indexed assetId, uint256 price, uint256 timestamp);

    constructor(address _accessControl) {
        require(_accessControl != address(0), "Invalid access control");
        accessControl = ProtocolAccessControl(_accessControl);
    }

    function setPrice(uint256 assetId, uint256 price) external {
        require(
            accessControl.hasRole(accessControl.ORACLE_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Oracle or admin role required"
        );
        require(price > 0, "Price must be positive");

        assetPrices[assetId] = PriceData({
            price: price,
            timestamp: block.timestamp
        });

        emit PriceUpdated(assetId, price, block.timestamp);
    }

    function getPrice(uint256 assetId) external view returns (uint256) {
        PriceData memory data = assetPrices[assetId];
        require(data.timestamp > 0, "No price data found");
        return data.price;
    }
}
