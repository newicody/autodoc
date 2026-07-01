# Changelog — Phase 5.7 — E5 ContextEngine status projection

## Objectif

Rendre le raccord E5 visible et auditable depuis le `ContextEngine` sans introduire d'automatisme.

La Phase 5.7 ajoute une projection passive :

```text
ContextEngine.current_inference_context
+ last_snapshot optionnel
-> E5ContextEngineStatus
-> JSON stable / texte lisible
```

## Ajouts

- `E5ContextEngineStatusPolicy` : sélection du composant inspecté, par défaut `e5_local_context`.
- `E5ContextEngineStatus` : projection sérialisable de l'état E5 attaché.
- `inspect_e5_context_engine()` : inspecte un `ContextEngine` sans mutation.
- `inspect_e5_inference_context()` : inspecte directement un `InferenceContext`.

## Frontières maintenues

```text
pas de lecture de fichiers
pas de mutation du contexte
pas d'autoload E5
pas de Scheduler vivant
pas de daemon
pas de réseau
pas d'API GitHub
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.7 ajoute une projection passive et typée de l'état E5 ; aucune règle de programmation nouvelle n'est nécessaire.
```
