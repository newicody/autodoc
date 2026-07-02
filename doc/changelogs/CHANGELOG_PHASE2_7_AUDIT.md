# Changelog — Phase 2.7 Audit / stratégie OpenVINO

## Nature

Audit documentaire et hygiène dépôt. Aucun changement runtime.

## Ajouté

- `doc/PROJECT_REVIEW_PHASE2_6.md` : analyse du modèle actuel, évolution depuis le modèle de départ, points positifs, limites et axes futurs.
- `doc/OPENVINO_MODEL_STRATEGY.md` : stratégie de choix des modèles OpenVINO avant intégration réelle.
- `.gitignore` : exclusion des caches Python, environnements virtuels et sorties locales.

## Modifié

- `README.md` : état actuel, commandes de validation, documentation utile.
- `doc/ARCHITECTURE_LAYERS.md` : mise à jour de l'introduction, de l'état de test et de la stratégie avant OpenVINO.
- `doc/code-rules/code_rule.md` : ajout d'un encadré sur l'état Phase 2.6 et le rôle de `BackendRegistry`.

## Non modifié

- Aucun fichier runtime.
- Aucun test runtime.
- Aucun `.dot`.
- Aucun `.svg`.

## Raison

Le code est maintenant à l'étape juste avant l'intégration réelle d'OpenVINO. Il fallait figer l'état du modèle, clarifier ce qui a évolué depuis la vision initiale et éviter de choisir un modèle OpenVINO au hasard.
