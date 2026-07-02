"""
Coordinator tests.

The Coordinator uses run_nondet_unsafe(), meaning these tests execute
real non-deterministic inference inside the GenLayer simulator.

As a result, they are slower than purely deterministic contract tests
and require a properly configured local validator network.

Run with:

    gltest test/test_coordinator.py --network localnet
"""

from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def test_submit_task_rejects_empty_registry():
    registry = get_contract_factory("AgentRegistry").deploy()
    aggregator = get_contract_factory("Aggregator").deploy()

    coordinator = get_contract_factory("Coordinator").deploy(
        args=[str(registry.address), str(aggregator.address)]
    )

    # No Agents are registered.
    # Coordinator must reject the request deterministically before
    # entering the non-deterministic planning stage.
    tx = coordinator.submit_task(
        args=["Any task description"]
    ).transact()

    assert not tx_execution_succeeded(tx)


def test_submit_task_picks_relevant_capability():
    registry = get_contract_factory("AgentRegistry").deploy()
    aggregator = get_contract_factory("Aggregator").deploy()

    coordinator = get_contract_factory("Coordinator").deploy(
        args=[str(registry.address), str(aggregator.address)]
    )

    security_agent = get_contract_factory("SecurityAgent").deploy(
        args=[str(registry.address)]
    )

    security_agent.register_self().transact()

    tx = coordinator.submit_task(
        args=[
            "Audit this smart contract for reentrancy vulnerabilities before mainnet deployment."
        ]
    ).transact()

    assert tx_execution_succeeded(tx)

    # The task counter should advance, indicating that the execution
    # plan was successfully generated and at least one emit() call was
    # dispatched to the security-audit Agent.
    count = coordinator.get_task_count().call()

    assert count == 1
