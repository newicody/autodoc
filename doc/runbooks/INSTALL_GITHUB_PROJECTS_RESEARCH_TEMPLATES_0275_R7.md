# Installer les formulaires et le workflow de `newicody/projects` — 0275-r7

## Préconditions

- 0275-r6 validé ;
- dépôt local `/home/eric/projet/git/projects` cloné depuis
  `git@github.com:newicody/projects.git` ;
- champ Project par défaut nommé `Status` ;
- champ facultatif `Thème` ;
- aucune clé ou token dans Git.

## 1. Copier le bundle

Depuis le dépôt Autodoc :

```bash
cd /home/eric/projet/git/projects

mkdir -p .github/ISSUE_TEMPLATE .github/workflows

cp /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/ISSUE_TEMPLATE/*.yml \
  .github/ISSUE_TEMPLATE/

cp /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml \
  .github/workflows/

cp /home/eric/projet/git/autodoc/templates/github/projects-repository/PROJECT_BOARD_TEMPLATE.md \
  PROJECT_BOARD_TEMPLATE.md
```

## 2. Vérifier les fichiers

```bash
find .github -maxdepth 3 -type f -print
git diff --check
git status --short
```

Attendu :

```text
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/research.yml
.github/ISSUE_TEMPLATE/theme.yml
.github/ISSUE_TEMPLATE/transversal-event.yml
.github/workflows/autodoc-controlled-research.yml
PROJECT_BOARD_TEMPLATE.md
```

## 3. Retirer l'ancien workflow automatique

Si le dépôt contient encore un workflow réagissant à `issues.opened` ou
`issues.edited`, le supprimer ou le désactiver avant le test.

Le workflow canonique 0275-r7 ne contient que :

```text
workflow_dispatch
```

## 4. Configurer Copilot désactivé

Dans le dépôt `newicody/projects` :

```text
Settings
→ Secrets and variables
→ Actions
→ Variables
```

Créer ou conserver :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED = false
```

Aucun secret n'est requis pour le premier test.

## 5. Commit et push

```bash
git add .github PROJECT_BOARD_TEMPLATE.md
git commit -m "install autodoc research issue templates"
git push origin master
```

## 6. Vérifier les formulaires

Dans GitHub :

```text
newicody/projects
→ Issues
→ New issue
```

Les trois choix doivent apparaître :

```text
Nouvelle recherche
Nouveau thème de recherche
Nouvelle recherche transversale liée
```

Créer une recherche de test et vérifier son auto-ajout au Project.

## 7. Configurer la vue

Dans le Project :

```text
Layout       : Board
Column field : Status
Group by     : Thème
```

Options `Status` :

```text
Recherche
En cours
Terminé
Développement
Production
Drop
```

Les tickets sans thème restent sans groupement thématique imposé.

## 8. Premier test contrôlé du workflow

Ouvrir :

```text
newicody/projects
→ Actions
→ Autodoc controlled research request
→ Run workflow
```

Entrer :

```text
issue_number     = numéro de l'issue de test
requested_status = Recherche
request_mode     = initial
parent_event_ref = vide
```

Le run doit produire :

```text
autodoc-authoritative-request
autodoc-dual-artifact-manifest
```

Aucune issue ni carte Project ne doit être modifiée.

## 9. Test d'une recherche transversale

Créer une issue avec `Nouvelle recherche transversale liée`, en ajoutant :

- une recherche d'origine ;
- plusieurs thèmes ;
- plusieurs tickets si nécessaire ;
- un événement parent facultatif.

Lancer ensuite le workflow avec :

```text
requested_status = Recherche
request_mode     = transversal
parent_event_ref = référence de l'événement parent, si elle existe
```

L'issue créée reste indépendante. Ses références dans le corps conservent sa
trace hiérarchique.

## 10. Limites de 0275-r7

Cette phase ne fournit pas encore :

- l'extraction typée des champs des formulaires ;
- le contrat enrichi cycles/thèmes/documents ;
- la lecture des commentaires ;
- le watcher automatique du champ `Status` ;
- le service OpenRC ;
- la mutation distante du Project.

Ces capacités restent séquencées dans 0275-r8 à 0275-r12.
