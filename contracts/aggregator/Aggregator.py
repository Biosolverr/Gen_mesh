# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json


@allow_storage
@dataclass
class AgentSubmission:
    agent_address: Address
    capability: str
    verdict: str
    summary: str


@allow_storage
@dataclass
class TaskManifest:
    expected_agents: DynArray[Address]
    submissions: DynArray[AgentSubmission]
    finalized: bool
    final_verdict: str
    final_summary: str


class Aggregator(gl.Contract):
    tasks: TreeMap[u32, TaskManifest]
    task_ids: DynArray[u32]

    def __init__(self):
        pass

    # ---------- internal helpers ----------

    def _is_registered(self, task_id: u32) -> bool:
        for t in self.task_ids:
            if t == task_id:
                return True
        return False

    def _is_expected(self, manifest: TaskManifest, agent_address: Address) -> bool:
        for a in manifest.expected_agents:
            if a == agent_address:
                return True
        return False

    def _has_submitted(self, manifest: TaskManifest, agent_address: Address) -> bool:
        for s in manifest.submissions:
            if s.agent_address == agent_address:
                return True
        return False

    def _deterministic_aggregate(self, submissions) -> tuple:
        # Приоритетный путь: детерминированная композиция, без сравнения
        # мнений друг с другом — просто табуляция того, что уже пришло.
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
        # Fallback-путь: включается только при конфликте verdict внутри
        # одной и той же capability — когда композиция без смыслового
        # разрешения объективно невозможна.
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
        # эквивалентности non-deterministic результата — сравнивается полный
        # смысл ответа, а не одно поле, как в Agent'ах.
        raw = gl.eq_principle.prompt_comparative(
            synthesize,
            principle=(
                "The verdict category and the overall meaning of the summary "
                "must match; exact wording may differ."
            ),
        )
        parsed = json.loads(raw)
        return parsed.get("verdict", "unresolved"), parsed.get("summary", "")

    def _finalize(self, task_id: u32, manifest: TaskManifest):
        submissions = manifest.submissions

        by_capability = {}
        for s in submissions:
            by_capability.setdefault(s.capability, []).append(s.verdict)

        has_conflict = any(len(set(v)) > 1 for v in by_capability.values())

        if has_conflict:
            final_verdict, final_summary = self._llm_aggregate(submissions)
        else:
            final_verdict, final_summary = self._deterministic_aggregate(submissions)

        manifest.finalized = True
        manifest.final_verdict = final_verdict
        manifest.final_summary = final_summary
        self.tasks[task_id] = manifest

    # ---------- public write API ----------

    @gl.public.write
    def register_task(self, task_id: u32, expected_agents: list):
        if self._is_registered(task_id):
            raise gl.vm.UserError("Task already registered")

        expected = DynArray[Address]()
        for a in expected_agents:
            expected.append(a)

        self.tasks[task_id] = TaskManifest(
            expected_agents=expected,
            submissions=DynArray[AgentSubmission](),
            finalized=False,
            final_verdict="",
            final_summary="",
        )
        self.task_ids.append(task_id)

    @gl.public.write
    def submit_result(
        self,
        task_id: u32,
        agent_address: Address,
        capability: str,
        verdict: str,
        summary: str,
    ):
        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")

        manifest = self.tasks[task_id]

        if manifest.finalized:
            return  # поздний результат по уже закрытой задаче — no-op, не ошибка

        # Не доверяет одному агенту: принимается только результат от адреса,
        # явно входящего в план этой задачи.
        if not self._is_expected(manifest, agent_address):
            raise gl.vm.UserError("Agent is not part of this task's execution plan")

        # Идемпотентность на случай повторного emit при апелляции.
        if self._has_submitted(manifest, agent_address):
            return

        manifest.submissions.append(
            AgentSubmission(
                agent_address=agent_address,
                capability=capability,
                verdict=verdict,
                summary=summary,
            )
        )
        self.tasks[task_id] = manifest

        if len(manifest.submissions) >= len(manifest.expected_agents):
            self._finalize(task_id, manifest)

    # ---------- public view API ----------

    @gl.public.view
    def get_result(self, task_id: u32) -> dict:
        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")
        manifest = self.tasks[task_id]
        return {
            "finalized": manifest.finalized,
            "verdict": manifest.final_verdict,
            "summary": manifest.final_summary,
            "submissions": [
                {
                    "agent_address": s.agent_address,
                    "capability": s.capability,
                    "verdict": s.verdict,
                    "summary": s.summary,
                }
                for s in manifest.submissions
            ],
        }
