# Modèle Phase 3.18 — Rebuild sûr du corpus E5

## Problème

Après l'index incrémental, l'écriture atomique et le verrou, il restait encore un geste manuel : construire un nouveau fichier puis le promouvoir à la main vers l'index final.

Ce geste est risqué parce qu'il mélange :

```text
build long
validation
promotion finale
```

## Solution

La Phase 3.18 ajoute `rebuild_e5_corpus.py`.

Le flux est :

```text
1. acquérir le lock du corpus final
2. lire l'ancien index s'il existe
3. reconstruire un candidat incrémental
4. écrire le candidat en staging atomique
5. relire le candidat
6. exécuter une recherche de validation optionnelle
7. promouvoir le staging vers l'index final
8. libérer le lock
```

## Commande

```bash
./tools/rebuild_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --source-dir /data/notes \
  --chunk-chars 1200 \
  --validation-query "test de recherche"
```

## Dry-run

```bash
./tools/rebuild_e5_corpus.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --index /tmp/e5_corpus.json \
  --source-dir /data/notes \
  --dry-run \
  --keep-staging
```

Dans ce mode, le candidat reste disponible mais l'index final n'est pas remplacé.

## Position dans l'architecture

Cette brique reste hors Scheduler. Elle prépare l'exploitation locale du moteur E5 avant un futur index vectoriel externe.
