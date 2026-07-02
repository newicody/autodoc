# Changelog Phase 4.7 — E5 corpus diagnostic gate

## Objectif

La Phase 4.7 rend les diagnostics du corpus E5 actionnables pour un workflow développeur ou CI.

La commande `inspect_e5_corpus.py` reste en lecture seule, mais peut maintenant échouer avec le code retour `2` quand un seuil demandé n'est pas respecté.

## Ajouté

- `E5CorpusDiagnosticGateConfig` : configuration immuable des seuils optionnels.
- `E5CorpusDiagnosticGateResult` : résultat stable avec `passed` et liste des violations.
- `evaluate_e5_corpus_diagnostic_gate()` : évaluation pure d'un diagnostic déjà calculé.
- Options CLI :
  - `--min-chunks` ;
  - `--max-missing-source-metadata` ;
  - `--max-empty-texts` ;
  - `--max-dimension-mismatches` ;
  - `--fail-on-warning`.
- Sortie texte `gate:` quand au moins un seuil est actif.
- Sortie JSON `gate` quand au moins un seuil est actif.
- Tests moteur et CLI du mode gate.
- Graphe DOT `61_e5_corpus_diagnostic_gate.dot`.

## Codes retour

```text
0 : diagnostic lu et gate respecté ou inactif
1 : erreur de lecture ou corpus invalide
2 : option invalide ou gate violé
```

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format corpus.
- Pas de promotion automatique.
- Pas de DOT hors sous-système inference.
- Pas de SVG.
- Pas de script de patch.

## Raison

Après l'inspection locale du corpus, il faut pouvoir refuser explicitement un corpus douteux avant de l'utiliser dans une recherche ou de l'introduire dans une étape plus lourde.

La Phase 4.7 garde cette vérification locale, déterministe et testable.
