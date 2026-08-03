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
    owner: Address
    # Unset until the deployer calls set_coordinator() — see __init__.
    # register_task / add_expected_agent are rejected until this is bound.
    coordinator_address: Address

    MAX_CAPABILITY_LENGTH = 64
    MAX_VERDICT_LENGTH = 64
    MAX_SUMMARY_LENGTH = 4000

    # Плоский список ПО ВСЕМ задачам сразу — единственная DynArray в этом
    # контракте, и она top-level (auto-инициализируется фреймворком при
    # деплое), поэтому append() безопасен. Никаких DynArray/TreeMap не
    # создаётся вручную внутри методов — inmem_allocate() оказался
    # нестабилен на текущем рантайме студионета, поэтому здесь его нет
    # вообще.
    submissions: DynArray[AgentSubmission]

    # "Кто ожидается по какой задаче, и с какой capability" — составной
    # строковый ключ "task_id:address" в плоском TreeMap, значение —
    # сама ожидаемая capability (непустая строка = "ожидается"), а не
    # просто bool. Раньше здесь хранился только bool: submit_result
    # проверял "зарегистрирован ли этот адрес по этой задаче", но не
    # проверял, ЧТО именно он должен был сдать — агент (или кто угодно,
    # пока execute() был не защищён) мог прислать результат под любой
    # capability, и Aggregator принимал это как есть. Теперь
    # add_expected_agent обязан указать capability при регистрации
    # ожидания, а submit_result сверяет присланную capability с этим
    # обязательством.
    expected_capabilities: TreeMap[str, str]
    expected_counts: TreeMap[u32, u32]

    task_ids: DynArray[u32]
    finalized_flags: TreeMap[u32, bool]
    final_verdicts: TreeMap[u32, str]
    final_summaries: TreeMap[u32, str]

    def __init__(self):
        self.owner = gl.message.sender_address
        # Coordinator's own constructor needs Aggregator's address, so the
        # two contracts can't know each other's address in the same deploy
        # step. Bootstrap in two steps instead: deploy Aggregator first
        # (coordinator_address unset), deploy Coordinator with this
        # Aggregator's address, then call set_coordinator() once as owner.
        self.coordinator_address = Address("0x0000000000000000000000000000000000000000")

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

    def _require_coordinator(self):
        if gl.message.sender_address != self.coordinator_address:
            raise gl.vm.UserError("Only the coordinator can modify a task manifest")

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
        # Раньше здесь был безусловный parsed.get(...), который
        # предполагал, что raw — валидный JSON-объект. Если LLM (или
        # смошенничавший leader) вернёт не-объект (например, JSON-массив)
        # или невалидный JSON вообще, .get() на не-dict бросал бы
        # AttributeError прямо внутри submit_result — а поскольку это
        # последняя транзакция, наполняющая expected_count, откат этой
        # транзакции откатывает и только что добавленный submission,
        # и задача навсегда остаётся недофинализированной без публичного
        # способа повторить попытку. Теперь любая неожиданная форма
        # results падает не в ошибку транзакции, а в безопасный
        # детерминированный fallback.
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}

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
    def set_coordinator(self, coordinator_address: str):
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("Only the owner can set the coordinator address")
        self.coordinator_address = Address(coordinator_address)

    @gl.public.write
    def register_task(self, task_id: u32, expected_count: u32):
        # Раньше любой адрес мог зарегистрировать задачу — единственной
        # границей был "кто первый вызвал". Теперь разрешено только
        # контракту Coordinator, привязанному через set_coordinator().
        self._require_coordinator()

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
    def add_expected_agent(self, task_id: u32, agent_address: str, capability: str):
        self._require_coordinator()

        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")
        if self.finalized_flags.get(task_id, False):
            raise gl.vm.UserError("Task already finalized")
        if not capability.strip():
            raise gl.vm.UserError("capability is required")
        if len(capability) > self.MAX_CAPABILITY_LENGTH:
            raise gl.vm.UserError(f"capability exceeds {self.MAX_CAPABILITY_LENGTH} characters")

        addr = Address(agent_address)
        self.expected_capabilities[self._expected_key(task_id, addr)] = capability

    @gl.public.write
    def submit_result(
        self,
        task_id: u32,
        capability: str,
        verdict: str,
        summary: str,
    ):
        # Идентичность агента берётся ТОЛЬКО из отправителя транзакции.
        # Раньше agent_address был обычным строковым параметром, который
        # вызывающий указывал сам — контракт верил ему на слово, и любой
        # адрес мог выдать себя за любого агента.
        sender = gl.message.sender_address

        if len(verdict) > self.MAX_VERDICT_LENGTH:
            raise gl.vm.UserError(f"verdict exceeds {self.MAX_VERDICT_LENGTH} characters")
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            raise gl.vm.UserError(f"summary exceeds {self.MAX_SUMMARY_LENGTH} characters")

        if not self._is_registered(task_id):
            raise gl.vm.UserError("Unknown task_id")

        if self.finalized_flags.get(task_id, False):
            return  # поздний результат по уже закрытой задаче — no-op

        key = self._expected_key(task_id, sender)
        expected_capability = self.expected_capabilities.get(key, "")
        if not expected_capability:
            raise gl.vm.UserError("Agent is not part of this task's execution plan")

        # Раньше capability принималась от вызывающего без проверки —
        # даже с верно аутентифицированным sender'ом, агент (или любой
        # адрес, вызвавший его execute() до фикса execute()) мог сдать
        # результат под чужой capability, искажая агрегацию по
        # by_capability в _finalize. Теперь сверяется с тем, что
        # Coordinator реально зарегистрировал для этого агента и этой
        # задачи в add_expected_agent.
        if capability != expected_capability:
            raise gl.vm.UserError(
                "Submitted capability does not match the registered task commitment"
            )

        for s in self._submissions_for(task_id):
            if s.agent_address == sender:
                return  # идемпотентность при повторном emit

        self.submissions.append(
            AgentSubmission(
                task_id=task_id,
                agent_address=sender,
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


