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

Le choix du premier modèle n'est pas encore fait. C'est volontaire : on a branché la capacité technique d'exécuter OpenVINO sans imposer embedding, génération ou tokenizer.

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

Le premier backend réel devrait probablement être nommé :

```text
openvino.embedding
```

Puis plus tard :

```text
openvino.generation
```

Le `BackendRegistry` permet déjà cette séparation.

## État technique Phase 2.9

Le runtime réel minimal existe :

```text
src/inference/openvino_runtime.py
```

Avec :

```text
RealOpenVINORuntime
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

Sans ces informations, il faut rester sur le runtime brut Phase 2.9 et ne pas ajouter de tokenizer ou de post-traitement spécifique.
