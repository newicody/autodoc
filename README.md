# Autodoc / MissiPy

`autodoc` est le prototype du micro-kernel coopératif IA MissiPy.

L'objectif n'est pas de construire une application Python monolithique, mais un noyau d'orchestration modulaire, observable, déterministe et rejouable.

## État courant

État de référence : **Phase 4.13 unified E5 command surface**.

Le prototype possède actuellement :

- un `Scheduler` coopératif ;
- une `PriorityQueue` comme chemin de commande ;
- un `Dispatcher` ;
- un `EventBus` passif, réservé à l'observation ;
- un `ComponentProxy` obligatoire entre le noyau et les composants réels ;
- un `ContextEngine` événementiel ;
- un `PolicyEngine` minimal ;
- une télémétrie kernel minimale (`kernel.telemetry`) ;
- une chaîne replay hors Scheduler vivant ;
- un chemin d'inférence fictif ;
- un `BackendRegistry` ;
- un contrat `OpenVINOBackend` ;
- un `RealOpenVINORuntime` optionnel, isolé dans `src/inference/openvino_runtime.py`, sans modèle imposé ;
- un `OpenVINOModelProfileRegistry` déclaratif pour préparer un ou plusieurs modèles sans les charger ;
- un `OpenVINOBackendFactory` qui transforme explicitement un profil en backend enregistrable ;
- un `OpenVINOEmbeddingProfileConfig` configurable, sans modèle local imposé ;
- un contrat embedding raw pour `input_ids` / `attention_mask` et sortie vecteur ;
- un contrat tokenizer injectable, sans dépendance Hugging Face imposée ;
- un pipeline embedding abstrait qui assemble tokenizer, raw inputs, backend et output adapter sans modèle concret imposé ;
- un tokenizer déterministe de test, pure stdlib, pour valider le pipeline sans Hugging Face ni vocabulaire réel ;
- une factory E5 locale validée avec OpenVINO ;
- une CLI embedding E5 ;
- un contrat `query:` / `passage:` ;
- une CLI de ranking local E5 avant Qdrant ;
- un corpus local E5 persistant depuis passages ou sources TXT/Markdown ;
- un rapport de recherche E5 avec score, source, lignes et extrait ;
- un rebuild sûr du corpus E5 avec staging, validation optionnelle et promotion atomique ;
- une procédure de recherche E5 locale dev-ready validée sur le corpus du repo ;
- un garde-fou `--min-score` pour filtrer les résultats E5 locaux trop faibles ;
- une hygiène de découverte des sources E5 locales qui exclut les répertoires et suffixes parasites ;
- des contrôles CLI `--exclude-dir` et `--exclude-file-suffix` pour étendre cette hygiène sans modifier le code ;
- une commande locale `inspect_e5_corpus.py` pour diagnostiquer un corpus E5 JSON en lecture seule ;
- un mode gate optionnel pour transformer les diagnostics E5 en garde-fous CI/dev ;
- un gate diagnostic optionnel dans `rebuild_e5_corpus.py` pour bloquer la promotion d'un candidat douteux ;
- un jeu de validation recherche E5 multi-requêtes avant promotion du corpus candidat ;
- un rapport JSON optionnel de rebuild E5 pour archiver diagnostic, validation et promotion;
- un rapport JSON optionnel de recherche E5 pour conserver requête, seuils, hits et contexte source ;
- une façade CLI E5 unifiée `tools/e5.py` avec sous-commandes `embed`, `rank`, `build`, `search`, `rebuild` et `inspect`.

OpenVINO est branché comme runtime générique à entrées brutes. Le choix du ou des modèles est décrit par profils déclaratifs : `embedding`, `generation` ou `raw`.

La Phase 3.1 ajoute le pont contrôlé entre profil et `BackendRegistry`, sans tokenizer, post-processing ou modèle précis imposé. La Phase 3.2 ajoute une configuration spécialisée pour déclarer un profil `openvino.embedding` local, toujours sans chemin en dur ni chargement automatique.

La Phase 3.3 ajoute la couche IO raw : tokens déjà préparés -> `InferenceRequest.context["inputs"]` -> sortie brute -> vecteur embedding stable.

La Phase 3.4 ajoute le contrat tokenizer : texte -> `TokenizationResult` -> `OpenVINOEmbeddingRawInputs`, sans tokenizer concret imposé.

La Phase 3.5 assemble ces pièces dans un pipeline embedding abstrait mono-texte : tokenizer injectable -> raw inputs -> `InferenceAdapter` -> sorties brutes -> vecteur.

La Phase 3.6 ajoute un tokenizer déterministe de test : il permet de valider le pipeline complet sans dépendance externe, sans vocabulaire réel, et sans prétendre être compatible avec un vrai modèle OpenVINO.

## Règle d'architecture

Le Scheduler ne contient pas de logique métier.

Le chemin d'exécution est :

```text
Component.tick()
-> yield Event(...)
-> ComponentProxy
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> Request.reply
-> ComponentProxy
-> tick().asend(result)
```

Le chemin d'observation est séparé :

```text
EventBus.publish(Event)
-> telemetry / recorder / replay artifacts
```

## Commandes de validation

Depuis la racine du dépôt :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Documentation

