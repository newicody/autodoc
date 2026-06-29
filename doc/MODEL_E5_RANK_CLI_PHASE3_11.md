# Phase 3.11 — CLI de ranking local E5

## Rôle

La Phase 3.11 transforme le mini-ranker local de la Phase 3.10 en commande de développement.

Elle permet de valider le comportement réel suivant avant Qdrant :

```text
query
  -> embedding query
  -> N passages
  -> N embeddings passage
  -> dot product / cosine similarity
  -> classement décroissant
```

## Commande

Depuis la racine du dépôt :

```bash
./tools/rank_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "je me suis fait baiser" \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel" \
  --passage "documentation OpenVINO"
```

La query brute reçoit automatiquement le préfixe E5 :

```text
query: je me suis fait baiser
```

Chaque passage brut reçoit automatiquement :

```text
passage: ...
```

## Fichier de passages

```bash
cat > /tmp/passages.txt <<'EOF'
j'ai été arnaqué par un vendeur
problème moteur diesel
documentation OpenVINO
EOF

./tools/rank_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  "je me suis fait baiser" \
  --passages-file /tmp/passages.txt
```

Les lignes vides sont ignorées.

## JSON

```bash
./tools/rank_e5.py \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --format json \
  --limit 2 \
  "je me suis fait baiser" \
  --passage "j'ai été arnaqué par un vendeur" \
  --passage "problème moteur diesel"
```

La sortie JSON est destinée aux scripts de développement et aux futurs tests d'indexation.

## Pourquoi avant Qdrant

Avant d'introduire une base vectorielle, on valide que le modèle local produit déjà un classement cohérent sur un petit corpus en mémoire.

Cette étape isole trois questions :

```text
1. Le modèle encode-t-il correctement query/passages ?
2. Le score cosine donne-t-il un classement plausible ?
3. La CLI permet-elle de diagnostiquer rapidement un corpus minuscule ?
```

Qdrant viendra ensuite comme stockage et moteur de recherche scalable, pas comme solution à un pipeline pas encore vérifié.

## Limite volontaire

Cette CLI encode les passages à chaque lancement. Elle ne met pas encore les vecteurs en cache.

La suite logique est donc :

```text
Phase 3.12 — batch embedding / corpus local
Phase 3.13 — stockage temporaire JSONL ou SQLite
Phase 3.14 — Qdrant
```
