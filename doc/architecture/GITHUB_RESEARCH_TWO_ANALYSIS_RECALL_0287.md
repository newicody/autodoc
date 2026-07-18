# Rappel et réhydratation des deux analyses sans synthèse

## But

Cette unité utilise les deux projections r16-r13 pour retrouver exactement les
deux objets SQL r16-r12 :

```text
requête de liaison
→ embedding OpenVINO/E5 avec rôle `query:`
→ recherche Qdrant dense bornée
→ recherche Qdrant sparse bornée
→ fusion par rang réciproque
→ regroupement par `source_ref`
→ deux références SQL attendues
→ réhydratation des deux objets depuis PostgreSQL
```

## Réutilisation

La fonction `execute_love_async_hybrid_retrieval` reste l’unique chemin
d’exécution. Elle attend l’embedder asynchrone injecté puis délègue à
`execute_hybrid_retrieval`, qui conserve :

- le profil canonique de collection;
- la validation du vecteur dense;
- la requête sparse déterministe;
- le contrôle des filtres;
- la fusion dense/sparse;
- la vérification de l’appartenance à la révision SQL;
- la comparaison des digests Qdrant/SQL;
- la réhydratation autoritative.

Aucun client Qdrant, runtime OpenVINO ou magasin SQL n’est créé.

## Périmètre exact

Le plan reprend directement les scopes utilisés par r16-r13 :

- révision SQL;
- branche;
- projet;
- conversation;
- laboratoire;
- périmètre de sécurité;
- noms des vecteurs dense et sparse;
- collection Qdrant attestée.

Le résultat est valide seulement lorsque l’ensemble rappelé est exactement égal
aux deux `context-object:*` persistés par r16-r12.

## Données sérialisées

Les deux corps autoritatifs sont présents en mémoire pour l’unité de synthèse
suivante. Le reçu sérialisable contient uniquement :

- références SQL;
- digests;
- titres;
- types de média;
- scores fusionnés;
- rangs dense et sparse;
- preuve de réhydratation SQL.

Il ne contient ni corps, ni texte de requête, ni vecteur.

## Limites

Cette unité :

- n’écrit pas dans Qdrant;
- n’écrit pas dans SQL;
- ne reprojette aucune analyse;
- ne construit aucune synthèse;
- ne modifie pas GitHub;
- ne crée aucun Scheduler;
- ne relance aucun spécialiste.

La prochaine unité consommera les deux objets réhydratés et produira une
synthèse de liaison distincte, sans effacer ni modifier les analyses sources.
