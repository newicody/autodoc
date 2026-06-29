# Header de recherche / Philosophie du projet

## Micro-Kernel Coopératif IA

### Vision

L'objectif de ce projet est de concevoir un micro-kernel coopératif destiné à l'orchestration d'une plateforme IA modulaire, observable et déterministe. Le système s'inspire davantage de l'architecture d'un système d'exploitation que d'une application Python traditionnelle.

Chaque fonctionnalité est un composant indépendant. Aucun composant n'appelle directement un autre composant. Toutes les interactions transitent exclusivement par des événements interprétés par un Scheduler central.

Le Scheduler constitue le cœur du système. Il ne contient aucune logique métier. Il orchestre uniquement l'exécution, les ressources, les priorités, les politiques de sécurité et le cycle de vie des composants.

### Principes fondamentaux

- Tout est un composant.
- Tout est piloté par événements.
- Tout composant est une coroutine coopérative.
- Toute décision est déterministe.
- Toute exécution est rejouable.
- Toute activité est observable.
- Toute fonctionnalité est extensible sans modification du noyau.

### Philosophie de développement

Le projet privilégie systématiquement :

- la bibliothèque standard Python avant toute dépendance externe ;
- Python 3.14 et les mécanismes modernes du langage ;
- le typage statique exhaustif ;
- les `dataclass(frozen=True)` pour les données immuables ;
- les générateurs (`yield`) plutôt que les appels bloquants ;
- les événements plutôt que les appels directs ;
- la composition plutôt que l'héritage profond ;
- le chargement paresseux (`Lazy Loading`) ;
- les politiques explicites plutôt que les comportements implicites ;
- des composants faiblement couplés ;
- des structures facilement testables et rejouables.

### Contrat d'un composant

Un composant ne réalise jamais directement une action.

Il exprime uniquement une intention :

```python
yield Event(...)
```

Le Scheduler est le seul autorisé à interpréter cette intention.

Chaque composant expose uniquement un contrat minimal :

```text
tick()
context()
```

Le reste de son comportement est géré par le noyau.

### Instrumentation native

Les mécanismes d'introspection de Python sont utilisés comme infrastructure de contrôle et d'observabilité.

Les hooks tels que :

- `__new__`
- `__init__`
- `__getattribute__`
- `__getattr__`
- `__setattr__`
- `__call__`
- `__iter__`
- `__enter__`
- `__exit__`

ne contiennent aucune logique métier. Ils servent exclusivement à :

- produire des événements ;
- mesurer les performances ;
- appliquer les politiques ;
- assurer le chargement paresseux ;
- alimenter la télémétrie ;
- tracer l'exécution ;
- garantir la reproductibilité.

Chaque composant est exposé au système à travers un `ComponentProxy`, chargé d'intercepter les accès, de publier les événements et de préserver l'isolation entre le noyau et les composants.

### Contexte global

Le Scheduler construit périodiquement une vision cohérente du système à l'aide de la primitive `GET_CONTEXT_ALL`.

Chaque composant publie son état sous forme de `ContextEvent`. Le `ContextCollector` agrège ces informations dans un `GlobalContextSnapshot` immuable, qui est ensuite transformé en `InferenceContext` destiné aux moteurs de raisonnement, à OpenVINO, au MCTS ou à tout autre composant décisionnel.

Cette approche permet d'adapter dynamiquement les priorités, les ressources et les stratégies d'exécution sans rompre le déterminisme du noyau ni introduire de dépendances directes entre les composants.

### Décisions architecturales maintenues

- Le Context Engine est une brique fondamentale du noyau, et non un simple module.
- Le ComponentProxy est obligatoire et fait partie du contrat du kernel.
- Le Scheduler construit un `GlobalContext` qui influence les décisions d'exécution sans casser le déterminisme.
- La Queue est le chemin de commande déterministe.
- L'EventBus est le chemin d'observation et ne commande pas les composants.
