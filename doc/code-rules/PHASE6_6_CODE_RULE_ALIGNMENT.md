# Phase 6.6 Code Rule Alignment

Phase 6.6 adds an optional local audit artifact to the existing SourceCandidate
decision live path.

The durable path remains Scheduler-first:

```text
SourceCandidateDecisionCommand
-> EventType.SOURCE_CANDIDATE_DECISION
-> Scheduler
-> Dispatcher
-> SourceCandidateDecisionHandler
-> SourceCandidateStore JSON real backend
-> SourceCandidateDecisionResult
-> optional decision audit JSON artifact
-> EventType.SOURCE_CANDIDATE_DECISION_RESULT
```

The Scheduler is not modified. The audit writer is a local filesystem boundary
implemented with Python stdlib only.

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: green
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
