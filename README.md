# Autodoc / MissiPy

`autodoc` est le prototype du micro-kernel coopératif IA MissiPy.

L'objectif n'est pas de construire une application Python monolithique, mais un noyau d'orchestration modulaire, observable, déterministe et rejouable.

## État courant

État de référence : **Phase 3.18 rebuild E5 sûr avec staging, validation et promotion**.

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
- un rapport de recherche E5 avec score, source, lignes et extrait;
- un rebuild sûr du corpus E5 avec staging, validation optionnelle et promotion atomique.

OpenVINO est branché comme runtime générique à entrées brutes. Le choix du ou des modèles est décrit par profils déclaratifs : `embedding`, `generation` ou `raw`. La Phase 3.1 ajoute le pont contrôlé entre profil et `BackendRegistry`, sans tokenizer, post-processing ou modèle précis imposé. La Phase 3.2 ajoute une configuration spécialisée pour déclarer un profil `openvino.embedding` local, toujours sans chemin en dur ni chargement automatique. La Phase 3.3 ajoute la couche IO raw : tokens déjà préparés -> `InferenceRequest.context["inputs"]` -> sortie brute -> vecteur embedding stable. La Phase 3.4 ajoute le contrat tokenizer : texte -> `TokenizationResult` -> `OpenVINOEmbeddingRawInputs`, sans tokenizer concret imposé. La Phase 3.5 assemble ces pièces dans un pipeline embedding abstrait mono-texte : tokenizer injectable -> raw inputs -> `InferenceAdapter` -> sorties brutes -> vecteur. La Phase 3.6 ajoute un tokenizer déterministe de test : il permet de valider le pipeline complet sans dépendance externe, sans vocabulaire réel, et sans prétendre être compatible avec un vrai modèle OpenVINO.

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
query:   texte qui cherche
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

Cette couche reste un banc de test local avant Qdrant : elle ne fait pas encore d'index ANN ou de filtrage avancé. La mise à jour incrémentale arrive en Phase 3.15 via `--reuse-index`.

## Phase 3.13 — Indexer un dossier TXT/Markdown

La Phase 3.13 ajoute l’ingestion locale de sources `.md`, `.markdown` et `.txt`. Les fichiers sont découverts dans un ordre stable, lus en UTF-8, découpés par paragraphes, puis convertis en `E5CorpusDocument` avec métadonnées `source_path`, `chunk_index`, `start_line` et `end_line`.

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

La sortie CLI indique maintenant `atomic_write: True`. Le fichier temporaire suit le modèle `.nom_du_fichier.tmp` dans le même répertoire que la cible, afin que le remplacement reste atomique sur le même système de fichiers.


## Phase 3.17 — Verrou fichier de build corpus

La Phase 3.17 ajoute un verrou fichier pendant la construction du corpus E5. L'écriture atomique protège le remplacement final, mais elle n'empêchait pas encore deux processus de construire simultanément le même index.

Désormais, `build_e5_corpus.py` crée par défaut un verrou voisin de la cible :

```text
/tmp/e5_corpus.json
/tmp/.e5_corpus.json.lock
/tmp/.e5_corpus.json.tmp
```

Le verrou est acquis par création atomique `O_CREAT | O_EXCL`. Si un autre build vise déjà le même fichier, la commande échoue explicitement au lieu de travailler en concurrence.

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

Cette commande évite le `mv` manuel après un build incrémental. Elle reste hors Scheduler, hors Qdrant et conserve le format `missipy.e5.corpus.v1`.
