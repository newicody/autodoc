# Installation cumulative de `newicody/projects`

Ce document est le mode opératoire cumulatif du bundle GitHub fourni par
Autodoc. Il doit être mis à jour chaque fois que la copie, les Actions, les
variables, les secrets, les vues ou les contrats du dépôt Projects évoluent.

Version du guide : `0284-r1-r5`.

## Frontière

```text
newicody/autodoc
  ├── moteur local, connecteurs et bundle source
  └── templates/github/projects-repository/
                         │ copie contrôlée
                         ▼
newicody/projects
  ├── Issues et ProjectV2
  ├── formulaires
  ├── workflows Actions
  └── artefacts et avis Copilot consultatifs
```

Le dépôt Projects n'embarque ni Scheduler, ni SQL, ni OpenVINO, ni Qdrant.
Autodoc ne doit pas activer à sa racine les workflows contenus dans ce bundle.

## 1. Préparer le dépôt local Projects

```bash
cd /home/eric/projet/git
git clone git@github.com:newicody/projects.git projects
```

Pour une copie déjà présente :

```bash
git -C /home/eric/projet/git/projects status --short
git -C /home/eric/projet/git/projects pull --ff-only
```

## 2. Simuler puis copier le bundle

```bash
SRC=/home/eric/projet/git/autodoc/templates/github/projects-repository
DST=/home/eric/projet/git/projects

rsync -aivn \
  --exclude README.md \
  "$SRC"/ \
  "$DST"/
```

Après contrôle du dry-run :

```bash
rsync -aiv \
  --exclude README.md \
  "$SRC"/ \
  "$DST"/

cp "$SRC/README.md" "$DST/AUTODOC_PROJECTS_BUNDLE.md"
```

Ne pas utiliser `--delete` : le dépôt Projects peut contenir des éléments qui
ne proviennent pas du bundle Autodoc.

## 3. Contrôler les fichiers copiés

```bash
git -C "$DST" status --short
git -C "$DST" diff -- \
  .github \
  scripts \
  projectv2_views.json \
  INSTALLATION.md \
  PROJECT_BOARD_TEMPLATE.md \
  RESULT_UPDATE_PRESENTATION_CONTRACT.md \
  AUTODOC_PROJECTS_BUNDLE.md
```

Le workflow actif attendu est :

```text
newicody/projects/.github/workflows/autodoc-controlled-research.yml
```

La copie conservée sous
`newicody/autodoc/templates/github/projects-repository/` n'est pas active dans
Autodoc.

## 4. Configurer GitHub Actions dans `newicody/projects`

Dans `Settings → Actions → General`, autoriser les Actions GitHub utilisées par
le workflow :

```text
actions/checkout@v6
actions/setup-python@v6
actions/cache@v4
actions/upload-artifact@v7
```

La politique peut rester restrictive en autorisant précisément ces Actions.
Une phase ultérieure pourra les verrouiller par SHA complet.

Créer d'abord la variable de dépôt avec la valeur sûre :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=false
```

Cette valeur est le défaut d'installation. Elle permet de valider le dispatch,
la requête autoritative et le manifeste sans rendre Copilot nécessaire. Le
workflow reste valide lorsqu'aucun artefact consultatif n'est produit.

Le workflow utilise le `GITHUB_TOKEN` éphémère avec la permission
`copilot-requests: write`. Ne pas créer de secret `AUTODOC_COPILOT_TOKEN` et ne
pas enregistrer de token Copilot durable dans le dépôt.

Après un premier dispatch validé sans Copilot, vérifier que la politique GitHub
autorise Copilot CLI pour ce dépôt, puis activer explicitement l'avis
consultatif :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=true
```

Copilot reste optionnel et non autoritatif. Si son exécution est indisponible ou
invalide, le workflow conserve la requête autoritative et le manifeste sans
bloquer le cycle.

Le workflow produit les artefacts sans se donner de permission d'écriture sur
les Issues ou ProjectV2. La publication et la projection sont déclenchées
séparément après décision opérateur, selon les sections 8 et 9.

## 5. Configurer les connecteurs locaux Autodoc

La lecture ProjectV2 et l'écriture `workflow_dispatch` utilisent désormais des
fichiers séparés. Deux déclencheurs distincts ne doivent pas être confondus :

- `github_action_on_ticket_event` décrit le pont de lecture d'artefacts et ne
  donne aucune autorisation de mutation ;
- `workflow_dispatch` est la commande sortante explicite vers
  `newicody/projects`, portée uniquement par sa configuration dédiée.

Fichiers à préparer :

```bash
cd /home/eric/projet/git/autodoc
mkdir -p .var/config

cp config/github_project_v2_query_only.example.ini \
  .var/config/github_project_v2_query_only.ini

cp config/github_projects_workflow_dispatch.example.ini \
  .var/config/github_projects_workflow_dispatch.ini
```

Dans la copie query-only, vérifier :

```text
project.owner = newicody
project.number = 3
project.id = PVT_kwHOA3ouXM4Ba3Ar
safety.query_only = true
safety.graphql_mutation_allowed = false
safety.allow_workflow_dispatch = false
safety.allow_remote_mutation = false
```

