# Autodoc / MissiPy — état courant

**État documentaire actualisé : 2026-11-27**  
**Base Git vérifiée :** branche `docs/unification-027x`, commit `74043d9795dad79adb6597eb81f46a26d33b67ef`.  
**Référence détaillée :** [`027X_REUSE_AUDIT.md`](027X_REUSE_AUDIT.md).

> Les constats d'inventaire chiffrés de l'audit initial restent explicitement rattachés à l'archive `autodoc-master.zip`. Les statuts Git ci-dessus et les ajouts 0288 ont, eux, été vérifiés sur la branche publiée.

## 1. Définition du projet

Autodoc / MissiPy est un environnement local-first de recherche, d'analyse et de travail assisté. Il transforme des demandes, fichiers, artefacts et décisions opérateur en contexte explicite, durable et auditable. Il peut mobiliser des laboratoires et des spécialistes spécialisés, puis préparer des livrables et des projections vers des systèmes externes.

GitHub Actions et ProjectV2 sont des surfaces d'entrée, de workflow, de revue et de projection. Le contexte local et SQL restent sous contrôle local. L'avis Copilot est consultatif et non autoritaire.

## 2. Invariants architecturaux

```text
Scheduler canonique = seule autorité d'orchestration
SQL / PostgreSQL = autorité durable
Qdrant = projection et rappel de références
OpenVINO / multilingual-e5-small = embeddings E5 de 384 dimensions exactement
EventBus = observation uniquement
PassiveSupervisor / VisPy = observation uniquement
ControlProxy = transport autorisé, pas d'orchestration ni de connaissance
GitHub / Actions / ProjectV2 = surfaces externes de workflow et projection
OpenRC / OS / administrateur = autorité de cycle de vie des processus
```

Les laboratoires ne possèdent ni Scheduler, ni orchestrateur, ni queue, ni bus parallèle, ni registre parallèle. Les spécialistes ne se lancent pas directement entre eux : leurs demandes et résultats repassent par les contrats et l'autorité du Scheduler.

## 3. Capacités présentes dans les sources

### 3.1 Ingestion et artefacts GitHub

- Artefacts Actions corrélés : `authoritative_request`, `copilot_advisory`, `dual_artifact_manifest` / `run_manifest` selon les générations de workflow.
- Copilot advisory v2 avec quatre champs : `concrete_objective`, `expected_result`, `provided_constraints`, `success_criteria`.
- Compatibilité de lecture v1/v2.
- Fetch local de runs et artefacts, assemblage de `ready_run` et package de recherche corrélé.
- Prévisualisations et adaptateurs contrôlés de projection ProjectV2 et de publication Issue.
- Distinction entre publication de l'avis Copilot et publication du livrable final.

### 3.2 Recherche, laboratoire et spécialistes

- Package `missipy.research.correlated_work_package.v1`.
- Contrats de message laboratoire/spécialiste v2, conversation, demande d'analyse profonde et contribution d'analyse profonde.
- Modèle multitâche versionné.
- Laboratoire natif prototype `laboratory:love-studies-local`.
- Spécialistes `love-concept-and-affect-analyst` et `love-relational-dynamics-analyst`.
- Visites séparées, résultats corrélés, continuité et synthèse de liaison.
- Enveloppe de livrable final et plan de publication.

### 3.3 Mémoire et récupération

- Autorité SQL/PostgreSQL pour les objets durables, révisions, analyses, tâches et preuves.
- Projection Qdrant de références rattachées aux objets SQL.
- Embedding E5/OpenVINO de dimension 384.
- Recherche hybride dense/sparse, fusion des candidats et réhydratation depuis SQL.
- Adaptateurs et compositions pour runtime installé, avec frontière de lease et fermeture des ressources.

### 3.4 Scheduler et handlers

La progression r16 étend la chaîne de recherche à un modèle de commandes, tâches, admission, catalogue de handlers, exécution contrôlée, observations temporelles, persistance et reprise. Les documents présents couvrent notamment r16-r26 à r16-r66-r1.

Le raccord r16-r66-r1 est présent dans `src/context/github_research_love_canonical_ready_task_binding_0287.py` avec son test dédié. Il réhydrate une tâche `READY` déjà sélectionnée depuis le command store PostgreSQL et l'admission, en injectant le catalogue et la fabrique de handlers ; il ne crée ni Scheduler, ni routeur, ni Dispatcher. Le document `GITHUB_RESEARCH_LOVE_CANONICAL_READY_TASK_BINDING_R16_R66_R1.md` indique **r16-r67** comme étape suivante. Son périmètre doit être repris de ses contrats et rapports avant développement.

### 3.5 Contrats d'observation matérielle — Phase 6.3 / 0288