- `code_rule.md` : philosophie et règles de codage.
- `doc/ARCHITECTURE_LAYERS.md` : couches logicielles actuelles.
- `doc/PROJECT_REVIEW_PHASE2_6.md` : audit du modèle actuel.
- `doc/OPENVINO_MODEL_STRATEGY.md` : stratégie proposée avant choix du ou des modèles OpenVINO.
- `doc/MODEL_PROFILES_PHASE3_0.md` : contrat des profils déclaratifs OpenVINO.
- `doc/MODEL_FACTORY_PHASE3_1.md` : construction contrôlée de backends depuis les profils.
- `doc/MODEL_EMBEDDING_PROFILE_PHASE3_2.md` : configuration déclarative d’un profil embedding OpenVINO.
- `doc/MODEL_EMBEDDING_RAW_PHASE3_3.md` : contrat IO raw pour entrées tokenisées et sortie vecteur.
- `doc/MODEL_TOKENIZER_CONTRACT_PHASE3_4.md` : contrat tokenizer injectable, sans dépendance externe imposée.
- `doc/MODEL_EMBEDDING_PIPELINE_PHASE3_5.md` : pipeline embedding abstrait sans tokenizer concret ni Qdrant.
- `doc/MODEL_DETERMINISTIC_TOKENIZER_PHASE3_6.md` : tokenizer de test déterministe, pure stdlib, pour valider le pipeline avant un tokenizer réel.
- `doc/MODEL_E5_PIPELINE_FACTORY_PHASE3_8.md` : factory de pipeline local `multilingual-e5-small`.
- `doc/MODEL_E5_CLI_PHASE3_9.md` : commande de développement pour tester un embedding E5 local depuis le terminal.
- `doc/MODEL_E5_QUERY_PASSAGE_PHASE3_10.md` : contrat `query:` / `passage:` et mini-ranker local avant Qdrant.
- `doc/MODEL_E5_RANK_CLI_PHASE3_11.md` : commande de développement pour classer plusieurs passages avec E5 local.
- `doc/MODEL_E5_CORPUS_PHASE3_12.md` : corpus local JSON persistant avant Qdrant.
- `doc/MODEL_E5_SOURCES_PHASE3_13.md` : ingestion TXT/Markdown vers corpus E5.
- `doc/MODEL_E5_SEARCH_REPORT_PHASE3_14.md` : rapport de résultats avec contexte source.
- `doc/CHANGELOG_PHASE4_2_E5_LOCAL_SEARCH.md` : procédure de recherche E5 locale dev-ready.
- `doc/CHANGELOG_PHASE4_3_E5_SCORE_GUARD.md` : garde-fou de score minimal pour recherche E5 locale.
- `doc/CHANGELOG_PHASE4_6_E5_CORPUS_DIAGNOSTICS.md` : diagnostic local du corpus E5 JSON.
- `doc/CHANGELOG_PHASE4_9_E5_SEARCH_VALIDATION_SET.md` : validation recherche multi-requêtes avant promotion.
- `doc/CHANGELOG_PHASE4_10_E5_REBUILD_REPORT_FILE.md` : rapport JSON optionnel du rebuild E5.
- `doc/CHANGELOG_PHASE4_11_E5_SEARCH_REPORT_FILE.md` : rapport JSON optionnel de la recherche E5.
- `doc/CHANGELOG_PHASE4_4_E5_SOURCE_HYGIENE.md` : hygiène de découverte des sources E5 locales.
- `doc/docs/architecture/inference/52_e5_search_report.dot` : rapport E5 enrichi avec lien vers le garde-fou de score.
- `doc/docs/architecture/inference/57_e5_score_guard.dot` : détail Phase 4.3 du filtrage `--min-score`.
- `doc/docs/architecture/inference/60_e5_corpus_diagnostics.dot` : inspection locale du corpus E5 JSON.
- `doc/docs/architecture/inference/63_e5_search_validation_set.dot` : validation recherche multi-requêtes du candidat rebuild.
- `doc/docs/architecture/inference/64_e5_rebuild_report_file.dot` : artefact JSON optionnel du rebuild E5.
- `doc/docs/architecture/inference/65_e5_search_report_file.dot` : artefact JSON optionnel de recherche E5.
- `doc/docs/architecture/inference/58_e5_source_hygiene.dot` : détail Phase 4.4 du filtrage des sources parasites avant chunking.
- `doc/docs/architecture/*.dot` : roadmap DOT navigable ; les SVG sont générés par le makefile.

## Développement

Les fichiers `.svg` ne sont pas édités à la main. Les graphes sources sont les `.dot`.

Les fichiers de cache Python (`__pycache__`, `.pyc`, `.pytest_cache`) ne doivent pas être versionnés.

## Rule audit

Before integrating real OpenVINO runtime code, the repository includes code-rule guard tests:

```bash
PYTHONPATH=src pytest -q tests/rules
```

These tests enforce the current interpretation of `code_rule.md`: stdlib-first imports, frozen contract dataclasses, Scheduler isolation from backend/domain layers, and no direct OpenVINO import outside the explicit runtime phase.

## Phase 3.8

La Phase 3.8 ajoute une factory de pipeline local `multilingual-e5-small`. Elle transforme le test OpenVINO réel validé localement en capacité configurable : profil E5, tokenizer local Transformers, runtime OpenVINO et pipeline embedding sont assemblés sans modifier le Scheduler.

## Phase 3.9 — Tester l'embedding E5 local

