"""
End-to-end integration tests for the complete GenMesh execution pipeline.

Execution flow:

    Registry -> Coordinator -> Agents -> Aggregator

All emit() calls execute asynchronously as independent transactions.
Because of this, Aggregator must be polled after Coordinator.submit_task()
instead of expecting synchronous completion.

Run with:

    gltest test/test_e2e_flow.py --network localnet

These tests require properly configured LLM providers in GenLayer
Studio/localnet (see the tooling setup documentation), since each Agent
performs real non-deterministic inference.
"""

import time

from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def _deploy_full_mesh():
    registry = get_contract_factory("AgentRegistry").deploy()

    aggregator = get_contract_factory("Aggregator").deploy()

    coordinator = get_contract_factory("Coordinator").deploy(
        args=[str(registry.address), str(aggregator.address)]
    )

    security_agent = get_contract_factory("SecurityAgent").deploy(
        args=[str(registry.address)]
    )

    research_agent = get_contract_factory("ResearchAgent").deploy(
        args=[str(registry.address)]
    )

    finance_agent = get_contract_factory("FinanceAgent").deploy(
        args=[str(registry.address)]
    )

    for agent in (security_agent, research_agent, finance_agent):
        tx = agent.register_self().transact()
        assert tx_execution_succeeded(tx)

    return registry, coordinator, aggregator, (
        security_agent,
        research_agent,
        finance_agent,
    )


def test_full_mesh_pipeline():
    registry, coordinator, aggregator, agents = _deploy_full_mesh()

    agents_listed = registry.getAgents().call()

    assert len(agents_listed) == 3

    tx = coordinator.submit_task(
        args=[
            (
                "Review this DeFi lending pool before listing: "
                "high leverage, no timelock on admin functions, "
                "TVL just crossed $2M. Proceed? "
                "What's the market outlook?"
            )
        ]
    ).transact()

    assert tx_execution_succeeded(tx)

    task_id = 0
    result = None

    for _ in range(30):
        result = aggregator.get_result(args=[task_id]).call()

        if result["finalized"]:
            break

        time.sleep(2)

    assert result is not None
    assert result["finalized"] is True

    assert result["verdict"] in (
        "flagged",
        "clear",
        "unresolved",
    )

    # This task should require only SecurityAgent and FinanceAgent.
    # Research capability is intentionally not selected by the planner.
    assert len(result["submissions"]) == 2

    capabilities = {
        submission["capability"]
        for submission in result["submissions"]
    }

    assert capabilities == {
        "security-audit",
        "market-analysis",
    }


def test_aggregator_rejects_unexpected_agent():
    registry, coordinator, aggregator, agents = _deploy_full_mesh()

    security_agent, research_agent, finance_agent = agents

    # Register a task with an empty execution manifest.
    # No Agent is expected to participate.
    aggregator.register_task(
        args=[99, []]
    ).transact()

    tx = aggregator.submit_result(
        args=[
            99,
            str(security_agent.address),
            "security-audit",
            "high",
            "unsolicited result",
        ]
    ).transact()

    assert not tx_execution_succeeded(tx)
