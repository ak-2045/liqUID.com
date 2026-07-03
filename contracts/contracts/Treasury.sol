// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./ProtocolAccessControl.sol";

/**
 * @title Treasury
 * @dev Collects and holds protocol revenue and liquidations fees.
 */
contract Treasury {
    ProtocolAccessControl public immutable accessControl;

    event FeesCollected(address indexed token, uint256 amount);
    event FundsWithdrawn(address indexed token, address indexed to, uint256 amount);

    constructor(address _accessControl) {
        require(_accessControl != address(0), "Invalid access control");
        accessControl = ProtocolAccessControl(_accessControl);
    }

    function withdraw(
        address token,
        address to,
        uint256 amount
    ) external {
        require(
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Admin role required"
        );
        require(to != address(0), "Invalid withdrawal recipient");

        IERC20(token).transfer(to, amount);

        emit FundsWithdrawn(token, to, amount);
    }

    // Allow receive native ETH
    receive() external payable {
        emit FeesCollected(address(0), msg.value);
    }
}