Quand le modèle local est installé, la commande de développement est :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "query: test de recherche vectorielle pour MissiPy"
```

Sortie JSON avec aperçu :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --format json \
  "query: test"
```

Le vecteur complet n'est imprimé qu'avec `--full-vector`.

## Phase 3.10 — Query / Passage E5

E5 distingue maintenant explicitement deux rôles :

```text
query: texte qui cherche
passage: texte qui peut être retrouvé
```

La CLI accepte `--role` pour éviter les textes bruts ambigus :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role query \
  "je me suis fait baiser"
```

Pour encoder un document :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role passage \
  "j'ai été arnaqué par un vendeur"
```

Un mini-ranker local `E5LocalRanker` permet aussi de valider `1 query -> N passages -> scores` avant Qdrant.

## Phase 3.11 — Classer des passages localement

Avant Qdrant, on peut tester un mini-corpus directement :

```bash
./tools/rank_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "je me suis fait baiser" \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel" \
  --passage "documentation OpenVINO"
```

Sortie JSON et limite :

```bash
./tools/rank_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --format json \
  --limit 2 \
  "je me suis fait baiser" \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel"
```

Cette commande encode la query en `query:` et les passages en `passage:` si les préfixes sont absents.

## Phase 3.12 — Corpus local E5 persistant

Le ranking direct recalcule les passages à chaque requête. La phase 3.12 ajoute un corpus local JSON pour persister les embeddings des passages.

Construire un corpus :

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --output /tmp/e5_corpus.json \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel" \
  --passage "documentation OpenVINO"
```

Rechercher dedans :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --limit 3 \
  "je me suis fait baiser"
```

Cette couche reste un banc de test local avant Qdrant : elle ne fait pas encore d'index ANN ou de filtrage avancé.

La mise à jour incrémentale arrive en Phase 3.15 via `--reuse-index`.

## Phase 3.13 — Indexer un dossier TXT/Markdown

La Phase 3.13 ajoute l’ingestion locale de sources `.md`, `.markdown` et `.txt`.

Les fichiers sont découverts dans un ordre stable, lus en UTF-8, découpés par paragraphes, puis convertis en `E5CorpusDocument` avec métadonnées `source_path`, `chunk_index`, `start_line` et `end_line`.

Construire un corpus depuis un dossier :

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir /data/notes \
  --chunk-chars 1200 \
  --output /tmp/e5_corpus.json \
  --overwrite
```

Puis rechercher :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  "question utilisateur"
```

Cette étape reste volontairement avant Qdrant : elle permet de vérifier le découpage, les métadonnées et la qualité des scores avec un corpus JSON local.

## Phase 3.14 — Résultats avec contexte source

La recherche dans un corpus local affiche maintenant le fichier source, les lignes et un extrait de chunk quand ces métadonnées existent :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --excerpt-chars 180 \
  "je cherche une arnaque vendeur"
```

Pour inclure le chunk complet :

```bash
./tools/search_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --full-text \
  "je cherche une arnaque vendeur"
```

Cette étape reste locale et déterministe : elle ne remplace pas Qdrant, elle prépare le format de résultat exploitable.

## Phase 3.15 — Reconstruire un corpus sans tout recalculer

La Phase 3.15 ajoute un build incrémental par hash. Quand un ancien index est fourni, les chunks inchangés réutilisent leur embedding existant. Seuls les chunks nouveaux ou modifiés sont recalculés.

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir /data/notes \
  --chunk-chars 1200 \
  --reuse-index /tmp/e5_corpus.json \
  --output /tmp/e5_corpus.next.json \
  --overwrite
```

La sortie indique :

```text
reused_count: chunks repris depuis l'ancien index
embedded_count: chunks recalculés
removed_count: chunks disparus depuis l'ancien index
```

Le schéma JSON reste `missipy.e5.corpus.v1`; les hash sont stockés dans les métadonnées pour préserver la compatibilité.

## Phase 3.16 — Build atomique du corpus

La Phase 3.16 rend l'écriture du corpus plus sûre : `build_e5_corpus.py` écrit d'abord dans un fichier temporaire situé à côté de la cible, relit et valide ce JSON, puis remplace l'index final seulement si tout est correct.

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir /data/notes \
  --reuse-index /tmp/e5_corpus.json \
  --output /tmp/e5_corpus.next.json \
  --overwrite
```

La sortie CLI indique maintenant `atomic_write: True`.

Le fichier temporaire suit le modèle `.nom_du_fichier.tmp` dans le même répertoire que la cible, afin que le remplacement reste atomique sur le même système de fichiers.

## Phase 3.17 — Verrou fichier de build corpus

La Phase 3.17 ajoute un verrou fichier pendant la construction du corpus E5.

L'écriture atomique protège le remplacement final, mais elle n'empêchait pas encore deux processus de construire simultanément le même index.

Désormais, `build_e5_corpus.py` crée par défaut un verrou voisin de la cible :

```text
/tmp/e5_corpus.json
/tmp/.e5_corpus.json.lock
/tmp/.e5_corpus.json.tmp
```

Le verrou est acquis par création atomique `O_CREAT | O_EXCL`.

Si un autre build vise déjà le même fichier, la commande échoue explicitement au lieu de travailler en concurrence.

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir /data/notes \
  --reuse-index /tmp/e5_corpus.json \
  --output /tmp/e5_corpus.next.json \
  --overwrite
```

