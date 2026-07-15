# Installation cumulative de `newicody/projects`

Version du guide : `0287-r5-r1`.

Ce document est le mode opératoire cumulatif simplifié pour installer et mettre à jour l’interface GitHub du projet.

Ce guide installe uniquement l’interface GitHub du projet : formulaires
d’Issues, workflow Actions, scripts de projection et configuration ProjectV2.
Le moteur Autodoc, SQL, Qdrant, OpenVINO et le Scheduler restent dans
`newicody/autodoc`.

## Installation rapide

### 1. Préparer les deux dépôts

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects

test -d "$AUTODOC/.git"

if test -d "$PROJECTS/.git"; then
  git -C "$PROJECTS" pull --ff-only
else
  git clone git@github.com:newicody/projects.git "$PROJECTS"
fi
```

### 2. Prévisualiser puis copier le bundle

```bash
SRC="$AUTODOC/templates/github/projects-repository"
DST="$PROJECTS"

rsync -aivn --exclude README.md "$SRC"/ "$DST"/
```

Contrôler la liste, puis appliquer la même copie sans `n` :

```bash
rsync -aiv --exclude README.md "$SRC"/ "$DST"/
cp "$SRC/README.md" "$DST/AUTODOC_PROJECTS_BUNDLE.md"
```

**Ne pas utiliser `--delete`** : le dépôt Projects peut contenir des fichiers
qui ne viennent pas d’Autodoc.

### 3. Contrôler, commit et push

```bash
git -C "$DST" status --short
git -C "$DST" diff -- \
  .github scripts projectv2_views.json INSTALLATION.md \
  PROJECT_BOARD_TEMPLATE.md AUTODOC_PROJECTS_BUNDLE.md

git -C "$DST" add .
git -C "$DST" commit -m "Install/update Autodoc Projects bundle"
git -C "$DST" push
```

## Réglages GitHub à faire une fois

Dans `newicody/projects → Settings → Actions → General`, autoriser les Actions
utilisées par le workflow :

```text
actions/checkout@v6
actions/setup-python@v6
actions/cache@v4
actions/upload-artifact@v7
```

Créer la variable de dépôt avec le défaut sûr :

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --body false \
  --repo newicody/projects
```

Aucun secret Actions n’est requis par défaut.

Cette valeur est le défaut d'installation. Ne pas créer de secret `AUTODOC_COPILOT_TOKEN` : le workflow actuel utilise uniquement le token éphémère fourni par GitHub.

## Tokens : lequel utiliser et où le trouver ?

| Nom | Où il existe | Action à faire |
|---|---|---|
| `GITHUB_TOKEN` dans GitHub Actions | Créé automatiquement pour chaque job | Rien à créer ni à copier |
| `GITHUB_TOKEN` en local | Variable attendue par certains outils Autodoc | La remplir depuis l’authentification `gh` |
| `AUTODOC_PROJECT_TOKEN` | Simple nom de variable locale pour les scripts ProjectV2 | Réutiliser le même token local |
| `AUTODOC_COPILOT_TOKEN` | Ancien nom, non utilisé par le workflow actuel | Ne pas le créer |

### Méthode recommandée avec GitHub CLI

```bash
gh auth status
gh auth refresh -h github.com -s project

export GITHUB_TOKEN="$(gh auth token -h github.com)"
export AUTODOC_PROJECT_TOKEN="$GITHUB_TOKEN"

test -n "$GITHUB_TOKEN"
```

Ne pas afficher le token avec `echo`, ne pas l’écrire dans un fichier versionné
et fermer le shell après les opérations sensibles :

```bash
unset AUTODOC_PROJECT_TOKEN GITHUB_TOKEN
```

Le scope `project` permet les lectures et mutations ProjectV2. Le compte actif
doit aussi avoir accès à `newicody/projects`. `gh auth status` permet de vérifier
le compte utilisé.

### Création manuelle seulement si `gh` n’est pas utilisable

Dans GitHub :

```text
Photo de profil
→ Settings
→ Developer settings
→ Personal access tokens
→ Tokens (classic)
→ Generate new token (classic)
```

Choisir une expiration et les scopes :

```text
project
repo
```

Pour un usage strictement en lecture, `read:project` remplace `project`. Le
bundle utilise toutefois des mutations ProjectV2 explicitement autorisées, donc
l’installation complète nécessite `project`.

Charger le token sans le mettre dans l’historique du shell :

```bash
read -rsp 'Token GitHub: ' TOKEN
printf '\n'
export GITHUB_TOKEN="$TOKEN"
export AUTODOC_PROJECT_TOKEN="$TOKEN"
unset TOKEN
```

Pour le ProjectV2 utilisateur `newicody` numéro `3`, un PAT classique reste la
solution la plus compatible. Certains endpoints de champs de Projects
utilisateur ne prennent pas encore en charge les PAT fine-grained.

## Installer les champs et vues ProjectV2

Depuis le dépôt Projects :

```bash
cd "$PROJECTS"

python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --format json
```

Le premier passage est un preview. Contrôler :

```text
missing_fields
missing_views
field_option_drift
manual_layout_steps
plan_digest
```

Pour appliquer le plan accepté :

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_CONFIGURATION_ALLOWED=true

python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --execute \
  --confirm-plan-digest '<PLAN_DIGEST>' \
  --format json
