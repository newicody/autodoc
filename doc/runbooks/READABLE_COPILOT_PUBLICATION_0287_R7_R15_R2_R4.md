# Readable Copilot publication runbook

Preview:

```bash
python tools/publish_readable_copilot_advisory_v2_0287.py \
  --preview /tmp/copilot_advisory_publication_preview_v2.json \
  --artifact-identity /tmp/artifact_identity.json \
  --config /home/eric/projet/git/projects/projectv2_views.json \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --policy-decision-id "policy:copilot-readable:$RUN_ID" \
  --operator-decision approve \
  --updated-date "$(date -I)" \
  --format json | tee /tmp/readable-copilot-preview.json
```

Execution after review:

```bash
PLAN_DIGEST="$(jq -r '.combined_plan.plan_digest' /tmp/readable-copilot-preview.json)"
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python tools/publish_readable_copilot_advisory_v2_0287.py \
  --preview /tmp/copilot_advisory_publication_preview_v2.json \
  --artifact-identity /tmp/artifact_identity.json \
  --config /home/eric/projet/git/projects/projectv2_views.json \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --policy-decision-id "policy:copilot-readable:$RUN_ID" \
  --operator-decision approve \
  --updated-date "$(date -I)" \
  --execute \
  --confirm-plan-digest "$PLAN_DIGEST" \
  --format json
```

A second identical run must report replay on both surfaces and perform no new mutation.
