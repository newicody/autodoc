# Règle 0287 r16 r54 — rejeu des projections et date initiale

1. Une référence `vector-projection:*` immuable conserve le `projected_at` de sa
   première matérialisation SQL lors d'un rejeu exact.
2. La valeur est relue depuis PostgreSQL avant la construction du plan ; le
   nouvel essai Scheduler ne doit pas modifier le digest du plan de projection.
3. Un état partiel de la paire est complété avec la date déjà persistée.
4. Deux dates persistées divergentes échouent fermées avant OpenVINO et Qdrant.
5. Tous les champs d'identité connus restent strictement comparés : source,
   digest, modèle, révision du modèle, dimension 384, normalisation, vecteur,
   collection, point et état.
6. Le calcul de `projection_ref` et `point_id` est mutualisé dans une fonction
   pure sur références typées et digest SHA-256. Le projecteur concret garde le
   contrôle strict des classes métier avant de déléguer à ce calcul ; le plan de
   paire ne doit pas imposer de nouveau contrôle `isinstance` aux doubles de ports.
7. Cette règle ne crée ni second Scheduler, ni stockage JSON interne, ni file
   JSONL. PostgreSQL demeure l'autorité durable et Qdrant une projection.
