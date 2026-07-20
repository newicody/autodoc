# Règle 0287 r16 r51 — synthèse compacte de publication finale

1. Ne pas modifier `FinalSynthesisPacket.to_mapping()` uniquement pour satisfaire
   un consommateur tardif lorsque la projection durable compacte est déjà
   persistée et adressée par digest.
2. Toute réhydratation de synthèse destinée à la publication doit vérifier la
   même `synthesis_ref` dans le paquet final, la synthèse de liaison et les
   métadonnées de l'objet SQL d'autorité.
3. La synthèse de liaison source doit rester `final_publication_ready=false`.
   Seule une copie de frontière en mémoire peut être promue à `true` après preuve
   portée par le livrable final SQL.
4. Aucune file JSONL, aucun second Scheduler et aucune autorité durable parallèle
   ne peuvent être introduits par cette compatibilité.
5. PostgreSQL demeure l'autorité durable ; GitHub et ProjectV2 demeurent des
   surfaces de publication contrôlée.

6. La compatibilité historique doit accepter un paquet complet contenant `packet.synthesis` même lorsque `packet.synthesis_ref` est absent ; si les deux formes sont présentes, leurs références doivent être strictement égales.