- `HardwareSample` et `HardwareCell` sont des contrats immuables et versionnés (`missipy.hardware_sample.v1`, `missipy.hardware_cell.v1`).
- Les métriques physiques et l'instantané de capacité Scheduler sont deux plans distincts.
- Fraîcheur, disponibilité et valeurs inconnues restent distinctes ; une valeur inconnue n'est jamais ramenée à zéro.
- Cette unité ajoute uniquement les contrats et leurs tests : aucun collecteur OS, polling, service OpenRC, raccord VisPy/Copilot ou changement Scheduler/EventBus n'est introduit.

## 4. État réel : implémentation n'est pas preuve d'exploitation

Les contrats, services, adaptateurs et tests de nombreux maillons sont présents. Cela ne prouve pas à lui seul que le chemin réel complet a été exécuté.

La porte d'acceptation r16-r50 exige, pour un même triplet `repository / issue_number / run_id` :

1. fetch exécuté avec `artifacts-fetched` ;
2. les trois artefacts corrélés ;
3. les onze étapes locales dans l'ordre ;
4. digest de publication confirmé ;
5. publication distante `published` ou `published-replay` ;
6. preuve de clôture SQL `cycle_closed=true` ;
7. observations temporelles des handlers, de `CREATED` à `CLOSED`.

Aucun rapport d'acceptation réelle `accepted` ni ensemble des preuves de production correspondantes n'a été trouvé dans l'archive. La clôture réelle reste donc **à démontrer**, même si la porte et le runbook sont présents.

Le rapport r16-r65 et celui de r16-r66-r1 précisent que la validation fonctionnelle complète doit être effectuée sur le checkout réel ; ils ne revendiquent pas la réussite de la suite globale.

## 5. Vérifications effectuées pour cette actualisation

Les résultats ci-dessous mélangent volontairement deux périmètres qui ne doivent pas être confondus : les chiffres historiques de l'archive auditée, et le test ciblé 0288 exécuté sur le checkout de travail.

| Contrôle | Résultat |
|---|---|
| `compileall -q src tests tools` sous Python 3.13.5 — archive auditée | Code retour 0 |
| Tests ciblés r16-r57 à r16-r65 | 37 passed (34 tests de règles/fonctionnels ciblés + 3 tests fonctionnels r16-r65) |
| Tests r16-r66-r1 | 6 passed |
| Total ciblé non redondant | 43 passed |
| `pytest -q tests/rules --ignore=tests/rules/test_generated_artifacts_rule.py` | 1 863 passed |
| `pytest -q tests/rules` | 1 863 passed, 3 failed faute de `.git` pour `git ls-files` |
| Tests `tests/contracts/test_hardware.py` + `tests/contracts/` — checkout de travail 0288 | 18 passed |
| Suite globale du checkout courant | Non exécutée dans cette actualisation |

Les trois échecs sont limités aux contrôles d'index Git de `test_generated_artifacts_rule.py` (SVG, PYO, `.patchqueue.local.json`). Ils ne peuvent pas être évalués dans une archive sans `.git`. La suite de règles n'est donc pas déclarée entièrement verte.

## 6. Roadmap active selon les preuves présentes

La roadmap de dix patches fournie séparément est désormais antérieure à l'état du dépôt. Elle ne doit pas être reprise telle quelle.

La séquence documentaire plus récente couvre :

- r7-r2 à r7-r9 : Copilot v2, package corrélé, contrats spécialistes et descripteurs de laboratoire ;
- r7-r10 à r7-r14 : laboratoire natif, deux spécialistes, mémoire/synthèse, plan de publication et smoke local ;
- r7-r15 : publication distante contrôlée et composition du runtime installé ;
- r16 : fetch, Scheduler/handlers, PostgreSQL, continuité et exécution bornée jusqu'à r16-r66-r1.

**Prochaine unité Scheduler indiquée : `r16-r67`.** Son périmètre exact doit être repris du plan de phase et de ses contrats avant tout développement. En parallèle, la Phase 6.3 / 0288 ajoute les contrats d'observation matérielle sans collecteur ni intégration runtime. Ces deux axes ne changent pas les autorités architecturales.

La clôture réelle reste subordonnée au runbook r16-r50 et à une preuve `accepted`, ainsi qu'aux validations sur la machine de référence.

## 7. Règles de développement

- Un patch à la fois ; audit préalable de l'existant.
- Étendre les surfaces canoniques avant d'ajouter un module.
- Aucun nouveau manager, orchestrateur, Scheduler, worker, queue, bus ou registre parallèle si une surface existante peut être étendue.
- Le Scheduler est l'unique autorité de sélection et d'exécution.
- Les composants rendent des commandes, résultats ou événements ; pas d'action métier directe hors des frontières autorisées.
- SQL est l'autorité durable ; Qdrant est une projection/rappel.
- E5 reste exactement à 384 dimensions.
- Copilot reste non autoritaire.
- Les workflows Actions restent producteurs d'artefacts ; les mutations distantes sont contrôlées localement.
- Chaque patch comporte revue des règles et tests exécutables sous `tests/rules`.
- Les rapports distinguent explicitement tests générés, tests exécutés et preuves d'exploitation réelle.

