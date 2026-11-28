# Admission des tâches Scheduler — 0287 r16-r30

Cette unité ajoute le calcul pur des budgets, priorités effectives, ressources,
échéances et reprises. Elle se place après le modèle de tâches r16-r28 et le
graphe r16-r29, mais avant toute exécution réelle de handler.

## Frontière

```text
SchedulerTask ready
+ budget global de commande
+ budget de tâche
+ politique d’équité
+ politique de retry
+ profil de ressources résolu
+ photographie de disponibilité
    ↓
SchedulerTaskAdmissionPlan immuable
    ↓
aucun effet appliqué dans r16-r30
```

PostgreSQL reste l’autorité durable des commandes, tâches, budgets, états et
réservations réellement appliquées. `/dev/shm` et ControlProxy resteront le plan
de données rapide. Cette unité n’ajoute aucune file JSON ou JSONL.

## Responsabilités couvertes

- budget maximal d’étapes Scheduler par commande ;
- budget maximal de visites de spécialistes ;
- budget de tentatives et timeout par tâche ;
- échéance de commande et échéance calculée de tentative ;
- backoff de retry entier, déterministe et borné ;
- priorité effective avec vieillissement contrôlé pour la prévention de famine ;
- boost d’échéance explicite ;
- profils de ressources typés ;
- réservation proposée, immuable et digestée ;
- ordre stable entre tâches de même priorité ;
- motifs typés `admitted`, `deferred` et `rejected`.

## Exclusions

Le planificateur ne démarre pas le Scheduler, ne modifie pas `Scheduler.run()`,
ne réclame rien dans PostgreSQL, ne réserve aucune ressource réelle, ne publie
aucun événement et aucun handler n’est exécuté. Le Dispatcher historique n’est
pas appelé. Le laboratoire et les spécialistes ne sont pas lancés.

L’EventBus et PassiveSupervisor restent des surfaces d’observation.
VisPy reste observation-only. La future mémoire temporelle VisPy pourra
conserver ou agréger les apparitions et disparitions d’objets, mais elle ne
modifiera jamais une décision d’admission.
