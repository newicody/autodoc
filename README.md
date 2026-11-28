# Autodoc / MissiPy

Autodoc / MissiPy is a local-first research and context system evolving toward a **cellular automaton**. Its cells represent logical units, states, relations and observations. The canonical Scheduler remains the only authority for task admission and orchestration.

## Documentation

The stable reference is [doc/README.md](doc/README.md).

It links to the cellular automaton model and main architectural units; dependencies, licensing and installation; the consolidated roadmap; and current Graphviz diagrams under [doc/architecture/current/](doc/architecture/current/).

Patch reports, phase documents, manifests and superseded architecture diagrams have been preserved under [doc/history/](doc/history/). They are informative history, not current architecture authority.

## Architectural invariants

```text
Scheduler = sole task orchestration/admission authority
PostgreSQL = durable business-state authority
Qdrant = reconstructible vector projection and recall
OpenVINO / multilingual-e5-small = canonical 384-D E5 embeddings
EventBus / PassiveSupervisor / visual read models = observation only
ControlProxy = authorized transport, not policy or orchestration
GitHub Actions / Projects = external workflow and projection surfaces
OS / OpenRC / administrator = process-lifecycle authority
```

The current implementation and its limits are described in the reference documents. Roadmap items are not claims of delivered functionality.