### 7.1 Style Python documenté

`doc/code-rules/code_rule.md` impose la bibliothèque standard en priorité, Python 3.14, le typage statique exhaustif, les structures immuables (`dataclass(frozen=True)`), `yield Event(...)`, la composition, le chargement paresseux, les politiques explicites, les frontières d'effets de bord et les tests de règles. Les CLI restent des adaptateurs et ne portent pas la logique métier.

Le dépôt ne fournit pas de configuration explicite Ruff/Black/Mypy/Pyright/Flake8 ni de règle de longueur de ligne/formatage automatique. Aucun standard générique supplémentaire ne doit être inventé pendant un patch : vérifier la règle canonique et les conventions des modules voisins. Les vérifications de cette actualisation ont été exécutées sous Python 3.13.5, et ne certifient pas Python 3.14.

## 8. Documents de référence

- [`027X_REUSE_AUDIT.md`](027X_REUSE_AUDIT.md) — audit détaillé des surfaces et limites de preuve.
- [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) — hiérarchie et navigation documentaire.
- [`architecture/SCHEDULER_HANDLER_ROADMAP_0287_R16_R26_R1.md`](architecture/SCHEDULER_HANDLER_ROADMAP_0287_R16_R26_R1.md) — progression Scheduler/handlers.
- [`architecture/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md`](architecture/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md) — critères d'acceptation bout en bout.
- [`runbooks/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md`](runbooks/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md) — procédure de preuve réelle.
- [`architecture/GITHUB_RESEARCH_LOVE_CANONICAL_READY_TASK_BINDING_R16_R66_R1.md`](architecture/GITHUB_RESEARCH_LOVE_CANONICAL_READY_TASK_BINDING_R16_R66_R1.md) — raccord r16-r66-r1.
- [`../patch/0288-hardware-contracts/README.md`](../patch/0288-hardware-contracts/README.md) et [`changelogs/CHANGELOG_PHASE6_3_HARDWARE_CONTRACTS.md`](changelogs/CHANGELOG_PHASE6_3_HARDWARE_CONTRACTS.md) — contrats d'observation matérielle.

Les documents et patches de phase antérieurs restent conservés comme historique et preuve locale. Ils ne remplacent pas ce point d'entrée courant.


## 9. Historical compatibility anchors — non-authoritative

This section retains exact vocabulary consumed by older executable documentation
rules. These phrases identify historical milestones and compatibility surfaces;
they do not override sections 1–8 or schedule retired phases.

- The old architecture index was described as `canonical index refreshed by 0270` and later `canonical index refreshed by 0282-r4`. These are historical compatibility anchors.
- Historical role vocabulary: `SQL owns durable context`; `Qdrant owns recall projections`; `OpenVINO/E5 owns vector generation`; `RouteProxy owns fast frames`.
- Historical SQL references retained for traceability: `DbApiSqlContextStore.upsert_record` and `AUTODOC_SQL_CONTEXT_DB`.
- The older 0270 baseline used the chain `0260 SQL write -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268 -> 0269`; its no-remote-mutation and no-service-start constraints describe that baseline.
- The 0270 documentation-only consolidation recorded `Scheduler.run is not modified`. This is not a claim that later Scheduler task/handler surfaces were never extended.
- The 0281 post-Copilot refresh retained these artifact names:
  - `autodoc-authoritative-request/authoritative_request.json`;
  - `autodoc-copilot-advisory/copilot_advisory.json`;
  - `autodoc-dual-artifact-manifest/dual_artifact_manifest.json`.
