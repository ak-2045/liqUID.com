const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("liqUID Protocol Layer tests", function () {
  let deployer, borrower, buyer;
  let accessControl, rwaAsset, vault, stablecoin, pool, oracle, auction, liquidation;

  beforeEach(async function () {
    [deployer, borrower, buyer] = await ethers.getSigners();

    // Deploy Access Control
    const Access = await ethers.getContractFactory("ProtocolAccessControl");
    accessControl = await Access.deploy(deployer.address);

    // Deploy RWA NFT
    const Asset = await ethers.getContractFactory("RWAAsset");
    rwaAsset = await Asset.deploy("liqUID RWA NFT", "liqRWA", await accessControl.getAddress());

    // Deploy Vault
    const Vault = await ethers.getContractFactory("CollateralVault");
    vault = await Vault.deploy(await accessControl.getAddress());

    // Deploy Stablecoin
    const Coin = await ethers.getContractFactory("LiqUSD");
    stablecoin = await Coin.deploy(await accessControl.getAddress());

    // Deploy Lending Pool
    const Pool = await ethers.getContractFactory("LendingPool");
    pool = await Pool.deploy(await accessControl.getAddress(), await stablecoin.getAddress(), await vault.getAddress());

    // Deploy Oracle
    const Oracle = await ethers.getContractFactory("PriceOracle");
    oracle = await Oracle.deploy(await accessControl.getAddress());

    // Deploy Auction
    const Auction = await ethers.getContractFactory("DutchAuction");
    auction = await Auction.deploy(await accessControl.getAddress(), await stablecoin.getAddress(), await vault.getAddress());

    // Deploy Liquidation
    const Liq = await ethers.getContractFactory("LiquidationEngine");
    liquidation = await Liq.deploy(await accessControl.getAddress(), await oracle.getAddress(), await pool.getAddress(), await auction.getAddress());

    // Roles configuration
    await accessControl.grantRole(await accessControl.MINTER_ROLE(), pool.getAddress());
    await accessControl.grantRole(await accessControl.LIQUIDATOR_ROLE(), liquidation.getAddress());
    await accessControl.grantRole(await accessControl.LIQUIDATOR_ROLE(), auction.getAddress());
  });

  it("Should allow registering and tokenizing an asset", async function () {
    const valuation = ethers.parseEther("100000"); // 100k
    
    // Mint RWA NFT to borrower
    await rwaAsset.mintAsset(borrower.address, "ipfs://metadata-hash", valuation, "liqUID Appraiser");
    expect(await rwaAsset.balanceOf(borrower.address)).to.equal(1);
    expect(await rwaAsset.ownerOf(0)).to.equal(borrower.address);
  });

  it("Should allow borrowing against deposited collateral", async function () {
    const valuation = ethers.parseEther("100000"); // 100k
    const principal = ethers.parseEther("50000");  // 50k LTV 50%

    // 1. Mint NFT to borrower
    await rwaAsset.mintAsset(borrower.address, "ipfs://metadata-hash", valuation, "liqUID Appraiser");

    // 2. Approve Vault for the NFT transfer
    await rwaAsset.connect(borrower).approve(await vault.getAddress(), 0);

    // 3. Deposit to vault
    await vault.connect(borrower).depositCollateral(await rwaAsset.getAddress(), 0);
    expect(await rwaAsset.ownerOf(0)).to.equal(await vault.getAddress());

    // 4. Initiate Borrow
    await pool.connect(borrower).borrow(0, principal);
    expect(await stablecoin.balanceOf(borrower.address)).to.equal(principal);
  });
});
