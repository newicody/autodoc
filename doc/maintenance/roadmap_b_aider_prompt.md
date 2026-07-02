
You are Aider operating inside the Autodoc/MissiPy git repository.

You must create a patch bundle only. Do not apply the patch to source files
outside the patch bundle.

Create exactly this directory:

patch/0039-part8_roadmap_b_part8_1_local_data_contract/
  README.md
  metadata.json
  patch.diff

Roadmap is locked to Roadmap B:
- build a robust local-first foundation before real external integration
- local server/repo remains source of truth
- GitHub/external surfaces are synchronization/review surfaces only
- no remote mutation by default
- no Scheduler path unless explicitly approved

Patch rules:
- use the existing patch queue contract
- patch.diff must be applicable by apply_patch_queue.py
- keep increments small
- add tests and docs for the new behavior
- keep Markdown under existing doc/ subdirectories
- do not version generated context SVG files
- if adding DOT, do not reference code_rule inside DOT labels or nodes
- no network code
- no token/authorization handling
- no dependency additions unless explicitly justified
- no significant rules changes unless explicitly justified
- no broad retroactive refactor unless explicitly justified

Current step:
id: part8_1_local_data_contract
title: Local data contract
goal: Define stable local data directories, manifests, generated artifacts policy and source-of-truth rules.
risk: low



Conversation/project context:

# README.md
# Autodoc / MissiPy

Autodoc / MissiPy is a local-first engineering workspace for turning files, notes, artifacts and operator decisions into explicit, auditable context.

The project is built around a simple rule:

```text
the local machine is the source of truth;
external services are workflow surfaces, not the authority.
```

## Why this exists

The goal is to build a small but strict context engine that can ingest candidate sources, review them, decide what to do with them, audit those decisions and prepare controlled handoffs.

This is useful for workflows where a human operator wants to keep ownership of the evolving knowledge base while still using automation, local inference and future external project surfaces.

Autodoc / MissiPy is not designed as a remote-first agent. It is designed as a local, inspectable and progressively extensible system.

## Current architecture

The current SourceCandidate chain is local and auditable:

```text
SourceCandidate store
-> review
-> decision
-> decision audit
-> review audit summary
-> operator report
-> operator report file
-> operator bundle
-> operator CLI
-> projection preview
-> projection bundle
-> projection gate
-> projection gate report
-> handoff dry-run
-> closure audit
```

The local operator/projection chain is now ready to support external boundary work. The next steps are contracts and dry-runs before any remote mutation.

## Source of truth

The local/server machine remains authoritative.

GitHub, future project trackers or other external systems are treated as projection and review surfaces. They may receive derived artifacts, status or operator-facing summaries, but they do not own the evolving local context.

The intended model is:

```text
local/server = authoritative evolving source
external surfaces = review, workflow and synchronization interfaces
```

## Patch queue workflow

Development is organized as small patch queue bundles under `patch/<patch-id>/`.

A patch bundle contains:

```text
patch/<patch-id>/
  patch.diff
  README.md
  metadata.json
```

Typical usage:

```bash
python apply_patch_queue.py --patch <patch-id> --dry-run
python apply_patch_queue.py --patch <patch-id> --commit --push
```

Repository status can be inspected with:

```bash
python apply_patch_queue.py --status
```

Generated or local-only files such as SVG renders, Python bytecode and local patch queue config must not be versioned.

## Tests

Common gates:

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Specific phase tests are listed in the corresponding test report files.

## Documentation map

Important documentation lives in:

```text
doc/releases/
doc/CHANGELOG_*
doc/*_CODE_RULE_ALIGNMENT.md
MANIFEST_*_CHANGED_FILES.md
doc/docs/architecture/
```

The root README is intentionally stable. It is an entrypoint, not a phase changelog.

## AI-assisted development

This project is developed with help from several AI systems, including ChatGPT, Claude, Gemini, Perplexity and Mistral.

That is a practical choice: the project is intentionally designed to run on accessible local hardware, without requiring an expensive dedicated GPU. The current direction favors CPU/iGPU-friendly components, local artifacts, explicit contracts and controlled handoffs over blind dependence on high-end accelerator hardware.

In other words: the project uses AI assistance to design, review and verify the system, while keeping the operational architecture local-first, inspectable and hardware-conscious.

