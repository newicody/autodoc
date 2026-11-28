# 0088 — Code rule alignment — ControlProxy Scheduler handler

`doc/code-rules/code_rule.md` is the authority for this patch. The automated
rule tests only guard the most important invariants; they do not replace the
rule text.

## Decision

0088 adds the smallest concrete runtime path that is still operational: a
Dispatcher handler receives an already-authorized Scheduler event payload and
calls the existing 0086 `handle_scheduler_route_request()` adapter.

The handler is intentionally not a policy engine, not a route materializer, not
a daemon, not a CLI, and not a Scheduler-loop modification.

## code_rule review block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0088 adds a concrete Dispatcher handler that calls the existing 0086 ControlProxy Scheduler adapter without changing the kernel loop or moving policy authority into ControlProxy.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

## Manual rule checklist

```text
no_unnecessary_cli: true
no_daemon_service_openrc: true
no_resident_watcher: true
scheduler_loop_unchanged: true
priority_queue_unchanged: true
dispatcher_unchanged: true
component_tick_contract_unchanged: true
controlproxy_policy_decision_added: false
policy_zone_scope_bypass_added: false
docs_match_runtime_scope: true
abstraction_added_only_for_import_boundary: true
```

## Runtime path

```text
Scheduler-authorized Event payload
-> Dispatcher
-> ControlProxySchedulerRouteRequestHandler.handle()
-> handle_scheduler_route_request()
-> existing 0086 Scheduler-facing ControlProxy adapter
-> adapter reply
-> Dispatcher resolves Request.reply
```

## Notes

The handler exposes dependency injection for tests and a resolver for the 0086
adapter function. This keeps the 0088 boundary importable without forcing a
Scheduler-loop change or a premature service/CLI wrapper.
