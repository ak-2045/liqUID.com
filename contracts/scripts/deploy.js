const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // 1. Deploy Access Control
  const ProtocolAccessControl = await hre.ethers.getContractFactory("ProtocolAccessControl");
  const accessControl = await ProtocolAccessControl.deploy(deployer.address);
  await accessControl.waitForDeployment();
  console.log("ProtocolAccessControl deployed to:", await accessControl.getAddress());

  // 2. Deploy RWA NFT
  const RWAAsset = await hre.ethers.getContractFactory("RWAAsset");
  const rwaAsset = await RWAAsset.deploy("liqUID Real World Asset NFT", "liqRWA", await accessControl.getAddress());
  await rwaAsset.waitForDeployment();
  console.log("RWAAsset ERC-721 deployed to:", await rwaAsset.getAddress());

  // 3. Deploy Vault
  const CollateralVault = await hre.ethers.getContractFactory("CollateralVault");
  const vault = await CollateralVault.deploy(await accessControl.getAddress());
  await vault.waitForDeployment();
  console.log("CollateralVault deployed to:", await vault.getAddress());

  // 4. Deploy stablecoin
  const LiqUSD = await hre.ethers.getContractFactory("LiqUSD");
  const stablecoin = await LiqUSD.deploy(await accessControl.getAddress());
  await stablecoin.waitForDeployment();
  console.log("LiqUSD Stablecoin deployed to:", await stablecoin.getAddress());

  // 5. Deploy Lending Pool
  const LendingPool = await hre.ethers.getContractFactory("LendingPool");
  const pool = await LendingPool.deploy(
    await accessControl.getAddress(),
    await stablecoin.getAddress(),
    await vault.getAddress()
  );
  await pool.waitForDeployment();
  console.log("LendingPool deployed to:", await pool.getAddress());

  // 6. Deploy Oracle
  const PriceOracle = await hre.ethers.getContractFactory("PriceOracle");
  const oracle = await PriceOracle.deploy(await accessControl.getAddress());
  await oracle.waitForDeployment();
  console.log("PriceOracle deployed to:", await oracle.getAddress());

  // 7. Deploy Dutch Auction
  const DutchAuction = await hre.ethers.getContractFactory("DutchAuction");
  const auction = await DutchAuction.deploy(
    await accessControl.getAddress(),
    await stablecoin.getAddress(),
    await vault.getAddress()
  );
  await auction.waitForDeployment();
  console.log("DutchAuction deployed to:", await auction.getAddress());

  // 8. Deploy Liquidation Engine
  const LiquidationEngine = await hre.ethers.getContractFactory("LiquidationEngine");
  const liquidation = await LiquidationEngine.deploy(
    await accessControl.getAddress(),
    await oracle.getAddress(),
    await pool.getAddress(),
    await auction.getAddress()
  );
  await liquidation.waitForDeployment();
  console.log("LiquidationEngine deployed to:", await liquidation.getAddress());

  // 9. Grant Minter/Oracle roles to contracts for autonomous interaction
  console.log("Setting up roles...");
  await accessControl.grantRole(await accessControl.MINTER_ROLE(), await pool.getAddress());
  await accessControl.grantRole(await accessControl.LIQUIDATOR_ROLE(), await liquidation.getAddress());
  console.log("Roles successfully granted.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
