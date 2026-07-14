# Phase 0284-r1-r4 — Projects bundle Copilot visibility and views

## Result

```text
status: green
live_path_status: n/a
live_path_uses_real_backend: n/a
projects_repository_bundle_changed: true
autodoc_project_mode_created: false
workflow_permissions_changed: false
workflow_self_authorized_publication: false
existing_0281_issue_publication_reused: true
projectv2_projection_operator_gated: true
```

## Delivered boundary

The source bundle copied to `newicody/projects` now contains:

- one versioned fields/views configuration for user ProjectV2 number 3;
- one non-destructive field/view reconciler;
- one operator-gated projection of an approved 0281 publication preview into
  Copilot-only ProjectV2 fields;
- cumulative installation instructions.

The GitHub Actions producer remains read-only for Issues and cannot call either
publication adapter. The complete comment continues to use the existing local
0281 adapter. The copied projection writes only the latest consultative card
state and cannot write `Résumé` or `Serveur`.

## Views

```text
Recherches
Résultats
Copilot
Connaissances serveur
Boîtes de thèmes
Historique
Tous
```

Detailed column/group settings remain explicit manual installation steps when
not accepted by the public view-creation endpoint.

## Safety

- plan-only is the default;
- execution requires two independent environment gates;
- execution requires the exact previewed `plan_digest`;
- configuration reconciliation creates only missing fields/views;
- existing fields/views are never deleted or overwritten;
- advisory content remains non-authoritative;
- no Scheduler, EventBus, SQL, OpenVINO or Qdrant code is modified.
