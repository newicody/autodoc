# Imported Actions run preview — 0287-r7-r15-r2

## Flow

```text
GitHub Actions run
  ├── authoritative request artifact
  ├── Copilot advisory artifact
  └── correlation manifest artifact
          │ read-only gh download
          ▼
GitHubDualArtifactRunMember tuple
          │ pure dual-artifact correlation preflight
          │ explicit promote/merge operator decision
          ├─────────────── explicit module:function factory
          │                  ├── existing Scheduler
          │                  ├── SQL authority + base revision
          │                  ├── real OpenVINO/E5-384 projection
          │                  ├── real Qdrant write/search
          │                  └── immutable backend attestation
          ▼
r14 full composition
          │ verify two projection receipts against attestation
          ├── proof_digest
          └── r13 publication plan + plan_digest
          │
          ▼
r15-r1 remote publication preview
          │ Issue + ProjectV2 reads only
          ▼
love-r14-result-<RUN_ID>.json
```

## Output compatibility

The generated file preserves `publication_plan` at the r14 top level. It can be
passed directly to:

```bash
python tools/publish_love_final_deliverable_0287.py --plan <file> ...
```

Imported-run metadata and runtime attestation live under `_r15_import`; preview
data lives under `remote_publication_preview`.

## No fake live proof

r12 requires real E5 projection proof. Therefore r15-r2 has no deterministic
fallback. The tool requires one configured real factory reference. Since
0287-r7-r15-r2-r1 it is loaded by default from
`.var/config/love_actions_closed_loop.ini`; `--runtime-factory` remains an
advanced override.

The returned `ImportedActionsRuntimePorts` must attest and expose real ports.
The tool also inspects the r14 result and confirms two normalized 384-dimensional
projection receipts in the attested Qdrant collection.

## Authority boundaries

- Actions adapter: read/download only;
- Scheduler: existing injected authority, unmodified; `tool-bounded` starts and
  stops a dedicated canonical loop, while `externally-managed` never touches the
  lifecycle of a server-owned loop;
- laboratory/specialists: existing r14 path;
- SQL: injected durable authority;
- OpenVINO/E5 and Qdrant: injected real ports, never constructed by the CLI;
- Issue/ProjectV2: remote reads for preview only;
- mutation: absent.

## Operator flow

1. configure the real runtime factory once;
2. explicitly choose `--candidate-decision promote` or `merge`;
3. run r15-r2 and inspect the generated JSON plus backend evidence;
4. rerun the publication command in preview when desired;
5. inspect body, destination, actions and `plan_digest`;
6. only then enable locks and use `--execute --confirm-plan-digest`.
