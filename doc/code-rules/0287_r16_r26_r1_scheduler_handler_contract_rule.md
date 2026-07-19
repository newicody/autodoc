# Règle — contrat Scheduler / handlers déclaratifs 0287 r16-r26-r1

## Déclaration obligatoire d'un handler concret

Chaque sous-classe concrète de `SchedulerHandler` déclare explicitement :

- `HANDLER_REF` ;
- `CAPABILITY_REF` ;
- `COMMAND_TYPE` ;
- `RESULT_TYPE` ;
- `CONTRACT_VERSION` ;
- `EXECUTION_POLICY` ;
- `INFORMATION`.

L'héritage exprime la spécialisation « est un handler Scheduler ». La composition porte les politiques, profils, informations et ports injectés.

## Rôle de la métaclasse

`SchedulerHandlerMeta` peut :

- vérifier les attributs obligatoires ;
- vérifier les références typées et la version ;
- imposer une méthode `execute()` asynchrone ;
- construire un `HandlerDescriptor` immuable ;
- valider les champs autorisés dans les textes informatifs.

Elle ne peut pas :

- exécuter le handler ;
- démarrer le Scheduler ou un laboratoire ;
- ouvrir SQL, Qdrant, OpenVINO ou `/dev/shm` ;
- créer un registre global par effet d'import ;
- imprimer directement ;
- choisir une priorité, un retry ou une tâche suivante.

## Information de cycle de vie

Il n'existe **aucun print implicite** dans la métaclasse ou la classe abstraite. Les attributs `INFORMATION` produisent des `HandlerLifecycleNotice` structurés. L'affichage réel passe par un `HandlerInformationSink` injecté.

Les phases autorisées sont :

```text
DECLARED, CREATED, STARTED, SUCCEEDED, FAILED, CANCELLED, CLOSED
```

Les textes peuvent utiliser uniquement les attributs contrôlés :

```text
handler_ref, capability_ref, handler_title,
command_ref, task_ref, result_ref,
elapsed_ms, attempt, error_type, error_message
```

## Autorité

Le Scheduler décide quand publier les phases d'exécution. L'EventBus, les logs et VisPy observent ces informations ; ils ne commandent jamais le handler.
