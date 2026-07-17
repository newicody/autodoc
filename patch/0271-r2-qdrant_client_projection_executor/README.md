# 0271-r2-qdrant_client_projection_executor

## Objet

Implémenter le protocole existant
`inference.qdrant_projection_adapter.QdrantProjectionExecutor` avec le SDK
Python officiel `qdrant-client`, après que l'audit 0271-r1 a confirmé l'absence
d'exécuteur réel réutilisable.

Le patch ajoute un seul module IO étroit. Il ne raccorde pas encore les CLI
0262/0263/0269 au chemin live : ce raccordement et le smoke sur un serveur
Qdrant réel restent réservés à 0271-r3.

## Base exacte

```text
repository: newicody/autodoc
branch: master
base_commit: 66c59a3aa5713c1666d924030eef880ed6148ca1
base_subject: r1-controlled-real-qdrant-executor-reuse-audit
```

## Dépendance non-stdlib justifiée

L'opérateur a retenu le SDK officiel plutôt qu'un client HTTP maison. La version
est fixée dans :

```text
config/requirements-qdrant-client-0271.txt
qdrant-client==1.18.0
```

Le module charge cette dépendance seulement dans sa factory. Les imports du
module, les tests et la patch queue restent utilisables sans paquet installé et
sans serveur Qdrant.

Installation locale, hors patch queue :

```bash
python -m pip install -r config/requirements-qdrant-client-0271.txt
```

## Contrat

Le nouvel exécuteur :

- réutilise `QdrantProjectionExecutor` ;
- exige un `policy_decision_id` typé ;
- sépare les gates écriture et recherche ;
- traduit les refs `qdrant-point:*` en UUID Qdrant déterministes ;
- conserve la ref Autodoc dans `payload.autodoc_point_ref` ;
- conserve `payload.sql_ref` et `payload.sql_context_ref` ;
- retourne des hits ref-only pour réhydratation SQL ;
- encapsule les erreurs SDK dans un échec typé et sérialisable ;
- échoue si un hit ne contient pas de `sql_ref` valide.

## Frontières

- SQL reste l'autorité durable ;
- Qdrant reste projection/recall reconstructible ;
- aucun démarrage ou arrêt Qdrant ;
- aucun appel OpenRC ou `rc-service` ;
- aucune création de collection en 0271-r2 ;
- aucune modification Scheduler ;
- aucun RuntimeManager ou Orchestrator ;
- aucune écriture SQL ;
- aucune exécution OpenVINO ;
- aucun appel GitHub ;
- aucune modification SHM, mmap, RouteProxy ou ControlProxy.

Le choix de `qdrant-client` ne change pas le data-plane SHM. L'appel SDK reste
une bordure IO externe et ne doit pas être exécuté dans une section critique
SHM.

## Application

```bash
cd /home/eric/projet/git/autodoc

git status --short
git log --oneline -5
git diff

tar -xJf /mnt/data/0271-r2-qdrant_client_projection_executor.tar.xz

python apply_patch_queue.py \
  --patch 0271-r2-qdrant_client_projection_executor \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0271-r2-qdrant_client_projection_executor \
  --commit \
  --push \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Readiness de dépendance

Après installation du paquet :

```bash
PYTHONPATH=src:. python \
  tools/check_qdrant_client_projection_executor_0271.py \
  --output .var/reports/qdrant_client_projection_executor_readiness_0271.json \
  --format summary
```

Sortie attendue :

```text
qdrant_client_projection_executor_ready=True installed=True version=1.18.0 required=1.18.0 network_used=False qdrant_called=False touches_shm=False
```

## Validation de construction

```text
focused compileall: OK
focused tests: 12 passed
DOT validation: OK
git diff --check: OK
```

La campagne complète et l'installation effective de la dépendance restent des
gates locales.
