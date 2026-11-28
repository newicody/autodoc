# Règle — catalogue Scheduler de handlers 0287 r16-r27

## Réutilisation et séparation

- Ne pas étendre `kernel.Registry` avec des classes de handlers : ce registre reste réservé aux `ComponentProxy` actifs.
- Ne pas créer de `HandlerManager` ou de registre global rempli à l'import.
- Construire `SchedulerHandlerCatalog` explicitement au bootstrap et l'injecter.
- Considérer le catalogue comme une valeur immuable de composition, sans cycle de vie propre.

## Résolution

La résolution exige exactement :

```text
command_type + capability_ref + contract_version
```

Le catalogue ne choisit jamais automatiquement la version la plus récente, une priorité, un laboratoire ou une politique de retry.

## Doublons

Refuser :

- deux handlers pour la même clé exacte ;
- un `handler_ref` réutilisé pour une autre capacité ;
- un binding divergent du `HandlerDescriptor` certifié ;
- une classe qui n'hérite pas de `SchedulerHandler`.

## Effets de bord interdits

La construction et la résolution du catalogue ne doivent :

- instancier aucun handler ;
- démarrer aucun Scheduler ;
- appeler aucun Dispatcher ;
- ouvrir aucune ressource ;
- publier aucun fait EventBus ;
- afficher aucun texte automatiquement.

Les informations avancées restent accessibles dans le descripteur pour l'exécuteur Scheduler futur.
