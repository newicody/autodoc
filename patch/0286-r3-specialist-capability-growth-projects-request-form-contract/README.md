# 0286-r3 — Specialist capability-growth Projects request form contract

Ce patch ajoute le premier élément déployable de la phase 0286 : un formulaire
Issue dédié dans le bundle `newicody/projects` et son contrat d'intake local,
immuable et stdlib-only.

## Effet

- nouvelle demande `specialist-capability-growth.yml` ;
- normalisation depuis l'artefact autoritatif, un événement GitHub ou une Issue ;
- distinction explicite entre demande recevable et proposition 0285-r2 prête ;
- aucun champ d'approbation et aucune autorisation d'exécution ;
- mise à jour cumulative de `INSTALLATION.md` vers `0286-r3` ;
- conservation des marqueurs historiques `0284-r9` et `0284-r1-r5`.

## Frontières

- GitHub Projects reste une surface de demande et de revue ;
- la décision opérateur reste locale ;
- SQL reste l'autorité durable ;
- le Scheduler existant reste l'unique orchestrateur ;
- aucune mutation distante, écriture SQL/Qdrant ou exécution laboratoire ;
- aucun nouveau secret, variable, workflow ou permission Actions.

## Vérification

```bash
python apply_patch_queue.py \
  --patch 0286-r3-specialist-capability-growth-projects-request-form-contract \
  --dry-run \
  --allow-dirty
```

Puis, après un dry-run vert :

```bash
python apply_patch_queue.py \
  --patch 0286-r3-specialist-capability-growth-projects-request-form-contract \
  --commit \
  --push \
  --allow-dirty
```

## Validation de construction

- formulaire YAML : valide, 14 champs identifiés ;
- `git apply --check` : OK ;
- `git diff --check` : OK ;
- `compileall` ciblé : OK ;
- tests contexte + règles : `13 passed` ;
- audit 0286 : r2 et r3 détectés, prochain jalon r4.
