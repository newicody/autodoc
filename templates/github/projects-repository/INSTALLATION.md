# Installation cumulative de `newicody/projects`

Version du guide : `0287-r5-r1`.

Extension de contrat Copilot : `0287-r7-r2`.

Diagnostic exact vues/Actions : `0287-r7-r15-r2-r2`.

Correctif de compatibilité du guide : `0287-r7-r15-r2-r2-r1`.

Ce document est le mode opératoire cumulatif simplifié pour installer et mettre
à jour l’interface GitHub du projet. Il couvre les formulaires d’Issues, le
workflow Actions, les scripts et la configuration ProjectV2. Le moteur Autodoc,
SQL, Qdrant, OpenVINO et le Scheduler restent dans `newicody/autodoc`.

## 1. Copier le bundle

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects

test -d "$AUTODOC/.git"

if test -d "$PROJECTS/.git"; then
  git -C "$PROJECTS" pull --ff-only
else
  git clone git@github.com:newicody/projects.git "$PROJECTS"
fi

SRC="$AUTODOC/templates/github/projects-repository"
DST="$PROJECTS"

rsync -aivn --exclude README.md "$SRC"/ "$DST"/
```

Contrôler le preview, puis copier sans `n` :

```bash
rsync -aiv --exclude README.md "$SRC"/ "$DST"/
cp "$SRC/README.md" "$DST/AUTODOC_PROJECTS_BUNDLE.md"
```

**Ne pas utiliser `--delete`** : le dépôt Projects peut contenir des fichiers
qui ne viennent pas d’Autodoc.

Contrôler et publier :

```bash
git -C "$DST" status --short
git -C "$DST" diff -- \
  .github scripts projectv2_views.json INSTALLATION.md \
  PROJECT_BOARD_TEMPLATE.md AUTODOC_PROJECTS_BUNDLE.md

git -C "$DST" add .
git -C "$DST" commit -m "Install/update Autodoc Projects bundle"
git -C "$DST" push
```

## 2. Régler GitHub Actions avec le défaut sûr

Le workflow utilise les Actions GitHub officielles suivantes :

```text
actions/checkout@v6
actions/setup-python@v6
actions/cache@v4
actions/upload-artifact@v7
```

Lorsque `allowed_actions=selected`, vérifier que
`github_owned_allowed=true`. Si `sha_pinning_required=true`, remplacer les
versions majeures par les SHA complets autorisés.

```bash
gh api repos/newicody/projects/actions/permissions | jq .
gh api repos/newicody/projects/actions/permissions/selected-actions | jq .
```

Installer d’abord Copilot désactivé :

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --body false \
  --repo newicody/projects
```

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=false
```

Cette valeur est le défaut d'installation. Ne pas créer de secret `AUTODOC_COPILOT_TOKEN` : le workflow actuel utilise le token éphémère GitHub.

## 3. Authentification locale

| Nom | Usage |
|---|---|
| `GITHUB_TOKEN` du workflow | créé automatiquement pour chaque job |
| `GITHUB_TOKEN` local | authentification des outils locaux |
| `AUTODOC_PROJECT_TOKEN` | alias local du même token pour ProjectV2 |
| `AUTODOC_COPILOT_TOKEN` | ancien nom, non utilisé par le workflow actuel |

Méthode recommandée :

```bash
gh auth status
gh auth refresh -h github.com -s project

export GITHUB_TOKEN="$(gh auth token -h github.com)"
export AUTODOC_PROJECT_TOKEN="$GITHUB_TOKEN"

test -n "$GITHUB_TOKEN"
```

Ne pas afficher le token, ne pas le versionner, puis nettoyer le shell :

```bash
unset AUTODOC_PROJECT_TOKEN GITHUB_TOKEN
```

Pour l’installation complète, le compte actif doit avoir accès au dépôt et au
ProjectV2 utilisateur. Un PAT classique avec `project` et `repo` peut être
utilisé uniquement lorsque `gh auth` n’est pas disponible.

## 4. Installer les champs et vues ProjectV2

Depuis le dépôt Projects, enregistrer le preview exact :

```bash
cd "$PROJECTS"

python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --format json | \
tee /tmp/projectv2-configuration-preview.json
```

Contrôler au minimum :

```text
missing_fields
missing_views
field_option_drift
manual_layout_steps
plan_digest
```

Extraire le digest réellement calculé :

```bash
PLAN_DIGEST="$(
  jq -r '.plan_digest // empty' \
    /tmp/projectv2-configuration-preview.json
)"

test -n "$PLAN_DIGEST" || {
  echo "plan_digest absent du preview" >&2
  exit 1
}
```

Appliquer exactement ce plan :

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_CONFIGURATION_ALLOWED=true

python scripts/reconcile_projectv2_configuration.py \
  --config projectv2_views.json \
  --execute \
  --confirm-plan-digest "$PLAN_DIGEST" \
  --format json | \
tee /tmp/projectv2-configuration-execute.json
```

Le réconciliateur crée uniquement ce qui manque et ne supprime rien. Les
dérives de vues ou d’options restent soumises au readback et, lorsque l’API ne
permet pas leur correction, à une intervention dans l’interface GitHub.

Vérifier notamment :

```text
vues : Recherches, Résultats, Copilot, Historique,
       Révisions spécialistes

champs : Spécialiste, Révision spécialiste, Capacité proposée,
         Action capacité, Décision capacité, Statut révision,
         Référence SQL, Digest décision, Laboratoire
```

### Compatibilité des anciens exemples — ne pas exécuter

Les anciens repères suivants restent visibles pour les règles cumulatives, mais
ce ne sont pas des valeurs exécutables :

