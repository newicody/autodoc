# Assemblage des recherches récupérées et vérification d’admissibilité

## But

Cette unité relie le `ready_run` produit par le fetch GitHub Actions aux
contrats existants, sans créer une nouvelle chaîne d’intake.

```text
fetch canonique
→ ready_run corrélé
→ lecture locale des trois fichiers
→ assemblage dual existant
→ intake sémantique existant
→ paquet de recherche corrélé existant
→ verrou d’admissibilité r16-r6
→ candidat de route
```

## Entrée

Le rapport canonique
`missipy.github_actions.artifact_fetch_cycle_once.v1` référence le rapport de
scan. Chaque `ready_run` doit contenir exactement :

- `authoritative_request`;
- `copilot_advisory`;
- `run_manifest`.

Les fichiers locaux attendus sont :

- `authoritative_request.json`;
- `copilot_advisory.json`;
- `dual_artifact_manifest.json`.

Le répertoire de préparation vient du `ready_run` ou, pour un artefact déjà
synchronisé, de l’état append-only du fetch.

## Réutilisations obligatoires

Cette unité appelle successivement :

1. `run_github_dual_artifact_run_assembly`;
2. `build_correlated_research_work_package`;
3. `evaluate_github_research_work_package_admissibility`.

Elle ne recalcule pas les digests et ne réinterprète pas la demande.

## Limites verrouillées

Cette unité :

- lit les fichiers locaux sans les modifier;
- ne crée aucune ligne SQL;
- n’écrit aucun vecteur Qdrant;
- ne modifie ni Issue ni ProjectV2;
- ne construit aucune commande Scheduler;
- ne lance aucun spécialiste ni laboratoire.

Le candidat admissible sera transformé en commande typée dans l’unité
suivante, sous l’autorité du Scheduler existant.
