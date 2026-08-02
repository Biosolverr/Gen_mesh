# Agent Integration Guide

## Overview

One of the primary design goals of GenMesh Core is that adding a new
Intelligent Contract should **never require modifying Coordinator,
Aggregator, or Registry**.

A new Agent becomes part of the execution graph simply by:

1. deploying the contract;
2. registering itself in the Registry;
3. binding itself to the Coordinator address that will dispatch tasks
   to it.

Everything else is discovered automatically at runtime.

---

# Agent Requirements

Every Agent must satisfy only a small contract.

It must:

- be a standard `gl.Contract`;
- expose a public `execute()` method, callable only by its bound
  Coordinator;
- expose a `register_self()` method;
- expose a `set_coordinator()` method, callable only by its owner;
- define a capability string;
- register itself inside the Registry.

Nothing else is required.

Agents remain independent Intelligent Contracts — each one still owns
its own domain logic, state, and capability, and is reusable across any
Coordinator that binds to it. Independence here means Agents don't
embed Coordinator's planning logic or know about other Agents, not that
they accept calls from anyone.

---

# Required Interface

Every Agent should expose the following execution interface.

```python
execute(
    task_id,
    task_description,
    capability,
    aggregator_address
)
```

The interface is intentionally generic.

Coordinator does not know what happens internally.

Aggregator does not know how the result was produced.

Only the interface is shared.

`execute()` accepts calls only from the agent's bound Coordinator
address (`gl.message.sender_address == self.coordinator_address`). An
earlier version left this open to any caller, on the assumption that an
Agent holds no state a malicious call could corrupt directly. That
assumption missed one thing: a caller could feed `execute()` fabricated
`task_description` for a real, already-registered `task_id`, and the
Agent — still using its own genuine, registered address — would submit
that fabricated result to Aggregator. Because Aggregator deduplicates
submissions per `(task_id, agent address)`, that forged submission
would win, silently discarding the real one Coordinator's own dispatch
produces afterward. Restricting the caller closes this: task content
now only ever reaches an Agent through Coordinator's trusted dispatch.

---

# Registration

Each Agent registers itself after deployment.

```
Deploy Agent

↓

register_self()

↓

Registry.register()

↓

Available Network-wide
```

Registration is permissionless.

The Agent proves ownership simply by calling Registry from its own
contract address. Only the agent itself — or the Registry's owner, for
initial bootstrap — can register a given address. No unrelated third
party can register a contract on someone else's behalf.

---

# Binding to a Coordinator

After registering, each Agent must also be bound to the Coordinator
that will dispatch tasks to it:

```
Deploy Agent

↓

register_self()

↓

set_coordinator(coordinator_address)

↓

execute() now accepts calls from that Coordinator only
```

`set_coordinator()` may only be called by the Agent's owner (the
account that deployed it) — the same one-owner, one-time-bootstrap
pattern already used for `Aggregator.set_coordinator()`. Until this
runs, `coordinator_address` defaults to the zero address and
`execute()` rejects every caller, including a legitimate Coordinator
that hasn't been bound yet.

This is a separate step from registration deliberately: Registry
discovery and Coordinator dispatch rights are independent concerns. An
Agent can be discoverable in Registry without yet being callable by any
particular Coordinator, and re-binding to a different Coordinator later
doesn't require re-registering.

---

# Self-Registration

Registration follows the identity model of GenLayer.

```
Contract Address

↓

register_self()

↓

Registry
```

Registry verifies that the sender matches the address being registered.

This prevents spoofing.

It also removes the need for centralized administration.

---

# Required Metadata

Each Agent provides metadata describing its capabilities.

Typical fields include:

- name
- capability
- version
- description
- active

Example:

```
SecurityAgent

Capability:
security-audit

Version:
1.0.0

Description:
Assesses security risks
```

Coordinator never hardcodes these values.

Everything is discovered dynamically.

---

# Capability Design

Capabilities should describe **what the Agent can do**, not how it
implements it.

Good examples:

```
security-audit

research

market-analysis

content-moderation

translation

legal-review
```

Poor examples:

```
agent1

llm-agent

gpt-agent

contract42
```

Coordinator reasons about capabilities rather than contract identities.

---

# Discovery

Coordinator discovers available Agents by reading Registry.

```
Registry

↓

getAgents()

↓

Available Capabilities

↓

Planning
```

The Registry acts as an on-chain discovery primitive.

There is no off-chain directory.

---

# Runtime Selection

Coordinator never stores Agent addresses.

Instead, every request performs fresh discovery.

```
Request

↓

Registry Lookup

↓

Capability Selection

↓

Execution
```

This allows the network topology to evolve over time without changing
Coordinator.

