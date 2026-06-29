# Phase 3.3 — Contrat embedding raw

Cette phase ajoute la couche d'entrée/sortie minimale autour d'un modèle d'embedding OpenVINO déjà tokenisé.

Elle ne choisit pas de modèle, n'intègre pas de tokenizer, ne branche pas Qdrant et ne modifie pas le Scheduler.

## Objectif

La Phase 3.2 permettait de déclarer un profil `openvino.embedding`.

La Phase 3.3 ajoute le contrat suivant :

```text
texte déjà tokenisé
  -> OpenVINOEmbeddingRawInputs
  -> InferenceRequest.context["inputs"]
  -> RealOpenVINORuntime
  -> sortie brute OpenVINO
  -> OpenVINOEmbeddingOutputAdapter
  -> OpenVINOEmbeddingVector
```

## Structures ajoutées

```text
OpenVINOEmbeddingRawInputs
OpenVINOEmbeddingOutputConfig
OpenVINOEmbeddingOutputAdapter
OpenVINOEmbeddingVector
```

## OpenVINOEmbeddingRawInputs

`OpenVINOEmbeddingRawInputs` transporte des tenseurs Python simples :

```text
input_ids
attention_mask
token_type_ids optionnel
```

La structure vérifie :

```text
matrice 2D non vide
forme rectangulaire
input_ids et attention_mask de même forme
attention_mask limitée à 0/1
input_ids non négatifs
metadata gelée
```

Elle sait produire :

```text
to_openvino_inputs()
to_inference_request()
```

mais elle ne crée pas de tableau NumPy et ne dépend pas d'OpenVINO.

## OpenVINOEmbeddingOutputAdapter

`OpenVINOEmbeddingOutputAdapter` prend une sortie brute et produit un vecteur stable.

Poolings pris en charge :

```text
model : le modèle retourne déjà un vecteur ou un batch de vecteurs
none  : idem, sans pooling token-level
cls   : prend le premier token du premier batch
mean  : moyenne pondérée par attention_mask sur le premier batch
```

La normalisation L2 est optionnelle.

## Ce que cette phase ne fait pas

```text
pas de tokenizer
pas de Hugging Face
pas de dépendance NumPy
pas de Qdrant
pas de choix BGE-M3 / E5 / MiniLM
pas d'appel direct depuis Scheduler
```

## Pourquoi cette étape est utile

Elle permet de tester la chaîne OpenVINO embedding sans mélanger trois problèmes :

```text
1. tokenisation texte -> tokens
2. inférence OpenVINO brute
3. post-traitement vecteur -> stockage/recherche
```

Le prototype peut maintenant recevoir des tokens préparés ailleurs, exécuter le backend brut, puis transformer une sortie brute en vecteur déterministe.