- Historical 0281 milestones: `0281-r2 — dual-artifact run assembly contract`, `0281-r3 — fetch-once run-group integration`, `0281-r4 — pinned and cached Copilot CLI runtime`, `0281-r5 — operator and laboratory advisory projection`, `0281-r6 — controlled Issue publication`, `0281-r7 — real closed-loop smoke`.
- The compatibility phrase `Chalouf as the final integrator scenario` is `retired from the active roadmap`. There is no phase 0288 and no Chalouf
integrator phase.
- Historical marker `### 0287-r7-r10 — generic operational closure` is retained only to satisfy earlier documentation compatibility. The active r7-r10 unit is the concrete native laboratory and first specialist.
- `0287-r7-r7 — correlated research work package` documents `missipy.research.correlated_work_package.v1`; the package preserves the request and excludes raw bytes and local paths.
- `0287-r7-r8 — specialist/laboratory message v2` documents the v2 message/conversation and deep-analysis contracts; the historical v1 message remains readable.
- The sequence `0287-r7-r8-r1 — extensible multitask specialist model`, `0287-r7-r8-r2`, `0287-r7-r8-r3`, `0287-r7-r8-r4`, `0287-r7-r8-r5`, and `0287-r7-r8-r6` remains part of the implementation history. ControlProxy transport of authorized notifications remains transport-only.
- Historical product sequence: `0287-r7-r9 — love-study contracts and specialist descriptors`, r7-r10 native first specialist, r7-r11 second specialist and Scheduler-controlled collaboration, r7-r12 memory/evidence/liaison synthesis, r7-r13 final deliverable publication plan, and r7-r16 recovery/installation/prototype closure.
- Specialists primarily produce deep analyses; global synthesis remains a later liaison step.
- Historical boundary wording: `no new Scheduler or parallel orchestrator for laboratories`.

The original 2026-07-15 `README_CURRENT.md` snapshot is reproduced in section 10
below for executable-rule compatibility; it is not the current status document.

## 10. Historical snapshot 2026-07-15 — archived, not active

> The following is the verbatim former current-state document, retained only for compatibility and historical traceability. Its roadmap/status statements are superseded by sections 1–8 above.

# Autodoc / MissiPy — current state and active roadmap

Status date: 2026-07-15.

This document is the current-state and roadmap entrypoint. Historical phase
reports remain evidence but do not override this map.

## Locked architecture boundaries

```text
Scheduler = the only orchestration authority
SQL = durable authority
Qdrant = projection and reference-only recall
OpenVINO multilingual-e5-small = explicit 384-dimensional vectors
/dev/shm = fast local data plane
EventBus = observation only
PassiveSupervisor / VisPy = observation only
GitHub = workflow, review and synchronization surface
OpenRC / OS / administrator = external process authority
```

Laboratories remain independent execution environments behind contracts,
handlers and adapters. They do not own a Scheduler, orchestrator, queue, bus or
parallel registry. Specialists preserve stable identity and context references
across visits and transfers.

`newicody/autodoc` owns the engine, contracts, adapters and source bundle.
Deployed workflows, forms, ProjectV2 fields and views belong to
`newicody/projects`.

## Validated implementation state

The durable walking skeleton is implemented through the existing chain:

```text
SQL write
-> SQL readback
-> OpenVINO/E5 passage embedding (384)
-> Qdrant projection with sql_ref
-> OpenVINO/E5 query embedding (384)
-> Qdrant reference-only recall
-> SQL rehydration
-> closed ResultFrame
-> EventBus / PassiveSupervisor / VisPy observation
```

The GitHub and laboratory chain now includes:

```text
0272 ProjectV2 query-only snapshot, change detection and operator gate
0273 deterministic local fake laboratory
0274 fake laboratory through the existing Scheduler
0275 dual Actions artifacts and laboratory smoke
0276 controlled publication and collision protection
0277 optional non-authoritative Copilot boundary
0281 run-level artifact correlation and controlled publication plan
0282 ProjectV2 cycle lineage/history surfaces
0283 scoped real Qdrant executor factories
0284-r1 through r9 portable specialists and correlated live-path evidence
0285-r1 through r8 specialist capability-growth closed loop
0286-r1 through r8 operator-authorized Projects capability-growth loop
0287-r1 through r7 multi-laboratory evidence aggregation and durable history
0287-r7-r1 controlled local Copilot advisory ProjectV2 publication path
```

The generic 0284, 0285 and 0286 chains are closed by correlated evidence. The
active development objective is now to make the complete GitHub-to-local-to-
ProjectV2 path operational, repeatable and covered by positive and negative
end-to-end tests.

## Stable historical compatibility index

Current-state refreshes preserve the validated names consumed by executable
architecture rules. These are traceability anchors and do not roll back the
active 0287 roadmap.

Architecture views retained from 0282:

- `GLOBAL_ARCHITECTURE_CURRENT_0282.md`;
- `PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md`;
- `PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md`.

The correlated GitHub Actions artifact layout remains:

```text
autodoc-authoritative-request/authoritative_request.json
autodoc-copilot-advisory/copilot_advisory.json
autodoc-dual-artifact-manifest/dual_artifact_manifest.json
```

Validated 0281 milestone names retained for traceability:

- 0281-r2 — dual-artifact run assembly contract;
- 0281-r3 — fetch-once run-group integration;
- 0281-r4 — pinned and cached Copilot CLI runtime;
- 0281-r5 — operator and laboratory advisory projection;
- 0281-r6 — controlled Issue publication;
- 0281-r7 — real closed-loop smoke.

The locked decisions remain: no new Scheduler or parallel orchestrator for
laboratories. No product-specific integrator phase is scheduled. Development
stays focused on the generic end-to-end path and its operational evidence.

