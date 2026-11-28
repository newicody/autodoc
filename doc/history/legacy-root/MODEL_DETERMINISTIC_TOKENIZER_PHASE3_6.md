# Phase 3.6 — Tokenizer déterministe de test

## Objectif

Ajouter un tokenizer concret minimal pour tester le pipeline embedding sans
introduire de dépendance externe ni choisir de modèle réel.

Cette phase ne remplace pas le tokenizer d'un modèle OpenVINO. Elle fournit un
outil de test stable pour vérifier l'assemblage :

```text
texte
  -> DeterministicTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> OpenVINOEmbeddingPipeline
```

## Ce que fait `DeterministicTokenizer`

Le tokenizer :

- découpe le texte avec une règle whitespace simple ;
- applique éventuellement `lowercase` ;
- génère des ids stables avec SHA-256 ;
- ajoute optionnellement des tokens spéciaux `CLS` / `SEP` ;
- produit `input_ids`, `attention_mask` et `token_type_ids` ;
- respecte `padding`, `max_length` et `truncation` du contrat Phase 3.4.

## Ce qu'il ne fait pas

Il ne fait pas :

```text
vocabulaire BGE/E5/MiniLM
SentencePiece
Hugging Face tokenizers
chargement depuis disque
téléchargement
compatibilité modèle réelle
```

Les ids produits sont utiles pour les tests, pas pour un vrai modèle.

## Pourquoi c'est utile

Avant de brancher un vrai tokenizer, il faut vérifier que la mécanique générale
est correcte :

```text
TokenizerRegistry
  -> tokenizer sélectionné
  -> TokenizationResult rectangulaire
  -> raw inputs OpenVINO
  -> InferenceAdapter
  -> backend embedding
  -> vecteur final
```

Cela permet de tester le pipeline sans mélanger trois problèmes :

```text
architecture pipeline
compatibilité tokenizer
compatibilité modèle OpenVINO
```

## Préparation OpenVINO

Pour cette phase, rien n'est nécessaire côté OpenVINO.

À partir de la prochaine phase d'intégration locale, il faudra préparer :

```bash
python3 -c "import openvino as ov; print(ov.__version__)"
```

et un modèle IR local :

```text
/path/to/model.xml
/path/to/model.bin
```

La configuration devra aussi préciser :

```text
device = CPU | AUTO | GPU
input_names
output_names
pooling
normalize
dimension attendue si connue
```
