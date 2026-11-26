# Audit de réutilisation MissiPy — 027X

**Date de l'audit : 2026-11-26**  
**Base examinée :** archive `autodoc-master.zip` fournie dans cette conversation.  
**Périmètre :** code source, patches présents dans l'archive, documentation, rapports et tests.  
**Nature :** audit documentaire et de réutilisation ; aucun code fonctionnel n'a été modifié.

## 1. Limites de preuve

L'archive contient le dépôt de travail mais **ne contient pas `.git/`**. Il est donc impossible, sur cette seule base, de certifier :

- la branche active, les branches distantes ou les tags ;
- l'ordre réel des commits et les SHA associés ;
- les commits effectivement poussés ;
- l'état `clean/dirty` du checkout au moment de l'archive ;
- si un patch est commité, seulement appliqué localement, ou encore en attente.

L'ensemble des 518 répertoires de patches a été inventorié (README, metadata disponibles, chemins des diffs et ordre de nommage). Les README/rapports des unités pertinentes pour la chaîne r7-r15/r16 et les bundles les plus récents ont été lus et confrontés aux sources/tests présents. Il ne s'agit pas encore d'une revue ligne par ligne des 518 diffs historiques. La présence d'un fichier correspondant prouve qu'il existe dans l'archive, mais ne remplace pas une comparaison avec le commit parent. Les statuts ci-dessous sont donc des **statuts d'implémentation observée**, pas une attestation Git.

## 2. Inventaire

| Élément | Constat |
|---|---:|
| Entrées ZIP | 6 699 |
| Fichiers Python sous `src/` | 407 |
| Fichiers de tests Python | 1 083 |
| Fichiers sous `doc/` | 2 419 |
| Répertoires de patches sous `patch/` | 518 |
| Patches avec `README.md` | 465 |
| Patches avec `metadata.json` | 449 |
| Patches sans README | 53 |
| Patches sans metadata | 69 |

Les fichiers `patch.diff` des 518 répertoires exposent **4 426 occurrences de chemins** (`+++ b/...` ; un même chemin peut apparaître dans plusieurs patches), correspondant à 3 861 chemins distincts. Répartition des occurrences : 355 sous `src/`, 1 042 sous `tests/`, 2 619 sous `doc/` ou rapports de phase, 410 autres. En nombre de bundles touchant chaque catégorie : 300 touchent `src/`, 486 `tests/`, 504 `doc/` ou rapports, et 280 d'autres chemins. Les catégories se recouvrent : un même patch peut toucher plusieurs catégories.

Le bundle r16-r66-r1 est aussi fourni à la racine sous forme d'archive tar.gz. Son diff est déjà reflété dans les sources de cette archive : un contrôle `patch -p1 --dry-run` le reconnaît comme déjà appliqué. Cela établit une concordance de contenu, pas un statut Git commité/poussé.

### Hygiène du bundle r16-r66-r1

Le diff de ce bundle contient deux fichiers binaires `__pycache__/*.pyc`. Cela contrevient à l'addendum d'hygiène de `doc/code-rules/code_rule.md` et au `.gitignore` du dépôt. Le fait que les chemins soient ignorés ne neutralise pas un fichier explicitement ajouté dans un diff. Le bundle doit être régénéré sans bytecode avant toute application ou publication ; l'absence de `.git` empêche de vérifier si ces fichiers sont suivis dans l'index courant.

Un bundle supplémentaire `0287-r16-r66-r1-lier-tache-deja-decidee-sans-modifier-contrat-handler.tar.gz` est présent à la racine de l'archive.

## 3. Hiérarchie documentaire observée

La documentation actuelle est très riche, mais elle n'a pas de hiérarchie de lecture suffisamment nette :

- `README.md` racine décrit encore le baseline 0260–0269 et des limites qui ne correspondent plus aux adaptateurs et compositions ajoutés ensuite ;
- `doc/README_CURRENT.md` est daté du 2026-07-15 et décrit le début de la progression 0287-r7, alors que l'archive contient des travaux r15/r16 ;
- `doc/architecture/`, `doc/changelogs/`, `doc/changelog/`, `doc/manifests/`, `doc/code-rules/`, `doc/reports/`, `doc/releases/` et les rapports de phase à la racine contiennent de nombreuses preuves spécialisées ;
- les répertoires `patch/<id>/` portent leurs propres README, metadata et diff ; ils constituent l'historique de proposition/application, pas une documentation d'état courant ;
- plusieurs documents de consolidation plus anciens (0153–0156, 0270, 0281, 0282) restent utiles pour la traçabilité, mais ne doivent pas prévaloir sur les preuves plus récentes.

