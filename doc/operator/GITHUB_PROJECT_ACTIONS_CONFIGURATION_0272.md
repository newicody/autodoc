# Mode ProjectV2 natif et pont GitHub Actions optionnel — phase 0272

## Décision opérateur

Le mode actuellement utilisé par Autodoc/MissiPy est le mode **Project-native** :

```text
GitHub ProjectV2 utilisateur newicody/2
-> lecture GraphQL query-only
-> snapshots locaux immuables
-> détection locale des changements
-> SourceCandidate
-> décision opérateur locale
```

Ce chemin fonctionne avec des `DRAFT_ISSUE` du ProjectV2 et ne demande pas de
dépôt d'idées externe, de workflow GitHub Actions ou de procédure d'installation.

Le workflow présent dans `templates/github/` est une seconde capacité,
optionnelle, destinée à transformer les événements `issues` d'un dépôt GitHub en
artefacts Actions. Il ne constitue pas l'installation du mode ProjectV2.

## 1. Configuration minimale du mode Project-native

La configuration utilisée est :

```text
config/github_project_v2_query_only.example.ini
```

Identité attendue :

```ini
[project]
owner = newicody
number = 2
project_id = PVT_kwHOA3ouXM4Ba3Ar
view_number_hint = 2
```

Le numéro de vue est un repère d'interface. L'identité durable est le couple
`owner/number` vérifié avec le `project_id`.

Le token n'est jamais placé dans le `.ini` :

```bash
export GITHUB_TOKEN='...'
```

Il doit permettre la lecture du ProjectV2. Les scripts interdisent les documents
GraphQL contenant une mutation et ne sérialisent jamais le token.

## 2. Test du système Project-native

Test local, sans réseau :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

Test réel, query-only :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-native-readiness \
  --format summary
```

Avec `require_actions_deployment = false`, le résultat Project-native peut être
vert même si aucun dépôt externe ou workflow Actions n'existe :

```text
project_read_ready=True
actions_deployment_ready=False
system_ready=True
```

`actions_deployment_ready=False` n'est alors pas une panne ; cela signifie
seulement que le pont secondaire n'a pas été demandé ou vérifié.

## 3. Flux entrant ProjectV2

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

Une décision est ensuite appliquée à une candidate précise :

```bash
PYTHONPATH=src:. python \
  tools/gate_github_project_v2_source_candidate_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --candidate-id ghpv2-... \
  --action inspect \
  --reason "reviewed by operator" \
  --execute \
  --policy-decision-id policy:0272:source-candidate-gate \
  --format summary
```

Les enregistrements de décision sont immuables et restent sous :

```text
.var/github/project_v2/decisions/
```

## 4. À quoi sert le pont Actions optionnel ?

Le pont Actions s'applique seulement à une vraie Issue d'un dépôt :

```text
Issue repository event
-> repository workflow
-> JSON artifact
-> future local artifact fetch/sync
```

Un `DRAFT_ISSUE` créé uniquement dans le ProjectV2 n'est pas un événement Issue
de dépôt et passe directement par la lecture GraphQL ProjectV2.

Ce pont peut être utile plus tard pour :

- récupérer un contexte enrichi par un workflow lié à une Issue réelle ;
- transporter des artefacts versionnés entre GitHub et la machine locale ;
- comparer le chemin ProjectV2 direct et le chemin Issue/Actions ;
- déclencher une analyse GitHub-side sans accorder de droit d'écriture à Autodoc.

Il reste facultatif tant que le travail est réalisé avec les drafts du ProjectV2.

## 5. Vérifier un pont Actions déjà déployé

Pour demander explicitement ce contrôle :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --check-actions-bridge \
  --policy-decision-id policy:0272:actions-bridge-readiness \
  --format summary
```

Le script vérifie seulement par lecture :

- le dépôt configuré ;
- le workflow actif ;
- le chemin du workflow ;
- l'absence de `workflow_dispatch` ;
- l'absence de permissions d'écriture ;
- la correspondance avec les templates locaux.

Il ne corrige et ne déploie rien.

## 6. Déploiement manuel éventuel du pont

Cette section ne concerne pas le mode Project-native minimal.

Si un dépôt externe d'Issues est volontairement choisi, reporter son nom dans
les sections `[artifact_source]`, `[safety]` et `[deployment_readiness]`, puis
copier manuellement :

```text
templates/github/autodoc-ticket-artifact.yml
-> .github/workflows/autodoc-ticket-artifact.yml

templates/github/scripts/build_autodoc_ticket_artifact.py
-> scripts/build_autodoc_ticket_artifact.py
```

Le commit et le push sont des opérations opérateur ordinaires. Aucun script
Autodoc ne les effectue. Le workflow doit conserver des permissions de lecture
et ne doit pas exposer `workflow_dispatch`.

## Frontières

```text
mode ProjectV2 sans Actions : supporté et mode par défaut
pont repository-Issue       : optionnel
script d'installation       : absent
script de déploiement        : absent
déploiement automatique     : interdit
workflow dispatch            : interdit
mutation GraphQL             : interdite
mutation GitHub distante     : interdite dans 0272
SQL/Qdrant dans r7           : aucune écriture
Scheduler.run() / SHM        : inchangés
```
