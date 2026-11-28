# Acceptation réelle bout en bout — 0287 r16-r50

## But

Cette unité ajoute la porte finale qui permet de dire qu'un cycle réel est
terminé. Elle ne confond pas présence du code et preuve d'exécution.

La porte exige un même triplet de corrélation :

```text
repository / issue_number / run_id
```

dans les rapports du fetch, de la préparation locale, de la publication et de
la clôture.

## Preuves obligatoires

1. Fetch exécuté avec le statut `artifacts-fetched`.
2. Triplet distinct `authoritative_request`, `copilot_advisory`,
   `run_manifest`.
3. Onze étapes locales présentes dans l'ordre.
4. Digest de publication confirmé sans divergence.
5. Publication distante `published` ou `published-replay`.
6. Preuve SQL de clôture avec `cycle_closed=true`.
7. Au moins dix handlers observés avec :
   `CREATED → STARTED → phase terminale → CLOSED`.

## Frontières

Aucun nouveau Scheduler n'est créé. Aucun Dispatcher autonome, aucun
LaboratoryManager et aucune nouvelle boucle de service ne sont ajoutés.

PostgreSQL reste l'autorité durable. Qdrant reste une projection de rappel.
Le JSON n'est utilisé que pour les rapports externes du CLI.

VisPy reste observation-only. Les traces temporelles prouvent l'apparition,
l'activité, la terminaison et la disparition logique des handlers, sans leur
donner d'autorité sur l'exécution.

## Résultat

La porte produit `accepted` uniquement lorsque toutes les preuves sont
présentes et corrélées. Sinon elle produit `rejected` avec les écarts exacts.
