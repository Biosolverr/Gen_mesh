# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class ResearchAgent(gl.Contract):
    owner: Address
    registry_address: Address
    # Unset until the deployer calls set_coordinator() -- same two-step
    # bootstrap pattern as Aggregator<->Coordinator. See SecurityAgent
    # for the full rationale.
    coordinator_address: Address
    capability: str
    name: str
    version: str
    description: str

    ALLOWED_VERDICTS = {"confirmed", "unconfirmed", "inconclusive"}
    MAX_TASK_DESCRIPTION_LENGTH = 4000

    def __init__(self, registry_address: str):
        self.owner = gl.message.sender_address
        self.registry_address = Address(registry_address)
        self.coordinator_address = Address("0x0000000000000000000000000000000000000000")
        self.capability = "research"
        self.name = "ResearchAgent"
        self.version = "1.0.0"
        self.description = "Evaluates how well-supported a claim or question is"

    def _require_coordinator(self):
        if gl.message.sender_address != self.coordinator_address:
            raise gl.vm.UserError("Only the coordinator can trigger execution")

    @gl.public.write
    def set_coordinator(self, coordinator_address: str):
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("Only the owner can set the coordinator address")
        self.coordinator_address = Address(coordinator_address)

    @gl.public.write
    def register_self(self):
        registry = gl.get_contract_at(self.registry_address)
        registry.emit(on="finalized").register(
            gl.message.contract_address.as_hex,
            self.name,
            self.capability,
            self.version,
            self.description,
        )

    # See SecurityAgent.execute() for why this restriction exists: an
    # unrestricted execute() let any caller feed this agent fabricated
    # task_description and have it submit_result() under its own
    # legitimate address, pre-empting the Coordinator's real dispatch.
    @gl.public.write
    def execute(
        self,
        task_id: u32,
        task_description: str,
        capability: str,
        aggregator_address: str,
    ) -> None:
        self._require_coordinator()

        if capability != self.capability:
            raise gl.vm.UserError("Capability mismatch")
        if not task_description.strip():
            raise gl.vm.UserError("Empty task description")
        if len(task_description) > self.MAX_TASK_DESCRIPTION_LENGTH:
            raise gl.vm.UserError(
                f"task_description exceeds {self.MAX_TASK_DESCRIPTION_LENGTH} characters"
            )

        task_text = task_description

        prompt = f"""
You are a research analyst evaluating the following task/question.

Task: {task_text}

Judge how confidently this can be answered from general knowledge.
Respond as strict JSON:
{{"verdict": "confirmed" | "unconfirmed" | "inconclusive", "summary": "one or two sentence explanation"}}
"""

        def leader_fn():
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            my_result = leader_fn()
            return my_result.get("verdict") == leaders_res.calldata.get("verdict")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # Fail-safe: нестандартный вердикт нормализуется в самый
        # консервативный вариант собственного словаря агента, а не
        # проходит непризнанным мимо Aggregator's escalation logic.
        verdict = result.get("verdict", "")
        if verdict not in self.ALLOWED_VERDICTS:
            verdict = "inconclusive"
        summary = result.get("summary", "")

        aggregator = gl.get_contract_at(Address(aggregator_address))
        aggregator.emit(on="finalized").submit_result(
            task_id,
            self.capability,
            verdict,
            summary,
        )

    @gl.public.view
    def get_capability(self) -> str:
        return self.capability
