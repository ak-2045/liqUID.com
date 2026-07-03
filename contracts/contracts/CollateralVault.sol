// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./ProtocolAccessControl.sol";

/**
 * @title CollateralVault
 * @dev Securely custody RWA NFTs deposited as collateral for loans.
 */
contract CollateralVault is ReentrancyGuard {
    ProtocolAccessControl public immutable accessControl;
    
    // Mapping: tokenId => depositor
    mapping(uint256 => address) public deposits;
    // Mapping: tokenId => isLocked
    mapping(uint256 => bool) public lockedAssets;

    event CollateralDeposited(uint256 indexed tokenId, address indexed depositor, address nftContract);
    event CollateralWithdrawn(uint256 indexed tokenId, address indexed depositor, address nftContract);
    event AssetLockStateChanged(uint256 indexed tokenId, bool isLocked);

    constructor(address _accessControl) {
        require(_accessControl != address(0), "Invalid access control");
        accessControl = ProtocolAccessControl(_accessControl);
    }

    function depositCollateral(address nftContract, uint256 tokenId) external nonReentrant {
        require(nftContract != address(0), "Invalid NFT contract");
        
        IERC721(nftContract).transferFrom(msg.sender, address(this), tokenId);
        
        deposits[tokenId] = msg.sender;
        lockedAssets[tokenId] = true;

        emit CollateralDeposited(tokenId, msg.sender, nftContract);
        emit AssetLockStateChanged(tokenId, true);
    }

    function releaseCollateral(
        address nftContract,
        uint256 tokenId,
        address receiver
    ) external nonReentrant {
        require(
            accessControl.hasRole(accessControl.LIQUIDATOR_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Unauthorized release access"
        );
        require(deposits[tokenId] != address(0), "No deposit found for asset");

        lockedAssets[tokenId] = false;
        deposits[tokenId] = address(0);

        IERC721(nftContract).safeTransferFrom(address(this), receiver, tokenId);

        emit CollateralWithdrawn(tokenId, receiver, nftContract);
        emit AssetLockStateChanged(tokenId, false);
    }

    function unlockAsset(uint256 tokenId) external {
        require(
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Admin required"
        );
        lockedAssets[tokenId] = false;
        emit AssetLockStateChanged(tokenId, false);
    }
}
