"""
Registry — deterministic unit tests with no LLM dependency.

Run:
    gltest test/test_registry.py --network localnet
"""

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded


def test_register_and_lookup():
    factory = get_contract_factory("AgentRegistry")
    registry = factory.deploy()
    account = get_default_account()

    tx = registry.register(
        args=[
            str(account.address),
            "TestAgent",
            "test-capability",
            "1.0.0",
            "demo agent",
        ]
    ).transact()
    assert tx_execution_succeeded(tx)

    agents = registry.getAgents().call()
    assert len(agents) == 1
    assert agents[0]["capability"] == "test-capability"
    assert agents[0]["active"] is True

    found = registry.findByCapability(args=["test-capability"]).call()
    assert len(found) == 1
    assert found[0]["name"] == "TestAgent"


def test_duplicate_registration_rejected():
    factory = get_contract_factory("AgentRegistry")
    registry = factory.deploy()
    account = get_default_account()

    registry.register(
        args=[
            str(account.address),
            "TestAgent",
            "test-capability",
            "1.0.0",
            "demo",
        ]
    ).transact()

    tx = registry.register(
        args=[
            str(account.address),
            "TestAgent",
            "test-capability",
            "1.0.0",
            "demo",
        ]
    ).transact()

    assert not tx_execution_succeeded(tx)


def test_third_party_cannot_register_someone_elses_address():
    factory = get_contract_factory("AgentRegistry")
    registry = factory.deploy()

    other_account_placeholder = "0x000000000000000000000000000000000000AA"

    tx = registry.register(
        args=[
            other_account_placeholder,
            "Impersonator",
            "test-capability",
            "1.0.0",
            "",
        ]
    ).transact()

    assert not tx_execution_succeeded(tx)


def test_find_by_unknown_capability_returns_empty():
    factory = get_contract_factory("AgentRegistry")
    registry = factory.deploy()

    result = registry.findByCapability(args=["does-not-exist"]).call()

    assert result == []
