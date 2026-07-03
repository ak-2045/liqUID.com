// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "./ProtocolAccessControl.sol";

/**
 * @title LiqUSD
 * @dev Mock stablecoin representing credit currency issued by the protocol.
 */
contract LiqUSD is ERC20, ERC20Burnable {
    ProtocolAccessControl public immutable accessControl;

    constructor(address _accessControl) ERC20("liqUID Stablecoin", "liqUSD") {
        require(_accessControl != address(0), "Invalid access control");
        accessControl = ProtocolAccessControl(_accessControl);
    }

    function mint(address to, uint256 amount) external {
        require(
            accessControl.hasRole(accessControl.MINTER_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Minter or admin role required"
        );
        _mint(to, amount);
    }
}
