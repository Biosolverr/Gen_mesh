# GenMesh Core Dashboard

> Execution trace visualizer for GenMesh Core.

The dashboard is intentionally **not** a wallet, explorer, or transaction
submission interface.

Its only purpose is to demonstrate and explain how a request flows through
the complete GenMesh Core execution graph.

```
User
   │
   ▼
Coordinator
   │
   ▼
Registry
   │
   ▼
Execution Plan
   │
   ▼
Agent ICs
   │
   ▼
Aggregator
   │
   ▼
Optimistic Democracy
   │
   ▼
Final Result
```

The dashboard is designed for reviewers, developers and anyone interested
in understanding how GenMesh Core composes Intelligent Contracts.

---

# Purpose

The contracts already prove that the architecture works.

The dashboard exists to make the architecture understandable.

Instead of reading several hundred lines of Python contracts,
a reviewer can observe the complete execution flow visually.

The visualization follows the exact architecture implemented in the
repository.

No hidden backend exists.

No simulated services replace Intelligent Contracts.

The dashboard is only a presentation layer.

---

# Dashboard Architecture

```
Browser
   │
   ▼
app.js
   │
   ├──────────────► Simulated Execution
   │
   └──────────────► genlayer-js
                          │
                          ▼
                  Registry (view)
                  Aggregator (view)
```

The frontend is intentionally simple.

```
index.html
style.css
app.js
```

No React.

No Vue.

No build system.

No bundler.

No framework.

The entire application is static and deploys directly to Vercel.

---

# Features

## 1. Simulated Run

This mode demonstrates the complete execution pipeline.

Every stage appears one after another.

```
User Request
        │
        ▼
Coordinator
        │
        ▼
Registry Lookup
        │
        ▼
Execution Plan
        │
        ▼
Agent Calls
        │
        ▼
Agent Responses
        │
        ▼
Aggregation
        │
        ▼
Optimistic Democracy
        │
        ▼
Final Result
```

Every stage expands independently.

Each section displays the information produced by the corresponding
Intelligent Contract.

Nothing is hidden.

---

## 2. Registry Lookup

Shows:

- deployed Registry contract
- discovered capabilities
- active agents
- selected execution candidates

Example:

```
Registry

security-audit
market-analysis
research
```

---

## 3. Coordinator

Displays:

- user request
- capability selection
- generated execution plan
- selected contracts

The dashboard intentionally illustrates that planning is dynamic.

Different requests produce different execution plans.

Coordinator does not contain a predefined workflow.

---

## 4. Agent Calls

Displays every Intelligent Contract selected by Coordinator.

Example:

```
Coordinator

      │

 ┌────┴───────────┐
 ▼                ▼

SecurityAgent   FinanceAgent
```

Each Agent card displays:

- contract address
- capability
- execution status
- returned result

---

## 5. Agent Responses

Responses are displayed exactly as they are produced by the Agent
contracts.

Example:

```
SecurityAgent

Verdict:
HIGH

Summary:
Missing access control and upgrade delay.
```

```
FinanceAgent

Verdict:
BEARISH

Summary:
Market conditions increase liquidation risk.
```

This corresponds directly to the JSON returned by the Intelligent
Contracts.

---

## 6. Aggregation

The dashboard visualizes both execution paths.

### Deterministic path

```
No conflict

↓

Deterministic aggregation

↓

Final Result
```

No LLM execution occurs.

---

### Non-deterministic path

```
Conflict

↓

Equivalence Principle

↓

LLM synthesis

↓

Final Result
```

This demonstrates the exact Aggregator logic implemented in the contracts.

---

## 7. Optimistic Democracy

The dashboard explicitly shows that every execution step remains an
ordinary GenLayer transaction.

Example:

| Transaction | Type | Status |
|-------------|------|--------|
| Coordinator | Non-det | Finalized |
| SecurityAgent | Non-det | Finalized |
| FinanceAgent | Non-det | Finalized |
| Aggregator | Deterministic | Finalized |

This reinforces one of the main architectural goals of GenMesh Core:

There is **no separate mesh consensus**.

Every contract continues using the native Optimistic Democracy protocol.

---

# Live Read Mode

Besides the simulated execution trace, the dashboard can query deployed
contracts directly.

Supported operations:

```
Registry.getAgents()
```

and

```
Aggregator.get_result(task_id)
```

using **genlayer-js**.

Only read operations are performed.

No wallet integration is required.

No private keys are stored.

No transactions are signed from the browser.

This preserves the same trust assumptions as the contracts themselves.

---

# Deployment

The dashboard is completely static.

No backend server is required.

No API server is required.

No database is required.

Contents:

```
index.html
style.css
app.js
```

Deploy using Vercel:

```bash
vercel
```

or import the repository directly into Vercel from GitHub.

# Deployment on Vercel

Clone the repository:

```bash
git clone <repository>
```

