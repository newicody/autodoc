# Changelog — Phase 2.3

## Objectif

Ajouter une écriture contrôlée des exports de replay vers fichiers texte/JSON, sans relier le replay au Scheduler vivant.

## Ajouté

- `ReplayReportWriteResult` dans `contracts.replay`.
- `ReplayReportFileWriter` dans `observability.replay_writer`.
- Tests d'écriture explicite vers fichier.
- Tests de refus d'écrasement par défaut.
- Tests de création de répertoire parent uniquement avec `create_parents=True`.
- Tests de checksum `sha256` stable.

## Modifié

- `observability.__init__` exporte `ReplayReportFileWriter`.
- `ARCHITECTURE_LAYERS.md` décrit la Phase 2.3.
- `00_global.dot`, `70_observability.dot` et `80_tests.dot` ajoutent la roadmap writer.

## Non modifié

- Aucun SVG généré.
- Aucun script de patch ajouté.
- Aucun branchement au Scheduler vivant.
- Aucun OpenVINO, Qdrant, SQLite ou MCTS.

## Garanties

- Aucun chemin implicite.
- Aucune extension implicite.
- Aucun overwrite implicite.
- Aucune création de parent implicite.
- Aucun `Future` ni payload vivant écrit.
- Le résultat d'écriture est une dataclass immuable.