---

# Trust Model

Agents are never trusted simply because Coordinator called them.

Every invocation is treated as an ordinary contract call, and `execute()`
now additionally verifies the caller is the Agent's bound Coordinator
before doing anything else.

The Agent validates:

- caller identity (must be the bound Coordinator);
- capability;
- task input;
- local execution rules.

The only privileged caller in this model is the bound Coordinator, and
that privilege is scoped to nothing more than triggering `execute()` —
it grants no access to any other Agent state or method.

---

# Coordinator Relationship

Agents reference exactly one piece of Coordinator-related state: the
address of the Coordinator currently allowed to call `execute()`. They
still hold:

- no coordinator whitelist (only one bound address, replaceable via a
  fresh `set_coordinator()` call by the owner);
- no coordinator planning logic;
- no coordinator state beyond that single address;
- no awareness of other Agents.

The execution relationship per task remains temporary:

```
Coordinator

↓

execute()

↓

Finished
```

After execution the relationship for that task disappears — only the
binding itself (which Coordinator may call `execute()` at all) persists
across tasks, until explicitly rebound.

---

# Aggregator Independence

Agents know only one destination for results.

```
Aggregator

↓

submit_result()
```

They never communicate with:

- Registry
- other Agents
- Coordinator, beyond accepting its calls to `execute()`

This keeps the execution graph loosely coupled.

---

# Result Format

Each Agent returns structured information.

Typical fields include:

```
Capability

Verdict

Summary
```

The internal reasoning may differ completely between Agents.

Aggregator only consumes the standardized output, and attributes it to
whichever address actually sent the transaction — not to a value the
Agent's code could set arbitrarily. Aggregator additionally verifies
the submitted capability against the one Coordinator registered for
that Agent on that task, so an Agent's submission can't be attributed to
a capability it wasn't actually assigned.

---

# Domain Specialization

Every Agent owns exactly one domain of expertise.

Examples:

SecurityAgent

```
Task

↓

Security Assessment

↓

Risk Verdict
```

FinanceAgent

```
Task

↓

Market Analysis

↓

Outlook
```

ResearchAgent

```
Task

↓

Evidence Evaluation

↓

Confidence
```

Agents remain isolated from one another.

---

# Non-Deterministic Execution

Every Agent may use its own reasoning strategy.

Typical implementation:

```
execute()

↓

run_nondet_unsafe()

↓

LLM

↓

Structured Result
```

The execution model is identical for every Agent.

Only prompts differ.

---

# Validator Behavior

Validators independently execute the same inference.

Agreement is established through GenLayer's existing Equivalence
Principle.

No Agent-specific consensus exists.

---

# Adding a New Agent

Suppose we create:

```
ContentModerationAgent
```

The process is straightforward.

Step 1

Implement:

```
execute()

register_self()

set_coordinator()
```

Step 2

Choose:

```
capability

↓

content-moderation
```

Step 3

Deploy.

Step 4

Call:

```
register_self()
```

Step 5

Call:

```
set_coordinator(coordinator_address)
```

Done.

Coordinator immediately discovers the new capability during the next
request, and — once bound — is able to dispatch to it.

No redeployment of Coordinator, Aggregator, or Registry is required.

---

# Why Coordinator Never Changes

Coordinator obtains its planning information dynamically.

```
Registry

↓

Current Capabilities

↓

Planning Prompt
```

Because capabilities are loaded at runtime:

- no address list exists;
- no capability list exists;
- no switch statement exists.

Adding Agents changes only Registry state and each new Agent's own
Coordinator binding. Coordinator's own logic remains unchanged.

---

# Versioning

Multiple versions of the same Agent may coexist.

Example:

```
SecurityAgent

v1.0

v1.1

v2.0
```

Registry exposes version metadata.

Future Coordinators may use version information as part of planning
without changing the Agent interface.

---

# Best Practices

Recommended guidelines:

- keep capabilities narrow;
- return structured JSON;
- avoid hidden dependencies;
- accept execution calls only from a bound Coordinator;
- avoid storing execution state;
- keep prompts domain-specific;
- make execution deterministic whenever possible.

---

# Design Philosophy

An Agent is **not** a worker owned by Coordinator.

An Agent is a fully independent Intelligent Contract that happens to
participate in a larger execution graph, and that only accepts
execution triggers from the specific Coordinator it has chosen to bind
to.

That distinction is fundamental.

GenMesh composes autonomous Intelligent Contracts rather than embedding
multiple roles inside a single orchestrator.

This makes every Agent reusable across multiple Coordinators over time
(by rebinding), multiple applications, and future execution graphs,
without requiring any changes to the Agent's own domain logic.
