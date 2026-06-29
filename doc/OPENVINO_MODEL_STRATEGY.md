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