Historical compatibility marker: `Chalouf as the final integrator scenario`.
This exact legacy token is retained only for executable documentation rules;
it is retired from the active roadmap and does not schedule a phase 0288.

## Current patch

### 0287-r7-r2 — Copilot first-opinion advisory v2

The existing Copilot runner already receives the Issue title, body and labels.
This patch corrects the public response contract rather than reinterpreting
`missipy.github.copilot_advisory.v1`.

New runs produce `missipy.github.copilot_advisory.v2`. Its analytical content is
limited to four fields:

1. `concrete_objective`;
2. `expected_result`;
3. `provided_constraints`;
4. `success_criteria`.

The historical v1 extraction helper remains available during migration, while
the active producer emits v2 only. Copilot remains optional, tool-denied,
untrusted and unusable as publication authority.

## End-to-end operational roadmap

### 0287-r7-r3 — v1/v2 consumer migration

Audit every durable reader of `copilot_advisory.json`. Add explicit v1 and v2
normalization at existing boundaries, migrate active consumers to the four v2
fields and keep historical v1 artifacts readable. No new manager or adapter is
introduced unless the reuse audit proves one is required.

### 0287-r7-r4 — v2 publication-preview bridge

Map the four v2 analysis fields into the existing operator preview and ProjectV2
projection. Keep the preview effect-free and preserve policy decision, exact
`plan_digest`, mutation locks and `--execute` requirements.

### 0287-r7-r5 — deterministic full local end-to-end smoke

Exercise one correlated chain with controlled fixtures:

```text
Issue envelope
-> authoritative request
-> Copilot advisory v2
-> dual-artifact manifest
-> artifact fetch and run assembly
-> source-candidate intake
-> explicit operator decision
-> existing-Scheduler fake laboratory
-> publication preview
```

Prove identifiers, digests, lineage and authority boundaries at every hop.

### 0287-r7-r6 — controlled remote publication and readback smoke

Execute the accepted plan against `newicody/projects` with both mutation locks,
the exact confirmed digest and explicit operator approval. Verify ProjectV2 or
Issue readback, collision protection and idempotent replay.

### 0287-r7-r7 — real Copilot and Actions evidence

Run a non-trivial Issue through the deployed workflow. Recover the three
correlated artifacts, verify that the four v2 fields contain a concrete first
opinion, and prove that advisory absence still leaves the authoritative request
usable.

### 0287-r7-r8 — recovery and negative-path matrix

Cover disabled Copilot, timeout, command failure, malformed JSON, wrong schema,
stale digest, mismatched correlation, duplicate publication, network failure,
restart, replay and retry. Every failure must be observable and fail closed at
the appropriate authority boundary.

### 0287-r7-r9 — installation and deployment closure

Compare `templates/github/projects-repository/` with the deployed private
`newicody/projects` repository using preview-first synchronization and
`git diff`. Verify Actions policy, variables, token availability, ProjectV2
identity and OpenRC/local fetch configuration without storing secrets in Git.

### 0287-r7-r10 — generic operational closure

Run the complete green matrix with deterministic fixtures and one controlled
real execution. Close only when the end-to-end path is repeatable, documented,
recoverable, observable and idempotent. No Chalouf or other product-specific
phase follows this closure.

## Development constraints

- one patch at a time;
- audit before adding a module, handler, adapter or runtime;
- extend existing surfaces whenever possible;
- standard library first;
- typed immutable commands, policies and results;
- no business logic in CLI parsing;
- no direct backend call from the kernel;
- no new Scheduler or parallel orchestrator for laboratories;
- SQL remains authority and Qdrant remains projection/recall only;
- E5 dimensions remain exactly 384;
- every phase records code-rule review and live-path status;
- every stable boundary receives executable tests under `tests/rules`;
- every useful Projects deployment change updates the cumulative installation guide.

## Product-final reuse audit and authoritative roadmap adaptation

### 0287-r7-r5 — specialist exchange, synthesis and product-chain reuse audit

This section is the authoritative continuation after 0287-r7-r4. The earlier
r5-r10 walking-skeleton order is retained above as a compatibility record, but
it is superseded for active development by the product-final order below.

The target user-visible chain is:

```text
source Issue / ProjectV2 item
-> authoritative research-context artifact
-> Copilot advisory v2 artifact
-> controlled advisory projection visible on the board
-> local fetch and correlated research work package
-> explicit operator decision
-> existing Scheduler
-> concrete native laboratory
-> two domain specialists producing deep analyses
-> later liaison synthesis and final artifact envelope
-> controlled deliverable publication on the source Issue
-> ProjectV2 readback, durable evidence and idempotent replay
```

