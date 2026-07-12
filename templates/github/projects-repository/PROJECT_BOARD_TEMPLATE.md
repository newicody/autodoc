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

### `Thème`

Champ facultatif utilisé pour les groupes horizontaux :

```text
Chalouf
Architecture réseau
Modèles d'inférence
Documentation
```

Ajouter les valeurs au fil des recherches. Ne pas créer de taxonomie serveur.

## Vue `Recherches`

```text
Layout       : Board
Column field : Status
Group by     : Thème
```

Le groupe horizontal est la boîte visuelle. Un ticket créé avec
`Nouveau thème de recherche` peut servir de boîte durable contenant les
références de plusieurs tickets du même thème.

## Vue `Thèmes`

```text
Layout : Table
```

Afficher les tickets dont le titre commence par `[Thème]`. Cette vue permet de
maintenir les boîtes thématiques et leurs listes de recherches.

## Vue `Événements liés`

```text
Layout : Table
```

Afficher les tickets dont le titre commence par `[Événement lié]`. Chaque
événement est indépendant, tout en conservant ses références de provenance.

## Recherches sans thème

Les tickets sans thème gardent le champ `Thème` vide. Ils restent visibles dans
le groupe sans valeur ou dans une vue non groupée.

## Déclenchement

Cette phase n'observe pas encore automatiquement les changements du Project.
Le workflow contrôlé est lancé manuellement ou par API avec :

```text
issue_number
requested_status
request_mode
parent_event_ref
```

Le détecteur idempotent de transitions `Status` est réservé à 0275-r10.
