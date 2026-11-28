# Recherche et contexte

`src/context/` regroupe les services qui construisent, enrichissent, stockent, réhydratent et projettent le contexte de recherche. `src/experts/` et `src/policy/` apportent des capacités spécialisées et décisions consommées par les compositions.

Capacités présentes selon les providers/configurations : ingestion et revue de sources, mémoire/contexte, références durables et réhydratation, laboratoires/spécialistes, agrégation/provenance d'évidences, intégrations GitHub et projections Projects/Copilot. Un contrat ou adaptateur ne prouve pas que le provider externe est configuré.

Les spécialistes sont des capacités, pas des orchestrateurs autonomes. Les labs ne créent ni Scheduler, ni queue, ni registre, ni EventBus parallèles. Les actions GitHub mutantes sont soumises aux gates d'autorisation. Copilot conseille ; le Scheduler décide.

### Cadrage Copilot et itérations

Le cadrage initial est un échange unique : Copilot propose la forme de représentation scientifique nécessaire au rapport attendu ; le serveur vérifie cette proposition au regard des données, outils, capacités et contraintes disponibles et renvoie une réponse structurée ; Copilot reformule alors une demande précise. Ce cadrage ne se répète pas en boucle et ne vaut pas admission ni lancement d'une tâche.

Le déclenchement d'exécution reste distinct : la transition ProjectV2 vers `En cours`, à partir d'une intention opérateur, est traitée par le dispatch prévu. Après consultation des résultats publiés dans Git, Copilot peut proposer une amélioration ou une actualisation. Celle-ci devient un nouveau cycle lié à la recherche durable, conserve la filiation et l'historique, puis repasse par les contrôles d'admission du Scheduler.

Évolution : associer chaque résultat au task/cell/research/source/evidence et instant d'observation ; construire la réponse initiale et les vues Copilot à partir de lecteurs autorisés, sans secret ni transfert d'autorité. Distinguer l'artefact initial, la réponse serveur unique, la demande reformulée et les propositions ultérieures issues de la lecture des résultats.
