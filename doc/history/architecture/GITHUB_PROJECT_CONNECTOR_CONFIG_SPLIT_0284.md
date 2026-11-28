# Séparation des configurations GitHub — 0284-r1-r3

## Décision

Autodoc conserve deux connecteurs explicites et distincts :

```text
entrée : ProjectV2 GraphQL query-only
sortie : workflow_dispatch borné vers newicody/projects
```

Le fichier query-only ne porte plus de section autorisant une mutation distante.
Le dispatch dispose de sa propre configuration, sûre par défaut, et nécessite
toujours `--execute`, un `policy_decision_id` et deux verrous locaux.

Le bundle `templates/github/projects-repository/` reste une source à copier. Son
`INSTALLATION.md` est le guide cumulatif de déploiement du dépôt Projects.

## Frontières conservées

- aucun workflow Project actif à la racine d'Autodoc ;
- aucun changement du Scheduler ;
- aucun accès SQL, OpenVINO ou Qdrant ;
- aucune valeur de token sérialisée ;
- la lecture et le dispatch restent deux responsabilités séparées ;
- `newicody/projects` reste propriétaire des Issues, vues et Actions de projet.
