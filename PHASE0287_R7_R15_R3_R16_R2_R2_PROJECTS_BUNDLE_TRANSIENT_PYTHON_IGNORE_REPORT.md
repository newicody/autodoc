# Phase 0287-r7-r15-r3-r16-r2-r2 — Projects bundle transient Python ignore

## Observation réelle

The first live drift audit correctly found the six r16-r2/r1 files still to
copy into `newicody/projects`. It also classified four generated Python bytecode
files as unknown extras:

```text
scripts/__pycache__/*.pyc
```

Those files are operational noise created by running the bundle scripts and do
not represent repository ownership drift.

## Correction

The local audit now recognizes only these Python transients:

```text
directory name: __pycache__
file suffixes: .pyc, .pyo
```

They are removed from `unknown_extra_files` and exposed transparently in
`ignored_transient_files`.

Transient evidence does not make `review_required` true and does not prevent
`managed_exact` from becoming true.

All other additional files, including arbitrary files inside `scripts`, remain
in `unknown_extra_files` and still require operator review.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: exercised with local newicody/projects checkout
external_dependencies_added: false
network_added: false
mutation_added: false
ignore_scope_bounded: true
```