**Décision documentaire :** un seul index d'état courant (`doc/README_CURRENT.md`), un audit de réutilisation (`doc/027X_REUSE_AUDIT.md`) et un index documentaire (`doc/DOCUMENTATION_INDEX.md`). Les documents de phase restent conservés comme preuves historiques ; ils ne sont pas supprimés ni réécrits en masse.

## 4. Architecture canonique à préserver

Les règles structurantes sont cohérentes dans les documents récents et doivent rester invariantes :

| Autorité / surface | Responsabilité |
|---|---|
| Scheduler canonique | Seule autorité d'orchestration et de sélection/exécution des tâches |
| SQL / PostgreSQL | Autorité durable pour commandes, tâches, révisions, analyses, preuves et clôture |
| Qdrant | Projection vectorielle et rappel de références ; jamais autorité durable |
| OpenVINO / multilingual-e5-small | Production et recherche des vecteurs E5 ; dimension exactement 384 |
| EventBus | Observation et diffusion de faits ; pas d'autorité d'exécution |
| PassiveSupervisor / VisPy | Read model et observation ; aucune commande sur l'ordonnancement |
| ControlProxy | Transport des routes/notifications autorisées ; pas de connaissance ni d'orchestration |
| GitHub Actions / ProjectV2 | Entrée de workflow, revue et projection externe ; pas d'autorité locale |
| OpenRC / OS / administrateur | Autorité externe sur le cycle de vie des processus |

Les laboratoires restent des environnements d'exécution derrière les contrats, handlers et adaptateurs existants. Les spécialistes ne déclenchent pas directement d'autres spécialistes et ne créent pas de tâches : ils rendent des résultats ou des propositions qui reviennent au Scheduler.

## 5. Surfaces canoniques à étendre

Les fichiers ci-dessous existent dans `src/` et sont cités par les documents/patches de la chaîne. Ils doivent être réutilisés avant toute création de nouvelle surface.

### 5.1 Contrats spécialistes, laboratoires et liaison

- `src/context/specialist_laboratory_message_contract_0284.py` — contrat historique d'échange v1 ;
- `src/context/specialist_laboratory_transfer_contract_0284.py` — continuité/transfert entre laboratoires ;
- `src/context/specialist_laboratory_message_v2_0287.py` — échange v2 et conversation corrélée ;
- `src/context/specialist_deep_analysis_contract_0287.py` — demande et contribution d'analyse profonde ;
- `src/context/specialist_multitask_model_0287.py` — tâches/capacités spécialisées versionnées ;
- `src/context/server_oriented_deliberation_cycle.py` — cycle de délibération orienté serveur ;
- `src/context/specialist_liaison_synthesis.py` — fragments et synthèse de liaison ;
- `src/context/portable_specialist_real_memory_closure_0284.py` — mémoire spécialiste SQL/E5/Qdrant.

### 5.2 Recherche corrélée et GitHub

- `src/context/github_research_work_package_admissibility_0287.py` — admissibilité du package de recherche ;
- `src/context/github_research_scheduler_intake_0287.py` — intake local ;
- `src/context/github_research_scheduler_command_0287.py` — commande typée ;
- `src/context/github_research_scheduler_command_claim_0287.py` — réclamation durable ;
- `src/context/github_actions_artifact_scan_once_live_0272.py` — scan/fetch existant ;
- `src/context/github_actions_ready_run_copilot_v2_projection_0287.py` — projection Copilot v2 à partir d'un ready run ;
- `src/context/github_copilot_advisory_v2_issue_publication_0287.py` et `src/context/love_final_deliverable_remote_publication_0287.py` — planification/adaptateurs de publication distincts.

### 5.3 Laboratoire natif et spécialistes

