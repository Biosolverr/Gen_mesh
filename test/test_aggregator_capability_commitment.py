"""
Regression test for the capability-commitment check added to
Aggregator.submit_result() alongside the coordinator-only execute()
fix (Pavel Kolosov's review, Jul 31 2026).

This check can't be exercised through the normal mesh flow: a real
Agent always sends its own hardcoded self.capability, never a
caller-supplied value, so there's no legitimate path that produces a
mismatch to test against. Instead, this test drives Aggregator in
isolation -- binding it to the test account itself as "coordinator",
then having that same account also stand in as the "expected agent"
for one task, so a capability mismatch can be triggered directly
against the contract's own state machine, independent of Coordinator
or any Agent contract.

Run with:
    gltest test/test_aggregator_capability_commitment.py --network studionet
    gltest test/test_aggregator_capability_commitment.py --network localnet
"""

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded, tx_execution_failed

TASK_ID = 0
EXPECTED_CAPABILITY = "security-audit"
WRONG_CAPABILITY = "market-analysis"


def _deploy_standalone_aggregator(account):
    """Deploys a bare Aggregator and binds coordinator_address to the
    test account itself, so the test can act as "coordinator" for
    register_task/add_expected_agent without needing a real Coordinator
    contract."""
    aggregator = get_contract_factory("Aggregator").deploy(account=account)

    bind_receipt = aggregator.set_coordinator(
        args=[account.address]
    ).transact(account=account)
    assert tx_execution_succeeded(bind_receipt)

    return aggregator


def test_submit_result_rejects_capability_mismatch():
    """
    The account registers itself as the expected agent for
    EXPECTED_CAPABILITY on this task (acting as "coordinator"), then
    tries to submit a result under a different capability (acting as
    the "agent") -- this must be rejected even though the sender
    address itself is legitimately part of the task's execution plan.
    """
    account = get_default_account()
    aggregator = _deploy_standalone_aggregator(account)

    register_receipt = aggregator.register_task(
        args=[TASK_ID, 1]
    ).transact(account=account)
    assert tx_execution_succeeded(register_receipt)

    add_expected_receipt = aggregator.add_expected_agent(
        args=[TASK_ID, account.address, EXPECTED_CAPABILITY]
    ).transact(account=account)
    assert tx_execution_succeeded(add_expected_receipt)

    mismatched_receipt = aggregator.submit_result(
        args=[TASK_ID, WRONG_CAPABILITY, "high", "mismatched capability submission"]
    ).transact(account=account)

    assert tx_execution_failed(
        mismatched_receipt,
        match_std_err=r"does not match the registered task commitment",
    )


def test_submit_result_accepts_matching_capability():
    """
    Sanity check for the same setup: submitting under the *correct*
    capability must succeed and finalize the task, confirming the
    rejection above is specifically about the mismatch, not a general
    regression in submit_result.
    """
    account = get_default_account()
    aggregator = _deploy_standalone_aggregator(account)

    aggregator.register_task(args=[TASK_ID, 1]).transact(account=account)
    aggregator.add_expected_agent(
        args=[TASK_ID, account.address, EXPECTED_CAPABILITY]
    ).transact(account=account)

    matching_receipt = aggregator.submit_result(
        args=[TASK_ID, EXPECTED_CAPABILITY, "high", "matching capability submission"]
    ).transact(account=account)
    assert tx_execution_succeeded(matching_receipt)

    result = aggregator.get_result(args=[TASK_ID]).call()
    assert result["finalized"] is True
    assert len(result["submissions"]) == 1
    assert result["submissions"][0]["capability"] == EXPECTED_CAPABILITY