Open the dashboard directory:

```bash
cd dashboard
```

Install Vercel CLI if needed:

```bash
npm install -g vercel
```

Deploy:

```bash
vercel
```

or connect the GitHub repository directly through:

```
https://vercel.com
```

No configuration is required.

No build step is required.

No environment variables are required for the simulated mode.

---

# Why Simulated Run Exists

A common question is:

> Why not execute the contracts directly?

The answer is simple.

A reviewer should be able to understand the architecture even without:

- deploying Localnet;
- deploying contracts;
- configuring wallets;
- installing the SDK;
- funding accounts.

The simulated execution trace exists purely for explanation.

It reproduces the exact message flow implemented by the contracts while
remaining completely deterministic and immediately accessible in any
browser.

The dashboard therefore complements the implementation rather than
replacing it.

---

# Security Considerations

The dashboard intentionally avoids becoming an application wallet.

Specifically, it does **not**:

- store private keys;
- sign transactions;
- submit write operations;
- proxy requests through a backend;
- expose deployment secrets.

The Live Read mode performs only view calls against deployed
Intelligent Contracts.

This mirrors the security philosophy of GenMesh Core itself:
presentation should never become part of the trust model.

---

# Relationship to GenMesh Core

The dashboard is **not** an independent project.

It is a visualization layer for the contracts implemented in the main
repository.

```
Contracts
      │
      ▼
Execution Trace
      │
      ▼
Dashboard
```

Every displayed stage corresponds directly to one implemented contract:

| Dashboard Stage | Intelligent Contract |
|-----------------|----------------------|
| Registry Lookup | AgentRegistry |
| Capability Planning | Coordinator |
| Agent Calls | SecurityAgent / ResearchAgent / FinanceAgent |
| Aggregation | Aggregator |
| Final Result | Aggregator Output |

No additional orchestration logic exists inside the frontend.

---

# Limitations

The dashboard intentionally does not attempt to replace blockchain
tooling.

Current limitations include:

- no transaction submission;
- no wallet integration;
- no explorer functionality;
- no live event streaming;
- no visualization of validator execution;
- no protocol debugging tools.

These omissions are intentional.

The objective is architectural visualization, not network management.

---

# Future Improvements

Potential future enhancements include:

### Testnet Support

Allow switching between:

- Localnet
- Studionet
- Public Testnet

without modifying the frontend.

---

### Transaction Explorer

Clickable execution graph:

```
Coordinator
      │
      ▼
Transaction
      │
      ▼
Block Explorer
```

showing the corresponding on-chain transactions.

---

### Live Execution Timeline

Instead of replaying a predefined trace, the dashboard could subscribe
to emitted events and visualize execution in real time.

---

### Agent Metrics

Display additional runtime information:

- execution duration;
- finalized block;
- validator agreement;
- Equivalence Principle usage;
- deterministic vs non-deterministic execution ratio.

---

### Capability Graph

Visualize Registry as a dynamic graph:

```
Coordinator

      │

 ┌────┼──────────────┐
 ▼    ▼              ▼

Security   Finance   Research
```

allowing users to understand how capabilities evolve as new Agents
register themselves.

---

# FAQ

### Does the dashboard execute contracts?

No.

Only the Live Read mode communicates with deployed contracts, and even
then only through read-only view calls.

---

### Does it require a backend?

No.

Everything is served as static files.

---

### Does it require a database?

No.

All execution data either comes from:

- simulated trace data; or
- deployed Intelligent Contracts.

---

### Why not use React?

The dashboard intentionally avoids frameworks.

The objective is maximum portability, zero build configuration and
simple deployment.

A reviewer should be able to inspect the entire frontend in minutes.

---

### Can it become a production interface?

Yes.

Nothing in the architecture prevents adding:

- wallet integration;
- transaction submission;
- explorer integration;
- authentication.

Those concerns are intentionally outside the scope of this MVP.

---

# Design Philosophy

The dashboard follows the same philosophy as the contracts themselves.

Keep every component focused on a single responsibility.

Contracts execute.

Optimistic Democracy validates.

The dashboard explains.

It does not become another execution layer.

---

# License

MIT License.

---

# Conclusion

The dashboard is intentionally minimal.

Its purpose is not to impress through frontend complexity.

Its purpose is to make the execution model of GenMesh Core immediately
understandable.

By visualizing every step—

```
User
    ↓
Coordinator
    ↓
Registry
    ↓
Agents
    ↓
Aggregator
    ↓
Optimistic Democracy
    ↓
Final Result
```

—it demonstrates that GenMesh Core is not a traditional AI-agent
framework running on a blockchain, but a composable execution pattern
built entirely from native GenLayer Intelligent Contracts.

Together, the contracts and the dashboard provide both halves of the
project:

- the implementation of the execution model;
- the visualization of how that execution model behaves end-to-end.

The Hobby plan is sufficient.
