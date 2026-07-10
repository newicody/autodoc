# Rule 0271-r6 — SQL-authority final aggregation

The 0269 CLI adapter must include `sql_authority_ref` in the immutable reference
pairs loaded from valid phase reports. The 0269 core remains responsible for
requiring one non-empty matching value from phases 0262 and 0263.

This correction must not alter the Scheduler loop, Qdrant IO, SQL IO, SHM,
RouteProxy, ControlProxy, OpenRC, GitHub or external-service ownership.
