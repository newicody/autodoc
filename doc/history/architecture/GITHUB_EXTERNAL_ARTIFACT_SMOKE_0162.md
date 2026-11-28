# 0162 — GitHub external artifact smoke

## Decision

0162 keeps the validated plumbing direction but corrects the source boundary.

The Autodoc/MissiPy development repository is infrastructure. It is not an
ingestable idea corpus. The ingestable source is an explicit external GitHub
Project/repository that produces artifacts through GitHub Action/Copilot.

Example external repository for the smoke:

```text
newicody/autodoc-ideas
```

The smoke must not ingest newicody/autodoc as an idea source.

## Flow

```text
external GitHub Project item
-> GitHub Action/Copilot artifact fixture
-> local source boundary validation
-> local publication review packet
-> future reviewed GitHub adapter
```

## Existing surfaces reused

0162 documents and reuses the already existing GitHub/external artifact
vocabulary:

| Surface | Role |
| --- | --- |
| `src/context/github_project_scenario.py` | GitHub artifact/scenario contracts |
| `src/context/server_oriented_deliberation_cycle.py` | server-side artifact exchange/deliberation vocabulary |
| `src/context/github_publication_review.py` | bounded publication review packet |
| `src/context/source_candidate_github_projection_payload.py` | local GitHub projection payload contract |
| `src/context/source_candidate_external_projection_contract.py` | external projection contract |
| `src/context/source_candidate_read_only_external_probe.py` | read-only probe vocabulary |
| `src/context/source_candidate_remote_mutation_gate.py` | remote mutation gate |
| `src/context/source_candidate_external_probe_bundle.py` | local external probe bundle |
| `src/context/vector_indexing_job_plan.py` | github-aware vector indexing plan vocabulary |
| `src/context/scheduler_deliberation_route_contract.py` | github artifact exchange scheduler route vocabulary |

## Boundary

0162 is local-only and does not perform:

- no SQL write
- no Qdrant write
- no GitHub API call
- no external network
- no Scheduler execution
- no LLM execution
- no OpenVINO execution
- no automatic publication

## Smoke command

```text
python tools/run_github_external_artifact_smoke.py . --execute --format json
```

## Expected result

```text
status: ok
external_repository: newicody/autodoc-ideas
publish_to_github: false
external_call_performed: false
publication_review_required: true
```

## Next

After 0162, the next GitHub phase should connect a read-only GitHub artifact
fetch/import surface for a configured external repository only. Publication
back to GitHub remains gated by a local publication review packet.