La sortie CLI indique maintenant :

```text
atomic_write: True
lock_enabled: True
lock_path: /tmp/.e5_corpus.next.json.lock
```

En développement uniquement, le verrou peut être désactivé avec `--no-lock`, mais le comportement normal doit rester verrouillé.

## Phase 3.18 — Rebuild sûr du corpus E5

La Phase 3.18 ajoute une commande dédiée au cycle opérationnel complet de reconstruction d'un corpus local : construire un candidat, le relire, exécuter éventuellement une recherche de validation, puis promouvoir le candidat vers l'index final seulement si tout a réussi.

Flux :

```text
corpus.json actuel
-> .corpus.json.lock
-> .corpus.json.rebuild.json
-> validation structurelle
-> validation recherche optionnelle
-> replace(corpus.json)
-> release lock
```

Exemple :

```bash
./tools/rebuild_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --source-dir /data/notes \
  --chunk-chars 1200 \
  --validation-query "test de recherche"
```

Cette commande évite le `mv` manuel après un build incrémental.

Elle reste hors Scheduler, hors Qdrant et conserve le format `missipy.e5.corpus.v1`.

## Phase 4.2 — Recherche E5 locale dev-ready

La Phase 4.2 fige l'usage opérationnel local de la recherche E5 avant l'introduction d'une base vectorielle externe.

Le corpus du dépôt peut être reconstruit avec promotion sûre :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --chunk-chars 1200 \
  --validation-query "rebuild sûr avec staging validation promotion"
```

La sortie validée confirme :

```text
promoted: True
atomic_write: True
lock_enabled: True
validation_search: True
size: 218
```

La recherche locale exploite ensuite le corpus JSON sans modifier son format :

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  "rebuild sûr avec staging validation promotion"
```

La sortie texte affiche les informations nécessaires au diagnostic :

```text
score
id
source
lines
chunk
excerpt
```

La sortie JSON reste disponible pour l'intégration future :

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 3 \
  --format json \
  "OpenVINO multilingual-e5-small local"
```

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas de nouveau backend ;
- pas d'index ANN ;
- pas de cache runtime supplémentaire.

## Phase 4.3 — Garde-fou de score E5 local

La Phase 4.3 ajoute un seuil minimal optionnel pour éviter de considérer comme exploitables les meilleurs résultats d'un corpus trop pauvre ou hors sujet.

La recherche conserve le comportement historique par défaut : sans seuil, tous les hits classés par score peuvent être retournés dans la limite demandée.

Avec `--min-score`, seuls les hits dont le score est supérieur ou égal au seuil sont conservés :

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --min-score 0.86 \
  "rebuild sûr avec staging validation promotion"
```

Le seuil est inclusif et doit rester dans l'intervalle `[-1.0, 1.0]`.

La sortie peut donc afficher :

```text
hit_count: 0
```

si aucun résultat ne franchit le seuil. Ce comportement est volontaire : il distingue un corpus interrogeable d'un corpus réellement utile pour la requête.

Cette phase reste locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas d'index ANN ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.


## Phase 4.4 — Hygiène des sources E5 locales

La Phase 4.4 ajoute une hygiène déterministe de découverte des sources avant lecture, découpage et vectorisation.

Le but est d'éviter qu'un `--source-dir .` ingère accidentellement des fichiers parasites quand le dépôt contient des caches, des artefacts générés ou des répertoires techniques.

Les exclusions par défaut couvrent notamment :

```text
.git
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.tox
.venv
venv
build
dist
```

Les suffixes exclus par défaut sont :

```text
.pyc
.pyo
.svg
```

Cette hygiène est centralisée dans `src/inference/e5_sources.py` afin que les commandes de build et de rebuild sûr en bénéficient via le même chemin source.

Le format du corpus reste inchangé :

```text
missipy.e5.corpus.v1
```

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format corpus ;
- pas d'index ANN ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.5 — Contrôles CLI d'hygiène des sources E5

La Phase 4.5 expose dans les commandes de build et de rebuild sûr les garde-fous d'hygiène centralisés en Phase 4.4.

Les exclusions par défaut restent actives. Les options CLI ajoutent seulement des exclusions supplémentaires, sans désactiver les garde-fous communs.

Exemple build :

```bash
PYTHONPATH=src ./tools/build_e5_corpus.py \
  --source-dir . \
  --exclude-dir vendor \
  --exclude-dir generated \
  --exclude-file-suffix .draft.md \
  --output /tmp/autodoc_e5_corpus.json \
  --overwrite
```

Exemple rebuild sûr :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --exclude-dir vendor \
  --exclude-dir generated \
  --exclude-file-suffix .draft.md \
  --validation-query "OpenVINO E5 local"
