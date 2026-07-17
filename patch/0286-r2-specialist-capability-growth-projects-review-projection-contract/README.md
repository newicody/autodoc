# 0286-r2 — Specialist capability-growth Projects review projection contract

Ce patch addition-only ajoute une projection de revue GitHub Projects immuable et
non autoritative à partir de la preuve fermée 0285.

## Frontières

- aucune mutation GitHub, Issue ou ProjectV2 ;
- aucune écriture SQL ou Qdrant ;
- aucun dispatch Scheduler ou laboratoire ;
- SQL reste l'autorité durable ;
- Scheduler reste l'unique orchestrateur ;
- GitHub Projects reste une surface de revue ;
- Copilot reste consultatif.

## Vérification

```bash
python apply_patch_queue.py \
  --patch 0286-r2-specialist-capability-growth-projects-review-projection-contract \
  --dry-run \
  --allow-dirty
```

Puis, après un dry-run vert :

```bash
python apply_patch_queue.py \
  --patch 0286-r2-specialist-capability-growth-projects-review-projection-contract \
  --commit \
  --push \
  --allow-dirty
```

## Validation de construction

- `git apply --check` : OK ;
- `git diff --check` : OK ;
- `compileall` ciblé : OK ;
- tests contexte + règles : `17 passed` ;
- patch addition-only : oui.

`templates/github/projects-repository/INSTALLATION.md` a été relu mais n'est pas
modifié : ce patch ne change aucun élément déployable dans `newicody/projects`.
