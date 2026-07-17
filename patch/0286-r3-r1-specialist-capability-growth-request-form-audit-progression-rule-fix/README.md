# 0286-r3-r1 — Request-form audit progression rule fix

Ce correctif s'applique après l'échec de la suite `tests/rules` survenu alors
que le patch `0286-r3-specialist-capability-growth-projects-request-form-contract`
a déjà été appliqué dans l'arbre de travail.

## Cause

La règle historique r2 imposait encore que l'audit recommande exactement r3.
Après ajout du formulaire r3, l'audit marque correctement r3 terminé et
recommande r4.

## Correction

La règle r2 devient cumulative :

- avant r3, r3 doit être le prochain patch ;
- à partir de r3, r3 doit appartenir aux phases terminées.

Cette propriété reste valide pendant r4 à r8.

## Frontières

Aucune modification du runtime, du Scheduler, de SQL, Qdrant, EventBus, des
laboratoires, des workflows GitHub ou des ressources ProjectV2.

`templates/github/projects-repository/INSTALLATION.md` est vérifié mais non
modifié ; sa version reste `0286-r3`.

## Application

Ne pas réappliquer r3 : ses changements sont déjà présents dans l'arbre sale.

```bash
python apply_patch_queue.py \
  --patch 0286-r3-r1-specialist-capability-growth-request-form-audit-progression-rule-fix \
  --commit \
  --push \
  --allow-dirty
```

## Validation de construction

- `git apply --check` : OK sur la règle r2 publiée ;
- `git diff --check` : OK ;
- `compileall` ciblé : OK ;
- tests du correctif et scénario audit r3→r4 : `4 passed`.
