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
