# Verrouillage de structure Scheduler / handlers — 0287 r16-r26-r1

## Décision canonique

- **Scheduler = autorité unique d'orchestration** dans le serveur Autodoc local.
- **PostgreSQL reste l'autorité durable** des commandes, tâches, états, résultats et preuves.
- `/dev/shm`, ControlProxy et les routes rapides constituent le plan de données et de contrôle rapide.
- **EventBus reste observation-only** : il reçoit des faits, jamais des commandes autoritatives.
- Le **Dispatcher reste mécanique et transitoire** tant que `Scheduler.run()` l'utilise pour associer un `EventType` à un handler. Il ne décide ni priorité, ni dépendance, ni retry, ni tâche suivante.
- La **métaclasse valide mais ne lance jamais** : elle certifie les attributs statiques des handlers et produit un descripteur immuable.

## Structure de code verrouillée

```text
src/kernel/
├── scheduler.py
│   └── autorité dynamique : admission, politique, priorité, tâches,
│       dépendances, budgets, ressources, exécution, reprise et clôture
├── scheduler_handler_contract.py
│   ├── SchedulerHandlerMeta
│   ├── SchedulerHandler[CommandT, ResultT]
│   ├── HandlerDescriptor
│   ├── HandlerExecutionPolicy
│   ├── HandlerInformation
│   └── HandlerLifecycleNotice
├── dispatcher.py
│   └── correspondance mécanique EventType → handler durant la migration
├── queue.py
│   └── file mémoire des événements immédiatement exécutables
└── registry.py
    └── registre existant des ComponentProxy

src/context/
├── commandes métier typées
├── stores PostgreSQL relationnels
├── plans de tâches et résultats typés
└── corrélations GitHub/laboratoire/spécialiste

src/runtime/
├── adaptateurs ControlProxy, /dev/shm, SQL, Qdrant, OpenVINO
├── fabriques injectant les ports dans les handlers
└── aucun orchestrateur parallèle
```

## Responsabilités complètes du Scheduler

Le Scheduler possède ou gouverne explicitement :

1. admission des intentions et commandes typées ;
2. décision de politique et contrôle des autorisations ;
3. réclamation atomique des commandes SQL ;
4. transformation commande → graphe de tâches ;
5. états et versions des commandes et tâches ;
6. priorités, échéances, équité et prévention de famine ;
7. dépendances, barrières et branches conditionnelles ;
8. budgets d'étapes, visites, durée, mémoire et appels ;
9. profils et réservations de ressources ;
10. sélection d'une capacité puis d'un handler compatible ;
11. injection du contexte d'exécution par une fabrique ;
12. démarrage, surveillance, timeout, annulation et fermeture du handler ;
13. classification des erreurs, retries, backoff et compensation ;
14. checkpoints et reprise après crash ou redémarrage ;
15. générations de contexte et invalidation des résultats périmés ;
16. choix du laboratoire, des visites et des capacités spécialistes ;
17. ordre des persistances SQL, projections Qdrant et réhydratations ;
18. tâches distinctes d'analyse, rappel, synthèse et livrable ;
19. plan, confirmation, publication GitHub et preuve de relecture ;
20. télémétrie, audit et faits d'observation ;
21. arrêt coopératif et libération des ressources ;
22. future distribution multi-nœuds sous une autorité coordonnée.

## Ce qui reste hors du Scheduler

Le Scheduler ne rédige pas, ne calcule pas d'embedding, n'interroge pas directement Qdrant, n'effectue pas directement les écritures métier SQL, ne manipule pas les buffers lourds et ne publie pas directement vers GitHub. Il ordonne des capacités explicites exécutées par des handlers minces.

## Cycle de vie informatif des handlers

Un handler déclare des attributs avancés : identité, capacité, types d'entrée/sortie, version, idempotence, politiques de timeout/retry, profil de ressources, laboratoires compatibles et textes informatifs.

```text
déclaration de classe
→ SchedulerHandlerMeta valide et construit HandlerDescriptor
→ aucun affichage, import dynamique ou enregistrement global

création d'instance
→ le propriétaire peut publier CREATED

exécution par le Scheduler
→ STARTED
→ SUCCEEDED | FAILED | CANCELLED

fermeture
→ CLOSED
```

Chaque phase produit un `HandlerLifecycleNotice` structuré. Un sink injecté peut l'afficher en texte, l'envoyer aux logs, à l'EventBus d'observation ou à VisPy. Le texte n'influence jamais l'ordonnancement.
