# Agent Integration Guide

## Overview

One of the primary design goals of GenMesh Core is that adding a new
Intelligent Contract should **never require modifying Coordinator,
Aggregator, or Registry**.

A new Agent becomes part of the execution graph simply by:

1. deploying the contract;
2. registering itself in the Registry.

Everything else is discovered automatically at runtime.

---

# Agent Requirements

Every Agent must satisfy only a small contract.

It must:

- be a standard `gl.Contract`;
- expose a public `execute()` method;
- expose a `register_self()` method;
- define a capability string;
- register itself inside the Registry.

Nothing else is required.

Agents remain completely independent Intelligent Contracts.

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

Every invocation is treated as an ordinary contract call.

The Agent validates:

- capability;
- task input;
- local execution rules.

There is no privileged caller.

---

# Coordinator Independence

Agents never reference Coordinator.

There is:

- no coordinator address;
- no coordinator whitelist;
- no coordinator permission;
- no coordinator state.

The execution relationship is temporary.

```
Coordinator

↓

execute()

↓

Finished
```

After execution the relationship disappears.

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
- Coordinator

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
Agent's code could set arbitrarily.

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

Done.

Coordinator immediately discovers the new capability during the next
request.

No redeployment is required.

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

Adding Agents changes only Registry state.

Coordinator logic remains unchanged.

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
- never reference Coordinator;
- avoid storing execution state;
- keep prompts domain-specific;
- make execution deterministic whenever possible.

---

# Design Philosophy

An Agent is **not** a worker owned by Coordinator.

An Agent is a fully independent Intelligent Contract that happens to
participate in a larger execution graph.

That distinction is fundamental.

GenMesh composes autonomous Intelligent Contracts rather than embedding
multiple roles inside a single orchestrator.

This makes every Agent reusable across multiple Coordinators, multiple
applications, and future execution graphs without requiring any changes
to the Agent itself.
