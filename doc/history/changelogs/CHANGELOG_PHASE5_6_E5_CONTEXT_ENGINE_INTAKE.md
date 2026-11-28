# Changelog — Phase 5.6 — ContextEngine E5 intake facade

## Ajouts

- Ajout d'une entrée E5 explicite dans `ContextEngine` :
  - `E5ContextEngineIntakePolicy` ;
  - `E5ContextEngineIntakeResult` ;
  - `ContextEngine.attach_e5_artifact_dir()` ;
  - `ContextEngine.attach_e5_runtime_context()`.
- Export des nouveaux contrats depuis `context.__init__`.
- Ajout du graphe `context/30_e5_context_engine_intake.dot`.
- Mise à jour du graphe global pour montrer le passage :

```text
E5ContextAttachment
-> ContextEngine E5 intake
-> ContextEngine
```

## Frontières conservées

```text
pas d'autoload
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
code_rule_reason: 5.6 ajoute une entrée explicite du runtime E5 dans ContextEngine ; aucune règle de programmation nouvelle n'est nécessaire.
```