```

Ces options passent par le même chemin central :

```text
CLI build/rebuild
-> options source hygiene
-> e5_sources.py
-> discover_e5_source_files()
-> read_text/chunking
-> corpus E5 local
```

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas d'index ANN ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.6 — Diagnostics locaux du corpus E5

La Phase 4.6 ajoute une commande d'inspection locale pour diagnostiquer un corpus E5 JSON déjà vectorisé, sans ouvrir le fichier à la main.

La commande lit le même format `missipy.e5.corpus.v1` que les étapes précédentes :

```bash
PYTHONPATH=src ./tools/inspect_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json
```

Elle affiche notamment :

```text
schema
model / backend / tokenizer
dimension
chunk_count
source_count
extensions
top_sources
embedding_reuse
health
```

La sortie JSON est disponible pour une intégration future :

```bash
PYTHONPATH=src ./tools/inspect_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --format json
```

Cette phase aide à répondre rapidement à des questions de contrôle :

- combien de chunks contient l'index ;
- quelles extensions dominent ;
- quelles sources dominent ;
- combien d'embeddings viennent d'un build incrémental ;
- si des métadonnées source manquent ;
- si le corpus contient des anomalies structurelles simples.

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas d'index ANN ;
- inspection en lecture seule ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.


## Phase 4.7 — Diagnostic gate du corpus E5

La Phase 4.7 rend les diagnostics de corpus E5 actionnables dans un workflow développeur ou CI.

La commande d'inspection reste en lecture seule, mais elle peut maintenant retourner un code d'échec si le corpus ne respecte pas les seuils demandés :

```bash
PYTHONPATH=src ./tools/inspect_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --min-chunks 10 \
  --max-missing-source-metadata 0 \
  --max-empty-texts 0 \
  --max-dimension-mismatches 0 \
  --fail-on-warning
```

Le mode gate conserve les sorties texte et JSON de la Phase 4.6, puis ajoute une section `gate` quand au moins un seuil est demandé.

Codes retour :

```text
0 : diagnostic lu et seuils respectés
1 : erreur de lecture ou corpus invalide
2 : option invalide ou seuil gate violé
```

Seuils disponibles :

- `--min-chunks N` : nombre minimal de chunks requis ;
- `--max-missing-source-metadata N` : nombre maximal de chunks sans `source_path` ;
- `--max-empty-texts N` : nombre maximal de textes vides ;
- `--max-dimension-mismatches N` : nombre maximal de dimensions incohérentes ;
- `--fail-on-warning` : échoue si le diagnostic contient des avertissements.

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas de promotion automatique ;
- inspection en lecture seule ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.8 — Diagnostic gate du rebuild E5 sûr

La Phase 4.8 réutilise les diagnostics et seuils de la Phase 4.7 directement dans le rebuild sûr du corpus E5.

Le flux reste le même : le corpus candidat est construit dans un fichier de staging, relu, diagnostiqué, validé, puis promu uniquement si les garde-fous demandés sont respectés.

Exemple :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-query "OpenVINO E5 local" \
  --min-chunks 10 \
  --max-missing-source-metadata 0 \
  --max-empty-texts 0 \
  --max-dimension-mismatches 0 \
  --fail-on-warning
```

Les seuils disponibles sont identiques au diagnostic gate en lecture seule :

- `--min-chunks N` : nombre minimal de chunks requis avant promotion ;
- `--max-missing-source-metadata N` : nombre maximal de chunks sans `source_path` ;
- `--max-empty-texts N` : nombre maximal de textes vides ;
- `--max-dimension-mismatches N` : nombre maximal de dimensions incohérentes ;
- `--fail-on-warning` : échoue si le diagnostic candidat contient des avertissements.

Si le gate est activé et passe, la sortie contient une section `diagnostic_gate` :

```text
diagnostic_gate:
  enabled: True
  passed: True
  violations: none
```

Si un seuil est violé, le staging n'est pas promu. Par défaut, le staging est nettoyé ; `--keep-staging` permet de conserver le candidat pour inspection.

Codes retour :

```text
0 : candidat construit, gate respecté si demandé, promotion ou dry-run OK
1 : erreur de lecture, build, validation ou écriture
2 : option invalide ou diagnostic gate violé
```

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas de promotion si le diagnostic gate échoue ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.9 — Jeu de validation recherche E5

La Phase 4.9 rend la validation recherche du rebuild E5 plus robuste : une seule `--validation-query` ne suffit pas toujours à vérifier qu'un corpus candidat répond aux intentions importantes du projet.

Le rebuild sûr accepte maintenant plusieurs requêtes de validation et un fichier de requêtes :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-query "rebuild sûr staging promotion" \
  --validation-query "Scheduler telemetry code_rule" \
  --validation-query "OpenVINO multilingual-e5-small local" \
  --validation-min-score 0.80
```

Ou depuis un fichier :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-queries-file doc/e5_validation_queries.txt \
  --validation-min-score 0.80
```

Chaque requête est exécutée sur le corpus candidat relu depuis le staging. Si une requête ne produit aucun hit après application du seuil `--validation-min-score`, le staging n'est pas promu.

La sortie texte indique maintenant :

```text
validation_search: True
validation_query_count: 3
validation_min_score: 0.80000000
validation_hit_count: 3
validation_best_score: 0.91230000
validation_passed: True
```

La sortie JSON expose aussi le détail de chaque requête dans `validation.queries`.

Cette phase reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format `missipy.e5.corpus.v1` ;
- pas de promotion si une requête de validation échoue ;
- validation après diagnostic gate et avant promotion finale ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.10 — Rapport JSON de rebuild E5

La Phase 4.10 ajoute un artefact de rebuild optionnel.

Le rebuild sûr peut écrire un rapport JSON stable contenant le même résumé que la sortie JSON CLI :

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --validation-query "rebuild sûr staging promotion" \
  --validation-query "OpenVINO multilingual-e5-small local" \
  --validation-min-score 0.80 \
  --report-file /tmp/autodoc_e5_rebuild_report.json
