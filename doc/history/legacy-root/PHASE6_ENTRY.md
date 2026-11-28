# Phase 6 — Local operator loop

Phase 6 démarre après la clôture Phase 5. L'objectif est de transformer les
contrats locaux en boucle opérateur contrôlée, sans serveur, réseau, GitHub API,
Qdrant ou LLM.

La première étape est volontairement modeste : créer une entrée locale
`SourceCandidate` depuis la ligne de commande et l'écrire dans le store JSON
atomique introduit en Phase 5.15.

## Frontières maintenues

- GitHub reste une projection future, pas une source appelée par le code.
- `newicody/autodoc` reste un namespace de projection, pas une API branchée.
- Le store local JSON reste la seule persistance introduite ici.
- Aucune décision opérateur ne déclenche de Scheduler, daemon ou serveur.
- Aucun modèle, OpenVINO, Qdrant ou LLM n'est appelé.

## Chaîne locale cible

```text
entrée opérateur locale
-> SourceCandidateInput
-> SourceCandidate
-> décision optionnelle locale
-> SourceCandidateStore JSON
-> rapport local optionnel
```

Cette étape prépare les futures commandes de boucle locale sans introduire de
nouvelle autorité externe.
