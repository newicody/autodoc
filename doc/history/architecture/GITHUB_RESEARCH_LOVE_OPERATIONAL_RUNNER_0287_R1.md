# Câblage opérationnel tool-bounded du lanceur r16-r20

## Corrections

Le lanceur reçoit désormais un `policy_decision_id` explicite et le transmet au
`runtime_context`. Le provider tool-bounded utilise cette référence pour ouvrir
la membrane Qdrant avec ses gates d’écriture et de recherche.

`--runtime-config` pilote réellement la variable
`AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG` pendant l’acquisition de la lease, puis
restaure l’environnement initial.

Le port `LoveQdrantLiveAnalysisProjection` expose maintenant
`read_named_reference_point()` en déléguant au même exécuteur Qdrant déjà ouvert.
Il devient donc simultanément :

- le port de projection;
- le port de relecture exacte sans vecteurs.

Aucune seconde connexion Qdrant et aucune fabrique de lecteur externe ne sont
nécessaires.

## Fabrique opérationnelle

```text
context.love_installed_runtime_factory_0287:build_runtime
```

Pour un appel CLI autonome, le fichier installé doit sélectionner :

```text
context.love_tool_bounded_installed_runtime_composer_0287:
build_tool_bounded_installed_runtime
```

et déclarer :

```text
[scheduler]
lifecycle = tool-bounded
```

## Gates de préparation

```text
AUTODOC_QDRANT_POINT_WRITE_ALLOWED=true
AUTODOC_QDRANT_SEARCH_ALLOWED=true
```

Le mot de passe PostgreSQL reste fourni par la variable référencée dans
`[postgresql] password_env`.

## Frontières

- un seul Scheduler process-local pour l’invocation;
- un seul exécuteur Qdrant partagé pour write/read/search;
- SQL reste l’autorité durable;
- E5 reste exactement en dimension 384;
- aucune valeur secrète n’est sérialisée.
