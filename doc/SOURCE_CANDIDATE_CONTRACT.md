# SourceCandidate local contract — Phase 5.14

Phase 5.14 introduit le contrat local `SourceCandidate`.

L'objectif est de représenter une matière brute susceptible de devenir contexte,
sans encore la stocker, la publier, la fusionner ou la projeter vers GitHub.

## Chaîne conceptuelle

```text
entrée locale / artifact-dir / note / futur item GitHub
-> SourceCandidateInput
-> SourceCandidate
-> SourceCandidateDecision optionnelle
-> nouvelle SourceCandidate immuable avec statut dérivé
```

## Statuts

```text
new
analyzed
rejected
archived
promoted
merged
```

Les statuts terminaux sont :

```text
rejected
archived
promoted
merged
```

## Décisions opérateur

```text
inspect   -> analyzed
relaunch  -> analyzed
reject    -> rejected
archive   -> archived
promote   -> promoted
merge     -> merged
```

En Phase 5.14, ces décisions ne produisent aucun effet externe. Elles retournent
une nouvelle candidate immuable.

## Origines

Origines acceptées :

```text
local
file
artifact_dir
github
manual
```

Le champ `repository` prépare la future projection GitHub. La politique par
défaut utilise :

```text
newicody/autodoc
```

Cette valeur ne déclenche aucune API GitHub. Elle est seulement sérialisée dans
le contrat local.

## Frontières

Phase 5.14 ne fait pas :

```text
pas de stockage persistant
pas d'écriture de rapport
pas de lecture artifact-dir
pas de GitHub API
pas de token
pas de réseau
pas de Scheduler vivant
pas de daemon
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Contrats ajoutés

```text
SourceCandidateOrigin
SourceCandidateInput
SourceCandidatePolicy
SourceCandidateDecision
SourceCandidate
SourceCandidateCreationResult
build_source_candidate()
apply_source_candidate_decision()
allowed_source_candidate_statuses()
allowed_source_candidate_decisions()
```

## Relation avec la boucle locale

La Phase 5.13 expose déjà `next_action` dans le rapport de boucle locale, mais
cette action reste purement reportée. Phase 5.14 donne maintenant le vocabulaire
métier qui permettra ensuite de transformer ce `next_action` en décision locale
sur une `SourceCandidate`.

La prochaine étape logique est le stockage/rapport local SourceCandidate, mais
pas encore GitHub ni serveur.
