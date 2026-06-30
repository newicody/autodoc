# Header de recherche / Philosophie du projet

## Micro-Kernel Coopératif IA

### Vision

L'objectif de ce projet est de concevoir un micro-kernel coopératif destiné à l'orchestration d'une plateforme IA modulaire, observable et déterministe.

Le système s'inspire davantage de l'architecture d'un système d'exploitation que d'une application Python traditionnelle.

Chaque fonctionnalité est un composant indépendant.

Aucun composant n'appelle directement un autre composant.

Toutes les interactions transitent exclusivement par des événements interprétés par un Scheduler central.

Le Scheduler constitue le cœur du système. Il ne contient aucune logique métier. Il orchestre uniquement l'exécution, les ressources, les priorités, les politiques de sécurité et le cycle de vie des composants.

## Principes fondamentaux

- Tout est un composant.
- Tout est piloté par événements.
- Tout composant est une coroutine coopérative.
- Toute décision est déterministe.
- Toute exécution est rejouable.
- Toute activité est observable.
- Toute fonctionnalité est extensible sans modification du noyau.

## Philosophie de développement

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

## Contrat d'un composant

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

## Instrumentation native

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

ne contiennent aucune logique métier.

Ils servent exclusivement à :

- produire des événements ;
- mesurer les performances ;
- appliquer les politiques ;
- assurer le chargement paresseux ;
- alimenter la télémétrie ;
- tracer l'exécution ;
- garantir la reproductibilité.

Chaque composant est exposé au système à travers un `ComponentProxy`, chargé d'intercepter les accès, de publier les événements et de préserver l'isolation entre le noyau et les composants.

## Contexte global

Le Scheduler construit périodiquement une vision cohérente du système à l'aide de la primitive `GET_CONTEXT_ALL`.

Chaque composant publie son état sous forme de `ContextEvent`.

Le `ContextCollector` agrège ces informations dans un `GlobalContextSnapshot` immuable, qui est ensuite transformé en `InferenceContext` destiné aux moteurs de raisonnement, à OpenVINO, au MCTS ou à tout autre composant décisionnel.

Cette approche permet d'adapter dynamiquement les priorités, les ressources et les stratégies d'exécution sans rompre le déterminisme du noyau ni introduire de dépendances directes entre les composants.

## Décisions architecturales maintenues

- Le Context Engine est une brique fondamentale du noyau, et non un simple module.
- Le ComponentProxy est obligatoire et fait partie du contrat du kernel.
- Le Scheduler construit un `GlobalContext` qui influence les décisions d'exécution sans casser le déterminisme.
- La Queue est le chemin de commande déterministe.
- L'EventBus est le chemin d'observation et ne commande pas les composants.

## État actuel du modèle après Phase 2.6

La philosophie initiale reste valide, mais le modèle s'est précisé.

Le Scheduler n'est plus décrit comme un interprète monolithique : il orchestre une chaîne explicite.

```text
Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
```

L'`EventBus` ne commande pas les composants.

Il reste le canal d'observation pour la télémétrie, le recorder et le replay.

Le chemin d'inférence ne dépend jamais directement d'un runtime concret :

```text
InferenceRequestHandler
-> InferenceAdapter
-> BackendRegistry
-> InferenceBackend
```

Tout backend réel doit être enregistré explicitement dans `BackendRegistry` et autorisé explicitement par `PolicyEngine`.

Aucun backend d'inférence ne doit être ajouté par défaut implicite.

Un runtime réel, comme OpenVINO, est autorisé uniquement comme adaptateur explicite, isolé, testable, et chargé à la frontière prévue. Il ne doit jamais devenir une dépendance implicite du Scheduler, du noyau, d'un contrat abstrait ou d'un composant métier.

## Addendum Phase 4.12-r2 — Application aux outils temporaires, E5 et futures phases

Cet addendum ne remplace pas les règles précédentes.

Il précise comment appliquer la philosophie du micro-kernel aux outils créés pendant les phases de développement, notamment les outils E5 de build, search, inspect et rebuild.

### 1. Les outils CLI ne sont pas une exception au style kernel

Un outil CLI est un adaptateur temporaire.

Il peut exister pour tester, diagnostiquer ou piloter une fonctionnalité pendant le développement, mais il ne constitue pas une zone spéciale où les règles du projet seraient affaiblies.

Même exposée par une CLI, une fonctionnalité doit être écrite comme un futur composant pilotable par événement.

La CLI peut :

- parser les arguments ;
- transformer les arguments en intention typée ;
- appeler un use-case local en attendant son intégration au Scheduler ;
- convertir le résultat en texte, JSON, fichier, code retour ou message d'erreur.

La CLI ne doit pas :

- contenir la logique métier principale ;
- propager `argparse.Namespace` hors de la couche d'adaptation ;
- charger implicitement un backend réel ;
- créer des politiques implicites ;
- contourner le modèle du noyau dans du code destiné à devenir composant.

### 2. Toute CLI doit produire une intention typée

Après parsing, une CLI doit produire une structure immuable représentant l'intention demandée.

Exemples attendus :

```python
@dataclass(frozen=True, slots=True)
class E5SearchCommand:
    index: Path
    query: str
    limit: int
    min_score: float | None
```

```python
@dataclass(frozen=True, slots=True)
class E5RebuildCommand:
    index: Path
    source_dirs: tuple[Path, ...]
    validation_queries: tuple[str, ...]
```

Le cœur d'exécution doit dépendre de ces commandes, pas de `argparse.Namespace`.

### 3. Toute règle de décision doit être une politique explicite

