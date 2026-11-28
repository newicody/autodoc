# Manifest — 0286-r3 specialist capability-growth Projects request form contract

## Added files

- `templates/github/projects-repository/.github/ISSUE_TEMPLATE/specialist-capability-growth.yml`
- `src/context/github_specialist_capability_growth_issue_contract_0286.py`
- `tests/context/test_github_specialist_capability_growth_issue_contract_0286.py`
- `tests/rules/test_github_specialist_capability_growth_issue_contract_0286_rule.py`
- `PHASE0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT_REPORT.md`
- `doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT_0286.md`
- `doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT_0286.dot`
- `doc/CHANGELOG_0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT.md`
- `doc/manifests/MANIFEST_0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT.md`

## Modified files

- `templates/github/projects-repository/INSTALLATION.md`
- `templates/github/projects-repository/README.md`

## Runtime and authority impact

```text
projects_bundle_modified: true
projects_installation_modified: true
workflow_modified: false
scheduler_modified: false
sql_modified: false
qdrant_modified: false
openvino_modified: false
eventbus_modified: false
external_dependencies_added: false
operator decision remains local
```

The intake is pure and local. It does not mutate GitHub, approve a revision,
write durable state, dispatch the Scheduler or execute a laboratory.

## Next patch

`0286-r4-specialist-capability-growth-projectv2-fields-views`
