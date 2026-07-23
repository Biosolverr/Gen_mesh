"""
End-to-end mesh test.

Registers all three agents, submits a single task through the
Coordinator, and polls the Aggregator until the task is finalized --
no manual resends, no manual reads from the dashboard. The LLM calls
made by the Coordinator and by each Agent are mocked so the test is
deterministic and does not depend on a live model provider.

Run with:
    gltest test/test_mesh_e2e.py --network studionet
    gltest test/test_mesh_e2e.py --network localnet
"""

import json
import time

import pytest
from gltest import get_contract_factory, get_default_account, get_validator_factory
from gltest.assertions import tx_execution_succeeded, tx_execution_failed

TASK_DESCRIPTION = (
    "Review this DeFi lending pool before listing: high leverage, "
    "no timelock on admin functions, TVL just crossed $2M. "
    "Proceed? What's the market outlook?"
)

POLL_INTERVAL_SECONDS = 3
POLL_MAX_ATTEMPTS = 40  # ~2 minutes on studionet


def _mock_validators():
    """
    Five mock validators with canned answers for every non-deterministic
    prompt used anywhere in the mesh (Coordinator's capability match +
    each Agent's assessment). Substring-matched against the prompt text,
    so exact wording of the task description does not matter.
    """
    mock_llm_response = {
        "nondet_exec_prompt": {
            "selecting which capabilities": json.dumps(
                {"capabilities": ["market-analysis", "research", "security-audit"]}
            ),
            "security auditor reviewing": json.dumps(
                {
                    "verdict": "high",
                    "summary": "High leverage with no timelock is a material risk.",
                }
            ),
            "market analyst reviewing": json.dumps(
                {
                    "verdict": "bearish",
                    "summary": "Centralization risk outweighs TVL growth.",
                }
            ),
            "research analyst evaluating": json.dumps(
                {
                    "verdict": "confirmed",
                    "summary": "The risk factors described are directly verifiable.",
                }
            ),
        }
    }

    factory = get_validator_factory()
    validators = factory.batch_create_mock_validators(
        count=5, mock_llm_response=mock_llm_response
    )
    return validators


def _transaction_context(validators):
    return {"validators": [v.to_dict() for v in validators]}


def _deploy_mesh(account, tx_ctx):
    """Deploys Registry -> Aggregator -> Coordinator, binds them, deploys
    and self-registers all three Agents. Mirrors deploy/deployScript.ts."""

    registry = get_contract_factory("AgentRegistry").deploy(
        account=account, transaction_context=tx_ctx
    )

    aggregator = get_contract_factory("Aggregator").deploy(
        account=account, transaction_context=tx_ctx
    )

    coordinator = get_contract_factory("Coordinator").deploy(
        args=[registry.address, aggregator.address],
        account=account,
        transaction_context=tx_ctx,
    )

    bind_receipt = aggregator.set_coordinator(
        args=[coordinator.address]
    ).transact(account=account, transaction_context=tx_ctx)
    assert tx_execution_succeeded(bind_receipt)

    agents = {}
    for contract_name in ("SecurityAgent", "ResearchAgent", "FinanceAgent"):
        agent = get_contract_factory(contract_name).deploy(
            args=[registry.address], account=account, transaction_context=tx_ctx
        )
        receipt = agent.register_self().transact(
            account=account, transaction_context=tx_ctx
        )
        assert tx_execution_succeeded(receipt), f"{contract_name} failed to self-register"
        agents[contract_name] = agent

    return registry, aggregator, coordinator, agents


def _wait_for_finalized(aggregator, task_id):
    """Polls get_result() until finalized=True. This replaces the manual
    'click get_result in the dashboard until it looks done' step."""
    last_result = None
    for _ in range(POLL_MAX_ATTEMPTS):
        last_result = aggregator.get_result(args=[task_id]).call()
        if last_result["finalized"]:
            return last_result
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(
        f"Task {task_id} did not finalize after "
        f"{POLL_MAX_ATTEMPTS * POLL_INTERVAL_SECONDS}s. Last state: {last_result}"
    )


def test_full_mesh_completes_without_manual_resends():
    """
    Registration -> submit_task -> Coordinator fan-out -> Agents execute
    -> Aggregator finalizes, driven entirely by the test -- no step
    requires a human to resend or re-trigger anything.
    """
    account = get_default_account()
    validators = _mock_validators()
    tx_ctx = _transaction_context(validators)

    registry, aggregator, coordinator, agents = _deploy_mesh(account, tx_ctx)

    active_agents = registry.getAgents().call()
    assert len(active_agents) == 3

    submit_receipt = coordinator.submit_task(args=[TASK_DESCRIPTION]).transact(
        account=account, transaction_context=tx_ctx
    )
    assert tx_execution_succeeded(submit_receipt)

    task_id = 0  # first task_counter value from a freshly deployed Coordinator
    result = _wait_for_finalized(aggregator, task_id)

    assert result["finalized"] is True
    assert len(result["submissions"]) == 3, (
        "expected one submission per registered capability "
        f"(security-audit, market-analysis, research), got: {result['submissions']}"
    )

    submitted_capabilities = {s["capability"] for s in result["submissions"]}
    assert submitted_capabilities == {"security-audit", "market-analysis", "research"}

    # High-risk security + bearish market verdicts -> deterministic
    # aggregation must escalate to "flagged".
    assert result["verdict"] == "flagged"


def test_submit_result_rejects_unauthorized_sender():
    """
    Regression check for the sender-authentication fix: a task's result
    can only come from the transaction sender that was actually assigned
    to it, not from an address the caller merely claims to be.
    """
    account = get_default_account()
    validators = _mock_validators()
    tx_ctx = _transaction_context(validators)

    registry, aggregator, coordinator, agents = _deploy_mesh(account, tx_ctx)

    submit_receipt = coordinator.submit_task(args=[TASK_DESCRIPTION]).transact(
        account=account, transaction_context=tx_ctx
    )
    assert tx_execution_succeeded(submit_receipt)

    # get_default_account() was never added as an expected agent for this
    # task, so a direct submit_result call from it must be rejected.
    forged_receipt = aggregator.submit_result(
        args=[0, "security-audit", "low", "forged submission"]
    ).transact(account=account, transaction_context=tx_ctx)
    assert tx_execution_failed(
        forged_receipt, match_std_err=r"not part of this task's execution plan"
    )


def test_register_task_rejects_non_coordinator():
    """
    Regression check for the coordinator-only manifest fix: only the
    address bound via set_coordinator() may create or extend a task
    manifest on the Aggregator.
    """
    account = get_default_account()
    validators = _mock_validators()
    tx_ctx = _transaction_context(validators)

    _registry, aggregator, _coordinator, _agents = _deploy_mesh(account, tx_ctx)

    receipt = aggregator.register_task(args=[999, 1]).transact(
        account=account, transaction_context=tx_ctx
    )
    assert tx_execution_failed(
        receipt, match_std_err=r"Only the coordinator can modify a task manifest"
    )
