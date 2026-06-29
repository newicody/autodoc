# Phase 3.9 — CLI de développement E5 local

## Objectif

La Phase 3.9 ajoute un point d'entrée terminal pour tester le pipeline
`multilingual-e5-small` local sans écrire un script temporaire à chaque essai.

Le CLI reste une couche de développement. Il ne modifie pas le Scheduler, ne
publie aucun événement et n'ajoute pas de dépendance obligatoire à la suite
portable.

## Commande

Depuis la racine du dépôt :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "query: test de recherche vectorielle pour MissiPy"
```

ou via le module :

```bash
PYTHONPATH=src python3 -m inference.e5_cli \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "query: test de recherche vectorielle pour MissiPy"
```

## Sortie texte

La sortie texte affiche les informations de diagnostic utiles : modèle,
backend, tokenizer, device, chemin du modèle, dimension, normalisation, norme L2
et aperçu du vecteur.

```text
model: openvino.embedding.e5-small
backend: openvino.embedding.e5-small
tokenizer: transformers.multilingual-e5-small
device: CPU
model_path: /home/eric/model/openvino/multilingual-e5-small/openvino_model.xml
dimension: 384
normalized: True
l2_norm: 1.00000000
values_preview: [...]
```

## Sortie JSON

Pour intégrer la commande dans un script :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --format json \
  "query: test"
```

Par défaut, le JSON ne contient qu'un aperçu du vecteur afin d'éviter une sortie
bruyante. Le vecteur complet peut être demandé explicitement :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --format json \
  --full-vector \
  "query: test"
```

## Préfixes E5 depuis Phase 3.10

Le modèle E5 attend une convention de texte :

```text
query: question ou recherche utilisateur
passage: document ou fragment indexé
```

Depuis la Phase 3.10, le CLI peut appliquer cette convention :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role query \
  "test de recherche vectorielle pour MissiPy"
```

Pour un document/chunk :

```bash
./tools/embed_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --role passage \
  "fragment de documentation à indexer"
```

`--role auto` reste le défaut : il respecte `query:` ou `passage:` si le texte
est déjà préfixé, sinon il applique `query:`.

## Limites volontaires

- pas de Qdrant ;
- pas de batch ;
- pas de stockage ;
- pas de cache ;
- pas de décision Scheduler ;
- pas de téléchargement automatique de modèle.

Le CLI est un outil de validation locale du pipeline embedding réel.
