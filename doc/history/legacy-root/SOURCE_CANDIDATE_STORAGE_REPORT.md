# SourceCandidate local storage/report — Phase 5.15

## Objectif

La Phase 5.15 ajoute une bordure IO locale et explicite pour les `SourceCandidate`.
Elle ne remplace pas la base de connaissance, ne crée pas de serveur et ne
contacte pas GitHub. Elle permet seulement de conserver un snapshot JSON local
et un rapport d'écriture atomique.

Chaîne cible :

```text
SourceCandidate
-> SourceCandidateStoreSnapshot
-> source_candidates.json atomique
-> SourceCandidateStoreReport optionnel
```

## Contrats ajoutés

```text
SourceCandidateStorePolicy
SourceCandidateReportPolicy
SourceCandidateStoreSnapshot
SourceCandidateStoreWriteResult
SourceCandidateStoreReport
load_source_candidate_store()
write_source_candidate_store()
upsert_source_candidate()
write_source_candidate_store_report()
source_candidate_store_snapshot_from_json_dict()
```

## Format du store

Le store est un objet JSON stable :

```json
{
  "schema": "missipy.source_candidate.store.v1",
  "repository": "newicody/autodoc",
  "candidate_count": 1,
  "candidate_ids": ["sc-..."],
  "metadata": {},
  "candidates": []
}
```

Le fichier est écrit atomiquement via un fichier temporaire voisin puis
`replace()`.

## Upsert

`upsert_source_candidate()` charge le store si le fichier existe, insère la
candidate si son `candidate_id` est nouveau, ou remplace l'entrée existante si
l'identifiant existe déjà.

Le résultat indique :

```text
inserted: true|false
replaced: true|false
candidate_count: N
```

## Rapport optionnel

Un rapport optionnel peut être écrit avec `SourceCandidateReportPolicy` :

```json
{
  "schema": "missipy.source_candidate.store_report.v1",
  "operation": "upsert_source_candidate",
  "write_result": {}
}
```

Ce rapport est aussi écrit atomiquement.

## Frontières

La Phase 5.15 conserve volontairement les frontières suivantes :

```text
pas de base de données
pas de serveur
pas de daemon
pas de watcher
pas de réseau
pas d'API GitHub
pas de token
pas de polling
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