- `src/context/love_study_contracts_0287.py` — contrats du domaine prototype ;
- `src/context/native_love_laboratory_scheduler_binding_0287.py` ;
- `src/context/native_love_laboratory_collaboration_scheduler_binding_0287.py` ;
- `src/context/native_love_laboratory_first_specialist_0287.py` ;
- `src/context/native_love_laboratory_second_specialist_0287.py`.

Le laboratoire déterministe fake (`0273/0274`) reste une preuve de chemin de test et ne doit pas être renommé en laboratoire natif. Le laboratoire natif est une surface distincte et déclarée.

### 5.4 Mémoire, récupération et composition du runtime

- `src/context/github_research_love_postgresql_continuation_store_0287.py` ;
- `src/context/github_research_love_transactional_step_runner_0287.py` ;
- `src/context/github_research_love_canonical_ready_task_binding_0287.py` ;
- `src/context/love_postgresql_authority_binding_0287.py` ;
- `src/context/love_openvino_e5_async_query_adapter_0287.py` ;
- `src/context/love_async_hybrid_retrieval_execution_0287.py` ;
- `src/context/love_qdrant_hybrid_query_adapter_0287.py` ;
- `src/context/love_tool_bounded_installed_runtime_composer_0287.py` ;
- `src/context/github_research_love_externally_managed_installed_composition_0287.py`.

Ces surfaces composent des ports/fournisseurs existants. Elles ne justifient pas la création d'un second Scheduler, d'un runtime OpenVINO caché, d'un client Qdrant global ou d'un manager de laboratoire.

## 6. État de la chaîne — preuves présentes dans l'archive

### 6.1 GitHub, Actions et Copilot

**Implémentation observée :**
- artefacts `authoritative_request`, `copilot_advisory` et manifeste corrélé ;
- schéma Copilot v2 avec `concrete_objective`, `expected_result`, `provided_constraints`, `success_criteria` ;
- compatibilité de lecture v1/v2 ;
- adaptateurs de prévisualisation/publication ProjectV2 et Issue ;
- fetch local de runs/artefacts et readiness de `ready_run` ;
- frontières de mutation, digest, décision opérateur, idempotence et readback prévues par les adaptateurs.

**Réserve :** le patch `r16-r4-r1` qui déplaçait la publication d'un commentaire Issue dans le workflow Actions a un correctif `r16-r4-r1-r1` qui rétablit la frontière read-only du workflow. Le workflow reste producteur d'artefacts ; la mutation distante reste locale et explicitement autorisée. Ne pas documenter le workflow comme autorisé à publier lui-même.

### 6.2 Package, contrats et laboratoire

**Implémentation observée :**
- package corrélé `missipy.research.correlated_work_package.v1` ;
- message laboratoire/spécialiste v2 et conversation ordonnée ;
- contrat de demande et contribution d'analyse profonde ;
- modèle multitâche spécialiste ;
- descripteur `laboratory:love-studies-local` ;
- premier et second spécialistes natifs, avec visites séparées soumises au Scheduler ;
- synthèse de liaison et enveloppe de livrable dans les compositions r12/r13/r14.

### 6.3 SQL, E5, Qdrant et runtime installé

**Implémentation observée dans les sources et les documents de phase :**
- autorité SQL/PostgreSQL pour les révisions et analyses ;
- projection/rappel Qdrant avec références SQL ;
- profil E5 384 dimensions ;
- récupération hybride dense/sparse et réhydratation SQL ;
- liaison du runtime PostgreSQL, OpenVINO et Qdrant par ports/fabriques injectés ;
- frontière de lease locale au processus et fermeture inversée des ressources ;
- composition de runtime tool-bounded et composition externe gérée.

**Réserve :** les rapports r16-r64 et r16-r65 indiquent explicitement que les tests fonctionnels de production doivent être exécutés sur le checkout réel ; ils ne revendiquent pas la réussite de la suite globale. La présence des adaptateurs n'est pas une preuve de disponibilité permanente des services ni de réussite d'une exécution distante.

### 6.4 Scheduler / handlers r16

Les documents d'architecture décrivent une progression au-delà du simple routage du package vers un laboratoire :

