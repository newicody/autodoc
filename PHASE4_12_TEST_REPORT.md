# Phase 4.12-r2 — test report

## Objet

Réalignement 4.2 → 4.11 avec conservation de l'ancien `doc/code_rule.md` comme socle.

## Vérifications effectuées dans l'environnement de génération

```text
python -m py_compile \
  src/inference/e5_cli_contracts.py \
  src/inference/report_io.py \
  src/inference/e5_corpus_cli.py \
  src/inference/e5_rebuild_cli.py \
  src/inference/e5_corpus_inspect_cli.py \
  tests/inference/test_report_io.py \
  tests/inference/test_e5_cli_contracts.py \
  tests/rules/test_e5_code_rule_alignment.py
```

Résultat : OK.

```text
PYTHONPATH=src pytest -q \
  tests/inference/test_report_io.py \
  tests/rules/test_e5_code_rule_alignment.py
```

Résultat : `7 passed`.

## Validation de la correction r2

Le test `test_code_rule_preserves_kernel_identity_and_adds_only_e5_application_note` vérifie :

- conservation du titre historique `Header de recherche / Philosophie du projet` ;
- conservation de `Micro-Kernel Coopératif IA` ;
- conservation du contrat composant / Scheduler / événements ;
- présence de l'addendum Phase 4.12-r2 ;
- absence de la formulation `Outillage CLI hors kernel`.

## Limite honnête

L'environnement de génération ne contient pas le dépôt complet : certains modules déjà présents chez l'utilisateur ne sont pas disponibles ici.
Le test `tests/inference/test_e5_cli_contracts.py` est livré mais doit être exécuté dans le dépôt local complet.

## Commandes à lancer localement

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT :

```bash
dot -Tsvg doc/docs/architecture/inference/65_e5_search_report_file.dot >/tmp/65_e5_search_report_file.svg
dot -Tsvg doc/docs/architecture/inference/66_e5_code_style_alignment.dot >/tmp/66_e5_code_style_alignment.svg
rm -f /tmp/65_e5_search_report_file.svg /tmp/66_e5_code_style_alignment.svg
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: true
reason: ajout court d'application E5 sans réécriture de la philosophie initiale
```
