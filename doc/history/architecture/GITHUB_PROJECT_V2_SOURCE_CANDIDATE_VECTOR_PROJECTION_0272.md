# Projection vectorielle contrôlée des SourceCandidate ProjectV2 — 0272-r9

## Décision

0272-r9 compose les surfaces existantes sans créer de moteur vectoriel parallèle :

```text
record durable r8
-> lecture SQL existante
-> 0261 OpenVINO/E5 passage
-> EmbeddingSpaceProfile
-> gate de compatibilité
-> 0262 projection Qdrant
-> payload.sql_ref + payload.embedding_profile_ref
```

SQL reste l'autorité durable. E5 produit un vecteur et Qdrant indexe cette
projection ; aucun des deux ne remplace le contenu SQL.

## Profil d'espace vectoriel

`EmbeddingSpaceProfile` rend explicites les propriétés qui doivent être
identiques entre ingestion et recherche :

- backend et modèle ;
- révision déclarée du modèle ;
- tokenizer ;
- pooling ;
- normalisation ;
- dimension ;
- distance Qdrant ;
- rôle et politique de préfixes E5 ;
- max_length, padding, troncature et présence des token_type_ids ;
- collection cible ;
- digest de l'artefact modèle lorsqu'il est disponible.

Le profil verrouille actuellement `max_length=128`, `padding=max_length`,
`truncation=longest_first`, le pooling moyen, les `token_type_ids`, des vecteurs
normalisés de dimension 384 et la distance Cosine, conformément au chemin E5
existant. Le `profile_ref` est déterministe. Tout changement de ces propriétés produit un
nouvel espace. Un embedding incompatible est refusé avant l'appel Qdrant.

La première version ne calcule pas elle-même le digest des fichiers OpenVINO.
Lorsqu'un digest `sha256:*` est déclaré, il doit déjà être porté par les
métadonnées d'embedding et il est vérifié strictement. La collecte du digest du
modèle local pourra être ajoutée à la readiness sans modifier la frontière r9.

## Laboratoires externes

Un laboratoire futur ne peut pas injecter directement son propre vecteur dans
la collection E5 Autodoc. Il doit fournir un artefact texte ou structuré,
persisté dans SQL, puis ré-embeddé par le profil local. Un espace externe peut
être conservé séparément avec un autre profil et une autre collection ou un
named vector explicitement décidé.

## Frontières

```text
SQL read                  = autorisé
SQL write                 = absent dans r9
OpenVINO/E5               = explicite en --execute
Qdrant write              = explicite en --execute
GitHub mutation           = fermée
laboratory selection      = fermée
Scheduler.run             = inchangé
ControlProxy / RouteProxy = inchangés
SHM                        = non touchée
```

Le client Qdrant réel reste confiné à la CLI et réutilise la membrane 0271.
Le module cœur r9 importe seulement les contrats 0261/0262.

## Suite

### 0272-r10 — smoke durable + projection + recall

Composer r6, r7, r8 et r9, puis utiliser 0263/0271 pour rappeler uniquement les
`sql_ref` et vérifier la réhydratation SQL. Tester le replay et le refus d'un
profil incompatible.

### 0273-r1 — audit de réutilisation laboratoire

Après fermeture du smoke r10, auditer les contrats spécialistes, le cycle de
délibération, les registres 0242/0257/0258, les routes SHM, EventBus,
PassiveSupervisor et VisPy avant d'introduire l'identité d'un laboratoire.
