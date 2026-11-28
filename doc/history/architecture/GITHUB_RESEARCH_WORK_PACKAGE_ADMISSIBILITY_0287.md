# Admissibilité d’une recherche récupérée — 0287 r16-r6

Cette unité ajoute un verrou pur entre le paquet de recherche déjà corrélé et
la future commande remise au Scheduler.

```text
fetch local
  -> triplet prêt
  -> assemblage dual existant
  -> intake sémantique existant
  -> CorrelatedResearchWorkPackage existant
  -> vérification d’admissibilité r16-r6
  -> candidat de route seulement
```

## Conditions

Le paquet est admissible uniquement lorsque :

- le dépôt source est exactement `newicody/projects` ;
- l’Issue et le run sont identifiés ;
- le paquet corrélé est déjà déclaré prêt pour une route laboratoire ;
- la demande autoritative porte explicitement `requested_status=Recherche` ;
- le mode vaut `initial` ou `continuation` ;
- un mode `initial` ne porte pas de parent ;
- un mode `continuation` porte une référence parente ;
- l’avis Copilot corrélé est présent, consultatif et jamais autoritatif ;
- aucune mutation, écriture durable, commande Scheduler ou exécution de
  laboratoire n’a déjà été effectuée par cette étape.

## Réutilisation

La validation des trois fichiers, de leurs schémas, de leurs digests et de
leurs corrélations reste la responsabilité des composants existants :

- `github_dual_artifact_run_assembly_0281.py` ;
- `github_dual_artifact_source_candidate_intake_0275.py` ;
- `correlated_research_work_package_0287.py`.

Cette unité ne relit pas les artefacts bruts et ne duplique pas ces contrôles.
Elle produit seulement un `research_laboratory_route_candidate.v1`
déterministe. Une unité ultérieure transformera ce candidat en commande typée
pour le Scheduler existant.
