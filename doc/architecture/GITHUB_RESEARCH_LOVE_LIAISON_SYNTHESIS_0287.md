# Synthèse de liaison des deux analyses réhydratées

## But

Cette unité transforme les deux analyses réhydratées par r16-r14 en une
synthèse locale distincte :

```text
objet SQL analyse concepts/affects
+ objet SQL analyse dynamiques relationnelles
→ validation des corps et digests
→ reconnaissance des deux schémas spécialistes
→ mutualisation des convergences, contradictions et incertitudes
→ deux fragments d’analyse profonds
→ un fragment d’audit comparatif
→ SpecialistLiaisonSynthesis existante
```

## Réutilisation

L’unité réutilise :

- `LoveEvidenceMutualization`;
- `SpecialistOutputFragment`;
- `SpecialistLiaisonPolicy`;
- `build_specialist_liaison_synthesis`.

Elle ne crée pas un second format de synthèse.

## Autorité et provenance

Les deux corps SQL sont seulement lus en mémoire. Leur digest SHA-256 est
recalculé avant l’analyse. Les deux objets restent inchangés et distincts.

Les fragments internes conservent :

- la référence de l’analyse;
- la référence exacte de l’objet SQL;
- le paquet de recherche;
- les preuves et artefacts compatibles;
- la profondeur d’analyse.

La surface utilisateur masque le nom des spécialistes, conformément au contrat
de liaison existant, mais la provenance reste disponible dans les fragments.

## Mutualisation locale

La mutualisation rassemble :

- les convergences terminologiques explicites;
- les contradictions;
- les incertitudes;
- les recommandations;
- les références de preuve.

Elle indique explicitement que deux spécialistes d’un seul laboratoire ne
constituent pas une validation multi-laboratoires.

## Non-publication

La synthèse produite conserve :

```text
final_publication_ready = false
publication_surface     = none until final adapter
```

Aucun `FinalSynthesisPacket` n’est créé dans cette unité.

## Limites

Cette unité :

- n’écrit ni dans PostgreSQL ni dans Qdrant;
- ne lance aucune inférence;
- ne relance aucun spécialiste;
- ne crée aucun Scheduler;
- ne produit aucun artefact final;
- ne publie rien vers GitHub.

L’unité suivante transformera cette synthèse locale validée en livrable final,
puis l’enregistrera dans une nouvelle révision SQL sans modifier les analyses
sources.
