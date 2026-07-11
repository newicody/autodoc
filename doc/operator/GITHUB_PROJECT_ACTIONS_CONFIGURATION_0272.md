# Configuration opérateur GitHub ProjectV2 et GitHub Actions — phase 0272

## Objet

Cette procédure configure manuellement les deux surfaces GitHub utilisées par
Autodoc/MissiPy :

```text
source canonique de lecture : ProjectV2 utilisateur newicody/2
surface secondaire          : workflow GitHub Actions dans un dépôt d'idées externe
```

Aucun script d'installation ou de déploiement n'est fourni. Les scripts Python
du dépôt testent et utilisent une configuration existante ; ils ne créent pas
de dépôt, ne copient pas de workflow, ne modifient pas les permissions GitHub et
ne déclenchent pas d'Action.

## 1. Comprendre les deux chemins

### ProjectV2 direct

Le chemin principal lit le ProjectV2 utilisateur par GraphQL query-only :

```text
https://github.com/users/newicody/projects/2
project_id = PVT_kwHOA3ouXM4Ba3Ar
```

Il récupère aussi les `DRAFT_ISSUE`, qui ne sont pas rattachées à un dépôt. Ce
chemin produit des snapshots locaux immuables.

### GitHub Actions secondaire

Le workflow fourni dans `templates/github/` écoute les événements `issues` d'un
dépôt GitHub externe. Il ne se déclenche pas lorsqu'une simple `DRAFT_ISSUE` est
créée ou modifiée dans le ProjectV2.

Pour déclencher ce workflow, il faut créer ou modifier une vraie Issue dans le
dépôt externe configuré. Le workflow transforme l'événement en artefact JSON et
l'enregistre comme artefact GitHub Actions. Ce chemin reste secondaire et ne
remplace pas le snapshot ProjectV2 direct.

## 2. Choisir le dépôt externe

Choisir ou créer manuellement un dépôt GitHub dédié aux idées. Exemple :

```text
newicody/autodoc-ideas
```

Le dépôt Autodoc lui-même ne doit pas devenir la source d'ingestion de ses
propres artefacts. Le dépôt externe est une surface de travail et d'échange ; la
machine locale reste l'autorité.

Reporter exactement le même nom de dépôt dans :

```ini
[artifact_source]
repositories = newicody/autodoc-ideas

[safety]
allowed_repositories = newicody/autodoc-ideas

[deployment_readiness]
workflow_repository = newicody/autodoc-ideas
```

Remplacer l'exemple par le dépôt réellement choisi. Ces trois valeurs doivent
rester cohérentes.

## 3. Copier manuellement les deux fichiers

Depuis le dépôt Autodoc, copier le workflow et son builder dans le dépôt externe :

```text
Autodoc                                             dépôt externe
templates/github/autodoc-ticket-artifact.yml     -> .github/workflows/autodoc-ticket-artifact.yml
templates/github/scripts/build_autodoc_ticket_artifact.py
                                                   -> scripts/build_autodoc_ticket_artifact.py
```

Créer les répertoires `.github/workflows/` et `scripts/` dans le dépôt externe
si nécessaire, puis committer et pousser ces deux fichiers avec les outils Git
habituels de l'opérateur.

Le script de readiness Autodoc ne fait pas cette copie et n'effectue aucun
`git commit` ou `git push`.

## 4. Vérifier les réglages GitHub Actions

Dans le dépôt externe, ouvrir :

```text
Settings -> Actions -> General
```

Vérifier que :

- les Actions nécessaires sont autorisées ;
- les workflows peuvent utiliser `actions/checkout@v4` et
  `actions/upload-artifact@v4` ;
- les permissions par défaut du `GITHUB_TOKEN` restent en lecture ;
- aucune permission d'écriture n'est ajoutée au workflow ;
- aucun secret Autodoc n'est requis par le builder actuel.

Le workflow versionné déclare seulement :

```yaml
permissions:
  contents: read
  issues: read
  actions: read
```

Il ne contient pas `workflow_dispatch` et ne peut donc pas être lancé à distance
par le système Autodoc.

## 5. Configurer le token local

Le token local est utilisé uniquement par les scripts query-only de snapshot et
de readiness. Il doit permettre de lire le ProjectV2 utilisateur et, pour le
test Actions, de lire le dépôt externe, ses workflows et leur contenu.

Le nom de la variable vient de :

```ini
[github]
token_env = GITHUB_TOKEN
```

Dans le terminal :

```bash
export GITHUB_TOKEN='...'
```

Ne jamais inscrire le token dans le fichier `.ini`, un rapport, un patch ou un
commit Git.

## 6. Lancer le test de readiness

Test local sans réseau :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

Test réel query-only :

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:deployment-readiness \
  --format summary
```

Le test distant vérifie le ProjectV2, l'existence du workflow, son état et la
correspondance entre les fichiers déployés et les templates locaux. Il ne répare
rien automatiquement.

## 7. Tester le workflow Actions secondaire

Créer ou modifier une vraie Issue dans le dépôt externe. Ouvrir ensuite :

```text
Actions -> autodoc-ticket-artifact
```

Le run doit produire au minimum :

```text
autodoc-ticket-artifact-<run_id>
autodoc-ticket-artifact-bundle-<run_id>
```

Une `DRAFT_ISSUE` créée uniquement dans le ProjectV2 ne déclenche pas ce run.
Elle doit apparaître dans le snapshot direct r3 à la place.

## 8. Lancer le flux ProjectV2 entrant

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

Le troisième outil produit des `SourceCandidate` locales nécessitant une gate
opérateur future. Il n'écrit ni dans SQL ni dans Qdrant.

## 9. Diagnostic rapide

### `project_read_ready=False`

Vérifier le token, l'owner, le numéro du Project et son identifiant GraphQL.

### `actions_deployment_ready=False`

Vérifier :

- le nom exact du dépôt externe dans les trois sections du `.ini` ;
- le chemin `.github/workflows/autodoc-ticket-artifact.yml` ;
- le chemin `scripts/build_autodoc_ticket_artifact.py` ;
- le commit/push manuel des deux fichiers ;
- l'activation des Actions dans le dépôt externe ;
- la capacité du token local à lire ce dépôt.

### Aucun run après modification du Project

C'est normal pour une `DRAFT_ISSUE`. Le workflow écoute les Issues du dépôt
externe, pas les drafts du ProjectV2. Utiliser le snapshot GraphQL direct pour
les drafts ou convertir manuellement le draft en Issue du dépôt externe.

## Frontières

```text
installation automatique : interdite
déploiement automatique  : interdit
workflow dispatch         : interdit
mutation GraphQL          : interdite
mutation GitHub distante  : interdite dans 0272
SQL/Qdrant                : interdits avant gate opérateur
Scheduler.run()           : inchangé
```
