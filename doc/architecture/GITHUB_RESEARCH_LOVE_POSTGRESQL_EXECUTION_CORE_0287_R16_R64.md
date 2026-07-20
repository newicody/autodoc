# Noyau d'exécution PostgreSQL partagé — 0287 r16-r64

Cette unité sépare les quatre fournisseurs métier du noyau durable d'exécution.
Le noyau reçoit la fondation OpenRC déjà ouverte et réutilise exactement son
port PostgreSQL partagé, son Scheduler canonique, sa transaction de lancement
r31 et sa transaction de fin r33.

Le store de continuation est construit par `LovePostgreSqlSharedAdapterPort`.
Il reçoit la connexion DB-API déjà possédée par le binding et doit exposer
`load_snapshot`, `commit_promotion` et `initialize_schema`. Aucune connexion
PostgreSQL supplémentaire n'est ouverte.

Le constructeur du step runner impose les objets de la fondation après les
arguments fournis par l'appelant. Une fabrique ne peut donc remplacer ni le
Scheduler, ni le store de continuation, ni les transactions de lancement et de
fin. Le runner produit doit réutiliser la chaîne existante
admission → lancement SQL → handler → exécution → fin SQL.

La composition r16-r63 reçoit le noyau r16-r64 et doit réexposer les mêmes
objets `continuation_store` et `step_runner_builder`. Elle ne conserve que
l'assemblage des quatre fournisseurs typés de première visite, pipeline groupé,
étapes aval et publication/clôture.

PostgreSQL reste l'autorité durable. Qdrant reste projection et rappel.
OpenVINO E5 reste injecté avec 384 dimensions. OpenRC possède le processus et
le Scheduler canonique unique conserve toute décision d'orchestration.

Aucun stockage métier JSON, aucune file JSONL, aucun nouveau Scheduler,
Dispatcher, EventBus, thread, processus ou backend n'est introduit. Les trois
fabriques d'exécution restent obligatoires et le service échoue fermé tant que
leurs références `module:function` ne sont pas installées.

## Suite

L'unité suivante doit fournir les implémentations relationnelles concrètes du
store de continuation et du step runner transactionnel, puis renseigner les deux
variables r16-r64 avant le smoke OpenRC réel.
