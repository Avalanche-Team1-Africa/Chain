import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import { config as dotenvConfig } from "dotenv";

dotenvConfig({ path: "./.env" });

// Debug environment variables
console.log("Environment variables loaded:");
console.log(
  "- BASESCAN_API_KEY:",
  process.env.BASESCAN_API_KEY ? `✓ Set (length: ${process.env.BASESCAN_API_KEY.length})` : "✗ Not set"
);
console.log("- ALCHEMY_API_KEY:", process.env.ALCHEMY_API_KEY ? "✓ Set" : "✗ Not set");
console.log("- PRIVATE_KEY:", process.env.PRIVATE_KEY ? "✓ Set" : "✗ Not set");

// Validate required environment variables
const PRIVATE_KEY = process.env.PRIVATE_KEY;
if (!PRIVATE_KEY) {
  console.error("Please set your PRIVATE_KEY in a .env file");
  process.exit(1);
}

const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY;
if (!ALCHEMY_API_KEY) {
  console.error("Please set your ALCHEMY_API_KEY in a .env file");
  process.exit(1);
}

const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";
const BASESCAN_API_KEY = process.env.BASESCAN_API_KEY || "";
if (!BASESCAN_API_KEY) {
  console.warn("BASESCAN_API_KEY not found in .env file. Contract verification might fail.");
}
const POLYGON_API_KEY = process.env.POLYGON_API_KEY || "";

const config: HardhatUserConfig = {
  solidity: {
    compilers: [
      { version: "0.8.20", settings: { optimizer: { enabled: true, runs: 200 } } },
      { version: "0.8.28", settings: { optimizer: { enabled: true, runs: 200 } } },
      { version: "0.8.30", settings: { optimizer: { enabled: true, runs: 200 } } },
    ],
  },
  networks: {
    hardhat: { chainId: 31337 },
    localhost: { url: "http://127.0.0.1:8545", chainId: 31337 },
    base: {
      url: "https://mainnet.base.org",
      accounts: [PRIVATE_KEY],
      chainId: 8453,
    },
    baseGoerli: {
      url: "https://goerli.base.org",
      accounts: [PRIVATE_KEY],
      chainId: 84531,
    },
    baseSepolia: {
      url: "https://sepolia.base.org",
      accounts: [PRIVATE_KEY],
      chainId: 84532,
    },
    mumbai: {
      url: `https://polygon-mumbai.g.alchemy.com/v2/${ALCHEMY_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 80001,
    },
    polygon: {
      url: `https://polygon-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`,
      accounts: [PRIVATE_KEY],
      chainId: 137,
    },
  },
  etherscan: {
    apiKey: {
      base: BASESCAN_API_KEY,
      baseGoerli: BASESCAN_API_KEY,
      baseSepolia: BASESCAN_API_KEY,
      polygon: POLYGON_API_KEY,
      polygonMumbai: POLYGON_API_KEY,
    },
    customChains: [
      {
        network: "base",
        chainId: 8453,
        urls: { apiURL: "https://api.basescan.org/api", browserURL: "https://basescan.org" },
      },
      {
        network: "baseGoerli",
        chainId: 84531,
        urls: { apiURL: "https://api-goerli.basescan.org/api", browserURL: "https://goerli.basescan.org" },
      },
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: { apiURL: "https://api-sepolia.basescan.org/api", browserURL: "https://sepolia.basescan.org" },
      },
    ],
  },
  sourcify: { enabled: true },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};

export default config;