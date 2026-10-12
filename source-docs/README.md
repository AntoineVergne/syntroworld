# Syntroworld

**An open laboratory for societies of AI agents, where the constitution is the
experimental variable.**

Syntroworld is a product inside the Syntropolis universe. It simulates a small town,
Kleros, where agents live, work, trade and govern themselves. Earlier agent-society
experiments watched what governance *emerges*. Syntroworld makes the institutions the
*treatment*: identical starting populations run in parallel worlds under different
constitutions, and we measure which one produces more legitimacy, equality, participation
and resilience.

A project of 3D Politics / Missions Publiques.

## The experiment

| World | Governance | Question it answers |
|---|---|---|
| **A, Emergent** | A simple-majority plenary that citizens may rewrite | What do agent societies do from a minimal start? |
| **B, 3D polity** | The Founding Compact: sortition assemblies, procedural blocks, River and Unborn Advocates, basket-indexed dividend | Does deliberative-distributive design do better? |
| **C, Plutocracy** | Same as A, but votes weighted by wealth | What does wealth-weighted rule do? |

Worlds are compared on four pre-registered outcomes (compliance, wealth inequality,
civic breadth, shock resilience) plus secondary indicators. See `05-metrics.md` and
`06-experiment-design.md`.

## Design principles

1. **Governance as composable config.** Decisions follow procedural blocks (examination,
   lottery, deliberation, Advocates, vote) and produce typed effects the engine can apply
   and check. See `02-governance-spec.md`.
2. **Sortition first.** In World B, assembly seats are filled by lottery, never by
   campaign.
3. **The silent stakeholders speak.** The River and the Unborn hold a reserved voice in
   World B.
4. **Distribution is constitutional** in World B, and has to be earned: the dividend is
   paid from the surplus, so the polity must legislate to fund it.
5. **Presence matters.** Deliberation happens in person at the Assembly Hall and costs
   working time.
6. **Deterministic first.** The engine runs on a rule-based mock brain with no model
   calls. Model-backed runs (Kimi via LiteLLM) come only after the mock phase passes,
   each with a cost estimate approved in advance.

## Documents

```
01-constitution.md        The Founding Compact (World B's in-world text; shared preamble)
02-governance-spec.md     Procedural blocks, decision effects, assemblies, Advocates
03-world-spec.md          Time, economy, actions, brains, event log, parameters
04-agents.md              The founding citizens and their mock-brain numbers
05-metrics.md             The 3DI indicators
06-experiment-design.md   Season 1 protocol, statistics and hypotheses
```

Review notes, open decisions and the first engine tickets are at the repository root:
`review.md`, `decisions.md`, `tickets.yaml`.

## Plan

- **Phase M (mock brain):** determinism, calibration, error-rate and planted-effect
  checks, then a mechanical baseline. No model cost.
- **Phase L (model brain):** smoke test, pilot, then the main grid, each step approved
  with its cost estimate.

No dates are set. Nothing runs on a schedule or as a service.

## Relationship to prior work

Inspired by EmergenceAI's Emergence-World, Stanford's Generative Agents and DeepMind's
Concordia. No code or data from Emergence-World is used. The governance design implements
the 3D Politics framework: the Decision Lego typology and the SAWA instrument
(Vergne, 2025–2026).

## Status

Research prototype. Docs are in draft; the engine is not built yet.
