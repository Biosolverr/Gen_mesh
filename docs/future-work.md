# Future Work

## Overview

GenMesh Core is intentionally implemented as a minimal proof of concept.

The goal of the MVP is not to solve every orchestration problem, but to
demonstrate that runtime-composed execution graphs can be built entirely
from Intelligent Contracts while remaining fully compatible with
GenLayer's execution and consensus model.

The current architecture deliberately leaves several areas for future
research and protocol-level experimentation.

---

# Short-Term Improvements

## Multi-Capability Agents

The Registry currently stores one capability per Agent.

```
SecurityAgent

↓

security-audit
```

A future version could support multiple capabilities.

```
SecurityAgent

↓

security-audit

↓

risk-analysis

↓

smart-contract-review
```

Coordinator would continue using the same discovery mechanism.

Only the Registry data model would expand.

---

## Rich Capability Metadata

Capabilities could evolve from simple strings into structured metadata.

Example:

```
Capability

↓

Name

↓

Version

↓

Description

↓

Tags

↓

Supported Models
```

This would allow more expressive planning without changing the execution
model.

---

## Better Agent Selection

Coordinator currently selects the first matching Agent returned by the
Registry.

Future implementations could consider:

- specialization;
- capability versions;
- historical performance;
- reputation;
- execution cost;
- latency.

Planning would remain non-deterministic while operating over a richer
dataset.

---

## Improved Aggregation

The current deterministic aggregation intentionally remains simple.

Future deterministic strategies may include:

- weighted voting;
- confidence scoring;
- statistical aggregation;
- domain-specific composition;
- configurable aggregation policies.

The LLM fallback would continue to be used only when deterministic
aggregation cannot resolve semantic disagreement.

---

# Medium-Term Research

## Multiple Coordinators

Nothing in the architecture assumes a single Coordinator.

```
Registry

      ▲

      │

 ┌────┴────┐

 │         │

 ▼         ▼

Coordinator A

Coordinator B

 │         │

 └────┬────┘

      ▼

Agents
```

Different Coordinators could implement different planning strategies
while sharing the same Registry and Agent ecosystem.

---

## Multiple Registries

Different application domains may maintain independent Registries.

Example:

```
Financial Registry

Research Registry

Legal Registry

Healthcare Registry
```

Each Registry could expose identical interfaces while serving different
ecosystems.

---

## Agent Reputation

Future Registries could maintain historical metadata.

Possible metrics include:

- successful executions;
- execution frequency;
- response consistency;
- appeal statistics;
- domain specialization.

Coordinator could incorporate reputation into planning without requiring
changes to Agent interfaces.

---

## Version Negotiation

Future Coordinators may negotiate Agent versions dynamically.

Example:

```
ResearchAgent

1.0

1.1

2.0
```

Planning could request:

- latest version;
- minimum compatible version;
- stable release;
- experimental release.

---

# Long-Term Research

## Nested Execution Graphs

An Agent could itself become another Coordinator.

```
Coordinator

↓

ResearchAgent

↓

Coordinator

↓

Sub Agents
```

This would allow recursive execution graphs while preserving the same
contract model.

No architectural changes would be required.

---

## Hierarchical Composition

Aggregation could become hierarchical.

```
Security

Finance

Research

↓

Domain Aggregators

↓

Global Aggregator
```

Each aggregation stage would remain independently validated by
Optimistic Democracy.

---

## Execution Graph Optimization

Future Coordinators could optimize execution graphs based on:

- execution cost;
- latency;
- available capabilities;
- dependency analysis.

Planning would become richer without changing the underlying protocol.

---

## Dynamic Capability Discovery

Instead of selecting capabilities from a flat list, future Registries
could expose richer relationships.

Example:

```
Security

├── Audit

├── Risk

└── Compliance
```

This would enable semantic planning over capability hierarchies.

---

## Cross-Domain Collaboration

Execution graphs could combine Agents from different domains.

Example:

```
Finance

+

Security

+

Research

+

Legal

↓

Unified Analysis
```

The architecture already supports this pattern without modification.

---

# Security Improvements

## Stronger Execution Manifest

The current MVP trusts Coordinator's execution manifest.

Future versions may introduce:

- signed manifests;
- immutable execution descriptors;
- independently verifiable planning metadata.

This would reduce the remaining trust assumptions.

---

## Capability Verification

Aggregator currently validates sender identity.

Future implementations may additionally verify:

- capability ownership;
- capability version;
- execution authorization.

---

## Richer Validation Policies

Future Aggregators could support configurable validation.

Examples:

- minimum required participants;
- capability-specific quorum;
- optional participants;
- weighted composition.

These policies would remain contract logic rather than protocol changes.

---

# Dashboard Evolution

The current dashboard focuses on explaining architecture.

Future versions may include:

- live transaction streaming;
- execution graph visualization;
- appeal visualization;
- execution timing;
- contract explorer integration;
- historical execution browser.

None of these require changes to GenMesh itself.

---

# Deployment Improvements

Potential deployment enhancements include:

- automated Agent discovery;
- deployment verification;
- Registry bootstrap scripts;
- contract upgrade tooling;
- multi-network deployment support.

---

# Research Questions

Several open questions remain intentionally unanswered.

Examples include:

- How should Agent reputation evolve?

- Should planning consider execution costs?

- Can deterministic aggregation cover more cases?

- How should nested execution graphs behave?

- What is the best capability taxonomy?

These questions are left for future experimentation rather than being
hardcoded into the MVP.

---

# Design Stability

Although many extensions are possible, the core architecture is expected
to remain stable.

The fundamental execution graph remains:

```
Registry

↓

Coordinator

↓

Agents

↓

Aggregator
```

Every future improvement is designed to extend one of these components
without replacing the overall execution model.

---

# Long-Term Vision

GenMesh Core aims to demonstrate that composable execution can become a
native execution primitive for Intelligent Contracts.

Rather than treating AI agents as external services orchestrated above
the blockchain, GenMesh treats every participant as an independently
validated Intelligent Contract.

As the ecosystem grows, new Coordinators, Registries, Agents, and
Aggregators can be introduced without changing the underlying execution
model.

This composability is the central idea of the project and the primary
direction for future development.
