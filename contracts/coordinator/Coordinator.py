# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class Coordinator(gl.Contract):
    registry_address: Address
    aggregator_address: Address
    task_counter: u32

    def __init__(self, registry_address: str, aggregator_address: str):
        self.registry_address = Address(registry_address)
        self.aggregator_address = Address(aggregator_address)
        self.task_counter = u32(0)

    @gl.public.view
    def get_task_count(self) -> u32:
        return self.task_counter

    @gl.public.write
    def submit_task(self, task_description: str) -> u32:
        registry = gl.get_contract_at(self.registry_address)

        # 1. Детерминированное чтение: какие capability вообще существуют.
        #    Это заземляет LLM — он выбирает только из реального пространства
        #    возможностей, а не изобретает capability на лету.
        all_agents = registry.view().getAgents()
        capability_pool = sorted({a["capability"] for a in all_agents if a["active"]})

        if not capability_pool:
            raise gl.vm.UserError("Registry has no active agents")

        # Локальные копии — non-det блок ниже не может обращаться к self.
        task_text = task_description
        capability_list_str = ", ".join(capability_pool)

        prompt = f"""
You are selecting which capabilities are required to fulfill this task.

Task: {task_text}

Available capabilities (choose only from this closed list, never invent new ones):
{capability_list_str}

Return strict JSON: {{"capabilities": ["cap1", "cap2", ...]}}
Include only capabilities that are genuinely necessary for this task.
If none apply, return an empty list.
Sort the list alphabetically.
"""

        def leader_fn():
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            my_result = leader_fn()
            return sorted(my_result.get("capabilities", [])) == sorted(
                leaders_res.calldata.get("capabilities", [])
            )

        # 2. Единственная non-det операция Coordinator'а: capability matching.
        #    Ничего больше — ни планирования шагов, ни ретраев, ни оркестрации.
        plan = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        required_caps = sorted(set(plan.get("capabilities", [])))

        if not required_caps:
            raise gl.vm.UserError("No matching capabilities found for this task")

        # 3. Снова детерминированно: конкретные адреса под каждую capability.
        assigned = []
        for cap in required_caps:
            candidates = registry.view().findByCapability(cap)
            if candidates:
                assigned.append((candidates[0]["address"], cap))

        if not assigned:
            raise gl.vm.UserError("No active agents available for required capabilities")

        task_id = self.task_counter
        self.task_counter += u32(1)

        # 4. Execution Plan материализуется как fan-out emit() — и ничего после.
        for agent_address, cap in assigned:
            agent = gl.get_contract_at(agent_address)
            agent.emit(on="finalized").execute(task_id, task_text, cap, str(self.aggregator_address))

        # Единственная связь с Aggregator: манифест ожидаемой задачи.
        # register_task больше не принимает список адресов (это ломало
        # декодирование при ручных тестах в Studio) — сначала фиксируется
        # количество, затем каждый агент добавляется отдельным вызовом.
        aggregator = gl.get_contract_at(self.aggregator_address)
        aggregator.emit(on="finalized").register_task(task_id, u32(len(assigned)))
        for agent_address, cap in assigned:
            aggregator.emit(on="finalized").add_expected_agent(task_id, agent_address.as_hex)

        return task_id

