# Copilot — contexte serveur de routage (0292)

**Schéma documentaire proposé :** `missipy.server.routing_context_snapshot.v1`  
**Statut :** spécification uniquement ; aucun producteur runtime n'est ajouté par 0292.

## 1. Objectif

Fournir à l'avis Copilot un instantané serveur borné et non secret afin qu'il puisse formuler une recommandation de destination ou de spécialiste en tenant compte de l'état réel du système. Le snapshot informe le conseil ; il ne délègue aucune autorité à Copilot.

## 2. Contenu logique

Le snapshot peut regrouper les vues suivantes, uniquement si elles sont exposées par des lecteurs existants et autorisés :

- **Projets et expériences** : identifiants, état, objectifs et références des projets actifs ; distinguer la source ProjectV2 #2 (snapshot query-only) de la cible ProjectV2 #3.
- **Outils** : capacités déclarées, version, disponibilité et contraintes d'usage ; aucune clé, aucun jeton ni secret.
- **Laboratoires et spécialistes** : identifiants stables, capacités déclarées, compatibilités et état de disponibilité connu ; ne pas inventer une capacité à partir du nom d'un composant.
- **État Scheduler** : quantité de cellules, identifiants/localisations logiques, tâches actives, réservations, charge courante et charge prédite, lorsque ces valeurs proviennent d'une vue contrôlée sous l'autorité du Scheduler.
- **Provenance et fraîcheur** : références de source, horodatage, version de snapshot et indication explicite des valeurs inconnues ou périmées.

Les valeurs de charge prédites sont des données de planification calculées sous l'autorité du Scheduler. Elles ne doivent pas être déduites de l'utilisation CPU, GPU ou mémoire.

## 3. Chaîne d'autorité

    lecteurs et contrats existants
      -> snapshot serveur typé et borné
      -> avis Copilot v2 (conseil non autoritaire)
      -> proposition éventuelle de routage
      -> validation et décision par le Scheduler canonique
      -> catalogue / binding / fabrique / handler existants

Copilot ne choisit pas la tâche READY, ne fait pas l'admission, ne réserve pas de capacité, ne crée pas de tâche et ne résout pas directement un handler. Toute proposition doit revenir à la frontière existante ; le Scheduler conserve la décision finale.

## 4. Séparation des plans d'observation

Les contrats 0288 définissent des observations matérielles versionnées, mais n'ajoutent pas de collecteur. Le snapshot de routage ne doit jamais confondre :

- les mesures physiques et leur fraîcheur ;
- les capacités logiques et réservations connues du Scheduler ;
- les projections d'observation EventBus/PassiveSupervisor/VisPy.

EventBus est un canal de faits observationnels, pas un service de commande. VisPy visualise ; il n'ordonnance pas.

## 5. Sécurité et minimisation

Le snapshot ne contient ni secrets, ni jetons GitHub, ni variables d'environnement, ni chemins locaux, ni octets d'artefacts, ni données personnelles non nécessaires. Les éléments doivent être des références typées et des résumés strictement utiles à l'analyse.

En cas d'indisponibilité, de fraîcheur inconnue ou de données contradictoires, le champ concerné reste explicitement inconnu ; aucune valeur par défaut ne doit simuler une disponibilité. Une proposition Copilot absente, invalide ou obsolète ne bloque pas le flux autoritatif.

## 6. Hors périmètre 0292

- aucun nouveau service, manager, orchestrateur, worker, queue, bus, registre ou proxy ;
- aucun changement Scheduler, EventBus, ControlProxy, SQL, Qdrant ou OpenVINO ;
- aucun appel API GitHub supplémentaire et aucune mutation ProjectV2 ;
- aucun collecteur matériel, polling ou service OpenRC ;
- aucune admission ni exécution déclenchée par Copilot.

## 7. Conditions préalables à une implémentation

Une phase ultérieure doit d'abord auditer les producteurs/readers existants pour chaque champ, vérifier les contrats et leurs versions, puis démontrer qu'un port de lecture minimal manque réellement. Elle pourra alors proposer une extension locale d'une frontière existante et des tests de règles dédiés. Elle ne doit pas matérialiser toute cette spécification en un nouveau sous-système.