- r16-r26 : réclamation atomique par un Scheduler canonique actif ;
- r16-r26-r1 à r16-r30 : contrats, catalogue, modèle de tâche, budget/politiques et exécution contrôlée de handlers ;
- r16-r31 à r16-r40 : lancement de tâches spécialistes, persistance, projections, rappel, synthèse, livrable, publication, reprise et prototype bout en bout ;
- r16-r50 : porte d'acceptation réelle corrélant fetch, préparation, publication, clôture SQL et observations temporelles ;
- r16-r64 : noyau d'exécution PostgreSQL ;
- r16-r65 : continuation PostgreSQL et runner transactionnel ;
- r16-r66-r1 : liaison d'une tâche `ready` déjà choisie avec réhydratation de la commande/admission et réutilisation par identité du catalogue/fabrique des handlers existants.

La documentation r16-r66-r1 indique explicitement que **r16-r67 est l'étape suivante** pour fournir les lectures PostgreSQL concrètes de l'admission et les ports d'exécution génériques, puis raccorder cette frontière à la composition OpenRC.

## 7. Matrice de statut à la date de l'audit

| Domaine | Statut observé | Ce qui reste à prouver |
|---|---|---|
| Contrats dual-artifact et Copilot v2 | Implémentés dans les sources | Exécution réelle complète d'un run corrélé |
| Projection Copilot v2 | Adaptateurs présents ; tests ciblés disponibles | Readback sur le ProjectV2 privé avec preuves conservées |
| Package de travail corrélé | Contrat/builder présent | Chaîne de production complète corrélée en exploitation |
| Contrats spécialiste/laboratoire v2 | Implémentés | Utilisation par un cycle complet réel |
| Deux spécialistes natifs | Handlers et bindings présents | Exécution opérationnelle réelle et preuves durables |
| Synthèse de liaison | Surfaces et composition présentes | Validation sur analyses réelles avec contradictions/limites préservées |
| Plan de publication finale | Présent | Publication distante réelle corrélée et readback conservé |
| PostgreSQL / OpenVINO / Qdrant | Adaptateurs et compositions présents | Vérification de l'environnement installé et exécution complète sur serveur |
| Scheduler/handlers r16 | Contrats, services et raccords jusqu'à r16-r66-r1 présents | Étape r16-r67 et validation intégrée |
| Acceptation réelle r16-r50 | Porte et runbook présents | Aucun rapport d'acceptation `accepted` n'a été trouvé dans l'archive |
| Git / commits / branche | Non vérifiable | Fournir un checkout ou bundle Git |

**Conclusion opérationnelle :** le dépôt n'est plus au stade « artefacts et contrats seulement ». Il contient un chemin local spécialisé, des surfaces de synthèse/publication, des adaptateurs runtime et une architecture Scheduler/handlers plus avancée. En revanche, l'archive ne suffit pas à conclure que la chaîne réelle complète a été exécutée et acceptée sur le serveur.

## 8. Contrôles exécutés pendant l'audit actualisé

Exécutés sur l'arborescence extraite de l'archive avec Python 3.13.5 :

- `PYTHONPATH=src:. python -m compileall -q src tests tools` — code retour 0 ;
- tests ciblés des composants r16-r57 à r16-r65 (tests fonctionnels et tests de règles) — **37 passed** au total, dont 34 dans le lot ciblé initial et 3 tests fonctionnels r16-r65 ;
- tests r16-r66-r1 (tests fonctionnels et tests de règles) — **6 passed** ;
- total ciblé non redondant — **43 passed** ;
- `PYTHONPATH=src:. python -m pytest -q tests/rules --ignore=tests/rules/test_generated_artifacts_rule.py` — **1 863 passed**.

La suite complète `PYTHONPATH=src:. python -m pytest -q tests/rules` a été exécutée jusqu'au bout : **1 863 passed, 3 failed**. Les trois échecs sont les tests de `tests/rules/test_generated_artifacts_rule.py` qui invoquent `git ls-files` pour vérifier les SVG, PYO et `.patchqueue.local.json`. Ils échouent parce que l'archive n'a pas de `.git` ; ils ne permettent donc pas de conclure sur l'index Git. Il ne s'agit pas d'une suite de règles entièrement verte.