```

Le rapport contient notamment :

```text
index
staging
promoted
model/backend/tokenizer/dimension
size
validation
diagnostic_gate, si activé
reused_count / embedded_count / removed_count, si disponibles
```

Le fichier est écrit uniquement après rebuild réussi, diagnostic gate réussi et validation recherche réussie.

Cette phase prépare les futurs usages CI, HTML et audit de corpus sans changer le format `missipy.e5.corpus.v1`.

Elle reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format corpus ;
- pas de promotion si le diagnostic ou la validation échoue ;
- rapport optionnel seulement ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.


## Phase 4.11 — Rapport JSON de recherche E5

La Phase 4.11 ajoute un artefact de recherche optionnel.

La recherche locale peut écrire un rapport JSON stable contenant le même résumé que la sortie JSON CLI :

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --min-score 0.80 \
  --report-file /tmp/autodoc_e5_search_report.json \
  "OpenVINO multilingual-e5-small local"
```

Le rapport contient notamment :

```text
query
prefixed_query
index
model/backend/tokenizer/dimension
hit_count
hits avec score, source, lignes, chunk et extrait
```

Le fichier est écrit uniquement si la recherche réussit. Il est produit via fichier temporaire voisin puis remplacement final.

Cette phase prépare les futurs usages d'audit, d'interface HTML et de workflow question -> contexte sans changer le format `missipy.e5.corpus.v1`.

Elle reste volontairement locale :

- pas de Qdrant ;
- pas de Scheduler ;
- pas de changement du format corpus ;
- rapport optionnel seulement ;
- mise à jour des graphes DOT d'inférence uniquement ;
- pas de SVG versionné.

## Phase 4.12-r2 — réalignement code_rule E5

La Phase 4.12-r2 ne change pas le format `missipy.e5.corpus.v1` et n'ajoute ni Qdrant ni Scheduler.
Elle conserve l'ancien `doc/code_rule.md` comme socle et ajoute seulement un addendum court pour appliquer cette philosophie aux phases E5 4.2 → 4.11 :

```text
CLI adapter
-> Command dataclass immuable
-> Policy dataclass immuable
-> use-case testable
-> Result dataclass immuable
-> renderer / report_io
```

Les outils E5 sont des adaptateurs temporaires, pas une exception à la philosophie du noyau. Même exposé par une CLI, le cœur du code doit rester écrit comme un futur composant pilotable par événement : intention typée, politiques explicites, résultat immuable et effets IO isolés.

Nouveaux contrats :

- `E5BuildCommand`
- `E5SearchCommand`
- `E5RebuildCommand`
- `E5InspectCommand`
- `E5SearchPolicy`
- `E5DiagnosticGatePolicy`
- `E5SearchValidationPolicy`
- `JsonReportWritePolicy`

Les écritures JSON de rapport sont centralisées dans `src/inference/report_io.py`.
Chaque phase future doit documenter explicitement la revue `code_rule` :

```text
code_rule_review: done
code_rule_update_required: true|false
```

## Phase 4.13 — Surface de commande E5 unifiée

La Phase 4.13 réduit la dispersion de l'outillage E5 sans supprimer les scripts historiques.

Les scripts existants restent des wrappers de compatibilité :

```text
tools/embed_e5.py
tools/rank_e5.py
tools/build_e5_corpus.py
tools/search_e5_corpus.py
tools/rebuild_e5_corpus.py
tools/inspect_e5_corpus.py
```

La nouvelle direction est une façade unique :

```bash
PYTHONPATH=src ./tools/e5.py embed "query: exemple"
PYTHONPATH=src ./tools/e5.py search --index /tmp/autodoc_e5_corpus.json "OpenVINO local"
PYTHONPATH=src ./tools/e5.py rebuild --index /tmp/autodoc_e5_corpus.json --source-dir .
PYTHONPATH=src ./tools/e5.py inspect --index /tmp/autodoc_e5_corpus.json
```

Le nouveau module `src/inference/e5_tool_cli.py` reste volontairement fin :

```text
argv
-> E5ToolCommand
-> E5ToolDispatchPolicy
-> handler de sous-commande existant
```

Cette phase ne change pas le format `missipy.e5.corpus.v1`, n'ajoute pas Qdrant, ne modifie pas le Scheduler et ne charge aucun backend implicitement. Elle applique l'addendum Phase 4.12-r2 : les CLI sont des adaptateurs temporaires et leur cœur reste une intention typée avec politique explicite.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: la réduction de surface CLI était déjà prévue par l'addendum Phase 4.12-r2 ; aucune nouvelle règle n'est nécessaire.
```


## Phase 4.14 — E5 context bundle

La Phase 4.14 ajoute un bundle de contexte dérivé des résultats de recherche E5.

La commande `search` peut maintenant produire un artefact JSON de contexte :

```bash
PYTHONPATH=src ./tools/e5.py search \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --context-file /tmp/autodoc_e5_context.json \
  "OpenVINO local"
