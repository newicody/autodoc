# 0284-r1-r1 — passive EventBus → VisPy live bridge

## Intention

Rendre visible en quasi temps réel le vrai EventBus dans le Cell Lens VisPy existant, sans ajouter de bus, de Scheduler, de manager, de backend de décision ou de dépendance externe.

## Périmètre

- ajoute un adaptateur passif `EventBusCellLensLiveBridge` ;
- réutilise `CellObservationEvent`, `CellSnapshot`, `CellSnapshotJournalWriter` et le schéma `missipy.cell.v1` ;
- compose l’adaptateur uniquement dans `src/main.py` quand `MISSIPY_CELL_LENS_JOURNAL` est défini ;
- active le mode existant `--tail` du profil VisPy avec un intervalle de 0,25 seconde ;
- ajoute rapport, changelog, manifest, documentation d’architecture, source DOT et tests de règles.

## Frontières préservées

- `Scheduler` et `kernel/launcher.py` ne sont pas modifiés ;
- l’EventBus reste observation-only ;
- aucun événement ni commande n’est réémis par le bridge ;
- aucun accès SQL, Qdrant, OpenVINO, LLM, GitHub ou réseau ;
- les erreurs de conversion ou d’écriture restent confinées dans les statistiques de l’observateur ;
- aucune nouvelle CLI et aucune dépendance externe.

## Hors périmètre

La projection des retours Copilot dans les champs et vues ProjectV2 nécessite une mutation GitHub contrôlée distincte. Ce patch ne modifie pas le dépôt `newicody/projects`.

## Suite

- support : `0284-r1-r2-copilot-projectv2-visibility-projection` ;
- chaîne fonctionnelle : `0284-r2-portable-specialist-contract`.
