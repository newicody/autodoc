# Phase 3.17 — Verrou fichier de build E5

La Phase 3.17 sécurise le build local du corpus E5 contre les reconstructions concurrentes.

## Problème

L'écriture atomique protège le remplacement final : un fichier temporaire est validé avant de remplacer l'index final. Mais deux commandes peuvent encore viser le même corpus en même temps :

```text
process A -> build corpus.json
process B -> build corpus.json
```

Même si chaque remplacement est atomique, le dernier processus gagne, et les coûts d'embedding peuvent être doublés.

## Solution

Avant le build, la CLI crée un verrou voisin de la cible :

```text
corpus.json
.corpus.json.lock
.corpus.json.tmp
```

Le verrou est acquis par création exclusive :

```text
os.O_CREAT | os.O_EXCL
```

Si le fichier existe déjà, le build échoue explicitement.

## Flux

```text
build_e5_corpus.py
  -> E5CorpusBuildLock.acquire()
  -> E5CorpusBuilder ou E5IncrementalCorpusBuilder
  -> E5CorpusJsonStore.write_atomic()
  -> E5CorpusBuildLock.release()
```

Le verrou est supprimé en sortie de contexte, y compris si une exception se produit pendant le build.

## Limites volontaires

- Pas de stale-lock automatique.
- Pas de retry/busy-wait.
- Pas de démon.
- Pas de Qdrant.

Si un processus est tué brutalement, le lock peut rester et doit être supprimé manuellement après vérification.
