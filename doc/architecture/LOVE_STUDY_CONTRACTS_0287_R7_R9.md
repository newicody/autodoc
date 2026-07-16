# Love-study contracts — 0287-r7-r9

## Contract-only composition

```text
CorrelatedResearchWorkPackage
        |
        v
missipy.love.study_request.v1
        |
        +-----------------------------+
        |                             |
        v                             v
concept-and-affect analyst     relational-dynamics analyst
(multitask descriptor)         (multitask descriptor)
        |                             ^
        v                             |
concept_affect_analysis.v1 -----------+
        |                             |
        +--------------+--------------+
                       v
             later liaison synthesis
                       v
              love.study_result.v1
```

`laboratory:love-studies-local` is declared as `autodoc_native` but remains
disabled until r10 attaches a provider through the existing Scheduler-owned
registry.

## Analysis versus synthesis

The specialist task catalogs primarily produce detailed domain analyses. A
local synthesis is allowed only through an explicit task type. Global synthesis
is not inferred from the presence of two analyses; it remains a distinct later
liaison task preserving evidence, contradictions and unresolved points.

## Architecture locks

- Scheduler remains the only orchestration authority.
- SQL remains the durable context authority.
- Qdrant remains projection and recall only.
- OpenVINO is reused and not reimplemented.
- ControlProxy remains transport-only.
- No runtime is attached in r9.
- Global synthesis remains a later liaison step.
