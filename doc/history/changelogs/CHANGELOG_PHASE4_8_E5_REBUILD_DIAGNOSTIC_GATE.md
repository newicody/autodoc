# Changelog Phase 4.8 — E5 rebuild diagnostic gate

## Objectif

La Phase 4.8 réutilise le diagnostic gate du corpus E5 dans la commande de rebuild sûr.

Le rebuild construit toujours un candidat en staging, le relit, le valide puis le promeut seulement si tout est correct. La nouveauté est qu'un gate diagnostic optionnel peut bloquer la promotion avant que le fichier final ne soit remplacé.

```text
source-dir / passages
-> rebuild_e5_corpus.py
-> staging .corpus.json.rebuild.json
-> inspect_e5_corpus(candidate)
-> evaluate_e5_corpus_diagnostic_gate()
-> validation-query optionnelle
-> promotion finale seulement si le gate passe
```

## Ajouté

- Options `rebuild_e5_corpus.py` :
  - `--min-chunks` ;
  - `--max-missing-source-metadata` ;
  - `--max-empty-texts` ;
  - `--max-dimension-mismatches` ;
  - `--fail-on-warning`.
- Section `diagnostic_gate` dans la sortie texte quand au moins un seuil est actif.
- Clé JSON `diagnostic_gate` dans la sortie `--format json` quand au moins un seuil est actif.
- Échec contrôlé avec code retour `2` si le gate diagnostic est violé.
- Conservation possible du staging échoué avec `--keep-staging`.
- Tests dédiés pour parser, succès gate, échec gate, staging conservé et validation d'options.
- Roadmap DOT : `62_e5_rebuild_diagnostic_gate.dot`.

## Non modifié

- Pas de Scheduler.
- Pas de Qdrant.
- Pas de changement du format `missipy.e5.corpus.v1`.
- Pas de changement du build incrémental.
- Pas de changement de l'écriture atomique.
- Pas de SVG versionné.
- Pas de script de patch.

## Raison

La Phase 4.6 permettait d'inspecter un corpus déjà construit. La Phase 4.7 permettait de transformer cette inspection en verdict actionnable.

La Phase 4.8 branche ce verdict au bon endroit opérationnel : juste avant la promotion finale d'un corpus candidat. Cela évite qu'un index local douteux remplace l'index final.
