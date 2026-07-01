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

Addendum Phase 6-r1 — Squelette porteur, chemin vivant et intégration progressive du spécialiste

Cet addendum ne remplace pas les règles précédentes. Il ajoute une discipline d'intégration qui gouverne les phases à venir.

Il applique deux patrons connus du génie logiciel :

    le squelette porteur (walking skeleton, Cockburn) ;

    les balles traçantes (tracer bullets, Hunt & Thomas).

Une implémentation minuscule mais réelle, traversant progressivement l'architecture de bout en bout, doit rester vivante pendant qu'on l'étoffe.

Objectif : empêcher deux dérives symétriques :

    le spécialiste accumule des surfaces typées mais reste fictif ;

    le noyau devient vestigial parce qu'un produit se construit à côté du Scheduler.

La règle générale est :

le churn vit dans la feuille ;
la stabilité vit à la frontière de contrats.

Le spécialiste peut évoluer vite, mais il ne doit jamais contaminer le noyau.
1. Le spécialiste doit converger vers le chemin noyau

Toute capacité destinée à devenir un comportement du système doit converger vers le chemin noyau :

Command dataclass
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> Event observable

Une CLI de développement reste autorisée comme adaptateur opérateur, mais elle ne doit pas devenir le chemin réel principal d'une capacité durable.

La CLI peut encore exister pour :

    parser les arguments ;

    produire une commande typée ;

    afficher un résultat ;

    écrire un rapport ;

    faciliter le diagnostic manuel.

Mais une capacité destinée au système doit disposer d'un chemin Scheduler vivant au plus tard à la phase d'intégration correspondante.

Formulation pratique :

contrat pur -> use-case local court -> chemin Scheduler vivant -> CLI fine autour

Un use-case local non câblé est accepté comme transition courte. Il ne doit pas devenir une architecture parallèle.
2. Le chemin noyau est le chemin réel cible

Le chemin réel cible d'une capacité durable est :

Command dataclass
-> Scheduler
-> PolicyEngine
-> Queue
-> Dispatcher
-> Handler
-> backend réel déclaré
-> résultat observable

Aucun code destiné à devenir composant durable ne doit appeler directement :

    E5 ;

    une base de données ;

    Qdrant ;

    un backend LLM ;

    GitHub ;

    OpenVINO ;

    un store persistant ;

sans passer par une commande typée et une frontière d'adaptation déclarée.

Les appels directs restent autorisés uniquement dans :

    les adaptateurs explicitement nommés ;

    les tests ciblés de bas niveau ;

    les CLI transitoires pendant une phase d'intégration ;

    les scripts de diagnostic clairement séparés du noyau.

3. Définition d'un backend réel

Un backend réel est un backend non-dummy déclaré comme backend de validation pour l'environnement courant.

Exemples :

machine développeur avec modèle local :
OpenVINO E5 local peut être backend réel

CI légère :
un backend local déterministe non-dummy peut servir de chemin vivant minimal

tests unitaires isolés :
un backend dummy reste autorisé, mais ne prouve pas le chemin vivant

Le dummy est un outil de test et un mode dégradé. Il ne doit pas être présenté comme preuve que le chemin système fonctionne réellement.

La validation complète distingue donc :

test unitaire avec dummy        -> autorisé
test d'intégration chemin vivant -> backend réel déclaré requis
validation matérielle locale     -> backend OpenVINO ou équivalent réel

4. Invariant de chemin vivant

À partir de la phase où une capacité est déclarée intégrée, il doit exister au moins un test de chemin vivant qui traverse :

commande typée
-> Scheduler
-> Handler
-> backend réel déclaré
-> résultat observable

Ce test doit rester vert.

Pendant la phase de transition, le rapport de phase peut indiquer :

live_path_status: transition

Mais une phase ne doit pas se déclarer close en tant que capacité intégrée si son chemin vivant reste absent.

Les états autorisés sont :

live_path_status: green|red|transition|n/a

    green : chemin vivant testé et valide ;

    red : chemin vivant attendu mais cassé ;

    transition : capacité encore en cours de câblage ;

    n/a : phase documentaire, audit, contrat pur ou correction sans capacité exécutable.

