# Phase 3.7b — correction des entrées OpenVINO réelles

## Problème

Le test local `multilingual-e5-small` échouait avec :

```text
OpenVINO inference failed: Incompatible inputs of type: <class 'mappingproxy'>
```

La cause n'était pas le modèle, mais la frontière entre les contrats internes
immuables de MissiPy et l'API OpenVINO réelle :

- MissiPy transporte les entrées dans des `MappingProxyType` et des tuples pour
  rester déterministe et rejouable.
- OpenVINO attend des `dict` mutables et/ou des tableaux compatibles.

## Correction

`RealOpenVINORuntime` prépare désormais les entrées juste avant l'appel au modèle :

- `MappingProxyType` -> `dict`
- tuples numériques -> `numpy.asarray(...)` si NumPy est disponible
- fallback stdlib -> listes Python
- valeurs `None` refusées avec une erreur stable

La conversion reste volontairement dans `openvino_runtime.py` afin de préserver
l'immutabilité des contrats internes.

## Tests

Ajout/extension des tests unitaires autour de la normalisation d'inputs et
inscription du marqueur pytest `integration`.
