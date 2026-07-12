# Modèle de Project — dépôt `newicody/projects`

## Champs

### `Status`

Utiliser le champ GitHub par défaut et remplacer ses options par :

```text
Recherche
En cours
Terminé
Développement
Production
Drop
```

La colonne `En cours` est la commande opérateur. Le passage depuis une colonne
d'intention lance une seule exécution :

```text
Recherche      → En cours → requested_status = Recherche
Développement → En cours → requested_status = Développement
Production     → En cours → requested_status = Production
sans valeur    → En cours → requested_status = Recherche
```

Une carte qui reste dans `En cours` ne relance rien. Pour relancer un ticket
terminé, le replacer d'abord dans `Recherche`, `Développement` ou `Production`,
puis le glisser dans `En cours`.

### `Thème`

Champ facultatif utilisé pour les groupes horizontaux :

```text
Chalouf
Architecture réseau
Modèles d'inférence
Documentation
```

Ajouter les valeurs au fil des recherches. Ne pas créer de taxonomie serveur.

### Champs natifs de hiérarchie

Activer aussi dans les champs visibles du Project :

```text
Parent issue
Sub-issue progress
```

Le ticket `[Thème]` devient la boîte englobante. Les recherches du thème sont
ajoutées comme sous-issues de ce ticket. La parenté est humaine et visuelle :
elle ne choisit aucun laboratoire, backend ou route serveur.

## Vue `Recherches`

```text
Layout       : Board
Column field : Status
Group by     : Thème
```

Chaque valeur `Thème` forme une bande horizontale visible contenant ses cartes.
Cette vue reste pratique pour les recherches sans parent ou liées à plusieurs
thèmes.

## Vue `Boîtes de thèmes`

```text
Layout       : Board
Column field : Status
Group by     : Parent issue
Fields       : Parent issue, Sub-issue progress, Thème
```

Cette vue affiche les vraies boîtes hiérarchiques :

```text
[Thème] Chalouf
├── Recherche #12
├── Recherche #18
└── Événement lié #24
```

Un ticket ne possède qu'un parent principal. Les thèmes supplémentaires restent
inscrits dans le champ `Thème`, le corps du ticket ou les références de
l'événement transversal.

## Vue `Thèmes`

```text
Layout : Table
```

Afficher les tickets dont le titre commence par `[Thème]` et le champ
`Sub-issue progress`. Cette vue permet de maintenir les boîtes et de suivre leur
progression.

## Vue `Événements liés`

```text
Layout : Table
```

Afficher les tickets dont le titre commence par `[Événement lié]`. Chaque
événement est indépendant, tout en conservant ses références de provenance et
son éventuel `Parent issue`.

## Recherches sans thème

Les tickets sans thème gardent le champ `Thème` et `Parent issue` vides. Ils
restent visibles dans le groupe sans valeur ou dans une vue non groupée.

## Déclenchement

Le serveur local exécute une passe bornée :

```text
snapshot ProjectV2 query-only 0272
→ diff local de snapshots 0272
→ sélection des transitions vers En cours
→ workflow_dispatch dans newicody/projects
```

Le workflow reçoit :

```text
issue_number
requested_status
request_mode
parent_event_ref
```

Le Project et l'issue ne sont pas mutés par le détecteur. Seul le lancement
explicite du workflow Actions est autorisé.
