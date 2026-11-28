# Roadmap complète — automate cellulaire

Cette roadmap fusionne les développements existants, les travaux encore pertinents des anciennes trajectoires et les orientations discutées récemment. Les identifiants de patch/phase sont des repères historiques, pas l'ordre obligatoire des travaux.

## Invariants
Le code de la branche courante est la référence de l'état implémenté. Un contrat ne prouve pas qu'un producteur existe. Les projections d'observation ne commandent pas. PostgreSQL est l'autorité durable ; Qdrant est une projection reconstruisible. Le Scheduler est l'autorité unique d'admission et d'orchestration. Les labs/spécialistes n'ont pas d'orchestrateur parallèle. Les objectifs de roadmap ne sont pas des fonctionnalités livrées.
- Une cellule logique n'est pas un processus OS, une machine ou un thread.
- Charge physique et capacité logique du Scheduler restent séparées ; l'une ne permet pas de déduire l'autre.

## 1. Socle déjà présent
- Kernel : Scheduler, PriorityQueue, Dispatcher, Registry, PolicyEngine, ContextEngine et EventBus.
- Recherche/contexte : ingestion, revue, mémoire, rehydratation, provenance, labs/spécialistes et intégrations selon composition.
- Données : chemins PostgreSQL, OpenVINO/E5 et Qdrant ; SQL reste l'autorité, Qdrant projection/rappel.
- GitHub : adaptateurs Actions/Projects v2, avis Copilot et publications consultatives présents.
- Observation : EventBus→Cell Lens bridge, journal append-only, projection et read-model visuel passif présents.
- Hardware : contrats versionnés `missipy.hardware_sample.v1` et `missipy.hardware_cell.v1` présents ; pas de collecteur OS livré par 0288.

Limites : le noyau n'est pas encore le moteur complet de recherche cellulaire adaptative ; le read-model ne prouve pas un renderer VisPy complet ; le snapshot serveur Copilot 0292 reste une spécification ; les contrats hardware ne collectent rien par eux-mêmes.

## 2. Consolidation actuelle — priorité immédiate
- Réduire la racine de doc à moins de dix références stables.
- Déplacer patches, changelogs, manifests, audits et graphes historiques dans `history/`.
- Maintenir une documentation par unité architecturale principale.
- Réconcilier les graphes .dot avec les seuls composants et flux fonctionnels.
- Contrôler liens, rendu Graphviz et synchronisation docs/code.

## 3. Modèle de l'automate cellulaire
- Définir identité, type, état, cycle de vie, provenance, relations et version des cellules.
- Distinguer cellule, tâche, handler, composant, ressource physique et projection visuelle.
- Définir transitions, événements, invariants et reconstruction depuis le durable.
- Relier `missipy.cell.v1` aux futurs contrats sans rupture de compatibilité.

## 4. Scheduler orienté recherche
- Représenter les recherches comme graphes de tâches dépendantes sous autorité du Scheduler existant.
- Les handlers rapportent résultats, état, preuves, coût et incertitude à l'instant t.
- Le Scheduler réévalue les branches et les tâches selon les observations.
- Mesurer couverture, fréquence, nouveauté, rendement et incertitude des cellules.
- Favoriser l'exploration des cellules/régions sous-représentées sans éliminer trop tôt une piste rare prometteuse.
- Abandonner une recherche de faible intérêt par transition explicite, sans annuler les tâches indépendantes.
- Persister décisions, justification, reprise et provenance dans PostgreSQL.
- Calculer la charge logique à partir des tâches, files, budgets et réservations du Scheduler.

## 5. Observation et visualisation
- Enrichir les événements avec identifiants de cellules, tâches, recherches, handlers et ressources.
- Consolider journal append-only, snapshots, replay et projections.
- Définir un read-model stable ; raccorder un renderer VisPy après validation.
- Montrer données absentes, périmées et incertaines ; le visualiseur reste passif et facultatif.

## 6. Collecte matérielle
- Créer un collecteur explicite et testable produisant HardwareSample 0288.
- Construire HardwareCell en séparant mesures physiques et snapshots logiques Scheduler.
- Conserver fraîcheur, provenance, erreurs et statut partiel ; inconnu n'est jamais zéro.
- Ne jamais inférer admission/capacité Scheduler depuis CPU/GPU/RAM seuls.

## 7. Copilot contextualisé serveur
- Conserver Copilot consultatif et les adaptateurs existants.
- Produire le snapshot `missipy.server.routing_context_snapshot.v1` décrit en 0292.
- Agréger projets/expériences, outils, laboratoires, cellules, état et charge logique depuis des lecteurs autorisés.
- Prédire la charge depuis le Scheduler, pas depuis l'utilisation matérielle seule.
- Snapshot borné, daté, traçable et sans secrets ; le Scheduler décide toujours.

## 8. Données, retrieval et intégrité
- Consolider migrations/contrats PostgreSQL comme autorité durable.
- Vérifier SQL→E5→Qdrant et rappel→références→réhydratation SQL.
- Rendre les projections vectorielles reconstructibles et versionner explicitement profils/collections.
- Préserver 384 dimensions pour le profil E5 canonique.

## 9. Labs, spécialistes et intégrations
- Réutiliser catalogue, fabrique et handlers du Scheduler.
- Aucun scheduler, queue, bus, registre ou manager parallèle dans les labs.
- Séparer lecture, proposition, approbation humaine et mutation GitHub.
- Clarifier les surfaces ProjectV2 source/read et cible/projection selon configuration déployée.

## 10. Installation et validation
- Ajouter un manifeste Python séparant runtime, dev et tests, avec versions compatibles.
- Définir installation minimale puis extras PostgreSQL, Qdrant, OpenVINO, GitHub et visualisation.
- Décrire secrets, migrations, modèles, services et OpenRC.
- Exécuter une acceptance end-to-end sur environnement réel.

## Ordre recommandé
1. Finir la documentation et les graphes fonctionnels.
2. Formaliser cellules et invariants.
3. Spécifier les graphes de recherche et transitions Scheduler.
4. Implémenter mesure de couverture et réévaluation contrôlée.
5. Compléter observation et visualisation passive.
6. Ajouter collecte matérielle.
7. Produire le snapshot serveur Copilot.
8. Stabiliser installation et acceptance end-to-end.

Les anciennes étapes r16-r67 sont conservées dans l'historique et ne sont reprises que si leur besoin demeure pertinent et n'est pas déjà satisfait.
