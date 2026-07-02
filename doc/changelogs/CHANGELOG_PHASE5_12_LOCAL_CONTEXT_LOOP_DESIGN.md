# Changelog — Phase 5.12 — Local context loop design

## Ajouté

- `doc/LOCAL_CONTEXT_LOOP_DESIGN.md`
- `doc/docs/architecture/context/36_local_context_loop_design.dot`

## Modifié

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/context/35_context_engine_contract_lock.dot`

## Résumé

La Phase 5.12 définit la boucle locale manuelle qui relie les artefacts E5, le
runtime local, l'intake explicite du `ContextEngine`, la projection de statut et
la décision humaine future.

Elle prépare la Phase 5.13, qui pourra ajouter une CLI d'orchestration mince.

## Frontières

```text
pas de nouvelle CLI
pas de serveur
pas de daemon
pas de polling
pas de réseau
pas d'API GitHub
pas de token
pas de Qdrant
pas de base persistante
pas de LLM
pas d'appel OpenVINO
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.12 ajoute une documentation d'architecture et un DOT ; aucune règle de programmation nouvelle n'est nécessaire.
```