```

Le script crée uniquement ce qui manque. Il ne supprime rien. Les dérives
d’options ou de mise en page restent visibles pour contrôle manuel.

Vérifier ensuite dans l’interface :

```text
vues : Recherches, Résultats, Copilot, Historique,
       Révisions spécialistes, etc.

champs spécialistes :
Spécialiste
Révision spécialiste
Capacité proposée
Action capacité
Décision capacité
Statut révision
Référence SQL
Digest décision
Laboratoire
```

## Vérifier les formulaires et le workflow

Fichiers importants :

```text
.github/workflows/autodoc-controlled-research.yml
.github/ISSUE_TEMPLATE/specialist-capability-growth.yml
projectv2_views.json
```

Le workflow actuel utilise le token éphémère `${{ github.token }}` comme
`GITHUB_TOKEN`, avec les permissions minimales déclarées dans le YAML. Il ne
nécessite pas `AUTODOC_COPILOT_TOKEN`.

Le workflow ne publie pas lui-même son avis : il produit les artefacts de demande et d’avis consultatif. Toute publication vers une Issue reste soumise à l’adapter contrôlé, au preview, au digest et à la décision opérateur.

Contrôles rapides :

```bash
gh variable get AUTODOC_COPILOT_ADVISORY_ENABLED \
  --repo newicody/projects

gh secret list --repo newicody/projects
gh workflow view autodoc-controlled-research.yml \
  --repo newicody/projects
```

La liste des secrets peut rester vide.

## Connecteurs locaux Autodoc

```bash
cd "$AUTODOC"
mkdir -p .var/config

test -f .var/config/github_project_v2_query_only.ini || \
  cp config/github_project_v2_query_only.example.ini \
     .var/config/github_project_v2_query_only.ini

test -f .var/config/github_projects_workflow_dispatch.ini || \
  cp config/github_projects_workflow_dispatch.example.ini \
     .var/config/github_projects_workflow_dispatch.ini
```

Vérification sans mutation :

Cette vérification query-only ne déclenche aucun dispatch et ne réalise aucune mutation distante.

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config .var/config/github_project_v2_query_only.ini \
  --format summary

PYTHONPATH=src:. python \
  tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py \
  --config .var/config/github_projects_workflow_dispatch.ini \
  --format json
```

Une exécution distante exige toujours les verrous locaux, `--execute` et la
décision de politique exacte. Les outils restent preview-first.

## Copilot optionnel

Le défaut reste :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=false
```

Après validation complète du workflow sans Copilot, l’option peut être activée :

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --body true \
  --repo newicody/projects
```

Le workflow utilise alors son `GITHUB_TOKEN` automatique avec
`copilot-requests: write`. Copilot reste consultatif et une indisponibilité ne
doit pas remplacer la requête autoritative.

## Commandes avancées conservées

Les opérations avancées restent dans Autodoc et ne sont pas nécessaires pour la
copie initiale :

```text
tools/publish_github_advisory_issue_comment_0281.py
tools/verify_specialists_laboratories_live_path_evidence_0284.py
scripts/project_copilot_advisory_fields.py
```

Elles restent soumises au preview, au `plan_digest`, à `--execute` et à une
décision opérateur explicite.

## Mise à jour ultérieure

Toujours reprendre les mêmes deux commandes :

```bash
rsync -aivn --exclude README.md "$SRC"/ "$DST"/
rsync -aiv  --exclude README.md "$SRC"/ "$DST"/
```

Puis contrôler `git diff`, commit et push. Ne pas utiliser `--delete`.

## Dépannage rapide

| Erreur | Correction |
|---|---|
| `401 Bad credentials` | `gh auth status`, puis reconnecter `gh auth login` |
| accès ProjectV2 refusé | `gh auth refresh -s project` |
| mauvaise identité GitHub | `gh auth switch`, puis `gh auth status` |
| Action interdite | autoriser précisément les quatre Actions listées plus haut |
| Copilot indisponible | remettre `AUTODOC_COPILOT_ADVISORY_ENABLED=false` |
| champ/vue déjà présent avec dérive | corriger manuellement après lecture du preview |

## Repères historiques conservés

Ces lignes restent présentes pour les règles cumulatives et l’historique :

- Version du guide : `0286-r4`.
- Version du guide : `0286-r3`.
- Version du guide : `0284-r9`.
- Version du guide : `0284-r1-r5`.

Évolutions principales :

| Phase | Évolution |
|---|---|
| `0284` | séparation lecture query-only, dispatch et publication contrôlée |
| `0286-r3` | formulaire de demande d’évolution de capacité |
| `0286-r4` | champs et vue `Révisions spécialistes` |
| `0287-r5` | simplification du guide et clarification des tokens |

## Compatibilité cumulative 0287-r5-r2-r2

Repère conservé pour la règle de simplification :

```text
Version actuelle du guide : `0287-r5`.
```

Après un premier dispatch validé sans Copilot, l’activation consultative
explicite donne :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=true
```

Repère historique de la preuve opérationnelle :

| Phase | Évolution |
|---|---|
| `0284-r9` | Vérification corrélée du chemin réel sans mutation. |

## Avis Copilot visibles

Le workflow produit l’artefact sans s’auto-publier. Le mode opératoire
preview-first est dans `COPILOT_ADVISORY_PUBLICATION.md`.
