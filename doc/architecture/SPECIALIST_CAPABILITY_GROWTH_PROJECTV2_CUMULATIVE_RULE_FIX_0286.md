# ProjectV2 cumulative rule compatibility — 0286-r4-r1

## Problem

Architecture rules must protect invariants, not freeze an extensible declarative
configuration at one historical snapshot. The r4 addition was valid, but two
older rules treated every new view or the closure of an audited gap as a
regression.

## Decision

The 0284 rule now requires its seven organized views to remain a subset of the
configured views. The 0286-r1 rule accepts either the original gap or the full
atomic r4 specialist surface; partial installation remains rejected.

```text
base views preserved
        +
future additive views allowed

specialist fields absent
        OR
all nine fields + projection + review view present
```

The dedicated r4 rules continue to validate the exact new fields, options,
projection mapping and `Révisions spécialistes` view.

## Authority boundary

This correction changes tests and documentation only. Scheduler remains the
only orchestration authority, SQL remains durable authority, Qdrant remains
projection/recall, and GitHub Projects remains a non-authoritative workflow and
review surface.