Dans la copie dispatch, conserver les deux verrous à `false` pendant les tests
sans effet. Les passer explicitement à `true` uniquement pour une exécution
acceptée :

```text
allow_workflow_dispatch = true
allow_remote_mutation = true
```

Le token reste dans l'environnement :

```bash
export GITHUB_TOKEN='...'
```

Aucune valeur de secret ne doit être écrite dans un fichier versionné.

## 6. Vérifier sans mutation

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config .var/config/github_project_v2_query_only.ini \
  --format summary
```

Puis vérifier le plan de dispatch sans `--execute`. Le chemin `--config` est
obligatoire dans cette procédure : le patch de séparation ne modifie pas le
défaut historique du CLI déjà présent dans Autodoc.

```bash
PYTHONPATH=src:. python \
  tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py \
  --config .var/config/github_projects_workflow_dispatch.ini \
  --format json
```

## 7. Exécuter un dispatch accepté

Après validation du change set et activation locale des deux verrous :

```bash
PYTHONPATH=src:. python \
  tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py \
  --config .var/config/github_projects_workflow_dispatch.ini \
  --execute \
  --policy-decision-id policy:0284:projects-workflow-dispatch \
  --format json
```

Le dispatch cible exclusivement :

```text
newicody/projects/.github/workflows/autodoc-controlled-research.yml
```

## Historique du guide

| Phase | Évolution |
|---|---|
| `0284-r1-r3` | Création du guide cumulatif et séparation query-only / dispatch. |
| `0284-r1-r3-r4` | Correction du contrat de déclenchement : lecture d’artefacts et dispatch sortant restent séparés. |

## 8. Installer les champs et les vues ProjectV2

Après la copie du bundle, `projectv2_views.json` appartient au dépôt
`newicody/projects`. Il décrit les champs et les vues sans devenir une
configuration runtime d'Autodoc.

Créer un PAT classique autorisé pour Projects, puis le charger uniquement dans
l'environnement de la session d'installation :

```bash
cd /home/eric/projet/git/projects
export AUTODOC_PROJECT_TOKEN='...'
```

Le plan par défaut est sans mutation :

```bash
python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --format json
```

Contrôler le `plan_digest`, puis ouvrir les deux verrous seulement pour
l'application acceptée :

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_CONFIGURATION_ALLOWED=true

python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --execute \
  --confirm-plan-digest '<digest du plan>' \
  --format json
```

Le réconciliateur crée uniquement les champs et vues manquants. Il ne supprime
rien et ne réécrit pas une vue existante. Les options manquantes d'un champ
single-select existant sont signalées comme dérive et restent à corriger
manuellement.

L'API de création ne configure pas encore les regroupements détaillés. Après
création, appliquer dans l'interface GitHub les réglages signalés par le plan :

```text
Recherches : colonnes Status, groupement Thème
Résultats  : colonnes Status, groupement Thème
```

## 9. Publier le retour Copilot après décision opérateur

Le workflow ne publie pas lui-même son avis. Le commentaire complet réutilise
l'adaptateur contrôlé déjà présent dans Autodoc :

```text
tools/publish_github_advisory_issue_comment_0281.py
```

Il doit d'abord être exécuté en prévisualisation, puis avec `--execute` et le
`plan_digest` exact après validation opérateur. Cette publication conserve un
marqueur idempotent et bloque les collisions.

Une fois le commentaire publié, projeter le dernier état consultatif dans les
champs de la carte depuis la copie locale de `newicody/projects` :

```bash
cd /home/eric/projet/git/projects
export AUTODOC_PROJECT_TOKEN='...'

python scripts/project_copilot_advisory_fields.py \
  --config projectv2_views.json \
  --preview /chemin/vers/publication_preview.json \
  --repository newicody/projects \
  --issue-number '<numéro>' \
  --policy-decision-id policy:0284:copilot-projectv2-preview \
  --operator-decision approve \
  --updated-date '<YYYY-MM-DD>' \
  --format json
```

Après contrôle du digest :

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python scripts/project_copilot_advisory_fields.py \
  --config projectv2_views.json \
  --preview /chemin/vers/publication_preview.json \
  --repository newicody/projects \
  --issue-number '<numéro>' \
  --policy-decision-id policy:0284:copilot-projectv2-preview \
  --operator-decision approve \
  --updated-date '<YYYY-MM-DD>' \
  --execute \
  --confirm-plan-digest '<digest du plan>' \
  --format json
```

La projection peut écrire uniquement :

```text
Copilot
Avis Copilot
Route Copilot
Confiance Copilot
Dernière mise à jour
Artefact
Cycle
```

Elle ne modifie jamais `Résumé`, `Serveur`, la requête autoritative ou la
décision opérateur.

## Historique du guide — complément

| Phase | Évolution |
|---|---|
| `0284-r1-r4` | Configuration versionnée des champs/vues et projection contrôlée du retour Copilot. |
| `0284-r1-r5` | Démarrage Copilot désactivé, authentification éphémère et comportement optionnel explicités. |