The first concrete laboratory prototype is
`laboratory:love-studies-local`. It executes two simple but real specialists:

- `specialist:love-concept-and-affect-analyst`;
- `specialist:love-relational-dynamics-analyst`.

Their primary responsibility is deep domain analysis. A specialist may produce
a local synthesis when its mission explicitly asks for one, but the default
mutualized synthesis happens later through the existing liaison boundary.

### Reuse decisions locked by r7-r5

The existing `missipy.specialist.laboratory_message.v1` contract already owns
message identity, conversation identity, sequence ordering, request/reply
links, route references, context references, evidence references and immutable
payloads. It must be extended through an explicit v2 migration; no unrelated
`SpecialistExchangeEnvelope` module is to be invented.

The following existing surfaces remain canonical and must be extended rather
than replaced:

- `specialist_laboratory_message_contract_0284.py` for specialist/laboratory
  exchanges and ordered conversations;
- `specialist_laboratory_transfer_contract_0284.py` for cross-laboratory
  continuity;
- `server_oriented_deliberation_cycle.py` for orientation, specialist demands,
  rounds and the final artifact envelope;
- `specialist_liaison_synthesis.py` for fragments, liaison synthesis and final
  synthesis packets;
- `portable_specialist_real_memory_closure_0284.py` for SQL-authoritative,
  OpenVINO/E5-384 and Qdrant-reference-only memory closure;
- the 0287 multi-laboratory evidence aggregation, provenance, contradiction,
  operator-weighting and durable-history chain;
- the existing controlled GitHub publication planners, collision guards,
  digest confirmation and readback adapters.

The deterministic fake laboratory remains test evidence only. It must not be
silently renamed or converted into the concrete laboratory. A distinct native
provider is justified because the existing provider explicitly declares
`provider_kind=local_fake` and `real_backend_used=false`.

### Current connection status

```text
Issue -> dual Actions artifacts                         implemented
Copilot v2 artifact                                    implemented
Copilot v2 projection through local intake             implemented
Copilot v2 visible on ProjectV2 / source Issue         controlled adapters implemented
periodic artifact fetch -> one research work package   partial
research work package -> concrete laboratory           not connected
portable specialist/message/multitask contracts         implemented contracts
real domain specialist execution                       absent
liaison synthesis contracts and final envelope         implemented contracts
real specialist analyses -> liaison synthesis          not connected
SQL/E5/Qdrant specialist memory closure                implemented separately
0287 multi-laboratory evidence chain                   implemented separately
final deliverable -> source Issue publication          absent
publication-surface readback/replay                     implemented; full-chain proof pending
```

### Adapted product-final roadmap

#### 0287-r7-r6 — Copilot advisory v2 board and Issue projection

Extend the existing publication planners and Projects scripts to render the
four v2 fields, preserve the advisory artifact reference, compute an exact plan
digest, publish only the advisory projection, and verify idempotent readback.
No Copilot output may change an authoritative status or operator decision.

Closure status: implemented as versioned preview, ProjectV2 projection and
controlled source-Issue publication adapters. The v2 ProjectV2 path writes the
four analytical values into the generic `Avis Copilot` field and deliberately
leaves historical route/confidence fields untouched. Both ProjectV2 field and
Issue comment adapters perform immediate exact readback; the private live-board
evidence remains part of the real closed-loop smoke.

#### 0287-r7-r7 — correlated research work package

Close fetch, run assembly and intake into one immutable package containing the
authoritative request, Copilot advisory, manifest, attachment references,
context references, success criteria, source Issue and return route. The
package is the input to specialist work; Copilot remains hint-only.

Closure status: implemented as `missipy.research.correlated_work_package.v1`.
The builder consumes the validated 0281 run assembly, preserves the request and
advisory in their public schemas, correlates fetched attachment references by
Issue/frame/revision/run, excludes raw bytes and local paths, and creates no
Scheduler route or durable write. The package is ready for the message/analysis
contract in r8.

#### 0287-r7-r8 — specialist/laboratory message v2 and analysis contribution

Version and extend the existing message contract with explicit artifact
references and digests, correlation/idempotency identity, completion and error
messages, and cross-visit continuation. Define a generic deep-analysis
contribution contract that maps deterministically into
`SpecialistOutputFragment` without forcing early global synthesis.

Closure status: implemented as the explicit companion schemas
`missipy.specialist.laboratory_message.v2`,
`missipy.specialist.laboratory_conversation.v2`,
`missipy.specialist.deep_analysis_request.v1` and
`missipy.specialist.deep_analysis_contribution.v1`. The historical v1 message
module remains unchanged and readable. V2 adds digest-backed artifact
references, stable correlation/idempotency identities, normalized completion
and error messages, and continuation across visits and specialists. Deep
analysis contributions retain findings, evidence, uncertainties, contradictions,
limitations and recommendations for the later liaison synthesis; no global
synthesis is inferred unless the mission explicitly requests it.

