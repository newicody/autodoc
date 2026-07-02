# Markdown documentation layout

The repository keeps only the root `README.md` at the repository root.

Markdown files are routed as follows:

```text
README.md                                  -> keep at root
PHASE*_TEST_REPORT.md                      -> doc/reports/phaseN/
PHASE*_AUDIT_REPORT.md                     -> doc/reports/phaseN/
PHASE*_CODE_STYLE_AUDIT.md                 -> doc/reports/phaseN/
MANIFEST*.md                               -> doc/manifests/
CHANGELOG*.md                              -> doc/changelogs/
doc/CHANGELOG*.md                          -> doc/changelogs/
doc/*CODE_RULE_ALIGNMENT*.md               -> doc/code-rules/
unclassified root markdown                 -> doc/reference/legacy/
patch/**/README.md                         -> keep in patch bundle
doc/releases/**                            -> keep
doc/docs/architecture/**                   -> keep
```

The migration must preserve referenced material. Files are moved, not deleted.
References in Markdown documents are rewritten by `tools/markdown_doc_layout.py`.

## Dry-run

```bash
python tools/markdown_doc_layout.py --root . --report-file doc/maintenance/markdown_layout_plan.json
```

## Apply

```bash
python tools/markdown_doc_layout.py --root . --apply --report-file doc/maintenance/markdown_layout_plan.json
```

Then inspect:

```bash
git status --short
PYTHONPATH=src pytest -q tests/tools/test_markdown_doc_layout.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
