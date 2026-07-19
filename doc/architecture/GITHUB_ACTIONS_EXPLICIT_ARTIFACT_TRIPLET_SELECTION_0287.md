# Sélection explicite d’un triplet d’artefacts dupliqué

## Situation

Le run GitHub Actions `29622831972` possède deux générations complètes :

```text
authoritative_request × 2
copilot_advisory × 2
run_manifest × 2
```

Le corrélateur normal le classe correctement en `deferred` avec la raison
`duplicate_roles`. Il ne doit pas choisir arbitrairement un triplet.

## Surface opérateur

L’outil suivant construit un nouveau rapport local :

```text
tools/select_github_actions_artifact_triplet_0287.py
```

Il exige trois identifiants explicites :

```text
--authoritative-request-artifact-id
--copilot-advisory-artifact-id
--run-manifest-artifact-id
```

## Validations

La sélection n’est admise que si :

- le rapport source et le scan sont valides;
- le run est différé uniquement pour `duplicate_roles`;
- aucun rôle ne manque;
- aucun artefact n’est indisponible;
- les trois rôles sont réellement dupliqués;
- chaque identifiant correspond exactement à un record local;
- le nom de chaque artefact correspond à son rôle;
- chaque répertoire de staging est résolu de manière unique;
- les trois fichiers JSON attendus sont lisibles et bornés.

## Résultat

Le rapport produit conserve le schéma :

```text
missipy.github_actions.artifact_fetch_cycle_once.v1
```

Il contient exactement un `ready_run` et peut être transmis directement à :

```text
run_github_research_love_prepare_once_0287.py
  --existing-fetch-cycle-report
```

Les chemins de staging absolus sont incorporés au `ready_run`, ce qui évite
toute ambiguïté ultérieure sur le chemin relatif de l’état durable.

## Frontières

- aucune sélection automatique du plus récent;
- aucune requête GitHub;
- aucune suppression d’artefact;
- aucun changement de l’état append-only;
- aucune écriture SQL/Qdrant;
- aucune exécution Scheduler/laboratoire;
- le rapport et le scan sources restent inchangés.
