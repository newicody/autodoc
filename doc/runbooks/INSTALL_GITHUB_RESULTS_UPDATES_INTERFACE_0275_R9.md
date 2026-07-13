# Installer l'interface Résultats / Actualisations — 0275-r9

## 1. Copier les formulaires

Après validation complète du patch Autodoc :

```bash
cd /home/eric/projet/git/projects

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/ISSUE_TEMPLATE/research.yml \
  .github/ISSUE_TEMPLATE/

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/ISSUE_TEMPLATE/update.yml \
  .github/ISSUE_TEMPLATE/

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/ISSUE_TEMPLATE/theme.yml \
  .github/ISSUE_TEMPLATE/

rm -f .github/ISSUE_TEMPLATE/transversal-event.yml

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/PROJECT_BOARD_TEMPLATE.md \
  .

cp \
  /home/eric/projet/git/autodoc/templates/github/projects-repository/RESULT_UPDATE_PRESENTATION_CONTRACT.md \
  .
```

Vérifier :

```bash
git diff --check
git status --short
```

Puis :

```bash
git add .github/ISSUE_TEMPLATE \
  PROJECT_BOARD_TEMPLATE.md \
  RESULT_UPDATE_PRESENTATION_CONTRACT.md

git commit -m "install results and updates github interface"
git push origin master
```

## 2. Créer les champs

Dans le Project personnel, conserver :

```text
Status
Thème
```

Ajouter :

```text
Type                  Single select
Affichage             Single select
Résumé                Text
Avis Copilot          Text
Serveur               Single select
Copilot               Single select
Dernière mise à jour  Date
```

Valeurs :

```text
Type       : Recherche, Actualisation
Affichage  : Résultat courant, Historique, Action, Groupe
Serveur    : En attente, En cours, Terminé, Partiel, Erreur
Copilot    : Non demandé, En attente, Terminé, Erreur
```

## 3. Créer les vues

### Résultats

```text
Layout       : Board
Column field : Status
Group by     : Thème
Filter       : Affichage = Résultat courant
Fields       : Résumé, Avis Copilot, Serveur, Copilot, Dernière mise à jour
```

### Actions serveur

```text
Layout       : Board
Column field : Status
Group by     : Thème
Filter       : Affichage = Action
Fields       : Type, Serveur, Copilot, Dernière mise à jour
```

### Historique

```text
Layout : Table
Filter : Affichage = Historique
```

### Groupes

```text
Layout : Table
Filter : Affichage = Groupe
```

### Tous

```text
Layout : Table
Filter : aucun
```

## 4. Configurer la fermeture

Dans les workflows intégrés du Project :

```text
Item closed
→ Set Status to Terminé
→ Save and turn on workflow
```

Le publisher futur fermera uniquement une action complètement publiée.

## 5. Tester les formulaires

Dans `newicody/projects → Issues → New issue`, vérifier :

```text
Nouvelle recherche
Actualiser un résultat
Nouveau groupe de contexte
```

Le formulaire `Nouvelle recherche transversale liée` ne doit plus apparaître.

## 6. Limites

Cette phase ne remplit pas encore automatiquement les champs Project et ne
publie aucun résultat. Elle verrouille l'interface avant le collecteur et le
publisher contrôlé.