La suite globale `pytest -q` n'a pas été exécutée. Aucune validation de la branche, du commit, du push ou du runtime réel n'est revendiquée.

## 9. Règles de programmation et de style à appliquer

La référence normative est `doc/code-rules/code_rule.md` (255 fichiers de règles et d'alignement dans `doc/code-rules/`, dont ce document canonique). Les exigences explicites retrouvées sont :

- Python 3.14 et mécanismes modernes du langage ; bibliothèque standard prioritaire ; toute dépendance externe doit être justifiée et annoncée ;
- typage statique exhaustif ; données/commandes/politiques/résultats immuables, notamment `dataclass(frozen=True)` ;
- générateurs et `yield Event(...)` plutôt que les appels bloquants ou les actions directes ; Scheduler seul interprète les intentions ;
- composition plutôt qu'héritage profond, chargement paresseux, politiques explicites, faible couplage, structures testables et rejouables ;
- CLI limitée à l'adaptation : commande typée immuable, aucune fuite de `argparse.Namespace`, logique métier hors du parseur, effets de bord aux frontières ;
- résultats stables, observables et sérialisables ; commandes de recherche bornées ; rapports et écritures de fichiers contrôlés ;
- revue `code_rule_review`, justification de toute mise à jour des règles et tests exécutables sous `tests/rules` pour les invariants stabilisés ;
- patch versionné dans `patch/<id>/` avec `patch.diff`, `README.md`, `metadata.json` ; pas de patch plat, pas de secret, cache/bytecode/SVG généré absent de l'index.

**Limite de style à ne pas masquer :** le dépôt ne définit pas de politique explicite PEP 8/longueur de ligne, ni de configuration Ruff, Black, Mypy, Pyright ou Flake8 repérée. `pytest.ini` ne configure que les chemins et marqueurs de tests. Les exécutables Ruff/Black/Mypy ne sont pas présents dans l'environnement d'audit. Il ne faut donc pas inventer une règle de formatage ou imposer un outil non adopté. Le style de chaque patch doit être contrôlé contre `code_rule.md` et les conventions réellement utilisées dans les modules voisins ; les règles de formatage automatiques restent à définir par le projet si souhaité.

**Écart environnemental :** la règle documentaire cite Python 3.14, tandis que les vérifications de cet audit ont été exécutées avec Python 3.13.5. La compilation et les tests observés sous 3.13 ne certifient pas le comportement sous Python 3.14.

## 9. Décisions de réutilisation

1. Étendre le Scheduler canonique et ses services existants ; ne pas créer un Scheduler de laboratoire ou un orchestrateur de recherche.
2. Réutiliser les contrats v1/v2 et les surfaces de conversation/transfert ; ne pas inventer un nouvel envelope concurrent.
3. Réutiliser `specialist_liaison_synthesis.py` pour la synthèse ; ne pas déplacer la synthèse globale dans chaque spécialiste.
4. Réutiliser le store SQL/PostgreSQL, les ports E5/Qdrant et la réhydratation SQL ; ne jamais faire de Qdrant une autorité.
5. Réutiliser les adaptateurs de publication distincts Copilot et livrable final ; ne pas confondre les deux commentaires/projections.
6. Conserver les workflows Actions comme producteurs d'artefacts ; la mutation GitHub reste derrière la porte locale contrôlée.
7. Garder EventBus, PassiveSupervisor et VisPy en observation-only.
8. Toute nouvelle surface doit être justifiée par un audit de réutilisation ciblé et des tests de règles.

## 10. Suite de travail recommandée

- Récupérer un vrai checkout Git ou `git bundle` pour comparer l'archive à l'historique.
- Exécuter la suite `tests/rules`, puis les tests fonctionnels ciblés r16, puis la suite globale sur la machine de référence.
- Suivre la progression documentée : r16-r67 est l'étape suivante indiquée par le document r16-r66-r1.
- Exécuter le runbook r16-r50 avec un Issue réel et conserver les quatre rapports + observations PostgreSQL ; ne déclarer la clôture qu'après `status=accepted`.
- Ne reprendre la roadmap de dix patches fournie séparément qu'après réconciliation : elle est antérieure à une grande partie du code et des documents présents dans cette archive.

