# Phase 3.16 — Build atomique du corpus E5

## Problème traité

Un corpus E5 peut devenir coûteux à reconstruire quand il contient beaucoup de chunks. Si le processus échoue pendant l'écriture du JSON final, l'ancien corpus peut être corrompu ou partiellement remplacé.

## Solution

`E5CorpusJsonStore.write_atomic()` applique le flux suivant :

```text
E5CorpusIndex
  -> sérialisation JSON stable
  -> écriture .<target>.tmp
  -> relecture + validation
  -> Path.replace(target)
```

La cible n'est remplacée que si le fichier temporaire a été correctement écrit et relu.

## Compatibilité

Le format reste `missipy.e5.corpus.v1`. Les index existants restent lisibles.

## Limite volontaire

Cette phase ne fait pas encore de lock inter-processus. Deux builds concurrents vers la même cible restent à éviter. Une phase ultérieure pourra ajouter un lock fichier explicite si nécessaire.
