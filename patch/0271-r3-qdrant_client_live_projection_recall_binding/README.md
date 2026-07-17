# 0271-r3-qdrant_client_live_projection_recall_binding

## Correctif de préimages Git exactes

Cette archive remplace les deux archives r3 précédentes.

La première archive utilisait des copies reformatées des CLI 0262 et 0263 et
annonçait aussi des modes incorrects. La deuxième corrigeait les modes, mais
conservait encore les mauvaises préimages de contenu.

Cette version est reconstruite depuis les blobs Git historiques exacts :

```text
tools/run_scheduler_managed_embedding_qdrant_projection_0262.py
  e240cfd5e4ceab5eccd4f60558bfcaabfce396b3  mode 100755

tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py
  5d7a84ee24e1fbeaf6ad97171971d8c0ee7d738d  mode 100755
```

Les autres préimages modifiées sont également celles du commit public :

```text
src/context/production_prototype_smoke_composition_0269.py
  cfca0d468f3fa09887a35d50de501183342cc75d

tools/run_production_prototype_smoke_composition_0269.py
  a54a102a6ad8b5b823a5692ea73099772b44be78  mode 100755
```

## Objet fonctionnel

Raccorder l'exécuteur `qdrant-client` de 0271-r2 aux outils existants 0262 et
0263, puis exposer ce chemin dans la composition 0269 sous un mode live
explicitement opt-in.

Aucun second pipeline Qdrant n'est créé. Le patch étend les CLI et le contrat de
composition déjà présents.

## Base

```text
repository: newicody/autodoc
branch: master
base_commit: 69d700e9b73301bc342b16587f6fa8737f78faa7
base_subject: r2-qdrant-client-projection-executor
```

## Comportement

- `--demo-qdrant` reste disponible pour les tests déterministes ;
- `--live-qdrant` injecte `QdrantClientProjectionExecutor` ;
- 0262 utilise une gate écriture seule ;
- 0263 utilise une gate recherche seule ;
- 0269 exige un mode Qdrant explicite en exécution ;
- le résultat live doit prouver `qdrant_projection_live=True` et
  `qdrant_recall_live=True` ;
- URL, collection, timeout et préférence gRPC sont injectés ;
- seule la variable d'environnement portant la clé API est nommée dans les
  arguments ; sa valeur n'est jamais sérialisée.

## Frontières

- SQL reste l'autorité durable ;
- Qdrant reste une projection/recall reconstructible ;
- les hits Qdrant transportent `sql_ref`, puis sont réhydratés depuis SQL ;
- OpenRC/OS/admin doit déjà avoir démarré Qdrant ;
- aucune création de collection ;
- aucun démarrage de daemon ;
- aucune modification Scheduler ;
- aucun RuntimeManager ou Orchestrator ;
- aucune lecture ou écriture SHM ;
- RouteProxy et ControlProxy restent inchangés.

## Remplacement de l'archive extraite

```bash
cd /home/eric/projet/git/autodoc

rm -rf patch/0271-r3-qdrant_client_live_projection_recall_binding

tar -xJf \
  /mnt/data/0271-r3-qdrant_client_live_projection_recall_binding-exactbase.tar.xz
```

## Application

```bash
python apply_patch_queue.py \
  --patch 0271-r3-qdrant_client_live_projection_recall_binding \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0271-r3-qdrant_client_live_projection_recall_binding \
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

## Smoke live

Le service Qdrant et la collection doivent déjà être disponibles.

```bash
PYTHONPATH=src:. python \
  tools/run_production_prototype_smoke_composition_0269.py \
  --execute \
  --policy-decision-id policy:0271:live-qdrant \
  --demo-eventbus \
  --live-qdrant \
  --qdrant-url http://127.0.0.1:6333 \
  --qdrant-collection autodoc_context_embeddings \
  --qdrant-timeout-seconds 10 \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

Pour gRPC, ajouter `--qdrant-prefer-grpc --qdrant-grpc-port 6334`.

## Validation de construction

```text
exact 0262 preimage hash: OK
exact 0263 preimage hash: OK
modes 0262/0263: 100755
exact-base git apply --check: OK
exact-base git apply: OK
focused compileall: OK
exact-base focused tests: 8 passed
earlier functional focused campaign: 16 passed
DOT validation: OK
git diff --check: OK
```
