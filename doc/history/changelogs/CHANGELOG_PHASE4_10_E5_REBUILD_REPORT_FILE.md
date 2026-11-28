# Changelog Phase 4.10 — E5 rebuild report file

## Objectif

La Phase 4.10 ajoute un rapport JSON optionnel au rebuild sûr du corpus E5.

Le rebuild sait déjà construire un staging, appliquer le diagnostic gate, valider plusieurs requêtes et promouvoir l'index final. Cette phase rend ce résultat archivable dans un fichier stable.

## Ajouté

- Option `--report-file FILE` dans `rebuild_e5_corpus.py`.
- Écriture JSON stable du résumé de rebuild.
- Rapport écrit de façon atomique via fichier temporaire voisin.
- Le rapport reprend `E5CorpusRebuildCliOutput.to_json_dict()`.
- Tests de parser, écriture du rapport, dry-run et erreur d'écriture.

## Contenu du rapport

Le rapport peut contenir :

- `index` ;
- `staging` ;
- `promoted` ;
- `model` ;
- `backend` ;
- `tokenizer` ;
- `dimension` ;
- `size` ;
- `validation` ;
- `diagnostic_gate` si activé ;
- `reused_count`, `embedded_count`, `removed_count` si disponibles.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format corpus `missipy.e5.corpus.v1`.
- Pas de changement du moteur de recherche.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

Le rapport fichier prépare les usages CI, audit, comparaison de rebuild et future interface HTML sans imposer de service externe.
