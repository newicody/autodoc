# 0270-r1-operational_documentation_consolidation

## Objet

Consolide l'état validé 0260→0269 dans les surfaces documentaires canoniques
existantes, sans ajouter de capacité runtime.

Le patch actualise :

- le README opérateur ;
- l'index canonique `CURRENT_ARCHITECTURE_STATE_0154.md` conservé à son chemin historique ;
- la synthèse de couches `ARCHITECTURE_LAYERS.md` ;
- le graphe maître `00_global.dot`.

Il ajoute aussi la décision 0270, son graphe, son changelog, son manifest, sa règle
et son test de cohérence.

## Audit de réutilisation

Le dépôt possède déjà les quatre points d'entrée canoniques ci-dessus. 0270 les
met à jour au lieu de créer une seconde carte globale, un second index courant ou
un nouveau plan concurrent.

Aucun fichier sous `src/` ou `tools/` n'est modifié. Aucun module, handler,
adapter, launcher, manager, orchestrateur ou daemon n'est ajouté.

## Baseline documentée

```text
0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268 -> 0269
```

Frontières verrouillées :

- Scheduler reste l'autorité d'orchestration Autodoc ;
- SQL reste l'autorité durable ;
- Qdrant reste projection/recall avec `payload.sql_ref` ;
- OpenVINO/E5 reste explicite ;
- EventBus et PassiveSupervisor restent observation-only ;
- GitHub reste une surface review/workflow sans mutation distante implicite ;
- OpenRC/OS/admin garde l'autorité sur les processus externes ;
- `Scheduler.run()` n'est pas modifié.

## Orientation opérationnelle après 0270

1. exécuteur Qdrant réel contrôlé en réutilisant les surfaces existantes ;
2. scan GitHub réel read-only avant toute mutation ;
3. gate distincte et approuvée pour la mutation GitHub distante ;
4. wrapper OpenRC optionnel, extérieur au Scheduler, seulement si nécessaire ;
5. spécialistes/distribution après stabilisation du chemin SQL/recall.

## Base exacte

```text
repository: newicody/autodoc
branch: master
base_commit: d7fce0c392399b356f5ae789e5f094d613c1915a
```

## Application

```bash
cd /home/eric/projet/git/autodoc

git status --short
git log --oneline -5
git diff

tar -xJf /mnt/data/0270-r1-operational_documentation_consolidation.tar.xz

python apply_patch_queue.py \
  --patch 0270-r1-operational_documentation_consolidation \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0270-r1-operational_documentation_consolidation \
  --commit \
  --push \
  --allow-dirty
```

Les nombreux répertoires `patch/...` non suivis déjà présents dans l'arbre local
ne sont pas utilisés comme source par ce patch.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Validation ciblée réalisée pendant la construction :

```text
git apply --check: OK
focused rule tests: 4 passed
00_global.dot: DOT valid
270_operational_documentation_consolidation.dot: DOT valid
```

La campagne complète du dépôt reste une gate locale de la patch queue.
