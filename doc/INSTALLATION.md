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
