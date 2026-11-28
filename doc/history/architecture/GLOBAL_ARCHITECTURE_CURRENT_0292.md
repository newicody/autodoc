# Autodoc / MissiPy — architecture globale consolidée (0292)

**Base Git :** `docs/unification-027x` à `56dc340a8f5c8b88295d35888b13a2d12e03c0cf`  
**Nature :** réconciliation documentaire ; aucune modification runtime.

## 1. Autorités

| Surface | Responsabilité | Limite non négociable |
|---|---|---|
| Scheduler canonique | Sélection, admission, priorité, orchestration et cycle de vie des tâches applicatives | Aucun Scheduler, dispatcher, queue ou orchestrateur parallèle |
| SQL / PostgreSQL | Autorité durable des commandes, tâches, admissions, analyses, preuves et clôtures | Qdrant ne remplace jamais SQL |
| Qdrant | Projection vectorielle reconstruisible et rappel de références | Aucun état métier faisant autorité |
| OpenVINO / multilingual-e5-small | Production des embeddings E5 | Dimension 384 exactement ; pas de backend caché dans le Scheduler |
| EventBus | Publication de faits pour observation | Aucun ordre, admission, mutation ou autorisation |
| PassiveSupervisor / VisPy | Read model et visualisation passive | Aucun contrôle de charge ou action sur le Scheduler |
| ControlProxy | Transport des routes et notifications déjà autorisées | Ni connaissance, ni politique, ni orchestration |
| GitHub Actions / ProjectV2 | Workflow, revue, intake et projection externe | Pas d'autorité sur l'état local |
| OpenRC / OS / administrateur | Cycle de vie des processus et services externes | Pas de gestion de processus par le Scheduler applicatif |

Les laboratoires sont des capacités d'exécution derrière les contrats et handlers existants. Ils ne possèdent pas de Scheduler, queue, bus, registre ou fabrique de capacités parallèle. Les spécialistes rendent des résultats ; ils ne lancent pas directement d'autres spécialistes.

## 2. Flux externes et locaux

Vue logique :

    ProjectV2 #2 (source query-only) ----+
                                         +--> Fetch / assemblage corrélé --> SQL
    Issue / Actions artifacts -----------+                                  |
                                                                            v
                                                                   Scheduler canonique
                                                                            |
                                                               Catalogue et handlers existants
                                                                            |
                                                                 Laboratoires / spécialistes
                                                                            |
                                                                          SQL
                                                                            |
                                                                   E5-384 --> Qdrant

    Scheduler / handlers / laboratoires / SQL --> EventBus --> PassiveSupervisor --> VisPy
    SQL --> projection contrôlée --> ProjectV2 #3 (cible de recherche/projection)
    Copilot advisory v2 - - - - - - - - - -> indice consultatif seulement

ProjectV2 `newicody/2` est documenté comme source GraphQL query-only du snapshot. ProjectV2 `newicody/3` est une cible de recherche/projection. La cible ne devient pas une autorité durable ; toute projection ou mutation reste soumise aux adaptateurs, plans, digests et autorisations explicites déjà présents.

## 3. Copilot : conseil, pas autorité

L'avis Copilot v2 porte les quatre champs analytiques documentés : `concrete_objective`, `expected_result`, `provided_constraints`, `success_criteria`. Il peut aider à préparer une proposition de routage, mais ne peut pas :

- choisir ou admettre une tâche à la place du Scheduler ;
- sélectionner un handler ou contourner son catalogue ;
- modifier une priorité, une capacité ou un statut durable ;
- lancer un laboratoire, un spécialiste, un processus ou un backend ;
- publier directement sur GitHub ou modifier ProjectV2.

Le contexte serveur décrit dans `GITHUB_COPILOT_SERVER_ROUTING_CONTEXT_0292.md` est une spécification, pas une capacité runtime livrée.

## 4. Observation matérielle et charge Scheduler

0288 ajoute les contrats immuables `HardwareSample` et `HardwareCell` (`missipy.hardware_sample.v1`, `missipy.hardware_cell.v1`). Cette unité n'ajoute aucun collecteur OS, poller, service OpenRC, visualisation ou raccord runtime.

Il faut conserver deux plans distincts :

1. **Physique** : mesures de CPU, mémoire, stockage, réseau et accélérateurs, avec source, horodatage, statut et fraîcheur.
2. **Scheduler** : tâches, cellules, capacités logiques, réservations, charge courante et charge prédite calculées ou publiées sous l'autorité du Scheduler.

Une mesure physique ne prouve pas une capacité Scheduler disponible. Une valeur inconnue n'est jamais convertie en zéro. EventBus peut diffuser les faits observés, mais ne devient pas leur autorité.

## 5. État de réalisation

| Domaine | État vérifié / documenté |
|---|---|
| Liaison r16-r66-r1 | Présente : réhydratation d'une tâche READY déjà choisie, sans création d'un Scheduler ou routeur |
| Contrats matériels 0288 | Présents et intégrés dans le commit parent 74043d9 ; contrat seulement, pas collecte |
| ProjectV2 #2 | Contrat de snapshot GraphQL query-only documenté |
| ProjectV2 #3 | Cible de recherche/projection, pas autorité locale |
| Copilot advisory v2 | Artefact consultatif ; le snapshot de routage serveur 0292 reste une spécification |
| Acceptation bout-en-bout r16-r50 | À démontrer par les preuves corrélées du runbook ; aucun statut accepted n'est créé par cette réconciliation |

## 6. Règle de réutilisation

Avant tout code de routage, rechercher les contrats, catalogues, builders, readers et handlers déjà présents. Réutiliser la composition existante. Si une donnée n'est pas exposée par une frontière existante, documenter précisément le manque et proposer le plus petit port de lecture possible. Ne pas ajouter un ComponentProxy, manager, registry, queue ou orchestrateur concurrent par simple commodité.

## 7. Historique Git de la réconciliation

    c9f829f -> 74043d9 (0288 hardware contracts) -> 56dc340 (documentation reconciliation) -> 0292 (this patch)

Le patch 0292 est construit directement sur `56dc340`. Les anciens patches 0289, 0290 et 0291 ne sont pas déclarés appliqués par cette unité.
