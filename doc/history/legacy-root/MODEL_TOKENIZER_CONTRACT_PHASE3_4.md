# Phase 3.4 — Contrat tokenizer injectable

## Objectif

La Phase 3.4 ajoute le contrat entre le texte utilisateur et les tenseurs déjà tokenisés utilisés par la Phase 3.3.

Le but n'est pas d'imposer Hugging Face, SentencePiece, BGE-M3, E5 ou MiniLM. Le but est de définir une membrane stable :

```text
texte
  -> TokenizationRequest
  -> TextTokenizer injectable
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
```

## Nouveaux objets

```text
TokenizerConfig
TokenizationRequest
TokenizationResult
TextTokenizer Protocol
TokenizerRegistry
TokenizerRegistrySnapshot
```

## Règle importante

Le tokenizer n'est pas un backend OpenVINO.

```text
TokenizerRegistry = tokenizers disponibles
BackendRegistry   = backends exécutables
```

La séparation évite de confondre :

```text
texte -> tokens
```

avec :

```text
tokens -> OpenVINO -> vecteur
```

## Ce que la phase fait

La phase valide :

```text
configuration tokenizer stable
batch de textes
paires de textes optionnelles
matrices input_ids / attention_mask / token_type_ids
projection vers OpenVINOEmbeddingRawInputs
registre explicite sans fallback caché
```

## Ce que la phase ne fait pas

```text
pas d'import transformers
pas d'import tokenizers
pas de SentencePiece
pas de vocabulaire chargé
pas de modèle local imposé
pas de téléchargement
pas de Qdrant
pas de branchement automatique dans le Scheduler
```

## Conséquence pour OpenVINO

On peut maintenant préparer un pipeline embedding complet, mais encore abstrait :

```text
TokenizationRequest
  -> TextTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> InferenceRequest.context["inputs"]
  -> RealOpenVINORuntime
  -> OpenVINOEmbeddingOutputAdapter
  -> OpenVINOEmbeddingVector
```

La prochaine étape peut donc ajouter un pipeline d'embedding orchestrant ces pièces sans choisir immédiatement l'implémentation concrète du tokenizer.


## Suite Phase 3.5

La Phase 3.5 ajoute `OpenVINOEmbeddingPipeline`, qui consomme ce contrat tokenizer sans l'étendre :

```text
TextTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> InferenceAdapter
  -> OpenVINOEmbeddingVector
```

Le tokenizer reste injectable. Aucun tokenizer concret n'est ajouté.
