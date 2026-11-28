# Propriétaire OpenRC du Scheduler de recherche GitHub — 0287 r16 r57

## Objectif

Cette unité transforme la composition `externally-managed` déjà existante en
un processus Python possédable par OpenRC. Elle ne compose pas encore les
backends installés : la fabrique concrète reste une unité suivante et doit être
explicitement configurée.

## Frontière canonique

```text
OpenRC / OS / administrateur
  -> possède le PID Python
  -> lance un unique Scheduler canonique
  -> boucle coopérative de ticks bornés
  -> claim relationnel PostgreSQL
  -> graphe et handlers existants
```

OpenRC possède le processus. Le Scheduler canonique unique reste l'autorité
d'orchestration. PostgreSQL reste l'autorité durable des commandes, graphes,
tâches et preuves. Qdrant reste une projection et un moteur de rappel.
ControlFS et `/dev/shm` restent le plan de données rapide.

## Absences garanties

- aucun second Scheduler ;
- aucun Dispatcher ou EventBus parallèle ;
- aucun `RuntimeManager` ;
- aucun stockage interne JSON ;
- aucune file JSONL ;
- aucun secret dans le template OpenRC ;
- aucun démarrage de PostgreSQL, Qdrant ou OpenVINO par le Scheduler.

Le JSON éventuel de la CLI est seulement une projection opérateur du reçu typé.

## Pourquoi une nouvelle entrée de service

`src/main.py` reste le launcher générique historique du micro-kernel et charge
encore le backend d'inférence de démonstration. Le chemin de recherche GitHub
possède déjà un runtime métier borné et dix handlers dédiés. Le wrapper OpenRC
est donc une frontière d'exploitation explicite, pas un nouvel orchestrateur.

## État de marche

Cette unité fournit le propriétaire de boucle et les templates OpenRC. Elle ne
doit pas être activée avant l'unité de composition installée qui retournera un
`GitHubResearchLoveOpenRcServiceBundle` réel. Le mode `tool-bounded` reste le
harnais de test jusqu'à ce raccordement.
