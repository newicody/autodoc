# Recherche et contexte

`src/context/` regroupe les services qui construisent, enrichissent, stockent, réhydratent et projettent le contexte de recherche. `src/experts/` et `src/policy/` apportent des capacités spécialisées et décisions consommées par les compositions.

Capacités présentes selon les providers/configurations : ingestion et revue de sources, mémoire/contexte, références durables et réhydratation, laboratoires/spécialistes, agrégation/provenance d'évidences, intégrations GitHub et projections Projects/Copilot. Un contrat ou adaptateur ne prouve pas que le provider externe est configuré.

Les spécialistes sont des capacités, pas des orchestrateurs autonomes. Les labs ne créent ni Scheduler, ni queue, ni registre, ni EventBus parallèles. Les actions GitHub mutantes sont soumises aux gates d'autorisation. Copilot conseille ; le Scheduler décide.

Évolution : associer chaque résultat au task/cell/research/source/evidence et instant d'observation ; construire le snapshot serveur Copilot à partir de lecteurs autorisés, sans secret ni transfert d'autorité.
