# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class AgentSubmission:
    task_id: u32
    agent_address: Address
    capability: str
    verdict: str
    summary: str


class Aggregator(gl.Contract):
    # Плоский список ПО ВСЕМ задачам сразу — единственная DynArray в этом
    # контракте, и она top-level (auto-инициализируется фреймворком при
    # деплое), поэтому append() безопасен. Никаких DynArray/TreeMap не
    # создаётся вручную внутри методов — inmem_allocate() оказался
    # нестабилен на текущем рантайме студионета, поэтому здесь его нет
    # вообще.
    submissions: DynArray[AgentSubmission]

    # "Кто ожидается по какой задаче" — вместо вложенной DynArray на
    # задачу, составной строковый ключ "task_id:address" в плоском TreeMap.
    expected_flags: TreeMap[str, bool]
    expected_counts: TreeMap[u32, u32]

    task_ids: DynArray[u32]
    finalized_flags: TreeMap[u32, bool]
    final_verdicts: TreeMap[u32, str]
    final_summaries: TreeMap[u32, str]

    def __init__(self):
        pass

    # ---------- internal helpers ----------

    def _is_registered(self, task_id: u32) -> bool:
        for t in self.task_ids:
            if t == task_id:
                return True
        return False

    def _expected_key(self, task_id: u32, agent_address: Address) -> str:
        return f"{task_id}:{agent_address.as_hex}"

    def _submissions_for(self, task_id: u32) -> list:
        return [s for s in self.submissions if s.task_id == task_id]

    def _deterministic_aggregate(self, submissions) -> tuple:
        negative_verdicts = {"high", "bearish", "unconfirmed", "inconclusive"}
        parts = []
        escalated = False
        for s in submissions:
            parts.append(f"[{s.capability}] {s.verdict}: {s.summary}")
            if s.verdict in negative_verdicts:
                escalated = True
        final_verdict = "flagged" if escalated else "clear"
        final_summary = " | ".join(parts)
        return final_verdict, final_summary

    def _llm_aggregate(self, submissions) -> tuple:
        lines = []
        for s in submissions:
            lines.append(f"- ({s.capability}) verdict={s.verdict}: {s.summary}")
        report = "\n".join(lines)

        prompt = f"""
You are synthesizing conflicting assessments from multiple specialized reviewers
into one final verdict.

Reviewer findings:
{report}

Resolve the disagreement and respond as strict JSON:
{{"verdict": "<short category>", "summary": "one or two sentence synthesis"}}
Respond with JSON only, no markdown formatting.
"""

        def synthesize() -> str:
            result = gl.nondet.exec_prompt(prompt, response_format="json")
            return json.dumps(result, sort_keys=True)

        # Штатный Equivalence Principle механизм GenLayer для проверки
        # эквивалентности non-deterministic результата.
        raw = gl.eq_principle.prompt_comparative(
            synthesize,
            principle=(
                "The verdict category and the overall meaning of the summary "
                "must match; exact wording may differ."
            ),
        )
        parsed = json.loads(raw)
        return parsed.get("verdict", "unresolved"), parsed.get("summary", "")

    def _finalize(self, task_id: u32, submissions: list):
        by_capability = {}
        for s in submissions:
            by_capability.setdefault(s.capability, []).append(s.verdict)

        has_conflict = any(len(set(v)) > 1 for v in by_capability.values())

        if has_conflict:
            final_verdict, final_summary = self._llm_aggregate(submissions)
        else:
            final_verdict, final_summary = self._deterministic_aggregate(submissions)

        self.finalized_flags[task_id] = True
        self.final_verdicts[task_id] = final_verdict
        self.final_summaries[task_id] = final_summary

    # ---------- public write API ----------

    @gl.public.write
    def register_task(self, task_id: u32, expected_count: u32):
        # Список адресов как параметр (list) ломается при ручном декодировании
        # через Studio UI (проверено — мусорные байты вместо адреса). Поэтому
        # регистрация задачи отделена от регистрации конкретных ожидаемых
        # агентов: сюда передаётся только количество, сами адреса добавляются
        # по одному через add_expected_agent — тем же проверенным паттерном
        # одиночного str-параметра, что и в Registry.register().
        if self._is_registered(task_id):
            raise gl.vm.UserError("Task already registered")
        if expected_count == 0:
            raise gl.vm.UserError("expected_count must be at least 1")

        self.expected_counts[task_id] = expected_count
        self.finalized_flags[task_id] = False
        self.final_verdicts[task_id] = ""
        self.final_summaries[task_id] = ""
        self.task_ids.append(task_id)

    @gl.public.write
    def add_expected_agent(self, task_id: u32, agent_address: str):
        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")
        if self.finalized_flags.get(task_id, False):
            raise gl.vm.UserError("Task already finalized")

        addr = Address(agent_address)
        self.expected_flags[self._expected_key(task_id, addr)] = True

    @gl.public.write
    def submit_result(
        self,
        task_id: u32,
        agent_address: str,
        capability: str,
        verdict: str,
        summary: str,
    ):
        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")

        if self.finalized_flags.get(task_id, False):
            return  # поздний результат по уже закрытой задаче — no-op

        addr = Address(agent_address)

        key = self._expected_key(task_id, addr)
        if not self.expected_flags.get(key, False):
            raise gl.vm.UserError("Agent is not part of this task's execution plan")

        for s in self._submissions_for(task_id):
            if s.agent_address == addr:
                return  # идемпотентность при повторном emit

        self.submissions.append(
            AgentSubmission(
                task_id=task_id,
                agent_address=addr,
                capability=capability,
                verdict=verdict,
                summary=summary,
            )
        )

        updated = self._submissions_for(task_id)
        expected_count = self.expected_counts.get(task_id, u32(0))
        if len(updated) >= expected_count:
            self._finalize(task_id, updated)

    # ---------- public view API ----------

    @gl.public.view
    def get_result(self, task_id: u32) -> dict:
        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")

        subs = self._submissions_for(task_id)
        return {
            "finalized": self.finalized_flags.get(task_id, False),
            "verdict": self.final_verdicts.get(task_id, ""),
            "summary": self.final_summaries.get(task_id, ""),
            "submissions": [
                {
                    "agent_address": s.agent_address,
                    "capability": s.capability,
                    "verdict": s.verdict,
                    "summary": s.summary,
                }
                for s in subs
            ],
        }

