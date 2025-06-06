import { ethers, run, network } from "hardhat";
import { HardhatRuntimeEnvironment } from "hardhat/types";

async function main(hre: HardhatRuntimeEnvironment = { network, run } as HardhatRuntimeEnvironment) {
  console.log("Deploying DocumentVerification contract...");

  // Get the contract factory
  const DocumentVerificationFactory = await ethers.getContractFactory("DocumentVerification");

  // Deploy the contract
  const documentVerification = await DocumentVerificationFactory.deploy();
  await documentVerification.waitForDeployment();

  // Get the deployed contract address
  const contractAddress = await documentVerification.getAddress();
  console.log(`DocumentVerification deployed to: ${contractAddress}`);

  // Skip verification for local networks
  if (hre.network.name === "hardhat" || hre.network.name === "localhost") {
    console.log("Skipping contract verification on local network");
    return;
  }

  // Wait for 60 seconds for testnet propagation
  console.log("Waiting 60 seconds before verification...");
  await new Promise((resolve) => setTimeout(resolve, 60000));

  // Verify the contract
  console.log(`Verifying contract on ${hre.network.name}...`);
  try {
    await hre.run("verify:verify", {
      address: contractAddress,
      constructorArguments: [], // Add constructor arguments if needed
    });
    console.log("Contract verified successfully");
  } catch (error: any) {
    console.error("Error verifying contract:", error.message);
    if (error.message.includes("already verified")) {
      console.log("Contract is already verified, continuing...");
    } else {
      throw error;
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });