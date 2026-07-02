# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass


@allow_storage
@dataclass
class AgentInfo:
    name: str
    address: Address
    capability: str
    version: str
    description: str
    active: bool


class AgentRegistry(gl.Contract):
    # Владелец — только bootstrap/fallback для модерации (спам/скомпрометированные
    # агенты). Основной путь управления записью — self-management самим агентом.
    owner: Address

    agents: TreeMap[Address, AgentInfo]
    # Источник истины для итерации и проверки существования — TreeMap не
    # гарантирует удобную итерацию по значениям.
    agent_addresses: DynArray[Address]

    def __init__(self):
        self.owner = gl.message.sender_address

    # ---------- internal helpers ----------

    def _is_registered(self, address: Address) -> bool:
        for a in self.agent_addresses:
            if a == address:
                return True
        return False

    def _require_registered(self, address: Address):
        if not self._is_registered(address):
            raise Exception("Agent is not registered")

    def _require_owner_or_self(self, address: Address):
        sender = gl.message.sender_address
        if sender != address and sender != self.owner:
            raise Exception("Only the agent itself or the registry owner can modify this entry")

    # ---------- public write API ----------

    @gl.public.write
    def register(
        self,
        address: str,
        name: str,
        capability: str,
        version: str,
        description: str,
    ):
        agent_address = Address(address)

        # Permissionless-инвариант: контракт может зарегистрировать сам себя
        # (sender == address), либо владелец реестра может забутстрапить запись.
        sender = gl.message.sender_address
        if sender != agent_address and sender != self.owner:
            raise Exception("Only the agent itself (or the registry owner) can register this address")

        if self._is_registered(agent_address):
            raise Exception("Agent already registered at this address")

        if not name or not capability or not version:
            raise Exception("name, capability and version are required")

        self.agents[agent_address] = AgentInfo(
            name=name,
            address=agent_address,
            capability=capability,
            version=version,
            description=description,
            active=True,
        )
        self.agent_addresses.append(agent_address)

    @gl.public.write
    def remove(self, address: str):
        agent_address = Address(address)
        self._require_registered(agent_address)
        self._require_owner_or_self(agent_address)

        del self.agents[agent_address]

        remaining = DynArray[Address]()
        for a in self.agent_addresses:
            if a != agent_address:
                remaining.append(a)
        self.agent_addresses = remaining

    @gl.public.write
    def update(
        self,
        address: str,
        name: str = "",
        capability: str = "",
        version: str = "",
        description: str = "",
        active: bool = True,
    ):
        agent_address = Address(address)
        self._require_registered(agent_address)
        self._require_owner_or_self(agent_address)

        current = self.agents[agent_address]

        self.agents[agent_address] = AgentInfo(
            name=name if name else current.name,
            address=agent_address,
            capability=capability if capability else current.capability,
            version=version if version else current.version,
            description=description if description else current.description,
            active=active,
        )

    # ---------- public view API (discovery) ----------

    @gl.public.view
    def getAgents(self) -> list:
        result = []
        for a in self.agent_addresses:
            info = self.agents[a]
            result.append({
                "name": info.name,
                "address": info.address,
                "capability": info.capability,
                "version": info.version,
                "description": info.description,
                "active": info.active,
            })
        return result

    @gl.public.view
    def findByCapability(self, capability: str) -> list:
        target = capability.strip().lower()
        result = []
        for a in self.agent_addresses:
            info = self.agents[a]
            if info.active and info.capability.strip().lower() == target:
                result.append({
                    "name": info.name,
                    "address": info.address,
                    "capability": info.capability,
                    "version": info.version,
                    "description": info.description,
                    "active": info.active,
                })
        return result
