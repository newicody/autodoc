# Frontière de digest de publication et preuve SQL — 0287 r16 r56

## Défaut observé

Le plan canonique de publication GitHub utilise historiquement un digest SHA-256
hexadécimal brut de 64 caractères. Ce digest est confirmé exactement par
l'opérateur et comparé sans transformation pendant la publication Issue et
ProjectV2.

La preuve durable PostgreSQL exige pour sa part une référence typée de la forme
`sha256:<64 caractères hexadécimaux>`. La publication distante pouvait donc être
réussie et relue exactement, puis la clôture SQL échouait avant toute écriture.

## Décision

La frontière de preuve SQL normalise le digest validé en ajoutant uniquement le
préfixe `sha256:`. Les 64 caractères restent inchangés. La comparaison distante,
la confirmation humaine et le digest du plan GitHub continuent d'utiliser la
valeur historique brute.

La normalisation accepte aussi une valeur déjà typée pour préserver les contrats
futurs. Toute valeur vide, non hexadécimale, de longueur incorrecte ou en
majuscules échoue fermée.

## Rejeu après publication distante

Une reprise de `complete` relit d'abord l'Issue et ProjectV2. Lorsque les deux
surfaces correspondent déjà exactement au plan approuvé, l'exécuteur existant
retourne l'action `replay` sans créer de second commentaire et sans réécrire le
champ ProjectV2. La preuve et la révision de clôture sont ensuite écrites dans
PostgreSQL.

## Frontières conservées

- Scheduler canonique unique ;
- PostgreSQL autorité durable ;
- GitHub frontière externe contrôlée ;
- aucun nouveau transport, daemon ou processus ;
- aucune file JSONL et aucun stockage métier JSON ;
- le JSON du rapport CLI reste une projection externe sérialisable.
