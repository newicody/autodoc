# Consommateur durable des SourceCandidate ProjectV2 — 0272-r8

## Décision

0272-r8 ferme la transition entre le gate opérateur r7 et l'autorité SQL.
Il consomme uniquement un gate record immuable dont la décision est `promote`
ou `merge`, puis construit un enregistrement SQL déterministe de type
`github_artifact`.

```text
handoff r6
-> gate opérateur r7
-> gate record immuable
-> validation r8
-> SqlContextRecord existant
-> écriture SQL insert-if-absent
-> readback SQL obligatoire
-> DurableSourceCandidate laboratory-neutral
```

Aucun nouveau store, manager, orchestrateur, worker ou bus n'est ajouté.
Le chemin réutilise `context.sql_context_store`, le builder
`build_sql_context_record` et la découverte/binding 0260 de
`DbApiSqlContextStore`.

## Sémantique durable

Le `context_ref` SQL est dérivé du `gate_ref`. Une seconde consommation du même
gate devient un replay idempotent. Un contenu différent sous le même
`context_ref` est refusé comme collision immuable au lieu d'écraser l'autorité
locale.

Le mode `merge` est conservé avec son `target_context_id` dans les métadonnées.
0272-r8 ne fusionne pas silencieusement le contenu dans la cible : cette
opération nécessite un traitement de contexte explicite ultérieur.

L'enregistrement durable porte aussi deux états de transition :

```text
embedding_projection_state = pending
laboratory_assignment_state = unassigned
```

Ils ne déclenchent aucun effet. Ils indiquent seulement que la candidate durable
peut être projetée puis orientée plus tard.

## Frontières

0272-r8 autorise uniquement l'effet SQL explicite :

```text
SQL write/readback        = autorisé en --execute
OpenVINO/E5               = fermé
Qdrant                    = fermé
GitHub mutation           = fermée
Scheduler.run             = inchangé
ControlProxy / RouteProxy = inchangés
EventBus                  = non sollicité dans r8
laboratoire               = non sélectionné dans r8
```

SQL reste l'autorité durable. Le record produit est neutre vis-à-vis du futur
framework de laboratoire.

## Suite verrouillée

### 0272-r9 — profil vectoriel et projection contrôlée

La prochaine étape doit réutiliser 0261, 0262, 0263 et 0271 pour ajouter un
`EmbeddingSpaceProfile` explicite : modèle/révision, tokenizer, pooling,
normalisation, dimension, métrique, rôle E5 et collection cible. Le gate de
compatibilité doit refuser tout mélange d'espaces vectoriels avant Qdrant.

```text
SQL r8
-> EmbeddingSpaceProfile
-> OpenVINO/E5 passage
-> VectorCompatibilityGate
-> Qdrant payload.sql_ref
-> recall
-> SQL rehydrate
```

### 0272-r10 — smoke ProjectV2 durable + vectoriel

Le smoke doit composer r6, r7, r8 et r9 avec replay idempotent et vérification
SQL après recall.

### 0273-r1 — audit de réutilisation laboratoire

Avant tout contrat ou provider de laboratoire, auditer :

- `specialist_kernel_boundary` ;
- `server_oriented_deliberation_cycle` ;
- `scheduler_deliberation_route_contract` ;
- registres 0242/0257/0258 ;
- variation de contexte 0114-0115 ;
- spécialiste factice et adapter LLM ;
- liaison/synthèse 0123-r2 ;
- RouteProxy/ControlProxy/SHM ;
- ResultFrame/EventBus/PassiveSupervisor/VisPy.

### 0273-r2/r3 — frontière puis laboratoire fictif

Ajouter seulement les identifiants et capacités réellement absents, attachés
aux registres existants. Le premier laboratoire fictif sera local,
déterministe, stdlib-only et devra composer les contrats spécialistes déjà
présents. Aucun `LaboratoryManager` ni orchestrateur parallèle ne sera créé.

## Chaîne fonctionnelle visée

```text
GitHub ProjectV2 / repository Issue
-> artefact demande + futur artefact Copilot advisory
-> SourceCandidate
-> gate r7
-> SQL r8
-> espace vectoriel contrôlé r9
-> orientation
-> laboratoire fictif
-> spécialistes / validation / synthèse
-> FinalArtifactEnvelope
-> EventBus / PassiveSupervisor / VisPy
-> gate de publication
-> remontée GitHub contrôlée
```
