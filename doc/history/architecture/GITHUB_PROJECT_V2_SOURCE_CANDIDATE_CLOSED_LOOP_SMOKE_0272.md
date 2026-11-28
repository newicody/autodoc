# 0272-r10 — ProjectV2 SourceCandidate closed-loop smoke

## Objectif

Fermer le parcours local après la décision opérateur :

```text
r6 handoff
-> r7 gate promote/merge
-> r8 SQL durable + readback
-> query E5 compatibility
-> r9 passage projection
-> 0263 Qdrant recall refs-only
-> SQL rehydrate
-> replay r8 idempotent
-> rapport fermé r10
```

Le module r10 reçoit un **gate record r7 déjà produit**. Il ne reconstruit ni le
handoff r6 ni la décision r7, afin d'éviter une seconde surface de workflow.

## Composition réutilisée

- `github_project_v2_source_candidate_durable_consumer_0272` pour r8 ;
- `scheduler_managed_sql_ref_openvino_embedding_usage_0261` pour E5 ;
- `github_project_v2_source_candidate_vector_projection_0272` pour r9 ;
- `scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263` pour le recall ;
- `scheduler_managed_db_api_sql_context_store_binding_0260` pour la CLI ;
- `qdrant_client_projection_executor` 0271 à la frontière CLI seulement.

Aucun nouveau manager, orchestrateur, registre, bus ou runtime n'est créé.

## Verrou de l'espace E5

Le profil passage et le profil query possèdent des `profile_ref` distincts car
leur rôle E5 diffère, mais ils doivent partager un même
`embedding_space_family_ref`. Celui-ci exclut seulement le rôle de l'identité
et verrouille le reste : modèle, révision, tokenizer, pooling, dimension,
normalisation, distance, prétraitement et collection.

L'embedding query est produit et validé **avant toute écriture Qdrant**. Si le
modèle, le tokenizer, la dimension ou une autre propriété diverge, le smoke
s'arrête avant la projection.

## Autorités

```text
SQL     = autorité durable et réhydratation
E5      = représentation vectorielle locale contrôlée
Qdrant  = projection et recall de références SQL
GitHub  = source/workflow, aucune mutation dans r10
```

SQL reste l'autorité durable. Un résultat Qdrant n'est accepté que s'il rend le
`sql_ref` de la candidate puis si ce `sql_ref` est réhydraté depuis SQL.

## Replay

Après la première consommation r8, r10 rejoue immédiatement le même gate record.
Le deuxième passage doit être reconnu comme idempotent et ne doit pas produire
une seconde écriture SQL.

## Frontières fermées

- pas de mutation GitHub ;
- pas de laboratoire sélectionné ;
- pas de `LaboratoryManager` ;
- pas de modification de `Scheduler.run()` ;
- pas de ControlProxy/RouteProxy/SHM ;
- pas d'embedding externe accepté ;
- pas de nouvelle dépendance non-stdlib.

## Suite

La chaîne durable et vectorielle étant fermée, la suite est :

```text
0273-r1 audit de réutilisation laboratoire
-> 0273-r2 identité/visite minimale
-> 0273-r3 laboratoire fictif
```

Le laboratoire fictif devra exploiter cette chaîne sans devenir une autorité
SQL/Qdrant et sans créer un orchestrateur parallèle.

## Query-role correction

The 0261 request contract already accepts `role=query`, but its text builder was passage-only. r10 extends that existing surface so query requests produce `query:` text and the default OpenVINO/E5 path reports the effective query role. No parallel query embedding adapter is introduced.
