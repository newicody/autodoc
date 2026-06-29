# Stratégie OpenVINO — choix des modèles

## Situation

Le code possède déjà :

```text
InferenceRequestHandler
  -> InferenceAdapter
  -> BackendRegistry
  -> OpenVINOBackend
  -> OpenVINORuntime injecté
```

Le runtime OpenVINO réel est maintenant isolé dans `src/inference/openvino_runtime.py`, mais il reste générique et raw-input only.

La Phase 3.0 ajoute `OpenVINOModelProfile` et `OpenVINOModelProfileRegistry`. Le choix du premier modèle n'est toujours pas fait, mais il peut maintenant être représenté proprement sans charger OpenVINO ni créer de backend exécutable.

## Options possibles

### Option A — Embedding d'abord

Brancher d'abord un modèle d'embedding.

Usage :

```text
texte / requête / contexte
  -> vecteur
  -> Qdrant plus tard
```

Avantages :

- simple à tester ;
- utile pour le futur RAG ;
- sortie numérique stable ;
- bon candidat pour iGPU/CPU ;
- moins risqué qu'un LLM génératif.

Inconvénient :

- ne produit pas directement de texte.

### Option B — Génération d'abord

Brancher d'abord un petit modèle de génération.

Usage :

```text
prompt
  -> texte généré
```

Avantages :

- plus visible immédiatement ;
- utile pour prototyper des réponses.

Inconvénients :

- nécessite tokenizer/detokenizer ;
- gestion KV-cache éventuelle ;
- sorties plus difficiles à tester ;
- coût plus variable ;
- plus de risques d'instabilité.

### Option C — Multi-backend dès le début

Enregistrer plusieurs backends :

```text
BackendRegistry
  ├── dummy
  ├── openvino.embedding
  └── openvino.generation
```

Avantage : architecture complète.

Inconvénient : trop de surface à déboguer d'un coup.

## Recommandation

Commencer par **Option A — embedding d'abord**.

Le premier profil réel devrait probablement être nommé :

```text
openvino.embedding
```

Puis plus tard :

```text
openvino.generation
```

`OpenVINOModelProfileRegistry` permet de préparer cette séparation. `BackendRegistry` reste réservé aux backends exécutables.

## État technique Phase 3.0

Le runtime réel minimal existe :

```text
src/inference/openvino_runtime.py
```

Le registre de profils existe :

```text
src/inference/model_profile.py
```

Avec :

```text
RealOpenVINORuntime
OpenVINOModelProfile
OpenVINOModelProfileRegistry
```

Responsabilités actuelles :

- importer `openvino` uniquement dans ce fichier ;
- charger un modèle depuis `OpenVINOBackendConfig.model_path` ;
- compiler le modèle sur `config.device` ;
- exécuter une inférence à partir d'entrées brutes ;
- retourner un `InferenceResult` générique.

Le Scheduler, le Dispatcher, le ComponentProxy, le Handler et l'Adapter n'ont pas changé.

## Condition avant intégration réelle

Avant d'intégrer OpenVINO réel, il faut savoir :

- chemin local du modèle OpenVINO ;
- type du modèle : embedding ou génération ;
- device cible : `CPU`, `GPU`, ou `AUTO` ;
- format d'entrée attendu ;
- format de sortie attendu.

Sans ces informations, il faut rester sur le runtime brut et les profils déclaratifs Phase 3.0, sans ajouter de tokenizer ou de post-traitement spécifique.

## Phase 3.1 — Activation explicite par factory

La Phase 3.1 ajoute :

```text
OpenVINOBackendFactory
```

Elle ne choisit toujours pas le modèle, mais elle rend possible l'activation contrôlée d'un profil :

```text
OpenVINOModelProfileRegistry.select("openvino.embedding")
  -> OpenVINOBackendFactory.build_and_register(...)
  -> BackendRegistry
```

Cela permet de préparer plusieurs profils sans enregistrer tous les backends au démarrage.

La décision d'architecture devient donc :

```text
profil déclaré != backend actif
```

