# Règle 0287 r16 r53 — rejeu SQL et date de première matérialisation

1. Une référence SQL immuable déterministe conserve le `created_at` de sa
   première matérialisation lors d'un rejeu exact.
2. La valeur persistée est lue depuis PostgreSQL ; la date du nouvel essai
   Scheduler ne doit pas provoquer une nouvelle révision ni un nouvel artefact.
3. La comparaison immuable complète demeure stricte après résolution de cette
   date. Aucun autre champ n'est ignoré ou normalisé.
4. Si plusieurs entités existantes de la même paire portent des dates
   différentes, l'exécution échoue fermée avant toute écriture.
5. Un état partiel peut être complété avec la date initiale, sans suppression,
   mise à jour destructive ou remplacement d'une entité existante.
6. Cette règle ne crée ni second Scheduler, ni stockage JSON interne, ni file
   JSONL. PostgreSQL demeure l'autorité durable et Qdrant une projection.
