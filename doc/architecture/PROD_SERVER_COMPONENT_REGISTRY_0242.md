# Production server component registry - 0242

## Intent

This patch builds a declarative component registry from the validated production
server INI file.

It answers:

```text
which components exist
which factory reference each component declares
which phase owns the component
which dependency order should be used later
which components are command path vs observation path
```

No component factory is imported or called in this phase.

## Factory reference shape

Factories are stored as strings using:

```text
module:function
```

Example:

```text
autodoc.scheduler:create_scheduler
```

This is only a reference. The registry does not import the module and does not
call the function.

## Ordering

The registry computes dependency order for enabled components. Current initial
order from the example server INI is:

```text
eventbus
scheduler
passive_supervisor_sink
sql_context_store
github_artifact_exchange
qdrant_projection
```

The order remains data only until 0243.

## No __init__ side effects

No __init__ side effects are allowed here. This phase cannot start threads,
create Scheduler/EventBus instances, call GitHub, write PostgreSQL, write Qdrant,
or publish EventBus events.

## Boundary

0242 is registry-only. 0243 may use this registry to prepare bootstrap logic, but
0242 remains read-only and declarative.
