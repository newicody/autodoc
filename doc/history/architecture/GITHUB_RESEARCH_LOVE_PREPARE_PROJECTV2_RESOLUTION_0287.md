# Résolution ProjectV2 intégrée au `prepare` r16-r20

## Objectif

La commande `prepare` n’exige plus la copie manuelle de
`project_item_id` et `project_field_ref`.

Elle reçoit désormais :

```text
--issue-number
--project-owner
--project-number
--project-field-name
```

puis réutilise le résolveur r16-r20-r3 et l’adaptateur GitHub CLI
existant.

## Ordre d’exécution

```text
rapport de fetch
→ sélection exacte du ready_run
→ résolution read-only Issue / ProjectV2 / champ
→ validation du readback
→ acquisition du runtime
→ composition locale r16-r19
```

Une cible absente, ambiguë ou incohérente bloque donc avant
l’ouverture du runtime, avant SQL, Qdrant, Scheduler et laboratoire.

## Overrides

Les options suivantes restent disponibles ensemble :

```text
--project-item-id-override
--project-field-ref-override
```

Elles ne court-circuitent pas le readback. Le contrat existant les
compare à la cible réellement résolue.

## Persistance du readback

`prepared.json` conserve sous `input.project_target` :

- le schéma de résolution;
- le statut;
- l’item;
- le champ;
- le readback complet;
- les frontières read-only.

Aucune valeur de token n’est sérialisée.

## Frontières

- aucune mutation ProjectV2 pendant `prepare`;
- aucun second adaptateur GitHub;
- aucun identifiant ProjectV2 deviné;
- aucun runtime ouvert avant résolution valide;
- publication distante toujours séparée dans `complete`.