## Current boundary

The project currently avoids:

```text
remote mutation by default
network dependency in local gates
GitHub API writes
tokens committed to the repository
Qdrant dependency in SourceCandidate control paths
LLM/OpenVINO dependency in local audit gates
Scheduler changes without explicit live-path justification
```

External systems must be approached through explicit contracts, dry-runs, reports and gates.

## Roadmap orientation

Immediate direction:

```text
7.0  root README operator entrypoint
7.1  external projection contract v1
7.2  GitHub projection payload dry-run
7.3  remote mutation gate
7.4  GitHub adapter interface with fake adapter first
7.5  GitHub export bundle
7.6  operator external review report
7.7  read-only external probe
```

Actual remote mutation should come later, behind explicit gates and operator approval.

## Non-goals

Autodoc / MissiPy is not currently:

```text
a hosted SaaS
a remote-first agent
a GitHub bot with write access by default
a replacement for human operator review
a hidden background daemon
a system that stores secrets in Git
```

The project grows by small, auditable patches.


# doc/maintenance/ROADMAP_B_LOCK.md
# Roadmap B Lock

Roadmap B is the active development direction.

The goal is to build a robust local-first foundation before opening real
external integrations.

## Source of truth

```text
local repository / local server = source of truth
GitHub / external systems = review and synchronization surfaces
```

GitHub is not the source of truth.

## Priority order

```text
1. local data contract
2. local document model
3. incremental file scan
4. context bundle builder
5. retrieval evaluation set
6. operator feedback loop
7. only then: real read-only external integration
```

## Closed boundaries

```text
external service calls: closed by default
remote mutation: closed by default
Scheduler execution: closed by default
new dependencies: operator approval required
rules changes: operator approval required
large retroactive refactors: operator approval required
```

## Development method

Every automated step must produce a patch bundle:

```text
patch/<patch-id>/
  README.md
  metadata.json
  patch.diff
```

The patch is then applied through:

```bash
python apply_patch_queue.py --patch <patch-id> --dry-run
python apply_patch_queue.py --patch <patch-id> --commit --push
```

Tests run after each applied step.


# doc/maintenance/PHASE7_FREEZE_HANDOFF_CONTRACT.md
# Phase 7 Freeze + Handoff Contract

Phase 7.20 freezes the completed Part 7 local boundary.

The handoff contract records:

```text
local source of truth
no external service calls allowed
no remote mutation allowed
no Scheduler execution allowed
documentation SVG policy required
operator confirmation required
```

## Build without closure report

```bash
python tools/source_candidate_phase7_handoff_contract_cli.py \
  --output doc/maintenance/source_candidate_phase7_handoff_contract.json
```

## Build from closure report

```bash
python tools/source_candidate_phase7_handoff_contract_cli.py \
  --closure-report doc/maintenance/source_candidate_phase7_closure_report.json \
  --output doc/maintenance/source_candidate_phase7_handoff_contract.json
```

## Part 8 candidates

```text
github_read_only_import_prototype
local_document_context_ingestion
retrieval_evaluation_set
operator_feedback_loop
```

The contract does not open any capability by itself. It only records what is
still closed at the end of Part 7.


# doc/maintenance/PHASE7_CLOSURE_REPORT.md
# Phase 7 Closure Report

Phase 7 closes the local SourceCandidate external-probe preparation path.

The phase stays local-first:

```text
no external service call
no token handling
no remote mutation
no Scheduler execution
```

## Closure command

```bash
python tools/source_candidate_phase7_closure_report_cli.py \
  --root . \
  --output doc/maintenance/source_candidate_phase7_closure_report.json \
  --strict
```

## What Phase 7 delivered

```text
external projection contract
GitHub-shaped dry-run payload
remote mutation gate
fake-only GitHub adapter boundary
local GitHub export bundle
operator review report
read-only external probe
external probe bundle
bundle CLI
SVG build policy
runbook
artifact index
operator summary
local audit trail
local replay
```

## Next

Phase 8 may open one of these directions:

```text
real read-only GitHub integration
GitHub Project orchestrator contract
Scheduler-facing ingestion queue
Copilot/artifact synchronization bridge
```


Repository snapshot:

