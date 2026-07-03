// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Pausable.sol";
import "./ProtocolAccessControl.sol";

/**
 * @title RWAAsset
 * @dev Tokenizes physical assets into ERC721 NFTs. Contains on-chain validation storage.
 */
contract RWAAsset is ERC721URIStorage, ERC721Pausable {
    ProtocolAccessControl public immutable accessControl;
    uint256 private _nextTokenId;

    struct AssetValuation {
        uint256 valuation;
        uint256 timestamp;
        string appraiser;
    }

    mapping(uint256 => AssetValuation) public assetValuations;

    event AssetMinted(uint256 indexed tokenId, address indexed owner, string tokenURI, uint256 valuation);
    event ValuationUpdated(uint256 indexed tokenId, uint256 newValuation, string appraiser);

    constructor(
        string memory name,
        string memory symbol,
        address _accessControl
    ) ERC721(name, symbol) {
        require(_accessControl != address(0), "Invalid access control address");
        accessControl = ProtocolAccessControl(_accessControl);
    }

    function mintAsset(
        address to,
        string memory uri,
        uint256 initialValuation,
        string memory appraiser
    ) external returns (uint256) {
        require(
            accessControl.hasRole(accessControl.MINTER_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Caller is not minter or admin"
        );

        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);

        assetValuations[tokenId] = AssetValuation({
            valuation: initialValuation,
            timestamp: block.timestamp,
            appraiser: appraiser
        });

        emit AssetMinted(tokenId, to, uri, initialValuation);
        return tokenId;
    }

    function updateValuation(
        uint256 tokenId,
        uint256 newValuation,
        string memory appraiser
    ) external {
        require(
            accessControl.hasRole(accessControl.ORACLE_ROLE(), msg.sender) ||
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Caller is not oracle or admin"
        );
        require(_ownerOf(tokenId) != address(0), "Asset does not exist");

        assetValuations[tokenId] = AssetValuation({
            valuation: newValuation,
            timestamp: block.timestamp,
            appraiser: appraiser
        });

        emit ValuationUpdated(tokenId, newValuation, appraiser);
    }

    function pause() external {
        require(
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Admin role required"
        );
        _pause();
    }

    function unpause() external {
        require(
            accessControl.hasRole(accessControl.ADMIN_ROLE(), msg.sender),
            "Admin role required"
        );
        _unpause();
    }

    // Required overrides
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Pausable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }
}
// Note: OpenZeppelin v5 uses _update instead of _beforeTokenTransfer hooks for execution rules.