```

Ce fichier contient :

```text
query
prefixed_query
index
model/backend/tokenizer/dimension
item_count
items avec rank, id, score, source_path, line_range, chunk_index, excerpt
```

Le bundle est construit depuis `E5SearchReport`, donc il ne relance pas une recherche séparée et ne change pas le format `missipy.e5.corpus.v1`.

Cette phase évite d'ajouter un nouveau script CLI : la surface reste `tools/e5.py search`, avec les wrappers historiques toujours conservés. L'écriture JSON reste centralisée dans `report_io.write_json_report_atomic()`.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: ajout de la règle demandée sur les bibliothèques hors stdlib ; 4.14 n'ajoute aucune dépendance externe.
```

## Phase 4.15 — E5 context consumer contract

La Phase 4.15 ajoute un contrat de consommation du bundle de contexte E5 sans brancher de LLM, de Scheduler ni de Qdrant.

Le flux préparé est :

```text
E5ContextBundle
-> E5ContextConsumptionPolicy
-> consume_e5_context_bundle()
-> E5ConsumedContext
```

`E5ConsumedContext` fournit un texte de contexte déterministe, borné par budget de caractères, et une projection JSON stable pour un futur composant de réponse ou un futur `InferenceContext`.

Exemple d'usage interne :

```python
from inference.e5_context_consumer import E5ContextConsumptionPolicy, consume_e5_context_bundle

consumed = consume_e5_context_bundle(
    bundle,
    E5ContextConsumptionPolicy(max_chars=4000, max_items=5),
)
```

Cette phase ne crée pas de nouveau script CLI. Elle garde le domaine pur : le consommateur ne lit ni n'écrit aucun fichier. Les effets IO restent dans les adaptateurs existants.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: le contrat de consommation applique les règles Phase 4.12-r2 existantes ; aucune nouvelle guideline n'est nécessaire.
```

## Phase 4.16 — E5 answer prompt packet

La Phase 4.16 ajoute un contrat de paquet de prompt E5 sans brancher de LLM, de Scheduler ni de Qdrant.

Le flux local devient :

```text
E5ContextBundle
-> E5ConsumedContext
-> E5AnswerPromptPacket
```

Le module `src/inference/e5_answer_prompt.py` introduit :

- `E5AnswerPromptPolicy` : instructions explicites de construction du prompt ;
- `E5AnswerPromptPacket` : résultat immuable, texte/JSON stable ;
- `build_e5_answer_prompt()` : fonction pure transformant un contexte consommé en paquet de prompt.

Cette phase ne génère pas de réponse. Elle prépare seulement un contrat déterministe pour une future couche d'inférence.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: le paquet de prompt applique les règles Phase 4.12-r2 existantes ; aucune nouvelle guideline n'est nécessaire.
```

## Phase 4.17 — E5 prompt file CLI

La Phase 4.17 branche la chaîne locale complète dans la sous-commande `search`, sans appeler de LLM, sans Qdrant et sans Scheduler.

Le flux disponible devient :

```text
search E5
-> E5SearchReport
-> E5ContextBundle
-> E5ConsumedContext
-> E5AnswerPromptPacket
-> artefacts JSON optionnels
```

La commande peut maintenant produire plusieurs artefacts en une seule recherche :

```bash
PYTHONPATH=src ./tools/e5.py search \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --context-file /tmp/autodoc_context.json \
  --consumed-context-file /tmp/autodoc_consumed_context.json \
  --prompt-file /tmp/autodoc_prompt.json \
  --context-max-chars 4000 \
  "OpenVINO local"
```

Les nouvelles options sont :

```text
--consumed-context-file FILE
--prompt-file FILE
--context-max-chars INT
--context-max-items INT
--context-include-scores
--prompt-system-instruction TEXT
--prompt-answer-instruction TEXT
```

La CLI reste un adaptateur de bordure : le domaine construit les structures immuables, et `report_io.write_json_report_atomic()` écrit les fichiers JSON.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.17 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```

## Phase 4.18 — E5 dry-run artifact directory

La Phase 4.18 ajoute un mode dry-run compact à la sous-commande `search`, sans créer de nouveau script et sans appeler de LLM, de Scheduler ni de Qdrant.

Le flux reste le même que 4.17, mais une seule option peut maintenant préparer les artefacts de prototype :

```bash
PYTHONPATH=src ./tools/e5.py search \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --artifact-dir /tmp/autodoc_e5_dry_run \
  --context-max-chars 4000 \
  "OpenVINO local"
```

Par défaut, `--artifact-dir DIR` écrit :

```text
DIR/report.json
DIR/context.json
DIR/consumed_context.json
DIR/prompt.json
```

Les chemins explicites restent prioritaires. Par exemple, `--artifact-dir DIR --report-file /tmp/report.json` écrit le rapport dans `/tmp/report.json`, mais conserve les autres artefacts dans `DIR/`.

Cette phase ferme le chemin local de prototype : recherche, contexte brut, contexte consommé et paquet de prompt peuvent être produits en une passe, sans génération de réponse.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18 applique les règles Phase 4.12-r2 et la règle stdlib introduite en 4.14 ; aucune nouvelle guideline n'est nécessaire.
```


## Phase 4.18-r1 — Source Candidate / GitHub Project Orchestrator Architecture

La Phase 4.18-r1 inscrit dans l’architecture une brique future : GitHub Projects, issues, actions et artefacts pourront servir de surface de pilotage pour le serveur local autodoc/MissiPy.

L’idée importante est qu’un push, un ticket, une issue ou un artefact peut devenir une **source candidate**. Cette source candidate peut ensuite être rejetée, archivée, enrichie, promue en contexte autonome ou fusionnée dans un contexte existant.

