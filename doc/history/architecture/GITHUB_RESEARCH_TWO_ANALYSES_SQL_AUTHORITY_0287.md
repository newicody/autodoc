# Deux analyses spécialistes dans l’autorité SQL

## But

Les deux productions du laboratoire restent séparées avant toute projection ou
synthèse :

```text
première analyse validée
+ seconde analyse validée
→ objet SQL autoritatif 1
→ artefact SQL 1
→ objet SQL autoritatif 2
→ artefact SQL 2
→ révision enfant acceptée
```

## Réutilisation

L’unité utilise exclusivement `authority_store` déjà injecté dans
`ImportedActionsRuntimePorts` :

- `get_object` / `put_object`;
- `get_artifact` / `put_artifact`;
- `get_revision` / `put_revision`.

Elle ne crée aucune table et n’importe aucun pilote PostgreSQL.

## Identités distinctes

Chaque analyse possède :

- son `ContextAuthorityObject`;
- son `ContextArtifactDescriptor`;
- son digest du résultat complet;
- son spécialiste;
- sa tâche;
- sa visite;
- son laboratoire;
- sa représentation humaine et son résultat machine.

Une révision enfant référence les quatre identités. La révision de base reste
inchangée.

## Reprise après interruption

Les entités sont immuables et la révision enfant est écrite en dernier. Une
interruption peut donc laisser une partie des objets déjà insérés, mais le rejeu
les reconnaît comme identiques, complète les éléments manquants puis vérifie
leur relecture exacte.

Une collision de même référence avec un contenu différent bloque tout nouveau
write détectable avant l’exécution.

## Limites

Cette unité :

- ne projette rien dans Qdrant;
- ne lance aucune inférence OpenVINO;
- ne produit aucune synthèse;
- ne modifie pas GitHub;
- ne crée ni Scheduler ni service;
- ne fusionne jamais le texte des deux analyses.

La prochaine unité projettera séparément les deux objets SQL avec E5-384 et
Qdrant, en ne plaçant que des références et métadonnées minimales dans le
payload vectoriel.
