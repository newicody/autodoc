# Phase 4.20 — Clôture Phase 4

## Statut

La Phase 4 est clôturée.

Elle livre un moteur local E5 utilisable en dry-run, avec sorties déterministes, sans brancher encore de service distant ou de boucle d'orchestration.

```text
corpus local
-> build / rebuild sûr
-> diagnostics / gates / validation
-> search local
-> E5SearchReport
-> E5ContextBundle
-> E5ConsumedContext
-> E5AnswerPromptPacket
-> artifact directory
```

## Capacités livrées

### Corpus local

La Phase 4 conserve le format :

```text
missipy.e5.corpus.v1
```

Elle fournit les opérations nécessaires à un corpus local testable :

```text
build
rebuild
safe promotion
source hygiene
report file
```

### Diagnostic et gate

Le corpus peut être inspecté et refusé avant promotion :

```text
min chunks
max missing source
max empty text
max wrong dimension
fail on warning
validation queries
validation min score
```

### Recherche locale

La recherche produit des hits contextualisés :

```text
score
source_path
line_range
chunk_index
excerpt
```

La sortie peut être lue par l'humain ou par le pipeline :

```text
stdout texte/json
report.json
```

### Contexte et prompt

La chaîne complète de contexte est disponible :

```text
E5SearchReport
-> E5ContextBundle
-> E5ConsumedContext
-> E5AnswerPromptPacket
```

Elle prépare une future réponse, mais ne répond pas elle-même.

### Dry-run artifact directory

Le mode pratique de fin de Phase 4 est :

```bash
PYTHONPATH=src ./tools/e5.py search \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --artifact-dir /tmp/autodoc_e5_dry_run \
  --context-max-chars 4000 \
  "OpenVINO local"
```

Il produit :

```text
report.json
context.json
consumed_context.json
prompt.json
```

## Frontières non franchies

La clôture confirme les limites volontaires :

```text
pas de Scheduler
pas de Qdrant
pas de LLM de réponse
pas d'API GitHub
pas de token
pas de polling réseau
pas de dépendance Copilot
```

Ces frontières évitent de mélanger le moteur local E5 avec l'orchestration future.

## SourceCandidate et GitHub Project Orchestrator

La couche GitHub Project / SourceCandidate est intégrée à l'architecture générale, mais elle reste future.

Son principe est maintenant documenté :

```text
GitHub Project / Issue / Push / Ticket
-> GitHub Action
-> metadata optionnelles
-> SourceCandidate
-> source autoritative serveur local
-> enrichissement local
-> validation / fusion contexte
-> projection GitHub
-> boucle de retour
```

Le point central est le suivant :

```text
GitHub n'est pas la base de connaissance autoritative.
GitHub est une interface de pilotage, de validation et de synchronisation.

La source autoritative enrichie vit sur le serveur local.
Une entrée GitHub peut devenir une SourceCandidate.
Une SourceCandidate peut être rejetée, archivée, enrichie, promue en contexte autonome ou fusionnée dans un contexte existant.
Les retours vers GitHub ne sont que des projections contrôlées de l'état local.
```

## Porte d'entrée Phase 5

La Phase 5 peut partir dans l'un de ces axes sans casser la Phase 4 :

```text
serveur local autour des artefacts E5
Context Engine / runtime local
handoff contrôlé vers InferenceContext
préparation de Qdrant plus tard
préparation GitHub Project Orchestrator encore plus tard
backend de réponse explicite seulement quand le prompt packet est stable
```

L'axe recommandé est :

```text
Phase 5.1 — Local server artifact intake
```

Objectif : lire un dossier d'artefacts Phase 4, l'enregistrer dans un état local contrôlé, et préparer son exposition au Context Engine sans déclencher encore de Scheduler lourd.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.20 clôture la Phase 4 par documentation et bilan ; aucune règle de programmation nouvelle n'est nécessaire.
```