Le flux conceptuel devient :

```text
push / issue / ticket / artefact
-> graine de source
-> enrichissement serveur
-> validation utilisateur
-> devient contexte autonome
   ou fusionne dans un contexte existant
-> retour GitHub
-> nouvelle itération
```

GitHub n’est pas la base de connaissance autoritative. GitHub sert d’interface de pilotage, de validation, de synchronisation et de miroir publiable. La source enrichie reste sur la machine serveur.

La roadmap future est clarifiée :

```text
Phase 4 = moteur local E5 et contexte
Phase 5 = serveur local / Scheduler / contexte runtime
Phase 6 = GitHub Project Orchestrator
Phase 7 = boucle aller-retour GitHub <-> serveur <-> git
```

Cette phase ne branche pas l’API GitHub, ne crée pas de token, n’ajoute pas de polling réseau et ne dépend pas de Copilot. Elle ajoute uniquement la place architecturale de cette couche.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18-r1 ajoute uniquement une architecture future documentée ; aucune règle de code nouvelle n'est nécessaire.
```

## Phase 4.18-r2 — Source Candidate dans l'architecture globale

La Phase 4.18-r2 corrige l'intégration documentaire de 4.18-r1 : la couche GitHub Project Orchestrator / SourceCandidate n'est plus seulement présente dans les graphes `integrations/`, elle devient visible depuis le graphe général `doc/docs/architecture/00_global.dot`.

Le graphe global ajoute un layer futur :

```text
Layer 11 — Remote Work Intake future
```

Ce layer expose :

```text
GitHubProject
GitHubAction
CopilotMetadata
SourceCandidate
LocalAuthority
GitHubFeedback
```

Le flux conceptuel affiché dans la carte générale devient :

```text
GitHub Project / Issue / Push / Ticket
-> GitHub Action
-> metadata Copilot optionnelles
-> SourceCandidate
-> source autoritative serveur local
-> ContextEngine / Knowledge future
-> projection GitHub
-> boucle de statut / validation
```

Cette intégration reste volontairement documentaire. Elle n'ajoute ni API GitHub, ni token, ni polling réseau, ni dépendance Copilot, ni branchement Scheduler.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18-r2 intègre une couche future dans le graphe global sans ajouter de code runtime ni de dépendance externe.
```

## Phase 4.19 — Audit final Phase 4

La Phase 4.19 clôt l'audit du moteur local E5 avant la phase de fermeture 4.20.

Le moteur local E5 est maintenant représenté comme un stack complet dans l'architecture globale :

```text
E5 local context stack — Phase 4 final
```

Il couvre :

```text
corpus local
-> build / rebuild sûr
-> diagnostics / gates / validation
-> search
-> E5SearchReport
-> E5ContextBundle
-> E5ConsumedContext
-> E5AnswerPromptPacket
-> dry-run artifact directory
```

La Phase 4.19 ajoute aussi un rapport documentaire :

```text
doc/PHASE4_FINAL_AUDIT.md
```

Ce rapport fixe les frontières importantes :

```text
pas de Scheduler
pas de Qdrant
pas de LLM de réponse
pas d'API GitHub
IO uniquement en bordure CLI / report_io.py
aucune dépendance hors stdlib
```

La carte globale `doc/docs/architecture/00_global.dot` relie maintenant la future couche `SourceCandidate` au stack E5 local afin de montrer le futur flux :

```text
GitHub Project / Issue / Push / Ticket
-> SourceCandidate
-> source autoritative serveur local
-> E5 local context stack
-> ContextEngine / Knowledge future
-> retour GitHub
```

La Phase 4.20 pourra maintenant être courte : rapport de capacité final, commandes utiles, artefacts produits, puis préparation Phase 5.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.19 audite les frontières existantes et ne modifie pas les règles de programmation.
```

## Phase 4.20 — Clôture Phase 4

La Phase 4.20 ferme officiellement l'étape 4.

Elle ne développe pas de nouveau runtime : elle fige le bilan, les commandes utiles, les artefacts produits et les portes d'entrée Phase 5.

Le résultat Phase 4 est maintenant clair :

```text
corpus local
-> build / rebuild sûr
-> diagnostics / gates / validation
-> search local
-> report.json
-> context.json
-> consumed_context.json
-> prompt.json
```

La commande de dry-run locale reste le point d'entrée pratique :

```bash
PYTHONPATH=src ./tools/e5.py search \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --artifact-dir /tmp/autodoc_e5_dry_run \
  --context-max-chars 4000 \
  "OpenVINO local"
```

La clôture confirme aussi les limites volontaires :

```text
pas de Scheduler
pas de Qdrant
pas de LLM de réponse
pas d'API GitHub
pas de token
pas de polling réseau
```

La couche GitHub Project / SourceCandidate est intégrée à l'architecture générale comme direction future, mais elle reste documentaire à ce stade. Elle sera reprise plus tard comme orchestration de travail distant, avec source autoritative côté serveur local et projection contrôlée vers GitHub.

La Phase 5 peut maintenant démarrer sur une base stable : serveur local, Context Engine/runtime, ou handoff contrôlé des artefacts E5.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.20 clôture la Phase 4 par documentation et bilan ; aucune règle de programmation nouvelle n'est nécessaire.
```
