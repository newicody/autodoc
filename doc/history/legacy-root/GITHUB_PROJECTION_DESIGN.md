# Phase 5.16 — GitHub projection design pour `newicody/autodoc`

## Objectif

Cette phase formalise la projection future entre le stockage local `SourceCandidate` et la surface GitHub `newicody/autodoc`.

GitHub n'est pas l'autorité de connaissance.
GitHub est une surface de pilotage, de validation et de synchronisation.

L'autorité locale reste :

```text
SourceCandidateStore
-> SourceCandidate
-> SourceCandidateDecision
-> rapports locaux
-> ContextEngine / boucle locale
```

La projection GitHub future ne fera que publier une vue contrôlée de cet état local.

## Position dans la chaîne Phase 5

```text
Phase 4 artifact-dir
-> Local context loop CLI
-> SourceCandidate contract
-> SourceCandidate local store/report
-> GitHub projection design
```

Cette phase ne branche pas GitHub. Elle définit seulement ce qui sera projetable plus tard.

## Repository cible

```text
newicody/autodoc
```

Cette valeur est une cible documentaire de projection. Elle ne déclenche aucun appel réseau.

## Flux entrant futur

Un élément GitHub futur pourra devenir une entrée locale :

```text
GitHub issue / project card / push event / action artifact
-> GitHub work item futur
-> SourceCandidateInput
-> SourceCandidate
-> SourceCandidateStore
```

Le traitement local décidera ensuite si cette entrée devient :

```text
analyzed
rejected
archived
promoted
merged
```

## Flux sortant futur

Une `SourceCandidate` locale pourra être projetée vers GitHub sous forme de payload documentaire :

```text
SourceCandidate
+ SourceCandidateDecision
+ SourceCandidateStoreReport
-> GitHubProjectionPayload futur
-> commentaire / statut / label / lien de rapport futur
```

La projection ne doit jamais contenir de secrets, token, chemin privé sensible ou dump non filtré.

## Règles de projection

- Le local reste autoritaire.
- GitHub ne décide pas seul de l'état interne.
- Un statut GitHub n'est qu'une projection contrôlée.
- Une action GitHub future doit revenir sous forme de `SourceCandidateInput` ou de décision opérateur explicite.
- Aucun worker réseau ne doit apparaître sans phase dédiée.
- Aucun token ne doit être stocké dans un contrat métier.
- Les erreurs de publication futures devront rester des résultats sérialisables, pas des exceptions opaques dans le cœur.

## Mapping documentaire futur

| SourceCandidate | Projection GitHub future |
| --- | --- |
| `new` | issue/card reçue, non analysée localement |
| `analyzed` | commentaire de synthèse ou label `analyzed` |
| `rejected` | commentaire de rejet contrôlé |
| `archived` | label `archived` ou fermeture future |
| `promoted` | lien vers contexte local promu / PR future |
| `merged` | lien vers contexte existant fusionné |

Ce mapping est indicatif. Il ne crée pas encore de code GitHub.

## Frontières 5.16

Cette phase n'ajoute pas :

```text
API GitHub
token
réseau
polling
GitHub Action exécutable
serveur
daemon
base de données
Qdrant
LLM
appel OpenVINO
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.16 formalise une projection GitHub future documentaire sans nouvelle règle de programmation.
```
