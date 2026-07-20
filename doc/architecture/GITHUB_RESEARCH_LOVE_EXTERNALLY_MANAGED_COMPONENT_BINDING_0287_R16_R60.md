# Liaison fondation → ports durables OpenRC — 0287 r16 r60

## Objectif

Cette unité relie la fondation réelle r16-r59 au bundle de composants r16-r58.
Elle ne recrée aucun backend. La fabrique durable reçoit la fondation déjà
ouverte et doit construire uniquement des adapters autour de ses ports.

```text
OpenRC
  → composition r16-r58
  → liaison r16-r60
  → fondation r16-r59 possédée une seule fois
  → ports durables injectés
  → dix handlers et cycle Scheduler borné
```

## Alignement obligatoire

La liaison vérifie avant de rendre le bundle :

- le même `scheduler_ref` ;
- la même révision de base PostgreSQL ;
- la même collection Qdrant ;
- la dimension OpenVINO E5 et Qdrant égale à 384 ;
- les méthodes des quatre fournisseurs de handlers ;
- le store de continuation, le constructeur du step runner et le store
  d'observation relationnel.

Toute divergence ferme la fondation et échoue avant le démarrage du service.

## Autorités

Le Scheduler canonique unique reste l'autorité d'orchestration. PostgreSQL reste
l'autorité durable. Qdrant reste projection et rappel. OpenVINO reste le moteur
d'embedding injecté. OpenRC possède seulement le processus et ses fermetures.

Aucune file JSONL et aucun stockage interne JSON ne sont ajoutés. Les mappings
sont seulement des reçus de frontière.

## Frontière suivante

La variable de fabrique durable reste vide jusqu'à l'unité suivante. Cette
frontière empêche l'activation d'un service partiellement câblé et interdit aux
fournisseurs d'ouvrir une deuxième connexion PostgreSQL, un second client
Qdrant ou un autre Scheduler.
