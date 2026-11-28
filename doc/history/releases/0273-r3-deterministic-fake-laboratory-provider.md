# 0273-r3 — Deterministic fake laboratory provider

The first laboratory provider is now active as a local deterministic tracer
bullet. It uses the existing Scheduler-owned registration type and executes one
bounded `missipy.laboratory.v1` visit behind the Handler membrane.

It is not a real backend. The provider has no network, model, persistence,
vector index, GitHub mutation, command bus or rendering ownership.

0274 will compose this provider with the durable candidate, deliberation,
synthesis, observation and publication-preview paths.
