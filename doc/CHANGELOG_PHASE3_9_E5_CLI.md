# Changelog — Phase 3.9 — CLI E5 local

## Ajouté

- `src/inference/e5_cli.py`
  - CLI testable pour exécuter le pipeline local `multilingual-e5-small`.
  - Sortie texte ou JSON.
  - Aperçu du vecteur par défaut.
  - Option `--full-vector` pour JSON complet.
  - Injection de builder pour tests sans OpenVINO réel.

- `tools/embed_e5.py`
  - Lanceur de développement depuis la racine du dépôt.
  - Ajoute `src/` au `sys.path` sans installation du paquet.

- `tests/inference/test_e5_cli.py`
  - Test du mode texte.
  - Test du mode JSON sans vecteur complet.
  - Test du mode JSON avec vecteur complet.
  - Test de validation des arguments avant construction du pipeline.

- `doc/MODEL_E5_CLI_PHASE3_9.md`
  - Documentation d'utilisation du CLI.
  - Rappel des préfixes E5 `query:` / `passage:`.

## Modifié

- `src/inference/__init__.py`
  - Exporte les points d'entrée CLI testables.

- `README.md`
  - Ajoute la commande de test embedding local.

- `doc/ARCHITECTURE_LAYERS.md`
  - Mentionne le CLI comme outil de développement autour du pipeline E5.

- `tests/rules/test_code_rule_compliance.py`
  - Autorise explicitement les imports optionnels déjà introduits aux frontières prévues :
    `openvino` et `numpy` dans `openvino_runtime.py`, `transformers` dans
    `transformers_tokenizer.py`.

## Non modifié

- Scheduler.
- Dispatcher.
- ComponentProxy.
- PolicyEngine.
- EventBus.
- Qdrant absent.
- Aucun SVG inclus.
