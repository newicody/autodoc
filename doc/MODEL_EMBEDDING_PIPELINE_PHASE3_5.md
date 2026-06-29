# Phase 3.5 — Pipeline embedding abstrait

## Objectif

La Phase 3.5 assemble les contrats déjà préparés sans imposer de modèle, de tokenizer concret ou d'index vectoriel.

Le pipeline cible est :

```text
texte
  -> TokenizationRequest
  -> TextTokenizer injectable
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> InferenceAdapter
  -> BackendRegistry
  -> backend OpenVINO embedding actif
  -> InferenceResult.metadata["raw_outputs"]
  -> OpenVINOEmbeddingOutputAdapter
  -> OpenVINOEmbeddingVector
```

## Nouveaux objets

```text
OpenVINOEmbeddingPipelineConfig
OpenVINOEmbeddingPipelineResult
OpenVINOEmbeddingPipeline
```

## Rôle du pipeline

Le pipeline est une composition de membranes existantes. Il ne remplace pas le Scheduler et ne publie aucun événement.

Il sert à valider l'enchaînement minimal suivant :

```text
TokenizerRegistry
InferenceAdapter
OpenVINOEmbeddingOutputAdapter
```

La sélection du moteur reste faite par `InferenceRequest.model`, donc par `BackendRegistry`.

## Limite volontaire

La Phase 3.5 supporte un seul texte à la fois.

Le batch embedding sera ajouté plus tard avec un contrat dédié, pour éviter de mélanger :

```text
un texte -> un vecteur
```

avec :

```text
N textes -> N vecteurs -> index vectoriel
```

## Ce que la phase ne fait pas

```text
pas de tokenizer concret
pas de Hugging Face imposé
pas de SentencePiece imposé
pas de modèle local imposé
pas de Qdrant
pas de batch vectoriel
pas de composant Scheduler
pas d'événement INFERENCE_REQUEST généré automatiquement
```

## Sorties brutes OpenVINO

Pour que le pipeline puisse construire un vecteur, le backend doit retourner la sortie brute dans :

```text
InferenceResult.metadata["raw_outputs"]
```

`RealOpenVINORuntime` expose maintenant cette sortie brute dans le résultat d'inférence. Cette valeur est destinée au chemin direct du pipeline, pas à une sérialisation longue durée.

## Pourquoi cette étape est importante

Avant cette phase, les contrats existaient séparément :

```text
tokenizer
raw inputs
backend
output adapter
```

Après cette phase, on sait les assembler dans un flux complet sans casser la règle centrale : le Scheduler ne connaît toujours ni OpenVINO, ni tokenizer, ni modèle, ni Qdrant.
