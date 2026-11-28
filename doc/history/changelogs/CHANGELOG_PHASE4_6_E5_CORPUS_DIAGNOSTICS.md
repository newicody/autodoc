# Changelog Phase 4.6 — E5 corpus diagnostics

## Objectif

La Phase 4.6 ajoute un diagnostic local du corpus E5 JSON déjà vectorisé.

Elle permet d'inspecter rapidement un index sans modifier son format et sans ouvrir manuellement le JSON.

Flux ajouté :

```text
corpus JSON missipy.e5.corpus.v1
-> E5CorpusJsonStore.read()
-> inspect_e5_corpus()
-> rapport texte ou JSON
```

## Ajouté

- `src/inference/e5_corpus_inspect.py`
  - `E5CorpusDiagnostics`
  - `E5CorpusTopSource`
  - `inspect_e5_corpus()`
- `src/inference/e5_corpus_inspect_cli.py`
  - `build_inspect_parser()`
  - `run_inspect()`
  - `E5CorpusInspectCliOutput`
- `tools/inspect_e5_corpus.py`
- `tests/inference/test_e5_corpus_inspect.py`
- `tests/inference/test_e5_corpus_inspect_cli.py`

## Diagnostic produit

Le rapport indique :

- schéma du corpus ;
- modèle ;
- backend ;
- tokenizer ;
- dimension ;
- nombre de chunks ;
- nombre de sources ;
- répartition par extension ;
- sources dominantes ;
- compte des embeddings réutilisés, recalculés ou inconnus ;
- métadonnées source manquantes ;
- textes vides ;
- dimensions inattendues.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format `missipy.e5.corpus.v1`.
- Pas de runtime OpenVINO supplémentaire.
- Pas de mutation de corpus.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

Avant d'introduire une base vectorielle externe ou un service persistant, le corpus local doit être inspectable et vérifiable en lecture seule.

La Phase 4.6 ajoute donc le pendant diagnostic de la chaîne locale : build, rebuild, recherche, hygiène, puis inspection.
