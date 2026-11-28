# Livrable final de recherche enregistré dans SQL

## But

Cette unité transforme la synthèse de liaison r16-r15 en livrable final durable :

```text
synthèse de liaison validée
→ build_final_synthesis_packet
→ synthèse clonée avec final_publication_ready=true
→ objet SQL final
→ artefact final
→ révision enfant acceptée
→ relecture exacte
```

## Réutilisation du contrat final

Le paquet est construit avec `build_final_synthesis_packet`. Ce contrat :

- assemble le corps final à partir des sections;
- rassemble les références de preuve;
- conserve les influences de contexte et validations;
- crée une identité `publication:final-synthesis:*`;
- marque une copie de la synthèse prête à la publication;
- conserve `runtime_import = external final publication adapter only`.

La synthèse locale r16-r15 reste inchangée et non prête.

## Autorité SQL

Le paquet complet est sérialisé de manière canonique dans un
`ContextAuthorityObject` de type `final-deliverable`.

Un `ContextArtifactDescriptor` indépendant référence cet objet avec
`storage_ref = sql:<object_ref>`.

Une nouvelle révision acceptée descend directement de la révision r16-r12 qui
contient les deux analyses. Elle ne remplace et ne modifie aucune analyse
source.

## Rejeu et interruption

Les trois entités sont immuables :

1. objet final;
2. artefact final;
3. révision enfant, écrite en dernier.

Une reprise reconnaît les éléments identiques, complète les éléments manquants
puis effectue une relecture exacte. Une collision de contenu bloque l’opération.

## Frontière distante

Cette unité ne publie rien :

```text
remote_publication_performed = false
github_mutation_performed    = false
projectv2_mutation_performed = false
```

Le `target_ref` prépare seulement la destination future, par exemple
`github:newicody/projects#15`.

L’unité suivante utilisera le reçu SQL et le digest du plan pour préparer,
confirmer, publier puis relire le commentaire final et les champs ProjectV2.