```text
--confirm-plan-digest '<PLAN_DIGEST>'
--confirm-plan-digest ''
```

Toujours utiliser `--confirm-plan-digest "$PLAN_DIGEST"` après le preview.

## 5. Audit exact des vues et de la readiness Actions

Le réconciliateur crée les ressources absentes. Le diagnostic read-only vérifie
aussi les vues existantes : layout, filtre, champs visibles et leur ordre,
colonnes et regroupement vertical.

```bash
python scripts/check_projects_bundle_readiness.py \
  --config projectv2_views.json \
  --workflow .github/workflows/autodoc-controlled-research.yml \
  --repository newicody/projects \
  --format json | \
tee /tmp/projects-bundle-readiness.json
```

Résumé :

```bash
jq '{
  projectv2_exact,
  authoritative_ready,
  copilot_ready,
  full_ready,
  workflow: {
    manual_dispatch_only: .workflow_readiness.workflow.manual_dispatch_only,
    blocked_actions: .workflow_readiness.blocked_actions,
    actions_policy: .workflow_readiness.actions_policy,
    copilot: .workflow_readiness.copilot
  },
  issues,
  warnings
}' /tmp/projects-bundle-readiness.json
```

Interprétation :

- `projectv2_exact` exige des champs, options et vues réellement conformes ;
- `authoritative_ready` couvre la requête et les artefacts obligatoires ;
- `copilot_ready` couvre la branche consultative optionnelle ;
- `full_ready` exige les deux chemins ;
- `manual_dispatch_only` documente le déclenchement actuel ;
- `github_owned_allowed` autorise les quatre Actions `actions/...` lorsque le
  pinning SHA complet n’est pas imposé.

Ce diagnostic ne crée aucun champ, aucune vue et aucun run. Il est query-only :
`remote_mutation_allowed=false` et `mutation_performed=false`.

## 6. Vérifier le workflow

Fichiers principaux :

```text
.github/workflows/autodoc-controlled-research.yml
.github/ISSUE_TEMPLATE/specialist-capability-growth.yml
projectv2_views.json
```

Le workflow utilise `${{ github.token }}` comme `GITHUB_TOKEN` et ne nécessite
pas `AUTODOC_COPILOT_TOKEN`.

Le workflow ne publie pas lui-même son avis : il produit les artefacts de demande et d’avis consultatif. La publication vers une Issue reste soumise au preview, au digest et à la décision opérateur.

```bash
gh variable get AUTODOC_COPILOT_ADVISORY_ENABLED \
  --repo newicody/projects
gh secret list --repo newicody/projects
gh workflow view autodoc-controlled-research.yml \
  --repo newicody/projects
```

La liste des secrets peut rester vide.

## 7. Connecteurs locaux Autodoc

```bash
cd "$AUTODOC"
mkdir -p .var/config

for name in \
  github_project_v2_query_only \
  github_projects_workflow_dispatch \
  love_actions_closed_loop
do
  test -f ".var/config/$name.ini" || \
    cp "config/$name.example.ini" ".var/config/$name.ini"
done
```

Cette vérification query-only ne déclenche aucun dispatch et ne réalise aucune
mutation distante :

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

### Preview final sans identifiants ProjectV2 manuels

`love_actions_closed_loop.example.ini` documente la factory runtime installée.
Le CLI résout automatiquement l’Issue, `PROJECT_ITEM_ID`, le champ et le projet.

```bash
python tools/run_love_actions_closed_loop_0287.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --candidate-decision promote \
  --format text
```

Le preview ne réalise aucune mutation distante. Les options d’identifiants et
`--runtime-factory` restent des overrides avancés.

## 8. Copilot optionnel

Après un premier dispatch validé sans Copilot, activer la branche consultative :

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --body true \
  --repo newicody/projects
```

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=true
```

Le workflow utilise alors son token automatique avec `copilot-requests: write`.
Copilot reste consultatif et ne remplace jamais la requête autoritative.

## 9. Mise à jour et dépannage

Pour une mise à jour, refaire le preview puis la copie `rsync`, contrôler le
diff, commit et push. Ne pas utiliser `--delete`.

| Erreur | Correction |
|---|---|
| `401 Bad credentials` | `gh auth status`, puis `gh auth login` |
| accès ProjectV2 refusé | `gh auth refresh -s project` |
| Action interdite | lire `blocked_actions` et la politique selected-Actions |
| Copilot absent | contrôler `copilot_ready`; `false` est valide si désactivé |
| vue en dérive | lire `field_checks` et `view_checks`, corriger puis relire |

## 10. Repères historiques et runbooks

Repères cumulatifs conservés :

- Version du guide : `0286-r4`.
- Version du guide : `0286-r3`.
- Version du guide : `0284-r9`.
- Version du guide : `0284-r1-r5`.
## Compatibilité cumulative 0287-r5-r2-r2

```text
Version actuelle du guide : `0287-r5`.
```

| Phase | Évolution |
|---|---|
| `0284` | lecture query-only, dispatch et publication contrôlée |
| `0284-r9` | preuve corrélée spécialistes/laboratoires sans mutation distante |
| `0286-r3` | formulaire d’évolution de capacité |
| `0286-r4` | champs et vue `Révisions spécialistes` |
| `0287-r5` | guide simplifié et tokens clarifiés |
| `0287-r7-r6` | publication Copilot v2 contrôlée |

Le mode opératoire de publication est dans
`COPILOT_ADVISORY_PUBLICATION.md`. Le contrat du premier avis est dans
`COPILOT_ADVISORY_V2.md`.

- `publish_github_advisory_issue_comment_0281.py` reste le repère de publication historique.
- `verify_specialists_laboratories_live_path_evidence_0284.py` reste le repère de preuve du chemin vivant.
