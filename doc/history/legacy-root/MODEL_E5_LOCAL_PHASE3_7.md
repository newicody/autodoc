# Phase 3.7 — Profil local multilingual-e5-small

Le premier modèle réel observé localement est :

```text
/home/eric/model/openvino/multilingual-e5-small/openvino_model.xml
```

OpenVINO expose :

```text
inputs:
 - input_ids [?,?]
 - attention_mask [?,?]
 - token_type_ids [?,?]

outputs:
 - last_hidden_state [?,?,384]
```

Le modèle ne fournit donc pas directement un vecteur `[384]`. Il fournit un tenseur token-level :

```text
batch × tokens × 384
```

La stratégie correcte pour le premier pipeline est :

```text
last_hidden_state
  -> mean pooling masqué par attention_mask
  -> normalisation L2
  -> OpenVINOEmbeddingVector dimension 384
```

## Pourquoi ajouter `token_type_ids` automatiquement

Le tokenizer local peut ne pas renvoyer `token_type_ids`, alors que le modèle OpenVINO exporté les attend. Dans ce cas, l'adapter `TransformersAutoTokenizer` peut produire une matrice de zéros de même forme que `input_ids`.

Cela évite l'erreur OpenVINO :

```text
TypeError: Incompatible inputs of type: <class 'NoneType'>
```

## Variables d'environnement

```text
MISSIPY_E5_SMALL_DIR
```

Dossier du modèle local. Défaut :

```text
/home/eric/model/openvino/multilingual-e5-small
```

```text
MISSIPY_RUN_OPENVINO_LOCAL=1
```

Active le test d'intégration réel.

## Commande de test réel

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```

## Statut

Cette phase valide le premier modèle local réel sans imposer ce modèle à toute l'architecture. Le profil E5 est une option enregistrable, pas un fallback implicite.
