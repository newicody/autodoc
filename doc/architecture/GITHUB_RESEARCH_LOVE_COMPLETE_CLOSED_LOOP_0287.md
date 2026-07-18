# Composition complète du cycle de recherche GitHub

## But

Cette unité relie les unités r16-r7 à r16-r18 sans créer un nouvel
orchestrateur.

```text
ready_run GitHub + trois artefacts
→ assemblage et admissibilité
→ politique automatique explicite
→ Scheduler existant
→ première visite spécialiste
→ seconde visite spécialiste
→ deux analyses SQL
→ deux projections Qdrant E5-384
→ rappel hybride et réhydratation SQL
→ synthèse de liaison
→ livrable final SQL
→ plan de publication
──────────────── frontière de confirmation opérateur ────────────────
→ commentaire Issue + projection ProjectV2
→ relecture distante exacte
→ preuve SQL de publication
→ cycle_status=closed
```

## Pas de nouvel orchestrateur

Le module est une composition d’application. Il ne contient :

- aucun `Scheduler(...)`;
- aucun `Dispatcher(...)`;
- aucun `EventBus(...)`;
- aucun gestionnaire de laboratoire;
- aucun client PostgreSQL, Qdrant, OpenVINO ou GitHub.

Le Scheduler existant reste le seul orchestrateur des tâches et visites. La
composition appelle les cas d’usage déjà présents dans leur ordre contractuel.

## Deux phases obligatoires

### Phase locale

`prepare_github_research_love_closed_loop` exécute les étapes locales et
distantes de lecture jusqu’au plan r16-r17.

Le résultat valide porte :

```text
status = publication-confirmation-required
publication_plan_digest = sha256:...
remote_publication_performed = false
cycle_closed = false
```

### Phase confirmée

`complete_github_research_love_closed_loop` exige :

- le résultat préparé complet;
- `operator_decision=approve`;
- le digest exact;
- le verrou global de mutation;
- le verrou Issue;
- le verrou ProjectV2;
- les ports distants déjà injectés.

La preuve r16-r18 n’est créée qu’après une publication valide et une relecture
exacte.

## Arrêt au premier échec

Chaque étape est ajoutée au résultat uniquement après son invocation. Une étape
invalide arrête immédiatement la chaîne et renseigne `failed_stage`.

Ainsi :

- une recherche inadmissible n’entre jamais dans le Scheduler;
- un dispatch invalide ne démarre jamais le laboratoire;
- une analyse invalide n’est jamais persistée;
- une projection invalide n’entre jamais dans la synthèse;
- un mauvais digest ne peut jamais fermer le cycle;
- une publication partielle ne peut jamais produire `cycle_status=closed`.

## Rejeu

Les unités SQL et Qdrant conservent leur idempotence propre. La publication
distante utilise son marqueur et son digest existants. La fermeture SQL est
elle aussi immuable.

La composition n’ajoute aucun registre de rejeu parallèle : elle expose
simplement les reçus produits par chaque unité.

## État opérationnel

Après cette unité, le chemin applicatif complet existe. L’étape suivante n’est
plus une nouvelle couche métier : elle consiste à fournir un adaptateur de
lancement réel qui construit les `ImportedActionsRuntimePorts`, charge le
`ready_run`, résout l’item/champ ProjectV2 et appelle les deux phases.
