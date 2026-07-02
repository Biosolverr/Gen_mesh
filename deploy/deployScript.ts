import { readFileSync } from "fs";
import { TransactionStatus } from "genlayer-js/types";
import type { GenLayerClient } from "genlayer-js";

/**
 * Deploys a contract, waits for confirmation, and returns
 * the deployed contract address.
 */
async function deployAndWait(
  client: GenLayerClient<any>,
  path: string,
  args: unknown[]
): Promise<string> {
  const code = readFileSync(path, "utf-8");

  const hash = await client.deployContract({
    code,
    args,
    leaderOnly: false,
  });

  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 50,
    interval: 5000,
  });

  const address = receipt.data?.contract_address as string;

  console.log(`Deployed ${path} → ${address}`);

  return address;
}

async function writeAndWait(
  client: GenLayerClient<any>,
  address: string,
  functionName: string,
  args: unknown[]
) {
  const hash = await client.writeContract({
    address,
    functionName,
    args,
  });

  return client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 50,
    interval: 5000,
  });
}

/**
 * Deployment order follows architectural dependencies rather than
 * alphabetical order.
 *
 * Registry and Aggregator are completely independent and may be
 * deployed first in any order.
 *
 * Coordinator depends on both Registry and Aggregator.
 *
 * Agents depend only on Registry. They are intentionally unaware of
 * Coordinator to preserve loose coupling between execution planning
 * and execution itself.
 */
export default async function main(client: GenLayerClient<any>) {
  const registryAddress = await deployAndWait(
    client,
    "contracts/registry/AgentRegistry.py",
    []
  );

  const aggregatorAddress = await deployAndWait(
    client,
    "contracts/aggregator/Aggregator.py",
    []
  );

  const coordinatorAddress = await deployAndWait(
    client,
    "contracts/coordinator/Coordinator.py",
    [registryAddress, aggregatorAddress]
  );

  const agentPaths = [
    "contracts/agents/SecurityAgent.py",
    "contracts/agents/ResearchAgent.py",
    "contracts/agents/FinanceAgent.py",
  ];

  const agentAddresses: string[] = [];

  for (const path of agentPaths) {
    const address = await deployAndWait(client, path, [
      registryAddress,
    ]);

    agentAddresses.push(address);
  }

  /**
   * Self-registration preserves the permissionless design.
   *
   * The deployment script never writes directly into the Registry.
   * Instead, every Agent registers itself by calling its own
   * register_self() method.
   */
  for (const address of agentAddresses) {
    await writeAndWait(client, address, "register_self", []);

    console.log(`Registered Agent ${address}`);
  }

  console.log("\n=== GenMesh Core deployment completed ===");

  console.log({
    registryAddress,
    coordinatorAddress,
    aggregatorAddress,
    agentAddresses,
  });

  return {
    registryAddress,
    coordinatorAddress,
    aggregatorAddress,
    agentAddresses,
  };
}
