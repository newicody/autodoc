# Port PostgreSQL partagé du runtime OpenRC — 0287 r16-r62

La fondation `externally-managed` possède déjà une connexion PostgreSQL unique.
Cette unité l'expose uniquement à travers un port typé de construction
d'adaptateurs. Aucun composant ne lit un attribut privé, ne récupère la
connexion brute et ne peut la fermer indépendamment de la fondation. Les
capacités DB-API sont vérifiées seulement lorsqu'un adaptateur les réclame.

Le premier adaptateur concret est le store relationnel d'observation temporelle
du Scheduler. Son schéma est initialisé sur la connexion déjà ouverte. Les
adaptateurs de continuation et de réhydratation utiliseront la même frontière.

OpenRC possède le processus, le Scheduler canonique unique orchestre, PostgreSQL
reste l'autorité durable, Qdrant reste projection et rappel, et OpenVINO E5 reste
en dimension 384. Aucun stockage interne JSON et aucune file JSONL ne sont
introduits.
