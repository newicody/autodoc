# Rapport 0287 r16-r5-r1

## Objet

Conserver l'intention contrôlée de recherche sans modifier le constructeur
générique conflictuel.

## Résultat

- nouveau script stdlib-only d'enrichissement ;
- étape workflow explicite avant Copilot et le manifeste ;
- conservation du schéma autoritatif v1 ;
- validation repository, Issue, statut, mode et collisions ;
- aucune dépendance au Scheduler, à SQL, Qdrant ou OpenVINO.

## Tests ciblés

```bash
/home/eric/python/bin/python -m pytest -q \
  tests/context/test_authoritative_request_research_intention_enrichment_0287_r16_r5_r1.py \
  tests/rules/test_authoritative_request_research_intention_enrichment_0287_r16_r5_r1_rule.py
```
