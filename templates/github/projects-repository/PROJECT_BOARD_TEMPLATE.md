# Interface GitHub finale — dépôt `newicody/projects`

## Principe

Le Board principal affiche uniquement le résultat courant de chaque recherche.
Les tickets, groupes, résultats liés, dépôts, fichiers et URL restent des
références dans l'issue et ne sont jamais dupliqués sous forme de cartes.

Une carte cliquée ouvre le panneau latéral natif de l'issue. La carte présente
un résumé court ; le panneau contient le résultat complet, l'avis Copilot et
les sources repliables.

## Champs du Project

### `Status`

```text
Recherche
Développement
Production
En cours
Terminé
Drop
```

Le passage vers `En cours` reste l'acte de lancement :

```text
Recherche      → En cours
Développement → En cours
Production     → En cours
```

`Drop` ne déclenche aucun traitement.

### `Thème`

Groupe horizontal facultatif et purement humain.

### `Type`

```text
Recherche
Actualisation
```

- `Recherche` transforme l'issue d'action en nouveau résultat courant ;
- `Actualisation` ajoute un UPDATE sous un résultat existant.

### `Affichage`

```text
Résultat courant
Historique
Action
Groupe
```

### Champs visibles de résultat

```text
Résumé
Avis Copilot
Serveur
Copilot
Dernière mise à jour
```

Valeurs recommandées :

```text
Serveur : En attente, En cours, Terminé, Partiel, Erreur
Copilot : Non demandé, En attente, Terminé, Erreur
```

Les états doivent être écrits en texte et ne jamais dépendre uniquement des
couleurs.

## Vue `Résultats`

```text
Layout       : Board
Column field : Status
Group by     : Thème
Filter       : Affichage = Résultat courant
Fields       : Résumé, Avis Copilot, Serveur, Copilot, Dernière mise à jour
```

Le résumé serveur et le résumé Copilot restent courts et lisibles sur la
carte. Le résultat complet est accessible en cliquant sur la carte.

## Vue `Actions serveur`

```text
Layout       : Board
Column field : Status
Group by     : Thème
Filter       : Affichage = Action
Fields       : Type, Serveur, Copilot, Dernière mise à jour
```

Une nouvelle recherche et une actualisation commencent comme actions.

```text
Type = Recherche
→ après succès, la même issue devient Résultat courant

Type = Actualisation
→ après succès, le résultat cible reçoit un UPDATE
→ l'issue d'action est fermée
```

## Vue `Historique`

```text
Layout : Table
Filter : Affichage = Historique
Fields : Thème, Type, Dernière mise à jour
```

## Vue `Groupes`

```text
Layout : Table
Filter : Affichage = Groupe
```

Un groupe est uniquement une référence de contexte réutilisable.

## Vue `Tous`

```text
Layout : Table
Filter : aucun
```

Cette vue sert au diagnostic et n'ajoute aucune sémantique d'exécution.

## Nouvelle recherche

Le formulaire distingue :

```text
result_parent_ref
related_result_refs[]
group_refs[]
issue_refs[]
repository_sources[]
attachment_refs[]
external_links[]
```

Le parent établit une filiation unique. Les résultats liés sont de simples
sources par lien. Ils ne sont pas copiés dans le Board.

Après réussite, l'issue de recherche devient le nouveau résultat courant. Si
un parent est indiqué, l'ancien résultat devient `Historique`.

## Actualisation

Une actualisation cible obligatoirement un résultat existant. Elle ne crée pas
un nouveau parent. Le serveur ajoute sous l'existant un commentaire immuable :

```text
UPDATE — date et heure
nouveaux paramètres
nouvelles références
résultat serveur
avis Copilot
artefacts et provenance
```

Les champs `Résumé`, `Avis Copilot`, `Serveur`, `Copilot` et
`Dernière mise à jour` reflètent le dernier état, tandis que les commentaires
conservent l'historique complet.

## Fin automatique

Après publication complète :

```text
fermer l'issue d'action
→ workflow Project « Item closed »
→ Status = Terminé
```

Si le serveur échoue, l'issue reste ouverte. Si Copilot a été demandé et
échoue, le résultat est marqué `Partiel` et l'action reste ouverte jusqu'à
décision explicite.

## Déclenchement

Le détecteur local reste borné et idempotent :

```text
snapshot ProjectV2 query-only
→ diff local
→ transition vers En cours
→ workflow_dispatch dans newicody/projects
```

Cette phase d'interface n'ajoute encore aucune publication ou mutation GitHub.
