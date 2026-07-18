# Projection séparée des deux analyses dans Qdrant

## But

Les deux objets autoritatifs SQL issus de r16-r12 sont projetés séparément :

```text
objet SQL analyse conceptuelle
→ probe live existant
→ E5 multilingual-small, passage, 384 dimensions
→ point Qdrant 1
→ métadonnée de projection SQL 1
→ relecture du point 1
→ réhydratation SQL 1

objet SQL analyse relationnelle
→ probe live existant
→ E5 multilingual-small, passage, 384 dimensions
→ point Qdrant 2
→ métadonnée de projection SQL 2
→ relecture du point 2
→ réhydratation SQL 2
```

## Réutilisation stricte

Cette unité appelle deux fois :

- `build_love_live_projection_probe_plan`;
- `inspect_love_live_projection_probe`;
- `execute_love_live_projection_probe`.

Elle ne construit ni client Qdrant, ni runtime OpenVINO, ni connexion SQL.

## Autorité et payload

Le corps complet de chaque analyse reste dans PostgreSQL. Le payload Qdrant
reste limité aux références et métadonnées déjà contrôlées par le probe :

- `point_id`;
- `sql_ref`;
- `source_ref`;
- digest du contenu source;
- révision de contexte;
- références de conversation, projet, spécialiste et laboratoire.

Le résultat de cette unité ne contient ni vecteur, ni corps autoritatif.

## Deux identités

Les deux plans possèdent :

- deux `object_ref` SQL distincts;
- deux digests de plan distincts;
- deux points Qdrant distincts;
- deux métadonnées `VectorProjectionMetadata` distinctes.

Ils utilisent la même collection attestée, le même modèle E5 et la même
révision SQL, sans fusion de leurs contenus.

## Rejeu

Le premier point peut déjà avoir été écrit lorsqu’une erreur survient sur le
second. Le rejeu utilise les mêmes références déterministes et le probe
persistant idempotent. La paire n’est déclarée complète qu’après relecture et
réhydratation des deux points.

## Limites

Cette unité :

- ne recherche encore aucun voisin;
- ne construit aucune synthèse;
- ne modifie pas GitHub;
- ne crée aucun Scheduler;
- ne supprime aucun point;
- ne modifie aucun alias ou schéma de collection.

La prochaine unité effectuera un rappel hybride borné sur les deux projections,
réhydratera leurs objets depuis SQL puis construira la synthèse de liaison dans
une étape distincte.