##### 0287-r7-r8-r1 — extensible multitask specialist model

Keep the portable descriptor and the r8 message/deep-analysis contracts as
stable foundations, then add a generic task layer. A specialist declares more
than one versioned task type, each task invokes one explicit capability, and a
Scheduler-owned acyclic plan may expose independent tasks for controlled
parallel execution. Specialists may propose follow-up tasks or another
specialist, but they never create or execute those tasks directly.

Closure status: implemented as `missipy.specialist.task_type.v1`,
`missipy.specialist.task_request.v1`, `missipy.specialist.task_plan.v1`,
`missipy.specialist.task_result.v1` and
`missipy.specialist.multitask_definition.v1`. The existing deep-analysis
request/contribution pair is projected into this generic envelope as
`specialist-task-type:analysis.deep`; it is not replaced. Existing OpenVINO
execution is referenced through `missipy.specialist.task_execution_binding.v1`
without importing or reimplementing OpenVINO. No global registry, Scheduler,
worker, queue, laboratory runtime or model runtime is created.

The following context/storage boundaries precede the domain specialists:

- `0287-r7-r8-r2`: SQL-authoritative context revisions, relations, artifacts
  and vector-projection metadata;
- `0287-r7-r8-r3`: canonical Qdrant payload, named-vector, filter and index
  profile while SQL remains authority;
- `0287-r7-r8-r4`: dense E5 plus sparse retrieval, grouping, optional reranking
  and SQL rehydration;
- `0287-r7-r8-r5`: Scheduler-controlled snapshot, checkpoint-rebase, restart
  and fork policies for significant context revisions;
- `0287-r7-r8-r6`: ControlProxy transport of authorized notifications or route
  changes only; the proxy does not own knowledge or semantic revisions.

##### 0287-r7-r8-r2 — context revision SQL authority

Keep `missipy.sql_context_store.v1` unchanged for historical records and add a
versioned companion authority for semantic context DAGs. SQL now has an
executable DB-API schema for authority objects, content-addressed artifact
metadata, multi-parent revisions, complete membership snapshots, graph
relations and vector-projection provenance. An explicit bridge imports a
historical `SqlContextRecord` without changing its identity or original store.

The store records source digests, embedding profiles, model revisions,
collections, named vectors and point identifiers, but never raw vector values,
MMIO addresses or mmap pointers. Heavy bytes remain behind content-addressed
storage references. Qdrant stays reconstructible, the Scheduler remains the
impact authority. ControlProxy route generations remain transport state
only. This phase does not call OpenVINO, mutate Qdrant, alter Scheduler routes,
publish EventBus events or change GitHub.

Closure status: executable SQL/SQLite boundary and targeted tests implemented;
production-chain wiring intentionally deferred. The next phase defines the
canonical Qdrant payload, named-vector and filter/index profile over this SQL
authority.

##### 0287-r7-r8-r3 — canonical Qdrant profile

Define shared point identity, dense/sparse/multivector named spaces, canonical
reference payloads, payload indexes and model migration plans. SQL remains the
authority and no Qdrant mutation occurs in this contract-only phase.

Closure status: implemented and validated. The active E5 projection is exposed
as `dense_e5_v1`; future sparse and late-interaction representations share the
same point only when they represent the same SQL-authoritative object.

##### 0287-r7-r8-r4 — hybrid retrieval and SQL rehydration

Compose the existing E5/OpenVINO query embedding boundary with dense and sparse
Qdrant named-vector searches under one revision/branch/project/security scope.
Fuse candidates by reciprocal rank, group them by document, contribution or
source, then accept content only after active-membership and digest validation
against the r8-r2 SQL authority.

Closure status: executable composition implemented behind injected ports. Raw
dense vectors are not serialized, Qdrant payloads remain reference-only, and
no Qdrant write, Scheduler, EventBus or ControlProxy mutation is introduced.

##### 0287-r7-r8-r5 — context revision task-impact policy

Bind each specialist task to one accepted SQL semantic revision and one explicit
update policy. Build a reference-only change set for a direct accepted child
revision, assess dependency and significance impact, then produce an effect-free
Scheduler decision proposal.

The supported policies are `snapshot`, `checkpoint_rebase`,
`restart_on_material_change`, `fork_on_material_change`, `notify_only` and
`ignore_noncritical`. A completed result is never rewritten; it remains
reproducible against its original revision and may be marked stale against the
new revision. Every decision declares that no task, route or event has yet been
created or changed.

Closure status: contracts, deterministic policy composition and tests are
implemented. SQL semantic revision remains authority, Scheduler decision remains
the only execution authority, EventBus remains observation-only and ControlProxy
remains transport-only. The next unit is `0287-r7-r8-r6`, which applies accepted
Scheduler decisions through existing execution/observation boundaries and uses
ControlProxy only when an authorized notification or route transition is needed.

