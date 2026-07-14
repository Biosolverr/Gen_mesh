# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class ResearchAgent(gl.Contract):
    registry_address: Address
    capability: str
    name: str
    version: str
    description: str

    def __init__(self, registry_address: str):
        self.registry_address = Address(registry_address)
        self.capability = "research"
        self.name = "ResearchAgent"
        self.version = "1.0.0"
        self.description = "Evaluates how well-supported a claim or question is"

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

    @gl.public.write
    def execute(
        self,
        task_id: u32,
        task_description: str,
        capability: str,
        aggregator_address: str,
    ) -> None:
        if capability != self.capability:
            raise gl.vm.UserError("Capability mismatch")
        if not task_description.strip():
            raise gl.vm.UserError("Empty task description")

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
