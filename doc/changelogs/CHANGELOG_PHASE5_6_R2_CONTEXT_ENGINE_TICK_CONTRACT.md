# Changelog — Phase 5.6-r2 — ContextEngine tick contract

## Objectif

Corriger la deuxième régression observée après 5.6-r1 : `execute_tick()` ne doit pas retourner directement le `InferenceContext` construit.

Le contrat historique du micro-kernel attend que le tick retourne le snapshot collecté/réduit, afin que les appelants existants puissent lire :

```python
snapshot.components
```

Le `InferenceContext` reste bien construit et mémorisé dans :

```python
ContextEngine.last_inference_context
ContextEngine.current_inference_context
```

## Changement

- `ContextEngine.execute_tick()` retourne de nouveau le snapshot historique.
- `last_inference_context` reste mis à jour par `InferenceContextBuilder`.
- L'intake E5 explicite ajouté en 5.6 reste inchangé.

## Frontières maintenues

```text
pas d'autoload E5
pas de Scheduler vivant déclenché par E5
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
code_rule_reason: 5.6-r2 restaure le contrat de retour historique de ContextEngine.execute_tick sans nouvelle règle de programmation.
```
