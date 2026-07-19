# Workflow initial automatique fondé sur l’ouverture d’Issue

## Décision

Le cycle initial de recherche utilise un seul déclencheur :

```text
issues: opened
```

`workflow_dispatch` est retiré du workflow initial. Une même demande
ne peut donc plus être lancée automatiquement puis relancée
manuellement avec la même intention initiale.

## Forme de la demande

Le job reste borné à `newicody/projects` et accepte une Issue lorsque :

- son titre commence par `[Recherche]`; ou
- son corps contient `### Question ou objectif` et
  `### Résultat attendu`.

## Intention initiale

L’événement Issue fixe sans entrée opérateur :

```text
requested_status = Recherche
request_mode = initial
parent_event_ref = ""
```

Copilot est requis pour ce cycle initial. La variable historique
`AUTODOC_COPILOT_ADVISORY_ENABLED` n’intervient plus dans le workflow.

## Compatibilité

Les scripts historiques dont le nom contient `workflow_dispatch`
restent temporairement réutilisés comme constructeurs d’événement.
Leur nom ne constitue pas un déclencheur GitHub. Leur éventuel
renommage sera traité séparément afin de ne pas dupliquer le code.

## Frontières

Ce patch ne modifie pas :

- la construction de la demande autoritative;
- l’enrichissement de l’intention;
- la génération Copilot;
- le manifeste corrélé;
- les trois uploads;
- la publication contrôlée du premier avis;
- le fetch local, SQL, Qdrant ou le Scheduler.

La validation atomique du triplet avant upload appartient à r16-r23.
