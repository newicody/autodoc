# Phase 3.15 — Corpus E5 incrémental

La Phase 3.15 ajoute une reconstruction incrémentale du corpus local E5.

## Problème

Depuis Phase 3.13, on peut indexer un dossier TXT/Markdown. Mais chaque reconstruction recalculait tous les embeddings :

```text
sources -> chunks -> embeddings complets -> corpus.json
```

Ce comportement est acceptable pour quelques fichiers, mais pas pour un vrai dossier de notes.

## Solution

Le build incrémental compare chaque document avec l'ancien index via :

```text
document.id + document.text.prefixed -> sha256
```

Si le document est inchangé, le vecteur existant est réutilisé. Sinon, seul ce document est ré-embeddé.

## Commande

```bash
./tools/build_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --source-dir /data/notes \
  --chunk-chars 1200 \
  --reuse-index /tmp/e5_corpus.json \
  --output /tmp/e5_corpus.next.json \
  --overwrite
```

Puis, après vérification :

```bash
mv /tmp/e5_corpus.next.json /tmp/e5_corpus.json
```

## Statistiques

La CLI affiche :

```text
reused_count:   chunks repris depuis l'ancien index
embedded_count: chunks recalculés
removed_count:  chunks présents avant mais absents maintenant
```

## Compatibilité

Le schéma reste :

```text
missipy.e5.corpus.v1
```

Les nouveaux champs de hash sont stockés dans `metadata`. Les anciens index restent lisibles ; si un ancien embedding ne contient pas encore `document_hash`, le builder peut le réutiliser par compatibilité si `id` et `prefixed_text` correspondent.

## Limite volontaire

Cette phase ne fait pas encore :

```text
watch filesystem
transaction atomique complète
base SQLite
Qdrant upsert/delete
index ANN
```

Elle prépare ces étapes avec une règle déterministe simple et testable.
