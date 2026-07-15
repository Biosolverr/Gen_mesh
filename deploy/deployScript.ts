import { readFileSync } from "fs";
import { TransactionStatus } from "genlayer-js/types";
import type { GenLayerClient } from "genlayer-js";

// Shared helper: deploy + wait for the receipt + extract the contract address.
async function deployAndWait(
  client: GenLayerClient<any>,
  path: string,
  args: unknown[]
): Promise<string> {
  const code = readFileSync(path, "utf-8");
  const hash = await client.deployContract({ code, args, leaderOnly: false });
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 50,
    interval: 5000,
  });
  const address = receipt.data?.contract_address as string;
  console.log(`deployed ${path} -> ${address}`);
  return address;
}

async function writeAndWait(
  client: GenLayerClient<any>,
  address: string,
  functionName: string,
  args: unknown[]
) {
  const hash = await client.writeContract({ address, functionName, args });
  return client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 50,
    interval: 5000,
  });
}

// Deploy order follows dependencies, not the alphabet:
// Registry and Aggregator know nothing about each other — deployed first,
// in either order relative to one another. Coordinator depends on both
// addresses. Agents depend only on Registry — they don't need to know
// about Coordinator.
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

  // Aggregator was deployed before Coordinator existed, so it couldn't be
  // given the Coordinator's address at construction time — bind it now.
  // Without this, register_task/add_expected_agent on Aggregator reject
  // every call with "Only the coordinator can modify a task manifest",
  // because coordinator_address is still the zero address.
  await writeAndWait(client, aggregatorAddress, "set_coordinator", [coordinatorAddress]);
  console.log(`bound Aggregator(${aggregatorAddress}) to Coordinator(${coordinatorAddress})`);

  const agentPaths = [
    "contracts/agents/SecurityAgent.py",
    "contracts/agents/ResearchAgent.py",
    "contracts/agents/FinanceAgent.py",
  ];

  const agentAddresses: string[] = [];
  for (const path of agentPaths) {
    const address = await deployAndWait(client, path, [registryAddress]);
    agentAddresses.push(address);
  }

  // Self-registration — the deploy script doesn't write to Registry
  // directly, it only triggers register_self() on each agent.
  for (const address of agentAddresses) {
    await writeAndWait(client, address, "register_self", []);
    console.log(`registered agent ${address}`);
  }

  console.log("--- GenMesh Core deployment complete ---");
  console.log({
    registryAddress,
    coordinatorAddress,
    aggregatorAddress,
    agentAddresses,
  });

  return { registryAddress, coordinatorAddress, aggregatorAddress, agentAddresses };
}
