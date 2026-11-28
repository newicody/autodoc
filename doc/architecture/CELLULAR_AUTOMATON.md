# Automate cellulaire

L'automate cellulaire est le modèle global d'Autodoc/MissiPy. Les cellules sont des unités logiques portant état, relations, provenance et observations ; elles ne sont pas nécessairement des processus, threads, machines ou modules Python.

## Fondations présentes
- Contrats et événements de cycle de vie `missipy.cell.v1`.
- `CellObservationEvent`, snapshots et journal append-only.
- Pont passif EventBus→journal Cell Lens.
- Projections et read-model visuel passif.
- Contrats matériels versionnés `missipy.hardware_sample.v1` et `missipy.hardware_cell.v1`.

Ces briques assurent une base de représentation/observation, pas encore un moteur adaptatif qui pilote les recherches selon les statistiques cellulaires.

| Terme | Sens |
|---|---|
| Cellule | Unité logique du modèle |
| Tâche | Travail admis et géré par le Scheduler |
| Handler | Exécuteur spécialisé d'une tâche |
| Observation | Fait daté, sourcé, éventuellement incomplet |
| Projection | Vue dérivée, reconstruisible et non autoritaire |
| Ressource physique | CPU, mémoire, stockage, GPU, réseau… |

Le Scheduler décide des transitions de tâches ; PostgreSQL conserve l'état durable ; EventBus diffuse les observations ; les modèles visuels ne décident pas. Le futur graphe de recherche permettra de réévaluer les pistes, mesurer la couverture et abandonner une branche peu intéressante sans interrompre les tâches indépendantes.
