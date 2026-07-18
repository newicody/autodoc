# Preuve de publication durable et clôture du cycle

## But

Cette unité ferme le cycle seulement après une publication distante complète et
relue exactement :

```text
livrable final SQL r16-r16
+ résultat de publication r16-r17
+ readback Issue valide
+ readback ProjectV2 valide
→ objet SQL de preuve distante
→ artefact SQL de preuve
→ révision enfant acceptée
→ cycle_status=closed
```

## Pas de nouveau gestionnaire de cycle

La fermeture est portée par la révision SQL existante. Aucun
`CycleManager`, Scheduler secondaire ou registre parallèle n’est créé.

La révision descend directement de la révision du livrable final et conserve :

- la référence du paquet final;
- l’objet et l’artefact finaux;
- le digest du plan de publication;
- le digest de lignée;
- l’identifiant et l’URL du commentaire;
- l’item, le champ et la valeur ProjectV2 relus;
- la date de clôture;
- la raison `final-publication-readback-verified`.

## Preuve minimale

Le corps complet du livrable et le corps du commentaire ne sont pas dupliqués.
La preuve conserve seulement :

- marqueur du commentaire;
- digest du corps publié;
- identifiant et URL du commentaire;
- snapshot ProjectV2;
- digests et références SQL;
- action distante;
- validité du readback.

PostgreSQL reste l’autorité durable.

## Conditions de clôture

La clôture refuse :

- une prévisualisation;
- un résultat distant invalide;
- une exécution partielle;
- une collision;
- un readback invalide ou absent;
- un digest incohérent;
- une lignée différente du livrable final.

Les actions complètes acceptées sont la création complète, la création Issue
avec ProjectV2 déjà conforme, la seule projection avec Issue déjà conforme, et
le rejeu intégral.

## Idempotence

L’objet, l’artefact et la révision sont immuables. Le premier passage produit
`created`; un rejeu identique produit `replay`; une reprise partielle produit
`mixed`. Une collision de contenu bloque la fermeture.

## Frontières

Cette unité ne :

- republie pas le commentaire;
- ne remodifie pas ProjectV2;
- ne relit pas GitHub;
- n’écrit pas dans Qdrant;
- ne crée aucun Scheduler;
- ne relance aucun laboratoire ou spécialiste.

Elle enregistre uniquement la preuve déjà obtenue par r16-r17.
