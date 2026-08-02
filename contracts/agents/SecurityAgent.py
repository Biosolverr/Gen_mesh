# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class SecurityAgent(gl.Contract):
    owner: Address
    registry_address: Address
    # Unset until the deployer calls set_coordinator() -- see __init__ and
    # the note on execute() below. Bound as a separate post-deploy step
    # (same two-step bootstrap pattern as Aggregator<->Coordinator)
    # rather than a constructor argument, so agents keep deploying with
    # only registry_address and don't need Coordinator's address to
    # exist yet at their own deploy time.
    coordinator_address: Address
    capability: str
    name: str
    version: str
    description: str

    def __init__(self, registry_address: str):
        self.owner = gl.message.sender_address
        self.registry_address = Address(registry_address)
        self.coordinator_address = Address("0x0000000000000000000000000000000000000000")
        self.capability = "security-audit"
        self.name = "SecurityAgent"
        self.version = "1.0.0"
        self.description = "Assesses risk indicators in a task description"

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

    # Previously callable by anyone: any caller could pass their own
    # task_description here and get this agent to run a real LLM call
    # and submit_result() for it under this agent's own (legitimate)
    # address -- pre-empting whatever the Coordinator's actual dispatch
    # for this task_id would have submitted, since Aggregator's
    # idempotency check silently no-ops the second submission from the
    # same agent address. Restricting the caller to the bound
    # Coordinator closes this: task content now only ever reaches this
    # method via Coordinator.submit_task's own trusted dispatch.
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

        task_text = task_description

        prompt = f"""
You are a security auditor reviewing the following task/request for risk indicators.

Task: {task_text}

Assess the risk level and explain briefly why. Respond as strict JSON:
{{"verdict": "low" | "medium" | "high", "summary": "one or two sentence explanation"}}
"""

        def leader_fn():
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            my_result = leader_fn()
            return my_result.get("verdict") == leaders_res.calldata.get("verdict")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # Результат уходит только через контрактный интерфейс.
        aggregator = gl.get_contract_at(Address(aggregator_address))
        aggregator.emit(on="finalized").submit_result(
            task_id,
            self.capability,
            result.get("verdict", "unknown"),
            result.get("summary", ""),
        )

    @gl.public.view
    def get_capability(self) -> str:
        return self.capability