Les seuils, limites, filtres, gates, stratégies de promotion et règles d'écriture ne doivent pas rester dispersés dans la CLI.

Ils doivent être exprimés par des politiques typées, immuables et testables.

Exemples :

```python
@dataclass(frozen=True, slots=True)
class E5SearchPolicy:
    limit: int
    min_score: float | None
```

```python
@dataclass(frozen=True, slots=True)
class E5DiagnosticGatePolicy:
    min_chunks: int
    max_empty_texts: int
    max_missing_source_metadata: int
    max_dimension_mismatches: int
```

```python
@dataclass(frozen=True, slots=True)
class ReportWritePolicy:
    report_file: Path | None
    atomic: bool = True
```

Une politique doit être validée à la construction, puis transmise explicitement.

### 4. Tout résultat doit être immuable, observable et sérialisable

Un use-case doit produire un résultat stable.

Le résultat doit pouvoir être :

- testé directement ;
- transformé en texte ;
- transformé en JSON stable ;
- enregistré comme artefact d'audit ;
- rejoué ou comparé.

Les méthodes attendues sont typiquement :

```text
to_text()
to_json_dict()
```

La sérialisation ne doit pas remplacer le contrat : elle en est seulement une projection.

### 5. Les effets de bord restent en bordure

Les accès fichiers, `stdout`, `stderr`, `sys.exit`, le chargement d'un runtime externe et l'écriture de rapports sont des effets de bord.

Ils doivent rester dans les couches d'adaptation.

Un use-case testable ne doit pas dépendre directement de :

- `sys.argv` ;
- `sys.exit` ;
- `stdout` ou `stderr` ;
- `argparse.Namespace` ;
- chemins temporaires implicites ;
- backend réel chargé sans injection ;
- écriture JSON dupliquée.

Les écritures de rapports doivent être centralisées, atomiques et testées.

### 6. Réduction de surface CLI

Créer une nouvelle CLI est une dette potentielle.

Avant d'ajouter un nouveau script dans `tools/`, il faut justifier pourquoi une sous-commande d'un outil existant ne suffit pas.

La direction préférée est :

```text
un adaptateur CLI fin
-> sous-commandes
-> Command dataclass
-> Policy dataclass
-> use-case
-> Result dataclass
```

Les scripts existants peuvent rester comme wrappers de compatibilité, mais ils ne doivent pas devenir le lieu principal de la logique.

### 7. Application aux phases E5 4.2 à 4.11

Les phases E5 restent valides fonctionnellement, mais leur style doit converger vers le contrat ci-dessus.

Le réalignement attendu est :

```text
4.2 search local
-> intention typée de recherche, politique de limite, résultat stable

4.3 score guard
-> min_score devient une politique explicite

4.4 source hygiene
-> déjà proche du style attendu, conserver comme référence

4.5 source hygiene CLI
-> parsing CLI séparé de la politique de découverte

4.6 diagnostics
-> diagnostic comme use-case pur, CLI comme adaptateur

4.7 diagnostic gate
-> gate comme politique explicite

4.8 rebuild gate
-> rebuild comme orchestration déterministe de politiques nommées

4.9 validation set
-> validation comme use-case séparé, sans logique cachée dans la CLI

4.10 rebuild report file
-> écriture de rapport centralisée et atomique

4.11 search report file
-> même règle de rapport, sans duplication
```

### 8. Revue obligatoire de `code_rule.md` à chaque phase

Chaque phase doit indiquer explicitement si elle modifie ou non les règles de programmation du projet.

Le rapport de phase doit contenir :

```text
code_rule_review: done
code_rule_update_required: true|false
code_rule_reason: ...
```

Si une phase introduit une nouvelle technique de programmation, une nouvelle frontière d'IO, une nouvelle politique, un nouveau backend, une nouvelle forme d'adaptateur ou une nouvelle exception apparente, elle doit proposer un ajout minimal à `doc/code_rule.md`.

La règle est :

```text
on n'adapte pas code_rule.md pour justifier une dérive ;
on adapte le code pour respecter code_rule.md ;
on ne complète code_rule.md que lorsqu'une nouvelle technique mérite d'être explicitée.
```

### 9. Tests de règles

Les règles importantes doivent devenir exécutables dans `tests/rules` dès qu'elles sont stabilisées.

Les tests doivent notamment empêcher :

- l'import direct d'un backend réel dans le noyau ;
- la modification implicite du Scheduler par une phase outillage ;
- l'utilisation de `argparse.Namespace` hors couche CLI ;
- la duplication d'écriture JSON atomique ;
- l'ajout non justifié de nouvelles CLI ;
- l'introduction de Qdrant avant la phase prévue ;
- la versionisation de fichiers générés comme les `.svg` ;
- le changement silencieux du format `missipy.e5.corpus.v1`.


### 10. Bibliothèques hors bibliothèque standard

La bibliothèque standard Python reste le choix par défaut.

Toute phase qui ajoute une bibliothèque externe doit l'annoncer explicitement dans la conversation et dans son rapport de phase.

Cette annonce doit préciser :

- le nom de la bibliothèque ;
- la raison technique ;
- pourquoi la bibliothèque standard ne suffit pas ;
- la frontière exacte où la dépendance est autorisée ;
- les tests qui empêchent cette dépendance de remonter vers le noyau.

Si aucune bibliothèque externe n'est ajoutée, le rapport de phase doit l'indiquer explicitement.

Une dépendance externe ne doit jamais devenir implicite dans le Scheduler, les contrats abstraits ou les structures de politique.
