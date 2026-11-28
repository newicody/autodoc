# Installation

## Prérequis fonctionnels
- Linux est l'environnement de référence des compositions locales documentées.
- Python compatible avec le code courant (Python 3.14 a été utilisé dans l'environnement du mainteneur, sans constituer une matrice de compatibilité garantie).
- PostgreSQL pour la persistance durable ; Qdrant pour projection/rappel ; OpenVINO et les artefacts E5 pour les embeddings locaux.
- Accès/jetons GitHub uniquement pour les intégrations activées.

## Limite actuelle
Le dépôt ne possède pas encore de manifeste de packaging Python racine unique ni d'installateur universel validé pour toutes les surfaces optionnelles. Installer selon la composition visée et les fichiers de configuration dédiés ; ne pas assimiler les anciens rapports readiness à une installation complète garantie.

## Configuration
Les racines ControlFS, paramètres SQL/Qdrant, modèles et permissions GitHub doivent être fournis explicitement. Les secrets ne sont pas placés dans les graphes ni les snapshots. OpenRC ou le gestionnaire de services de l'OS contrôle la durée de vie des processus ; le Scheduler ne remplace pas l'init système.

## Validation
Valider imports, contrats, tests ciblés, accès aux services réels configurés et smoke test local contrôlé. Distinguer tests simulés et intégration réelle. Les runbooks spécifiques aux intégrations restent dans les sous-répertoires documentaires/historiques jusqu'à consolidation.

## Mode GitHub Projects

Le bundle du mode Projects est maintenu dans `templates/github/projects-repository/`
et doit être installé dans le dépôt de gestion prévu. Le réconciliateur
`reconcile_projectv2_configuration.py` couvre la configuration ProjectV2 des
champs et vues, mais ne constitue pas encore un installateur complet et
idempotent de tous les formulaires, workflows, permissions et secrets. Cette
installation intégrée est un objectif de l'étape 01 de la roadmap ; ne pas
présenter le bundle ou le réconciliateur seuls comme une installation achevée.

Le cadrage initial Copilot est distinct du dispatch d'exécution : l'ouverture
d'une Issue de recherche produit le premier artefact Copilot ; le serveur
renvoie une seule réponse de cohérence, puis Copilot reformule la demande. Le
cycle d'exécution est lancé séparément par la transition ProjectV2 vers
`En cours`. Les secrets GitHub sont configurés hors dépôt et ne doivent jamais
être versionnés.
