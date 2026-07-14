# Connecteur GitHub ProjectV2 et bundle externe — phase 0272

## Décision opérateur

Autodoc/MissiPy ne possède pas de mode de gestion de projet.

Les capacités ProjectV2 présentes dans Autodoc sont des connecteurs explicites
vers une surface externe :

```text
GitHub ProjectV2 utilisateur
-> lecture GraphQL query-only
-> snapshots locaux immuables
-> détection locale des changements
-> SourceCandidate
-> décision opérateur locale
```

Le ProjectV2, ses vues, ses formulaires d'Issue, ses variables, ses secrets et
ses workflows appartiennent au dépôt externe `newicody/projects`.

La source à copier dans ce dépôt est :

```text
templates/github/projects-repository/
```

Les fichiers placés dans ce bundle peuvent appeler des scripts réutilisables
conservés dans Autodoc. Ils ne doivent pas être activés sous `.github/` dans le
dépôt Autodoc.

## 1. Configuration du connecteur query-only

La configuration de lecture locale est :

```text
config/github_project_v2_query_only.example.ini
```

Elle décrit une cible externe et ne transforme pas Autodoc en gestionnaire de
projet. Le token n'est jamais stocké dans le fichier de configuration :

```bash
export GITHUB_TOKEN='...'
```

Les opérations de lecture, les snapshots, les changements et les handoffs
restent sous autorité locale. Les documents GraphQL query-only ne contiennent
aucune mutation.

### Compatibilité terminologique avec la règle 0272

La formulation historique mode **Project-native** désignait uniquement ce
connecteur query-only. Elle ne définit plus un mode de gestion de projet dans
Autodoc.

Le paramètre historique `require_actions_deployment = false` signifiait que la
lecture ProjectV2 pouvait être validée sans workflow externe. De même,
l'expression historique pont secondaire désignait le bundle Actions facultatif.
Ces marqueurs sont conservés uniquement pour la compatibilité des règles 0272 ;
les workflows actifs, les formulaires, les vues et leur configuration restent
la responsabilité de `newicody/projects`.

## 2. Vérifier le connecteur

Vérification locale, sans réseau :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

Vérification réelle en lecture seule :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-native-readiness \
  --format summary
```

L'identifiant historique de policy est conservé pour compatibilité. Il ne
définit pas un mode Project dans l'architecture.

## 3. Chaîne entrante

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_v2_query_only_snapshot_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-query-only \
  --format summary

PYTHONPATH=src:. python \
  tools/detect_github_project_v2_snapshot_changes_0272.py \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-detection \
  --format summary

PYTHONPATH=src:. python \
  tools/build_github_project_v2_change_handoffs_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-handoff \
  --format summary
```

Les handoffs sont écrits sous :

```text
.var/github/project_v2/handoffs/
```

Une décision locale explicite peut ensuite être appliquée à une candidate. Les
enregistrements restent immuables sous :

```text
.var/github/project_v2/decisions/
```

## 4. Bundle destiné à `newicody/projects`

Le bundle externe contient les surfaces de gestion :

```text
templates/github/projects-repository/
├── .github/ISSUE_TEMPLATE/
├── .github/workflows/
├── scripts/
└── documentation du board
```

Après copie, ces fichiers deviennent la configuration du dépôt
`newicody/projects`. Le dépôt Autodoc conserve seulement :

- les contrats et adaptateurs de connecteur ;
- les outils locaux de lecture, d'intake et de publication verrouillée ;
- les helpers réutilisables appelés par le dépôt externe ;
- le bundle source destiné à la copie.

Il ne conserve pas de workflow de recherche ni de formulaire de gestion actif
sous sa propre arborescence `.github/`.

## 5. Dette de configuration identifiée

Le fichier nommé `github_project_v2_query_only.example.ini` contient encore des
paramètres historiques de `workflow_dispatch`, consommés par un adaptateur de
sortie existant. Les retirer sans migrer l'adaptateur casserait la surface
opérationnelle.

Cette dette doit être traitée dans un patch séparé :

```text
lecture query-only                    -> configuration de lecture
workflow_dispatch / mutation distante -> configuration de connecteur sortant
```

Jusqu'à cette migration, la présence de ces paramètres ne définit pas un mode
Project dans Autodoc ; elle constitue un mélange de responsabilités documenté.

## Frontières

```text
mode projet Autodoc                 : absent
ProjectV2                           : surface externe
source des vues et formulaires      : newicody/projects
bundle à copier                     : templates/github/projects-repository/
workflow de recherche actif Autodoc : absent
formulaires de gestion actifs       : absents
connecteurs de lecture/intake       : conservés
publication distante                : explicite et verrouillée
Scheduler / SHM                     : inchangés
SQL / Qdrant                        : autorité locale inchangée
```
