# État des composants et cadrage scientifique serveur

## Responsabilité des composants

Chaque composant reste propriétaire de son état et expose, par son interface
existante, un instantané à la demande. Le Scheduler et le serveur ne déduisent
pas un état absent à partir d'une liste de composants configurés.

Le contrat `missipy.server.component_state_snapshot.v1` porte notamment :

- disponibilité et état de collecte ;
- fraîcheur et date d'observation ;
- état de communication ;
- capacités déclarées et vérifiées par le composant ;
- réservations et interfaces ;
- statistiques d'utilisation propres au composant ;
- données disponibles et manquantes ;
- représentations scientifiques prises en charge ou non ;
- contraintes, erreurs et provenance.

Les valeurs inconnues, indisponibles, partielles ou périmées restent explicites.
Une information absente n'est jamais transformée en zéro ni présentée comme
une capacité vérifiée.

## Agrégation pour Copilot

`build_server_scientific_framing_assessment` agrège uniquement les
instantanés qui lui sont fournis. Il ne consulte aucun backend et n'invente
aucune observation. Il conserve les références de source et les dates,
sépare les statistiques d'utilisation, et dégrade la cohérence globale si un
état est partiel, inconnu, périmé, indisponible ou en erreur.

L'agrégateur ne déduit jamais la capacité d'admission du Scheduler depuis les
mesures CPU/GPU/RAM. La capacité logique relève du Scheduler et ses propres
données ; la télémétrie matérielle demeure une observation distincte.

## Raccordement au runtime

La composition OpenRC existante accepte un fournisseur d'instantanés injecté
dans le bundle des composants installés. Le runtime expose une opération
d'évaluation qui appelle ce fournisseur puis agrège les résultats. Aucun
nouveau registre, manager, poller, EventBus ou Scheduler n'est créé.

Le fournisseur concret appartient à la fabrique de composants installée.
Il doit interroger les interfaces des composants déjà composés et retourner
leurs observations typées. Le contrat ne remplace pas ces interfaces et ne
déclare pas qu'elles sont déjà implémentées.

L'adaptateur `publish_git_exchange_server_response.py` accepte soit une
évaluation structurée, soit un fichier d'instantanés de composants. Il valide
la réponse, la corrèle à l'artefact initial Copilot et la publie dans Git.
Le traitement vivant qui détecte l'arrivée de l'artefact initial, appelle
l'évaluation du runtime et lance cet adaptateur reste à raccorder.

## Limites d'autorité

- L'avis Copilot et sa reformulation restent non autoritatifs.
- La réponse serveur décrit cohérence, données, capacités, contraintes et
  provenance ; elle n'autorise jamais l'exécution.
- La transition ProjectV2 vers `En cours` et les contrôles d'admissibilité
  existants restent les portes d'entrée vers le Scheduler.
- EventBus et les projections d'observation ne deviennent pas des canaux de
  commande.
