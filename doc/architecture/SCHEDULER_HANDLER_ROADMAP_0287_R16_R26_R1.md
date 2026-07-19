# Roadmap complète Scheduler / handlers — après 0287 r16-r26

## Socle déjà construit

- r16-r23 : triplet GitHub fetché et validé avant intake ;
- r16-r24 : tentative historique de remise fichier, désormais non canonique ;
- r16-r24-r1 : commande de recherche typée ;
- r16-r25 : persistance relationnelle PostgreSQL ;
- r16-r26 : réclamation atomique par un Scheduler canonique déjà actif.

## Nouvelle séquence verrouillée

### r16-r26-r1 — structure Scheduler / handlers et information de cycle de vie

- verrouiller la liste complète des responsabilités du Scheduler ;
- ajouter `SchedulerHandlerMeta`, `SchedulerHandler`, `HandlerDescriptor` ;
- déclarer les attributs avancés d'exécution ;
- produire les notices `CREATED/STARTED/SUCCEEDED/FAILED/CANCELLED/CLOSED` ;
- conserver l'affichage derrière un sink injecté ;
- ne modifier ni `Scheduler.run()` ni le Dispatcher.

### r16-r27 — catalogue explicite des capacités et registre de handlers

- étendre une surface de registre existante plutôt que créer un orchestrateur ;
- associer `command_type + capability_ref + version` à un type de handler ;
- détecter doublons et incompatibilités au bootstrap ;
- aucun auto-enregistrement par effet d'import.

### r16-r28 — modèle typé des tâches Scheduler

- `SchedulerTask`, états, priorité effective, dépendances et tentative ;
- relation commande/tâches en PostgreSQL ;
- transitions versionnées et auditables ;
- planification déterministe et bornée.

### r16-r29 — budgets, ressources et politiques d'exécution

- budget restant par commande et tâche ;
- profils CPU/iGPU/mémoire/SQL/Qdrant/laboratoire ;
- timeouts, retries, backoff, annulation et compensation ;
- aucune ressource réelle ouverte par les contrats.

### r16-r30 — exécuteur contrôlé de handlers sous autorité Scheduler

- résolution du handler ;
- construction par fabrique injectée ;
- notices informatives de début/fin ;
- résultat ou erreur typée ;
- Dispatcher limité à la compatibilité mécanique pendant la migration.

### r16-r31 — commande réclamée → tâche de préparation de laboratoire

- transformer `GitHubResearchSchedulerCommand` réclamée en première tâche ;
- préserver repository/issue/run/digests/conversation/return route ;
- demander au ControlProxy la route nécessaire ;
- ouvrir une visite, pas un second Scheduler.

### r16-r32 — première capacité spécialiste

- choisir explicitement spécialiste et version de capacité ;
- produire une analyse approfondie typée ;
- enregistrer l'analyse dans PostgreSQL ;
- publier les notices informatives du handler.

### r16-r33 — projection de la première analyse

- embedding E5 passage en 384 dimensions ;
- projection Qdrant avec référence SQL ;
- preuve de readback ;
- Qdrant ne devient jamais autorité.

### r16-r34 — seconde capacité spécialiste

- le Scheduler crée la seconde tâche après le premier résultat ;
- le spécialiste 1 ne lance rien directement ;
- analyse distincte, identité et digest propres ;
- persistance SQL séparée.

### r16-r35 — projection et rappel des deux analyses

- projection Qdrant séparée de l'analyse 2 ;
- recherche E5 query ;
- retour des références SQL ;
- réhydratation des deux analyses sans synthèse prématurée.

### r16-r36 — synthèse de liaison

- tâche Scheduler distincte ;
- conservation des accords, divergences et limites ;
- références explicites aux deux analyses ;
- synthèse durable séparée.

### r16-r37 — livrable final

- tâche distincte de construction ;
- demande autoritative + avis Copilot indicatif + analyses + synthèse ;
- livrable SQL versionné et digesté ;
- aucune publication implicite.

### r16-r38 — publication contrôlée

- plan immuable et digest de confirmation ;
- commentaire Issue et projection ProjectV2 ;
- autorisations distantes explicites ;
- idempotence et relecture distante.

### r16-r39 — clôture, reprise et compensation

- preuve de publication en SQL ;
- états `completed/failed/cancelled/timed-out` ;
- checkpoints et reprise après crash ;
- fermeture des routes et visites ;
- libération des ressources.

### r16-r40 — prototype bout-en-bout et automatisation serveur

- fcron/OpenRC déclenchent seulement les commandes one-shot nécessaires ;
- fetch → SQL → Scheduler canonique → laboratoire → publication ;
- EventBus/PassiveSupervisor/VisPy observent tout le cycle ;
- aucun daemon, queue JSONL, Scheduler ou Dispatcher autonome supplémentaire.

## Après le prototype bout-en-bout

- durcissement de concurrence et charge ;
- multi-laboratoires et transferts de spécialistes ;
- politiques d'équité et de préemption ;
- distribution multi-serveurs coordonnée ;
- observateur/accélérateur FPGA ou ASIC passif ;
- consolidation documentaire et dictionnaire français final.
