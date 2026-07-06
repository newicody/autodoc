# Code rule — 0154 architecture current-state refresh

0154 adds current-state documentation and summary DOT graphs only.

Rules:

- keep historical phase docs; do not delete them as part of current-state refresh.
- preserve the existing documentation hierarchy.
- SQL remains the durable authority.
- Qdrant remains projection and recall metadata.
- OpenVINO/E5 remains vector generation behind the existing embedding path.
- RouteProxy remains fast frame IO.
- Scheduler remains the orchestrating boundary and must not import vector or inference backends.
- do not introduce parallel worker/orchestrator/adapter surfaces in documentation refresh patches.
- broad documentation rewrites should be driven by the 0153 audit report.
