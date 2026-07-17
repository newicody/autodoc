# 0287-r7-r2-copilot-first-opinion-advisory-v2

## Objet

Remplacer le correctif rejeté par un vrai contrat public
`missipy.github.copilot_advisory.v2`. Les nouveaux artefacts contiennent
uniquement quatre champs analytiques : objectif concret, résultat attendu,
contraintes déjà fournies et critères de réussite observables.

Le lecteur v1 historique reste disponible pendant la migration, mais le
producteur actif écrit uniquement v2. La roadmap est recentrée sur le câblage
bout en bout et les tests opérationnels ; aucune phase Chalouf n’est conservée.

## Important

Ne pas appliquer l’archive précédente
`0287-r7-r2-copilot-first-opinion-versioned-contract`. Ce bundle la remplace.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-copilot-first-opinion-advisory-v2 \
  --dry-run \
  --allow-dirty
```

Puis, après un dry-run vert :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-copilot-first-opinion-advisory-v2 \
  --commit \
  --push \
  --allow-dirty
```

## Tests ciblés

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_copilot_first_opinion_advisory_v2_0287_r7_r2.py \
  tests/rules/test_copilot_first_opinion_advisory_v2_0287_r7_r2_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
```

## Contrôle après application

Le bundle est ciblé sur le `master` public observé au commit `d96d0bf`. Le clone
réseau n’était pas disponible dans l’environnement de génération ; le dry-run
sur le checkout réel reste donc obligatoire avant commit.