5. Le spécialiste peut être impur derrière sa membrane

Le spécialiste peut utiliser des bibliothèques externes ou du code impur si cela est justifié :

    numpy ;

    OpenVINO ;

    Qdrant ;

    LibCST ;

    client GitHub ;

    backend LLM ;

    autre dépendance explicitement validée.

Mais cette impureté reste confinée derrière une frontière de module en liste blanche.

Le noyau, les contrats abstraits et les politiques générales restent stdlib-first.

Le Scheduler ne doit jamais dépendre implicitement d'un backend réel.

Le noyau ne voit que :

Command
Policy
Event
Result
Context

Il ne voit jamais directement :

OpenVINO
Qdrant
PostgreSQL
GitHub API
LLM runtime

6. Reformulation de contexte : fréquente autorisée, silencieuse interdite

Les reformulations fréquentes du contexte du spécialiste sont autorisées.

Toute reformulation qui change le contrat public doit être versionnée.

Exemple :

missipy.context.v1
missipy.context.v2

Le changement de version est requis si :

    un champ public disparaît ;

    un champ change de type ;

    une signification change ;

    un nouveau consommateur durable dépend d'une structure différente.

Le changement de version doit être testé.

Règle :

fréquent est permis ;
silencieux est interdit.

Le contexte du spécialiste peut commencer minimal et s'enrichir sous l'usage. On ne cherche pas à deviner trop tôt un contrat complet.
7. Les CLI restent des adaptateurs, pas des chemins parallèles

Les CLI existantes restent valides comme outils opérateur et diagnostic.

Cependant, quand une capacité devient durable, la CLI doit progressivement devenir :

argparse
-> Command dataclass
-> chemin Scheduler ou use-case explicitement transitoire
-> Result dataclass
-> rendu text/json/report

Une CLI ne doit pas :

    contenir la logique métier principale ;

    choisir implicitement un backend réel ;

    contourner les politiques ;

    devenir le seul chemin de validation durable ;

    faire évoluer un store ou un contexte sans contrat typé.

8. Effet sur la roadmap

Aucune phase fonctionnelle n'est annulée.

Mais les phases à venir doivent éviter d'ajouter seulement des surfaces typées sans comportement réel.

Formulation attendue :

mauvais :
ajouter un contrat de recherche, sans chemin réel

bon :
ajouter une commande de recherche bornée,
un handler,
un backend réel déclaré,
un événement observable,
un rapport testable

Une phase documentaire peut rester documentaire. Mais une phase qui prétend ajouter une capacité doit fournir un chemin d'exécution correspondant ou déclarer explicitement son état de transition.
9. Tests de règles ajoutés

La section tests/rules et les tests d'intégration doivent progressivement empêcher :

    l'absence de chemin vivant pour une capacité déclarée intégrée ;

    l'usage d'un backend dummy comme validation par défaut d'une capacité intégrée ;

    l'appel direct d'un backend réel depuis un module destiné à devenir composant ;

    le changement silencieux du contrat de contexte ;

    l'import direct d'une dépendance spécialiste dans le noyau ;

    la régression d'un chemin Scheduler vers un chemin CLI direct.

Ces tests peuvent être introduits progressivement.

Ils ne doivent pas invalider rétroactivement tout le code existant sans phase de migration.
10. Revue de phase — champs ajoutés

Le bloc obligatoire de revue de phase devient :

code_rule_review: done
code_rule_update_required: true|false
code_rule_reason: ...
live_path_status: green|red|transition|n/a
live_path_uses_real_backend: true|false|n/a
context_contract_version: missipy.context.vN|n/a
context_contract_changed: true|false
search_commands_bounded: true|false|n/a

Règles :

    live_path_status: n/a est autorisé pour une phase documentaire, un audit ou une correction sans nouvelle capacité ;

    live_path_status: transition est autorisé pour une capacité en cours de câblage ;

    live_path_status: green est requis pour clore une capacité déclarée intégrée ;

    live_path_uses_real_backend: false est autorisé pour les tests unitaires, mais pas comme preuve de validation complète ;

    context_contract_changed: true impose d'indiquer la nouvelle version du contrat ;

    search_commands_bounded: true est requis pour toute commande de recherche ou d'exploration.

