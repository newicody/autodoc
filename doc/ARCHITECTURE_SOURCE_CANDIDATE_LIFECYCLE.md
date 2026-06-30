# Architecture — Source Candidate Lifecycle et GitHub Project Orchestrator

## Statut

Ce document ajoute une brique future à l’architecture MissiPy/autodoc. Il ne branche pas encore l’API GitHub, Copilot, le Scheduler, Qdrant ou un LLM. Il fixe seulement la place du mécanisme dans les couches futures pour éviter qu’il soit oublié lors de la clôture de la Phase 4.

Aucune bibliothèque hors stdlib Python n’est introduite par cette phase documentaire.

## Intuition

Le flux GitHub ne doit pas être vu comme une simple entrée de ticket. Une chose poussée, un ticket, une issue, un artefact ou une note de projet peut devenir une **source candidate**.

Une source candidate peut ensuite être rejetée, archivée, enrichie, promue en contexte autonome ou fusionnée dans un contexte existant.

Le cycle n’est donc pas :

```text
GitHub -> serveur -> résultat
```

mais plutôt :

```text
push / issue / ticket / artefact
-> graine de source
-> enrichissement serveur
-> validation utilisateur
-> devient contexte autonome
   ou fusionne dans un contexte existant
-> retour GitHub
-> nouvelle itération
```

## Rôle exact de GitHub

GitHub n’est pas la base de connaissance autoritative.

GitHub devient :

```text
interface de pilotage
surface de validation
journal de discussion
kanban projet
déclencheur d’actions
miroir publiable
```

La machine serveur reste :

```text
source autoritative
base enrichie
index local
historique de contexte
moteur d’inférence
mémoire technique structurée
```

Donc l’architecture devient :

```text
GitHub Project
  -> propose / déclenche / valide

Serveur local
  -> comprend / enrichit / relie / versionne / indexe

Git repo
  -> reçoit les changements stabilisés

Artefacts
  -> transportent les états intermédiaires
```

## Place dans les couches

La brique future est placée au-dessus du moteur local E5 et à côté du futur Scheduler :

```text
GitHub Project / Issue / Action
        |
        v
Work Artifact Intake
        |
        v
Source Candidate
        |
        v
Enrichment Pipeline
        |
        v
Context Decision
   /          \
new context   merge into existing context
   \          /
        v
Local authoritative source
        |
        v
GitHub feedback / git commit / PR / status
```

Elle ne doit pas polluer les couches suivantes :

```text
src/inference
src/context
src/contracts
Scheduler
E5 corpus
```

La place de code future sera une couche d’intégration explicite, par exemple :

```text
src/integrations/github_project/
```

ou, si l’on veut une frontière encore plus claire au départ :

```text
src/github_intake/
```

## Cycle complet

```text
[1] L’utilisateur pousse une idée, un ticket, un fichier, une demande

[2] GitHub Action crée un artefact de travail
    - metadata utilisateur
    - metadata Copilot ou assistant GitHub-side optionnel
    - repo concerné
    - branche
    - issue
    - statut projet
    - intention supposée
    - fichiers liés

[3] Le serveur local récupère l’artefact à intervalle régulier

[4] Le serveur le classe
    - nouveau contexte ?
    - extension d’un contexte existant ?
    - anomalie ?
    - dette technique ?
    - demande utilisateur ?
    - hypothèse de recherche ?

[5] Le serveur enrichit
    - recherche E5 locale
    - contexte projet
    - historique
    - règles code_rule
    - fichiers liés
    - graphes architecture
    - tests possibles
    - contradictions
    - dépendances

[6] Le serveur produit un résultat
    - rapport
    - proposition
    - patch futur
    - contexte enrichi
    - décision attendue
    - statut recommandé

[7] Retour vers GitHub
    - commentaire issue
    - artefact enrichi
    - changement de colonne kanban
    - label
    - PR éventuelle
    - demande validation utilisateur

[8] L’utilisateur valide ou relance
```

## États d’une source candidate

Une source candidate ne doit pas devenir automatiquement une vérité stable. Elle traverse des états explicites :

```text
raw
triaged
enriched
candidate_context
validated_context
merged_context
rejected
archived
```

La promotion vers un contexte stable exige une règle claire :

```text
validation utilisateur
ou test réussi
ou règle projet
ou PR mergée
ou statut GitHub passé à Validated
```

## Contrat d’artefact futur

Un artefact ne doit pas seulement dire “voici une tâche”. Il doit porter l’origine, l’intention, les métadonnées de triage, la source brute et la politique de contexte.

Exemple de forme future :

```json
{
  "schema": "missipy.source_candidate.v1",
  "origin": {
    "platform": "github",
    "repo": "newicody/autodoc",
    "issue": 123,
    "project_status": "triage"
  },
  "user_intent": "...",
  "assistant_metadata": {
    "triage": "...",
    "suspected_context": "...",
    "risk": "...",
    "suggested_next_action": "enrich"
  },
  "candidate_source": {
    "kind": "idea|bug|doc|code|research|architecture",
    "raw_content": "...",
    "linked_files": [],
    "linked_commits": []
  },
  "context_policy": {
    "can_create_new_context": true,
    "can_merge_existing_context": true,
    "requires_user_validation": true,
    "allow_cross_repo_context": false
  }
}
```

## Aller-retour GitHub ↔ serveur

Le projet évolue par boucles contrôlées :

```text
GitHub Project / Copilot / utilisateur
        |
        v
artefact de travail
        |
        v
serveur local autoritatif
        |
        v
enrichissement / contexte / décision
        |
        v
projection GitHub : statut, commentaire, artefact, PR
        |
        v
validation ou relance utilisateur
```

La source est donc sur la machine serveur, et GitHub sert de surface de pilotage et de synchronisation. Un push peut devenir une source ; une source peut devenir un contexte ; un contexte peut revenir sur GitHub sous forme d’état, de rapport, de PR ou de demande de validation.

## Placement dans la roadmap

```text
Phase 4 = moteur local E5 et contexte
Phase 5 = serveur local / Scheduler / contexte runtime
Phase 6 = GitHub Project Orchestrator
Phase 7 = boucle aller-retour GitHub <-> serveur <-> git
```

La Phase 4.18-r1 inscrit seulement l’idée dans l’architecture. Elle ne code pas encore l’intégration GitHub.

## Formulation d’architecture à conserver

```text
GitHub n’est pas la base de connaissance autoritative.
GitHub est une interface de pilotage, de validation et de synchronisation.

La source autoritative enrichie vit sur le serveur local.
Une entrée GitHub peut devenir une SourceCandidate.
Une SourceCandidate peut être rejetée, archivée, enrichie, promue en contexte autonome ou fusionnée dans un contexte existant.
Les retours vers GitHub ne sont que des projections contrôlées de l’état local.
```

En résumé : **GitHub pilote, le serveur comprend, le dépôt matérialise, l’utilisateur valide.**