Un modèle n'est actif que si la configuration de lancement ou une décision explicite demande sa construction.


## Phase 3.2 — Embedding configurable sans modèle imposé

La Phase 3.2 concrétise la recommandation "embedding d'abord" sans imposer
BGE-M3, MiniLM, E5 ou un chemin local fixe.

Le nouveau point d'entrée est :

```text
OpenVINOEmbeddingProfileConfig
```

Il permet de déclarer :

```text
model_path
name
device
dimension optionnelle
input_names
output_names
pooling déclaratif
normalize déclaratif
metadata
```

La stratégie reste prudente : on sait maintenant représenter un profil embedding
local, mais le runtime OpenVINO réel reste raw-input. La prochaine difficulté
n'est pas le Scheduler : c'est le pré-traitement texte -> tenseurs, puis le
post-traitement sortie modèle -> vecteur normalisé.


## Phase 3.3 — Embedding raw IO

La stratégie reste : embedding d’abord, génération ensuite. La Phase 3.3 ne choisit toujours pas BGE-M3, E5 ou MiniLM ; elle ajoute seulement le contrat qui permet de tester un modèle embedding déjà tokenisé. Cela évite de confondre le tokenizer, le runtime OpenVINO et le post-traitement du vecteur.


## Phase 3.4 — Contrat tokenizer injectable

La Phase 3.4 ajoute le contrat manquant entre texte et entrées raw :

```text
TokenizationRequest
  -> TextTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
```

Ce contrat ne choisit toujours pas Hugging Face, SentencePiece, BGE-M3, E5 ou MiniLM. Il permet seulement de préparer l’endroit exact où un tokenizer concret sera injecté plus tard. Le choix d’implémentation peut donc rester expérimental sans modifier `Scheduler`, `InferenceAdapter`, `OpenVINOBackend` ou `RealOpenVINORuntime`.


## Phase 3.5 — Pipeline embedding abstrait

La Phase 3.5 assemble les contrats préparés sans choisir de modèle concret :

```text
TokenizationRequest
  -> TextTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> InferenceAdapter
  -> BackendRegistry
  -> InferenceResult.metadata["raw_outputs"]
  -> OpenVINOEmbeddingOutputAdapter
  -> OpenVINOEmbeddingVector
```

Cette étape confirme que l'option embedding peut être branchée progressivement. Il reste à choisir plus tard l'implémentation concrète du tokenizer et le chemin réel du modèle local.


## Phase 3.6 — Tokenizer déterministe de test

La Phase 3.6 n'est pas encore le tokenizer réel du modèle. Elle ajoute un
`DeterministicTokenizer` pure stdlib pour valider le pipeline complet sans
dépendance Hugging Face, sans vocabulaire local, sans téléchargement et sans
modèle OpenVINO réel.

Ce tokenizer est volontairement artificiel : ses ids sont stables grâce à
SHA-256, mais ils ne correspondent à aucun vocabulaire BGE/E5/MiniLM/Qwen.
Il sert uniquement au test structurel du chemin :

```text
texte
  -> tokens déterministes
  -> raw inputs
  -> backend fake ou OpenVINO brut
  -> vecteur
```

## Préparation OpenVINO pour les prochains tests

Pour les tests unitaires ordinaires, rien n'est requis : ils doivent continuer
de passer sans OpenVINO installé.

Pour les prochains tests d'intégration locaux, préparer :

```bash
python3 -c "import openvino as ov; print(ov.__version__)"
```

Puis disposer d'un modèle OpenVINO IR local, c'est-à-dire au minimum :

```text
model.xml
model.bin
```

Le chemin sera passé par profil/configuration. Il ne doit pas être codé en dur
dans le Scheduler ni dans le pipeline.

Recommandation pour ton prototype : commencer par un modèle embedding exporté
OpenVINO, puis vérifier seulement :

```text
input_names
output_names
dimension de sortie
pooling attendu
device CPU ou AUTO
```

Tant que ces informations ne sont pas figées, on garde le tokenizer réel et le
modèle réel hors du noyau.