11. Règle de clôture

on n'ajoute pas seulement une surface typée ;
on ajoute une capacité portée par le noyau ou on déclare explicitement la transition.

le squelette marche,
il reste petit,
il grandit sans cesser d'être testable.

Addendum Phase 6-r2 — Borne de ressources obligatoire pour la recherche

Cet addendum ajoute un invariant de frontière. Il ne décrit aucune heuristique de recherche.
1. Toute recherche porte un budget borné

Toute commande qui explore un espace de solutions doit porter un budget de ressources borné.

Cela concerne notamment :

    MCTS ;

    best-of-n ;

    recherche hybride ;

    exploration de plans ;

    reranking itératif ;

    génération multi-candidats ;

    toute boucle de recherche susceptible de croître.

Une recherche sans borne est interdite.

Le budget est un contrat typé, validé à la construction :

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SearchBudget:
    max_evaluations: int
    max_wall_time_s: float

    def __post_init__(self) -> None:
        if self.max_evaluations <= 0:
            raise ValueError("max_evaluations must be > 0")
        if self.max_wall_time_s <= 0:
            raise ValueError("max_wall_time_s must be > 0")

La recherche s'arrête dès qu'une borne est atteinte.
2. Pourquoi c'est une règle de frontière

Cette règle ne choisit pas la qualité de la recherche.

Elle garantit seulement que le spécialiste ne peut pas monopoliser les ressources et bloquer le système.

Elle ne définit pas :

    le barème de récompense ;

    le facteur de branchement ;

    le nombre de candidats ;

    la stratégie d'expansion ;

    le progressive widening ;

    la coupure précoce ;

    le choix entre recherche complète et best-of-n.

Ces décisions appartiennent au spécialiste.

Un mauvais réglage peut produire un spécialiste médiocre, mais proprement isolé. Il ne doit pas corrompre le noyau.
3. Application aux commandes

Toute commande de recherche doit porter explicitement :

SearchBudget

ou un contrat équivalent nommé et testé.

Exemples :

E5SearchCommand              -> limit/min_score suffisants pour recherche simple non exploratoire
MCTSSearchCommand            -> SearchBudget obligatoire
BestOfNCommand               -> SearchBudget obligatoire
PlanExplorationCommand       -> SearchBudget obligatoire
LLMMultiCandidateCommand     -> SearchBudget obligatoire
HybridRetrievalCommand       -> SearchBudget obligatoire si itératif

Une recherche simple bornée par limit peut être considérée comme bornée si :

    limit est validé ;

    aucune boucle exploratoire non bornée n'existe ;

    le rapport de phase indique search_commands_bounded: true.

4. Test de règle

tests/rules doit progressivement empêcher :

    l'acceptation d'une commande de recherche itérative sans budget ;

    l'acceptation d'un budget nul ou négatif ;

    l'ajout d'une boucle exploratoire sans borne explicite.

5. Revue de phase

Le champ suivant est obligatoire :

search_commands_bounded: true|false|n/a
true : une commande de recherche existe et elle est bornée ;
false : une commande de recherche existe mais n'est pas bornée ;
n/a : la phase n'ajoute aucune commande de recherche.

## Addendum Phase 6-r3 — Patch Queue, hygiène Git et documentation générée

Cet addendum formalise le nouveau mode de développement du dépôt. Les changements proposés par IA, outil externe ou session longue ne doivent plus être livrés comme scripts Python modifiant directement le dépôt. Le format normal est un patch Git standard, rangé dans un répertoire versionné.

### 1. Un patch = un répertoire versionné

Chaque patch doit être déposé sous la forme :

```text
patch/
  <patch-id>/
    patch.diff
    README.md
    metadata.json
```

Les patchs plats directement posés dans `patch/*.patch` ou `patch/*.diff` sont interdits. Le répertoire de patch est l’unité de revue, d’application, de test et de commit.

`README.md` décrit l’intention du patch, son scope et ses limites. `metadata.json` peut préciser le sujet de commit, les commandes de test attendues et les notes d’intégration. `patch.diff` reste le patch Git standard applicable par `git apply`.