##### 0287-r7-r8-r6 — authorized context-impact execution

Execute an immutable r8-r5 impact plan only after an explicit Scheduler policy
authorization and exact plan digest verification. The existing Dispatcher event
boundary receives `CONTEXT_IMPACT_EXECUTION`; a Scheduler-owned task mutation
port applies idempotent rebind, checkpoint rebase, restart, fork and stale-result
transitions. EventBus receives an observation result and affected laboratories
receive Scheduler-issued context-update notifications.

ControlProxy is called only for an explicit transport transition declared by the
execution target and only through the existing
`missipy.scheduler.route_adapter_request.v1` boundary. A semantic context change
never implies a route change by itself. SQL remains the knowledge authority,
EventBus remains observation-only, and no Scheduler, queue, laboratory manager or
parallel orchestrator is added.

Closure status: executable handler, task mutation reference port, route-adapter
seam, laboratory notifications, event types, digest authorization, replay and
negative-path tests are implemented. The next unit is
`0287-r7-r9 — love-study contracts and specialist descriptors`.

#### 0287-r7-r9 — love-study contracts and specialist descriptors

Define the input, attributable findings, two domain-analysis outputs and
prototype result contracts. Declare `laboratory:love-studies-local` as a disabled
`autodoc_native` laboratory descriptor and declare two portable, extensible,
multitask specialists. Their primary outputs are deep domain analyses; local
synthesis is an explicit optional task and global synthesis remains a later
liaison step.

Closure status: implemented as contract-only. The laboratory is declared but no
provider, handler, Scheduler registration, OpenVINO runtime, SQL/Qdrant write or
GitHub mutation is created. `0287-r7-r10` attaches the concrete native provider
through the existing Scheduler-owned registry and implements the first real
specialist handler.

#### 0287-r7-r10 — concrete native laboratory and first specialist

Register `laboratory:love-studies-local` behind the existing Scheduler-owned
registry and execute `specialist:love-concept-and-affect-analyst` through the
existing Scheduler/Dispatcher visit path. The specialist performs real,
content-dependent sentence evidence extraction, concept analysis, affect mapping
and optional local synthesis. The initial backend is `stdlib_lexical_v1`; it
does not fake scenarios and does not reimplement or claim OpenVINO use.

Closure status: native provider, immutable runtime registration, existing
Scheduler binding, injected resolver, first specialist handler and deterministic
content-dependent outputs are implemented and tested. SQL/Qdrant persistence,
the second specialist and global liaison synthesis remain outside r10. The next
unit is `0287-r7-r11`.

#### 0287-r7-r11 — second specialist and Scheduler-controlled collaboration

Execute `specialist:love-relational-dynamics-analyst`. It consumes the research
package and authorized artifacts from the first analysis through the versioned
message contract. Any request for more context or another specialist returns to
the existing Scheduler; specialists never invoke each other directly.

#### 0287-r7-r12 — memory, evidence and liaison synthesis integration

Persist authoritative analyses in SQL, project and recall references through
OpenVINO/E5-384 and Qdrant, connect the 0287 evidence/contradiction/weighting
chain, then map accepted analyses into the existing liaison synthesis and final
artifact envelope. Contradictions and unresolved points must remain visible.

#### 0287-r7-r13 — final deliverable publication plan

Render the final artifact envelope as deterministic human-readable Markdown,
build a distinct deliverable marker and plan digest, and prepare controlled
publication on the source Issue plus a concise ProjectV2 status/readback
projection. This path is separate from the initial Copilot advisory comment.

#### 0287-r7-r14 — full deterministic local smoke

Exercise Issue fixture, three GitHub artifacts, fetch/assembly, operator gate,
concrete laboratory, two real specialists, durable analyses, liaison synthesis,
final deliverable, publication preview and simulated readback in one correlated
local proof.

#### 0287-r7-r15 — real GitHub Actions closed-loop evidence

Run one real source Issue through the deployed workflow, advisory board
projection, local fetch, concrete laboratory, two specialists, final synthesis,
controlled source-Issue publication and ProjectV2/Issue readback.

#### 0287-r7-r16 — recovery, installation and prototype closure

Close disabled/invalid Copilot, missing or mismatched artifacts, specialist
failure, timeout, restart, replay, duplicate/collision, stale digest, network
failure and partial publication. Verify OpenRC/fcron deployment, compare the
Projects source bundle with the deployed repository, run the global suite and
prove installation from a clean checkout.

The prototype is complete only when the full real chain is repeatable,
observable, recoverable and idempotent. There is no phase 0288 and no Chalouf
integrator phase.
