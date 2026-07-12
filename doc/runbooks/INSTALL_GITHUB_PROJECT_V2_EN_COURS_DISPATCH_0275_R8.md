# Activer le drag `En cours`, Copilot et les boîtes de thèmes — 0275-r8

## Portée

Cette phase compose les surfaces ProjectV2 0272 déjà validées :

```text
snapshot query-only
→ diff local immutable
→ transition Status
→ workflow_dispatch gouverné
```

Elle n'ajoute ni Scheduler, ni daemon, ni boucle permanente, ni mutation du
Project ou des issues.

## 1. Mettre à jour `newicody/projects`

Après validation du patch Autodoc :

```bash
cd /home/eric/projet/git/projects

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml \
  .github/workflows/

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/PROJECT_BOARD_TEMPLATE.md \
  .

git diff --check
git diff -- .github/workflows PROJECT_BOARD_TEMPLATE.md
git add .github/workflows PROJECT_BOARD_TEMPLATE.md
git commit -m "enable copilot and en cours project workflow"
git push origin master
```

## 2. Activer Copilot

Dans `newicody/projects` :

```text
Settings
→ Secrets and variables
→ Actions
→ Variables
```

Définir :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED = true
```

Ne pas créer `AUTODOC_COPILOT_TOKEN`. Le workflow utilise le `GITHUB_TOKEN`
éphémère et la permission bornée `copilot-requests: write`.

## 3. Afficher les groupes comme boîtes

Dans le Project personnel, conserver la vue principale :

```text
Recherches
Layout       : Board
Column field : Status
Group by     : Thème
```

Elle affiche une bande horizontale par thème.

Activer les champs natifs :

```text
View
→ Fields
→ Parent issue
→ Sub-issue progress
```

Créer la vue :

```text
Boîtes de thèmes
Layout       : Board
Column field : Status
Group by     : Parent issue
Fields       : Parent issue, Sub-issue progress, Thème
```

Pour chaque boîte :

1. ouvrir ou créer une issue `[Thème] ...` ;
2. ouvrir son panneau `Sub-issues` ;
3. ajouter les issues de recherche existantes ;
4. conserver les thèmes secondaires dans le champ `Thème` ou dans le corps.

Une recherche sans thème peut rester sans parent.

## 4. Préparer le token local

Le processus local doit disposer d'un token lisant le Project personnel et
pouvant lancer le workflow du dépôt privé `newicody/projects`.

Le token reste uniquement dans l'environnement local :

```bash
export GITHUB_TOKEN='...'
```

Ne jamais l'écrire dans Git, l'INI ou un rapport.

## 5. Test manuel d'une passe

Premier passage de référence :

```bash
cd /home/eric/projet/git/autodoc

python tools/run_github_project_v2_en_cours_dispatch_once_0275_r8.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0275-r8:manual-baseline
```

Déplacer ensuite une carte :

```text
Recherche → En cours
```

puis relancer :

```bash
python tools/run_github_project_v2_en_cours_dispatch_once_0275_r8.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0275-r8:manual-drag-1
```

Résultat attendu :

```text
snapshot 0272 = vert
diff 0272 = transition Recherche → En cours
dispatch 0275-r8 = 1
workflow projects = vert
autodoc-authoritative-request = présent
autodoc-copilot-advisory = présent
autodoc-dual-artifact-manifest = présent
```

Relancer immédiatement la même commande avec un autre `policy_decision_id` ne
doit pas créer un second run pour la même transition.

## 6. Fréquence fcron

Après le test manuel, installer une passe bornée chaque minute :

```text
* * * * * cd /home/eric/projet/git/autodoc && \
  /home/eric/python/bin/python \
  tools/run_github_project_v2_en_cours_dispatch_once_0275_r8.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0275-r8:fcron-en-cours-dispatch
```

Le programme ne boucle pas. Chaque invocation effectue une seule passe et
l'état local empêche un double dispatch.

## 7. Règles de relance

```text
Recherche      → En cours = recherche
Développement → En cours = développement
Production     → En cours = production
```

`Terminé → En cours` et `Drop → En cours` sont ignorés. Replacer d'abord le
ticket dans une colonne d'intention.

## 8. Limites

0275-r8 ne :

- modifie pas automatiquement `Status` après le run ;
- ne publie pas encore le résultat dans l'issue ;
- n'installe pas de service OpenRC ;
- n'écrit ni SQL ni Qdrant ;
- ne modifie pas `Scheduler.run()`.
