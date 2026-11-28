# ContextEngine contract — Phase 5.11

## Objet

La Phase 5.11 verrouille les contrats du `ContextEngine` qui ont été fragilisés
pendant l'intégration E5 de la Phase 5.6.

Cette phase ne crée pas de nouveau moteur. Elle documente et teste les garanties
qui doivent rester stables avant la boucle locale et les futures couches
SourceCandidate / serveur local.

## Contrats verrouillés

### Constructeur historique

Le constructeur historique reste valide :

```python
ContextEngine(registry, scheduler, event_bus)
```

Cette compatibilité est nécessaire parce que le `Scheduler` construit encore le
moteur contexte avec ces trois arguments.

### Constructeur local InferenceContext

L'usage local reste accepté :

```python
ContextEngine(inference_context)
```

Il sert aux bordures Phase 5 qui travaillent sans Scheduler vivant.

### Tick contexte historique

`execute_tick()` conserve son contrat historique : il retourne le snapshot issu
de la collecte/réduction.

Les appelants historiques peuvent donc continuer à faire :

```python
snapshot = await engine.execute_tick()
snapshot.components
```

Le `InferenceContext` construit pendant le tick est mémorisé séparément dans :

```python
engine.current_inference_context
```

### État courant d'inférence

`current_inference_context` expose toujours le dernier `InferenceContext` connu
par le moteur.

Il peut provenir :

- d'un contexte initial explicite ;
- d'un `execute_tick()` ;
- d'un intake E5 explicite.

### Intake E5 explicite uniquement

Les entrées E5 restent manuelles :

```python
engine.attach_e5_artifact_dir(...)
engine.attach_e5_runtime_context(...)
```

Elles ne déclenchent pas de Scheduler vivant, pas de daemon, pas de réseau, pas
de Qdrant, pas de LLM et pas d'appel OpenVINO.

## Frontières conservées

La Phase 5.11 confirme :

- pas de modification du Scheduler ;
- pas d'autoload E5 ;
- pas de boucle en arrière-plan ;
- pas de GitHub API ;
- pas de token ;
- pas de polling ;
- pas de dépendance hors stdlib.

## Raison

Avant d'ajouter une boucle locale, il faut verrouiller les contrats de sol :

```text
ContextEngine
Scheduler boundary
InferenceContext
E5 explicit intake
```

La Phase 5.11 sert de garde anti-régression avant les phases suivantes.

## Suite prévue

Après ce verrouillage, la suite logique est :

```text
5.12 Local context loop design
5.13 Local loop CLI
5.14 SourceCandidate local contract
```
