# Rapport 0287 r16-r4-r3-r4-r2

## Objet

Aligner les règles cumulatives avec la création automatique des artefacts pour
les nouvelles Issues de recherche de `newicody/projects`.

## Corrections

- le détail d'installation reste dans le README du bundle afin que
  `INSTALLATION.md` demeure sous son budget verrouillé de 380 lignes ;
- le libellé historique « Produire également un avis Copilot séparé » reste
  présent et la phrase explicite confirme que sa production est automatique ;
- le défaut sûr du dispatch manuel reste documenté par le marqueur
  `AUTODOC_COPILOT_REQUIRED: "false"` ;
- le chemin historique `ProjectV2 query-only → diff local` reste documenté sans
  redevenir le déclencheur de création initiale ;
- l'ancien test interdisant `issues.opened` est remplacé par un test du
  déclencheur strictement borné aux recherches de `newicody/projects`.

## Invariants conservés

- permissions globales `contents: read` et `issues: read` ;
- absence de `contents: write`, `issues: write` et `actions: write` ;
- secret de commentaire limité aux étapes de publication ;
- `workflow_dispatch` conservé pour les reprises explicites ;
- aucun changement du Scheduler, du laboratoire, de SQL ou de Qdrant.
