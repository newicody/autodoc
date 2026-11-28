# Cadrage scientifique initial Copilot–serveur

## Portée

Le cadrage initial est un échange borné, distinct de l'admission et de
l'exécution. Copilot propose l'objectif, le résultat attendu et surtout les
représentations scientifiques nécessaires au rapport (tableaux, séries,
visualisations, comparaisons, preuves et structure). Le serveur examine cette
proposition à partir des informations réellement détenues par les composants
et renvoie une seule réponse de cohérence. Copilot reformule ensuite la demande
une seule fois à partir de cette réponse.

Il n'existe pas de boucle automatique de clarification. Une proposition
ultérieure après consultation des résultats Git est une nouvelle itération de
la recherche, avec filiation et admission normale par le Scheduler.

## Contrat initial 0293

Le contrat `contracts.copilot_scientific_framing` définit trois artefacts
corrélés :

1. l'avis initial existant `missipy.github.copilot_advisory.v2` ;
2. la réponse serveur `missipy.github.server_scientific_framing_response.v1` ;
3. la demande reformulée `missipy.github.copilot_refined_research_request.v1`.

La réponse serveur expose l'état de cohérence, les représentations prises en
charge ou non, les données disponibles/manquantes, les capacités vérifiées,
les contraintes, le plan de rapport et la provenance/fraîcheur des informations.
Elle ne prétend pas disposer d'informations absentes et n'autorise jamais
l'exécution.

Chaque artefact référence la demande initiale et l'empreinte de l'avis
précédent. La demande reformulée est liée au digest exact de la réponse serveur.
Les contenus Copilot restent non fiables et non autoritatifs.

## Frontières

- Ce contrat est une validation de données, pas un producteur de capacités ni
  un moteur d'évaluation de cohérence.
- Il ne crée ni manager, ni orchestrateur, ni queue, ni bus, ni registre.
- Il n'appelle pas Copilot, GitHub, PostgreSQL, Qdrant ou le Scheduler.
- La réponse serveur doit être produite par des lecteurs existants autorisés ;
  toute donnée inconnue ou périmée doit le rester explicitement.
- La transition ProjectV2 vers `En cours` demeure le déclencheur du cycle
  d'exécution. Le cadrage initial ne vaut pas admission.

## État de réalisation

0293 établit le contrat typé et ses validations. Le producteur serveur, le
second appel Copilot, la persistance append-only et le raccordement au parcours
d'artefacts restent à intégrer avant de déclarer l'échange opérationnel.
