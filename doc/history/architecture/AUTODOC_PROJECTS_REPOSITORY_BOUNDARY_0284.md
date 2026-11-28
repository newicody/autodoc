# Frontière Autodoc / dépôt Projects — 0284-r1-r2

## Décision

Autodoc n'est pas un gestionnaire de projet et ne possède pas de mode Project.
GitHub ProjectV2 est une surface externe observée ou alimentée par des
connecteurs explicites.

La séparation canonique est :

```text
Autodoc
├── contrats de connecteur GitHub
├── adaptateurs query-only, intake et publication contrôlée
├── helpers réutilisables pour GitHub Actions
└── templates/github/projects-repository/  # source à copier

newicody/projects
├── ProjectV2 et ses vues
├── .github/ISSUE_TEMPLATE/
├── .github/workflows/
├── configuration locale du board
└── variables et secrets du dépôt
```

## Surfaces interdites dans Autodoc

Les éléments suivants ne doivent pas être actifs dans le dépôt Autodoc :

- workflow de recherche contrôlée sous `.github/workflows/` ;
- formulaires de recherche, thème ou cycle sous `.github/ISSUE_TEMPLATE/` ;
- configuration de vues ProjectV2 traitée comme configuration runtime Autodoc ;
- orchestrateur ou mode d'exécution propriétaire du ProjectV2.

## Surfaces conservées

Les éléments suivants restent légitimes dans Autodoc :

- lecture GraphQL query-only d'un ProjectV2 externe ;
- snapshots locaux et détection de changements ;
- transformation en `SourceCandidate` ;
- décision opérateur locale ;
- fetch des artefacts Actions ;
- publication distante explicitement autorisée et verrouillée ;
- contrats purs de dispatch et de projection ;
- scripts partagés utilisés par un workflow copié dans `newicody/projects` ;
- bundle source `templates/github/projects-repository/`.

La présence de connecteurs GitHub n'implique donc aucun « mode projet » dans
Autodoc.

## Bundle externe

`templates/github/projects-repository/` est la seule source canonique des
surfaces destinées au dépôt Projects. Après copie, le dépôt `newicody/projects`
devient propriétaire de ces fichiers et peut les adapter indépendamment.

Un helper peut rester dans Autodoc lorsqu'il est générique et réutilisable. Son
activation, ses permissions et sa configuration de board appartiennent au dépôt
Projects.

## Dette de configuration

`config/github_project_v2_query_only.example.ini` mélange encore une cible de
lecture query-only et des paramètres historiques de `workflow_dispatch`.
L'adaptateur sortant existant consomme ces paramètres ; leur suppression brute
casserait son contrat.

La migration sera un patch unitaire ultérieur :

1. créer une configuration dédiée au connecteur sortant ;
2. migrer l'outil de dispatch et ses tests ;
3. retirer les paramètres de mutation du fichier query-only ;
4. retirer les anciennes références `autodoc-ideas` après audit de leurs usages.

## Invariants

```text
Scheduler modifié                  : non
nouveau bus                        : non
nouveau orchestrateur             : non
SQL autorité durable              : inchangé
Qdrant projection / recall        : inchangé
GitHub autorité du contexte local : non
Copilot autoritaire               : non
```