### 2. `apply_patch_queue.py` est un outil de développement

`apply_patch_queue.py` est l’outil local autorisé pour appliquer les patchs versionnés. Il reste un outil de développement, pas une capacité métier du micro-kernel.

Son rôle est limité à :

```text
découvrir patch/<patch-id>/
-> vérifier patch.diff
-> nettoyer les artefacts générés
-> appliquer le patch Git
-> relancer les tests
-> proposer ou créer le commit
-> pousser optionnellement via Git SSH
```

Il ne doit pas contenir de logique métier Autodoc/MissiPy. Il ne remplace pas le Scheduler, le Dispatcher, le PolicyEngine ou les handlers métier.

### 3. SSH sans `ssh-agent`

L’outil peut effectuer des opérations Git réseau optionnelles sans dépendre de `ssh-agent`.

Les chemins vers clé privée, certificat SSH utilisateur et `known_hosts` doivent venir uniquement de :

```text
arguments CLI
variables d’environnement
.patchqueue.local.json
```

`.patchqueue.local.json` doit rester ignoré par Git.

Aucune clé privée, aucun certificat SSH utilisateur, aucun secret et aucun token ne doivent être versionnés.

L’outil peut construire temporairement `GIT_SSH_COMMAND` avec une configuration explicite :

```text
IdentityAgent=none
IdentitiesOnly=yes
IdentityFile=<clé privée hors dépôt>
CertificateFile=<certificat hors dépôt>
UserKnownHostsFile=<known_hosts hors dépôt>
StrictHostKeyChecking=yes|accept-new|no
```

Ce mécanisme est une frontière d’IO Git. Il ne doit pas devenir une dépendance implicite du noyau ni d’un composant métier.

### 4. README racine figé

Le README racine doit rester général, stable et orienté projet. Il ne doit plus être remplacé par un README de phase.

Les README de version, de phase ou de migration doivent vivre dans :

```text
doc/releases/
```

La documentation courante détaillée peut vivre dans :

```text
doc/README_CURRENT.md
```

Tout patch qui modifie le README racine doit justifier pourquoi une documentation de phase ne suffit pas.

### 5. DOT versionnés, SVG générés

Les sources d’architecture sont les fichiers `.dot`.

Les `.svg` sont des artefacts générés localement. Ils ne doivent pas être versionnés.

La règle locale est :

```bash
make -C doc
make -C doc clean
```

avant revue ou push lorsque les graphes sont générés.

Les `.svg`, `.pyo`, caches Python et sorties de build doivent rester absents de l’index Git.

### 6. Documentation obligatoire par phase

Chaque patch de phase doit maintenir à jour, selon le scope :

```text
MANIFEST_CHANGED_FILES.md
doc/CHANGELOG_*.md
PHASE*_TEST_REPORT.md
doc/*CODE_RULE_ALIGNMENT*.md ou bloc code_rule équivalent
DOT d’architecture si un flux change
README de phase dans doc/releases/ si nécessaire
```

Le rapport de phase doit toujours contenir un bloc :

```text
code_rule_review: done
code_rule_update_required: true|false
code_rule_reason: ...
live_path_status: green|red|transition|n/a
live_path_uses_real_backend: true|false|n/a
external_dependencies_added: true|false
scheduler_modified: true|false
network_added: true|false
github_api_added: true|false
qdrant_added: true|false
llm_or_openvino_added: true|false
search_commands_bounded: true|false|n/a
```

### 7. Tests de règles

Les règles stabilisées doivent être rendues exécutables dans `tests/rules`.

Les tests doivent notamment empêcher :

```text
- l’ajout de patchs plats sous patch/*.patch ou patch/*.diff ;
- la versionisation de .svg ou .pyo ;
- la versionisation de .patchqueue.local.json ;
- le remplacement du README racine par un README de phase ;
- l’ajout de logique métier dans apply_patch_queue.py ;
- l’utilisation de Git réseau sans configuration SSH explicite et hors dépôt ;
- l’oubli de manifest, changelog ou rapport de test pour une phase structurante.
```
