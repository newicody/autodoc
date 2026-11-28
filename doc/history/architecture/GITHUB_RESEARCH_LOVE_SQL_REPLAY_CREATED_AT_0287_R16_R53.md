# Rejeu SQL des analyses et horodatage initial — 0287 r16 r53

## Problème observé

Le couple d'analyses spécialistes produit des références déterministes à partir du
paquet de travail et des digests des deux résultats. Les objets d'autorité SQL
étaient donc identiques lors d'un rejeu, mais les deux descripteurs d'artefact et
la révision recevaient l'horodatage du nouvel essai Scheduler. PostgreSQL
signalait alors trois collisions immuables malgré un contenu métier inchangé.

## Décision

PostgreSQL reste l'autorité durable. Lorsqu'au moins un descripteur d'artefact ou
la révision déterministe existe déjà, son `created_at` devient l'horodatage de
première matérialisation pour reconstruire le plan exact. Un rejeu ne réécrit
pas cet horodatage et ne relâche pas la comparaison immuable complète.

Les trois entités temporelles existantes doivent porter le même horodatage. Une
divergence échoue fermée avant toute écriture. Un état partiel valide peut ainsi
être repris : l'horodatage déjà persisté est réutilisé pour les entités encore
absentes, puis le readback exact demeure obligatoire.

## Frontières conservées

- les deux analyses restent deux objets SQL et deux artefacts distincts ;
- la révision enfant reste écrite en dernier ;
- aucun état PostgreSQL existant n'est supprimé ou écrasé ;
- Qdrant reste une projection et n'intervient pas dans cette décision ;
- aucun Scheduler, Dispatcher, daemon, thread ou processus supplémentaire ;
- aucune file JSONL et aucun JSON comme stockage interne ;
- le JSON présent dans le module reste une représentation canonique de frontière
  pour le corps et les digests, jamais l'autorité durable.
