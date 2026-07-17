# 0271-r1-controlled_real_qdrant_executor_reuse_audit

## Objet

Auditer les surfaces Qdrant existantes avant toute implémentation d'un exécuteur
réel contrôlé.

Le patch prouve, par inspection de sources sans import ni exécution, si le dépôt
contient déjà une implémentation concrète du protocole
`inference.qdrant_projection_adapter.QdrantProjectionExecutor`.

## Résultat attendu sur la base 70bda8c

- le protocole existant `QdrantProjectionExecutor` est présent ;
- 0262 utilise encore `DemoQdrantProjectionExecutor` ;
- 0263 utilise encore `DemoQdrantRecallExecutor` ;
- 0247 et 0248 restent des readiness read-only ;
- 0269 conserve la gate explicite `--demo-qdrant` ;
- aucun exécuteur concret non-démo n'est identifié ;
- une seule implémentation IO étroite du protocole existant est donc justifiée
  pour 0271-r2.

Le résultat local réel reste déterminé par le smoke d'audit après application.
S'il découvre une implémentation concrète, 0271-r2 devra la réutiliser au lieu
d'ajouter un module.

## Frontières

0271-r1 est un audit passif :

- aucun appel Qdrant ou réseau ;
- aucune écriture SQL ;
- aucune exécution OpenVINO ;
- aucun appel GitHub ou OpenRC ;
- aucun démarrage de service ;
- aucune modification de Scheduler ou de `Scheduler.run()` ;
- aucun RuntimeManager ou Orchestrator ;
- aucune dépendance non-stdlib ;
- aucune modification des surfaces 0247, 0248, 0262, 0263 ou 0269.

SQL reste l'autorité durable. Qdrant reste projection/recall et transporte des
références `sql_ref`.

## Base exacte

```text
repository: newicody/autodoc
branch: master
base_commit: 70bda8c028e347e6740bc6389441262d362cb3a9
```

## Application

```bash
cd /home/eric/projet/git/autodoc

git status --short
git log --oneline -5
git diff

tar -xJf /mnt/data/0271-r1-controlled_real_qdrant_executor_reuse_audit.tar.xz

python apply_patch_queue.py \
  --patch 0271-r1-controlled_real_qdrant_executor_reuse_audit \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0271-r1-controlled_real_qdrant_executor_reuse_audit \
  --commit \
  --push \
  --allow-dirty
```

Les répertoires `patch/...` non suivis déjà présents ne sont pas utilisés comme
source par cette rustine.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Smoke d'audit

```bash
PYTHONPATH=src:. python \
  tools/audit_controlled_real_qdrant_executor_reuse_0271.py \
  --repo-root . \
  --output .var/reports/controlled_real_qdrant_executor_reuse_audit_0271.json \
  --format summary
```

Sortie attendue sur la base auditée :

```text
controlled_real_qdrant_executor_reuse_audit_valid=True issues=0 ... protocol_found=True live_executor_found=False implementation_needed=True new_executor_module_justified=True next=0271-r2-stdlib_qdrant_http_executor_protocol_implementation
```

Validation ciblée réalisée pendant la construction :

```text
compileall ciblé: OK
focused tests: 6 passed
271_controlled_real_qdrant_executor_reuse_audit.dot: DOT valid
git apply --check: OK
```

La campagne complète du dépôt reste une gate locale de la patch queue.
