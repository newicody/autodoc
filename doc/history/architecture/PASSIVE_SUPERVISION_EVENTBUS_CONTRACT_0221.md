# 0221 — Passive supervision EventBus contract

## Decision principale

Le superviseur n'est pas un nouveau runtime. Il est une projection passive de ce qui se passe deja dans le systeme.

Le chemin canonique est :

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState en memoire
  -> snapshot optionnel
  -> audit/replay optionnel
  -> vue VisPy plus tard
```

## Role du Scheduler

Le Scheduler reste l'autorite d'orchestration. Il decide de l'ordre, du declenchement, du passage par les handlers, des gates, des politiques d'execution et des transitions runtime.

Le superviseur ne doit jamais devenir un Scheduler parallele.

```text
Scheduler = upstream authority
Supervisor = downstream observer
```

Donc :

```text
Scheduler emet ou expose des evenements vers l'EventBus.
Le superviseur lit ces evenements.
Le superviseur ne lance pas Scheduler.run().
Le superviseur ne modifie pas les handlers.
Le superviseur ne decide pas a la place du Scheduler.
```

## Role de l'EventBus

L'EventBus est le transport principal des evenements runtime.

Il ne faut pas contourner le bus par defaut avec des fichiers `status.json`, `events.jsonl`, ou des bridges paralleles.

Le bus transporte les evenements issus de :

```text
Scheduler
RouteProxy
ControlProxy
SHM ring/status
Policy gate
GitHub artifact flow
SourceCandidate flow
SQL persistence
Qdrant projection/recall
Rehydration
Pushback status/result
```

## Role du superviseur passif

Le superviseur recoit les evenements du bus et maintient une representation cellulaire en memoire.

Il peut exposer :

```text
snapshot()
write_snapshot(path)
optional audit/replay
```

Mais il ne doit pas piloter le systeme.

Il ne fait pas :

```text
pas de Scheduler.run()
pas de decision policy
pas de controle RouteProxy/ControlProxy
pas de lecture brute obligatoire /dev/shm
pas d'ecriture SQL
pas d'ecriture Qdrant
pas de mutation GitHub
pas de dispatch de taches
pas de worker autonome
```

## Role de CellularState

`CellularState` est la projection vivante de ce qui se passe.

Chaque cellule represente une surface ou un etat observable :

```text
scheduler
route_proxy
control_proxy
shm_ring
policy_gate
github_artifact
source_candidate
sql_store
qdrant_projection
rehydration
pushback
```

Chaque cellule peut porter :

```text
cell_id
cell_kind
state
health
last_event
last_seen_at
route_ref
shm_ref
policy_decision_id
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
error
```

Les cellules peuvent etre regroupees selon leur localisation runtime. Elles peuvent aussi se deplacer logiquement lorsqu'une donnee, une responsabilite ou une reference liee est transmise vers une autre surface.

## Role du snapshot

Le snapshot n'est pas le flux principal.

C'est une sortie lisible pour :

```text
debug
inspection humaine
test
VisPy plus tard
rapport d'etat
```

Donc :

```text
EventBus -> Supervisor -> CellularState
```

est principal.

Et :

```text
CellularState -> snapshot.json
```

est optionnel.

## Role de events.jsonl

`events.jsonl` ne doit pas devenir la colonne vertebrale du runtime.

Il sert uniquement a :

```text
audit
replay
preuve de run
debug
tests hors bus reel
```

Donc :

```text
EventBus -> events.jsonl -> superviseur
```

ne doit pas etre le chemin normal.

Le chemin normal est :

```text
EventBus -> superviseur
```

Puis eventuellement :

```text
superviseur -> events.jsonl
```

si audit active.

## Role des proxy et SHM

RouteProxy, ControlProxy et SHM restent des surfaces runtime rapides.

Ils peuvent emettre ou exposer des evenements au bus.

Le superviseur peut observer :

```text
route active
route draining
lease state
proxy health
ring state
blocked area
priority update
emitter lag
context changed
```

Mais il ne doit pas :

```text
bloquer une zone
modifier une route
prendre un lease
ecrire dans SHM
reordonner les taches
prioriser directement
```

Ces decisions restent dans les couches prevues : Scheduler, policy, proxy/control plane.

## Role de Policy

Policy reste une autorite de decision.

Le superviseur observe :

```text
policy_decision_id
allowed
blocked
deferred
reason
gate
```

Mais il ne decide pas.

Il peut rendre visible :

```text
la decision
son effet
la cellule bloquee
le composant concerne
```

## Role futur de VisPy

VisPy n'est pas dans le chemin critique.

VisPy sera une vue humaine.

Elle doit lire :

```text
snapshot()
ou snapshot.json
```

Elle ne possede pas l'etat, ne decide pas, et ne controle rien.

## Correction de trajectoire

Les patchs orientes bridge/fichiers ne doivent pas etre consideres comme la bonne direction.

La bonne direction est :

```text
0221 = extension du superviseur passif existant
       avec PassiveSupervisorSink direct sur EventBus

0222 = Scheduler explicitement upstream emitter via EventBus,
       sans modifier Scheduler.run()

0223 = RouteProxy / ControlProxy / SHM / Policy comme upstream event sources,
       sans controle ni mutation

0224 = seulement ensuite GitHub / SourceCandidate / SQL / Qdrant / Rehydrate / Pushback
       comme surfaces observees
```

Mais avant `0224`, il faut verrouiller par ecrit :

```text
le contrat d'evenement bus canonique
les champs minimaux
les refs transversales
les responsabilites exactes
les limites d'autorite
```

## Contrat minimal d'evenement bus

Un evenement bus supervisable devrait avoir au minimum :

```text
event_id
event_kind
emitted_at ou observed_at
source
surface
cell_id
cell_kind
state
health optionnel
refs optionnelles
payload optionnel
```

Refs communes :

```text
route_ref
shm_ref
policy_decision_id
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
handoff_ref
pushback_ref
```

## Principe final

Le superviseur ne doit pas rendre le systeme plus complexe.

Il doit rendre visible ce qui existe deja.

S'il faut ajouter beaucoup d'adaptation, c'est probablement que le contrat d'evenement bus n'est pas assez clair.

La priorite est donc :

```text
clarifier le contrat EventBus
reutiliser l'existant
brancher le superviseur en aval
garder audit/replay/snapshot optionnels
ne pas creer de runtime parallele
```
