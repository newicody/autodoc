# Dictionnaire français Autodoc/MissiPy — clôture 0287 r16-r50

Ce dictionnaire fixe les équivalents français employés dans la documentation.

| Terme courant | Formulation française retenue |
|---|---|
| artifact | artefact |
| authoritative request | demande autoritative |
| bootstrap | amorçage explicite |
| binding | raccord ou liaison de dépendances |
| capability | capacité |
| claim | réclamation atomique |
| closed loop | boucle fermée |
| commit | validation transactionnelle |
| rollback | annulation transactionnelle |
| handler | gestionnaire de traitement |
| handler factory | fabrique de gestionnaires |
| issue | ticket GitHub |
| lifecycle | cycle de vie |
| manifest | manifeste |
| pipeline | chaîne de traitement |
| projection | projection dérivée |
| readback | relecture de confirmation |
| recall | rappel de références |
| replay | rejeu idempotent |
| retry | nouvelle tentative contrôlée |
| runtime | environnement d'exécution |
| scheduler | ordonnanceur central |
| sink | récepteur d'observation |
| smoke test | essai de fonctionnement minimal |
| task graph | graphe de tâches |
| tick | pas borné d'exécution |
| timeout | expiration du délai |
| workflow | flux de travail automatisé |
| work package | paquet de travail |
| observation-only | sans autorité d'exécution |

## Termes d'architecture

- **Autorité durable** : stockage qui fait foi après redémarrage. Dans ce
  projet, il s'agit de PostgreSQL.
- **Projection de rappel** : index dérivé utilisé pour retrouver des
  références. Qdrant n'est pas l'autorité du texte.
- **Réclamation atomique** : prise en charge concurrente d'une commande par un
  seul Scheduler, dans une transaction SQL.
- **Relecture de confirmation** : lecture effectuée après une écriture ou une
  mutation distante afin de prouver l'état réellement obtenu.
- **Gestionnaire de traitement** : composant exécutant une capacité précise
  après sélection et autorisation par le Scheduler.
- **Observation sans autorité** : collecte ou visualisation qui ne choisit
  jamais la tâche, le handler ou la décision suivante.
