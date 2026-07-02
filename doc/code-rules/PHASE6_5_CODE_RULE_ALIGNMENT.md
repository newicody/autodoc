# Phase 6.5 Code Rule Alignment

Phase 6.5 adds a durable SourceCandidate operation. It therefore uses the live
kernel path rather than a direct CLI-only shortcut.

```text
SourceCandidateDecisionCommand
-> EventType.SOURCE_CANDIDATE_DECISION
-> Scheduler.emit()
-> PolicyEngine.decide()
-> Queue
-> Scheduler.run()
-> Dispatcher
-> SourceCandidateDecisionHandler
-> SourceCandidateStore JSON real backend
-> SourceCandidateDecisionResult
-> EventType.SOURCE_CANDIDATE_DECISION_RESULT
-> Request.reply
```

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