## git log --oneline -12
c9965b1 part8-0-roadmap-b-aider-orchestrator
47c1f9a archive patch bundle 0038
8100ab6 automat
55efed1 archive phase7 patch bundles and closure artifacts
91585e2 phase7-20-freeze-handoff-contract
64bc95a phase7-19-part7-closure-report
b6c9dd3 phase7-18-external-probe-local-replay
47ea737 phase7-17-external-probe-local-audit-trail
21bcda1 phase7-16-external-probe-operator-summary
b06ce5a phase7-15-external-probe-artifact-index
9ea2dbd phase7-14-external-probe-bundle-runbook
67e5487 phase7-13-documentation-svg-build-policy-apply


## git status --short


## find src tests tools doc -maxdepth 3 -type f
src/context/source_candidate_operator_report_cli.py
src/context/e5_context_engine_status.py
src/context/source_candidate_review_audit.py
src/context/source_candidate_operator_report_file_cli.py
src/context/source_candidate_read_only_external_probe.py
src/context/source_candidate_projection_bundle.py
src/context/source_candidate_review.py
src/context/source_candidate_github_export_bundle.py
src/context/source_candidate_review_cli.py
src/context/source_candidate_external_probe_local_replay.py
src/context/source_candidate_projection_handoff_dry_run.py
src/context/source_candidate_store.py
src/context/source_candidate_external_probe_bundle.py
src/context/source_candidate_review_audit_cli.py
src/context/e5_local_context_runtime.py
src/context/source_candidate_phase7_closure_report.py
src/context/source_candidate_operator_bundle.py
src/context/e5_context_engine_cli.py
src/context/source_candidate_decision.py
src/context/source_candidate_remote_mutation_gate.py
src/context/source_candidate_operator_report.py
src/context/builder.py
src/context/source_candidate_github_projection_payload.py
src/context/source_candidate_decision_cli.py
src/context/collector.py
src/context/__init__.py
src/context/source_candidate_projection_gate_report.py
src/context/handlers.py
src/context/source_candidate_github_adapter.py
src/context/source_candidate_external_probe_artifact_index.py
src/context/e5_context_attachment.py
src/context/source_candidate_phase7_handoff_contract.py
src/context/source_candidate_operator_report_file.py
src/context/source_candidate_external_probe_local_audit_trail.py
src/context/e5_artifact_cli.py
src/context/source_candidate_external_projection_contract.py
src/context/e5_runtime_bridge.py
src/context/source_candidate.py
src/context/source_candidate_external_probe_operator_summary.py
src/context/source_candidate_handlers.py
src/context/engine.py
src/context/source_candidate_operator_bundle_cli.py
src/context/source_candidate_operator_external_review_report.py
src/context/e5_artifact_loader.py
src/context/source_candidate_decision_handlers.py
src/context/source_candidate_intake.py
src/context/source_candidate_phase6_closure_audit.py
src/context/__pycache__/handlers.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_external_review_report.cpython-314.pyc
src/context/__pycache__/source_candidate_read_only_external_probe.cpython-314.pyc
src/context/__pycache__/builder.cpython-314.pyc
src/context/__pycache__/__init__.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_report_file_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_review.cpython-314.pyc
src/context/__pycache__/local_context_loop_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_phase7_closure_report.cpython-314.pyc
src/context/__pycache__/source_candidate_intake_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_external_probe_operator_summary.cpython-314.pyc
src/context/__pycache__/local_server_boundary.cpython-314.pyc
src/context/__pycache__/e5_context_engine_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_github_export_bundle.cpython-314.pyc
src/context/__pycache__/source_candidate_review_audit.cpython-314.pyc
src/context/__pycache__/source_candidate_handlers.cpython-314.pyc
src/context/__pycache__/reducer.cpython-314.pyc
src/context/__pycache__/source_candidate_decision.cpython-314.pyc
src/context/__pycache__/e5_artifact_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_github_adapter.cpython-314.pyc
src/context/__pycache__/source_candidate_github_projection_payload.cpython-314.pyc
src/context/__pycache__/source_candidate_phase7_handoff_contract.cpython-314.pyc
src/context/__pycache__/source_candidate_store.cpython-314.pyc
src/context/__pycache__/source_candidate.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_report_cli.cpython-314.pyc
src/context/__pycache__/e5_runtime_bridge.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_bundle.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_bundle_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_review_cli.cpython-314.pyc
src/context/__pycache__/e5_local_context_runtime.cpython-314.pyc
src/context/__pycache__/source_candidate_intake.cpython-314.pyc
src/context/__pycache__/source_candidate_projection_gate.cpython-314.pyc
src/context/__pycache__/source_candidate_external_probe_local_replay.cpython-314.pyc
src/context/__pycache__/e5_context_engine_status.cpython-314.pyc
src/context/__pycache__/source_candidate_projection_handoff_dry_run.cpython-314.pyc
src/context/__pycache__/source_candidate_remote_mutation_gate.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_report.cpython-314.pyc
src/context/__pycache__/source_candidate_external_probe_local_audit_trail.cpython-314.pyc
src/context/__pycache__/source_candidate_decision_cli.cpython-314.pyc
src/context/__pycache__/engine.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_external_projection_contract.cpython-314.pyc
src/context/__pycache__/source_candidate_review_audit_cli.cpython-314.pyc
src/context/__pycache__/source_candidate_external_probe_bundle.cpython-314.pyc
src/context/__pycache__/source_candidate_operator_report_file.cpython-314.pyc
src/context/__pycache__/e5_context_attachment.cpython-314.pyc
src/context/__pycache__/source_candidate_decision_handlers.cpython-314.pyc
src/context/__pycache__/source_candidate_projection_bundle.cpython-314.pyc
src/context/__pycache__/source_candidate_projection_gate_report.cpython-314.pyc
src/context/__pycache__/collector.cpython-314.pyc
src/context/__pycache__/source_candidate_phase6_closure_audit.cpython-314.pyc
src/context/__pycache__/source_candidate_projection_preview.cpython-314.pyc
src/context/__pycache__/e5_artifact_loader.cpython-314.pyc
src/context/__pycache__/source_candidate_external_probe_artifact_index.cpython-314.pyc
src/context/source_candidate_projection_gate.py
src/context/local_server_boundary.py
src/context/reducer.py
src/context/local_context_loop_cli.py
src/context/source_candidate_projection_preview.py
src/context/source_candidate_operator_cli.py
src/context/source_candidate_intake_cli.py
src/policy/engine.py
src/policy/__init__.py
src/policy/__pycache__/__init__.cpython-314.pyc
src/policy/__pycache__/engine.cpython-314.pyc
src/experts/__init__.py
src/experts/dummy.py
src/experts/__pycache__/dummy.cpython-314.pyc
src/experts/__pycache__/__init__.cpython-314.pyc
src/main.py
src/__pycache__/main.cpython-314.pyc
src/inference/embedding_pipeline.py
src/inference/e5_cli.py
src/inference/e5_context_bundle.py
src/inference/e5_corpus_inspect_cli.py
src/inference/e5_corpus_cli.py
src/inference/e5_corpus.py
src/inference/e5_corpus_lock.py
src/inference/e5_context_consumer.py
src/inference/simple_tokenizer.py
src/inference/transformers_tokenizer.py
src/inference/e5_corpus_inspect.py
src/inference/e5_ranker.py
src/inference/e5_tool_cli.py
src/inference/e5_search_report.py
src/inference/e5_pipeline.py
src/inference/__pycache__/tokenizer_contract.cpython-314.pyc
src/inference/__pycache__/adapter.cpython-314.pyc
src/inference/__pycache__/embedding_raw.cpython-314.pyc
src/inference/__pycache__/model_profile.cpython-314.pyc
src/inference/__pycache__/report_io.cpython-314.pyc
src/inference/__pycache__/e5_rank_cli.cpython-314.pyc
src/inference/__pycache__/openvino_runtime.cpython-314.pyc
src/inference/__pycache__/embedding_pipeline.cpython-314.pyc
src/inference/__pycache__/e5_context_bundle.cpython-314.pyc
src/inference/__pycache__/backend.cpython-314.pyc
src/inference/__pycache__/openvino_backend.cpython-314.pyc
src/inference/__pycache__/e5_rebuild_cli.cpython-314.pyc
src/inference/__pycache__/e5_corpus_lock.cpython-314.pyc
src/inference/__pycache__/e5_sources.cpython-314.pyc
src/inference/__pycache__/embedding_profile.cpython-314.pyc
src/inference/__pycache__/e5_tool_cli.cpython-314.pyc
src/inference/__pycache__/e5_context_consumer.cpython-314.pyc
src/inference/__pycache__/e5_profile.cpython-314.pyc
src/inference/__pycache__/e5_corpus_cli.cpython-314.pyc
src/inference/__pycache__/e5_search_validation.cpython-314.pyc
src/inference/__pycache__/simple_tokenizer.cpython-314.pyc
src/inference/__pycache__/transformers_tokenizer.cpython-314.pyc
src/inference/__pycache__/e5_answer_prompt.cpython-314.pyc
src/inference/__pycache__/e5_ranker.cpython-314.pyc
src/inference/__pycache__/e5_search_report.cpython-314.pyc
src/inference/__pycache__/e5_text.cpython-314.pyc
src/inference/__pycache__/e5_corpus.cpython-314.pyc
src/inference/__pycache__/e5_corpus_inspect.cpython-314.pyc
src/inference/__pycache__/e5_incremental.cpython-314.pyc
src/inference/__pycache__/handlers.cpython-314.pyc
src/inference/__pycache__/e5_corpus_inspect_cli.cpython-314.pyc
src/inference/__pycache__/e5_cli.cpython-314.pyc
src/inference/__pycache__/openvino_factory.cpython-314.pyc
src/inference/__pycache__/__init__.cpython-314.pyc
src/inference/__pycache__/registry.cpython-314.pyc
src/inference/__pycache__/e5_cli_contracts.cpython-314.pyc
src/inference/__pycache__/e5_pipeline.cpython-314.pyc
src/inference/e5_text.py
src/inference/e5_cli_contracts.py
src/inference/embedding_raw.py
src/inference/tokenizer_contract.py
src/inference/openvino_runtime.py
src/inference/report_io.py
src/inference/e5_profile.py
src/inference/registry.py
src/inference/backend.py
src/inference/model_profile.py
src/inference/e5_rebuild_cli.py
src/inference/e5_incremental.py
src/inference/e5_search_validation.py
src/inference/adapter.py
src/inference/e5_sources.py
src/inference/openvino_factory.py
src/inference/e5_rank_cli.py
src/inference/__init__.py
src/inference/openvino_backend.py
src/inference/handlers.py
src/inference/e5_answer_prompt.py
src/inference/embedding_profile.py
src/observability/__pycache__/recorder.cpython-314.pyc
src/observability/__pycache__/replay_bundle.cpython-314.pyc
src/observability/__pycache__/replay_reader.cpython-314.pyc
src/observability/__pycache__/replay_scenario.cpython-314.pyc
src/observability/__pycache__/replay_writer.cpython-314.pyc
src/observability/__pycache__/replay_exporter.cpython-314.pyc
src/observability/__pycache__/__init__.cpython-314.pyc
src/observability/__pycache__/replay_sandbox.cpython-314.pyc
src/observability/__pycache__/telemetry.cpython-314.pyc
src/observability/replay_bundle.py
src/observability/replay_sandbox.py
src/observability/replay_exporter.py
src/observability/replay_writer.py
src/observability/__init__.py
src/observability/recorder.py
src/observability/replay_scenario.py
src/observability/telemetry.py
src/observability/replay_reader.py
src/kernel/queue.py
src/kernel/__init__.py
src/kernel/lifecycle.py
src/kernel/event_bus.py
src/kernel/dispatcher.py
src/kernel/scheduler.py
src/kernel/registry.py
src/kernel/context_engine.py
src/kernel/__pycache__/lifecycle.cpython-314.pyc
src/kernel/__pycache__/launcher.cpython-314.pyc
src/kernel/__pycache__/scheduler.cpython-314.pyc
src/kernel/__pycache__/event_bus.cpython-314.pyc
src/kernel/__pycache__/dispatcher.cpython-314.pyc
src/kernel/__pycache__/registry.cpython-314.pyc
src/kernel/__pycache__/__init__.cpython-314.pyc
src/kernel/__pycache__/queue.cpython-314.pyc
src/kernel/__pycache__/priority.cpython-314.pyc
src/kernel/__pycache__/context_engine.cpython-314.pyc
src/kernel/launcher.py
src/kernel/priority.py
src/runtime/loader.py
src/runtime/__init__.py
src/runtime/component.py
src/runtime/__pycache__/component.cpython-314.pyc
src/runtime/__pycache__/loader.cpython-314.pyc
src/runtime/__pycache__/__init__.cpython-314.pyc
src/contracts/__init__.py
src/contracts/context.py
src/contracts/lifecycle.py
src/contracts/replay.py
src/contracts/scheduler.py
src/contracts/event.py
src/contracts/policy.py
src/contracts/telemetry.py
src/contracts/inference.py
src/contracts/__pycache__/__init__.cpython-314.pyc
src/contracts/__pycache__/replay.cpython-314.pyc
src/contracts/__pycache__/event.cpython-314.pyc
src/contracts/__pycache__/telemetry.cpython-314.pyc
src/contracts/__pycache__/inference.cpython-314.pyc
src/contracts/__pycache__/scheduler.cpython-314.pyc
src/contracts/__pycache__/lifecycle.cpython-314.pyc
src/contracts/__pycache__/policy.cpython-314.pyc
src/contracts/__pycache__/context.cpython-314.pyc
src/contracts/__pycache__/component.cpython-314.pyc
src/contracts/component.py
src/contracts/telemetry.py.old
tests/rules/test_source_candidate_github_export_bundle_rule.py
tests/rules/test_dot_code_rule_cleanup_rule.py
tests/rules/test_source_candidate_phase6_closure_audit_rule.py
tests/rules/test_source_candidate_external_probe_artifact_index_rule.py
tests/rules/__pycache__/test_source_candidate_external_probe_operator_summary_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_bundle_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_review_audit_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_local_audit_trail_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_projection_contract_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_cli_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_operator_external_review_report_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_markdown_doc_layout_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_e5_code_rule_alignment.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_read_only_external_probe_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_patch_queue_status_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_review_live_path_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_cli_help_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_github_adapter_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_docs_svg_build_policy_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_docs_svg_build_policy_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_decision_live_path_rule.cpython-314.pyc
tests/rules/__pycache__/test_generated_artifacts_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_report_file_rule.cpython-314.pyc
tests/rules/__pycache__/test_code_rule_compliance.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_report_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_phase7_closure_report_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_projection_handoff_dry_run_rule.cpython-314.pyc
tests/rules/__pycache__/test_markdown_doc_layout_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_review_live_path_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_local_replay_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_phase6_closure_audit_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_projection_gate_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_runbook_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_projection_contract_rule.cpython-314.pyc
tests/rules/__pycache__/test_generated_artifacts_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_phase6_closure_audit_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_github_projection_payload_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_operator_cli_help_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_remote_mutation_gate_rule.cpython-314.pyc
tests/rules/__pycache__/test_dot_code_rule_cleanup_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_github_projection_payload_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_markdown_doc_migration_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_projection_bundle_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_remote_mutation_gate_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_operator_report_file_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_artifact_index_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_cli_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_read_only_external_probe_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_operator_cli_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_projection_handoff_dry_run_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_cli_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_github_adapter_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_operator_bundle_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_phase7_handoff_contract_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_projection_gate_report_rule.cpython-314.pyc
tests/rules/__pycache__/test_roadmap_b_aider_orchestrator_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_local_audit_trail_rule.cpython-314.pyc
tests/rules/__pycache__/test_e5_code_rule_alignment.cpython-314.pyc
tests/rules/__pycache__/test_patch_queue_status_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_projection_gate_rule.cpython-314.pyc
tests/rules/__pycache__/test_dot_code_rule_cleanup_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_review_audit_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_decision_live_path_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_artifact_index_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_projection_bundle_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_code_rule_compliance.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_projection_gate_report_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_phase7_closure_report_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_operator_summary_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_decision_audit_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_operator_report_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_phase7_handoff_contract_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_projection_preview_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_github_export_bundle_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_root_readme_operator_entrypoint_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_decision_audit_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_projection_preview_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_github_export_bundle_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_local_replay_rule.cpython-314.pyc
tests/rules/__pycache__/test_roadmap_b_aider_orchestrator_rule.cpython-314.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_runbook_rule.cpython-314.pyc
tests/rules/__pycache__/test_root_readme_operator_entrypoint_rule.cpython-314-pytest-9.1.1.pyc
tests/rules/__pycache__/test_source_candidate_external_probe_bundle_rule.cpython-314.pyc
tests/rules/__pycache__
