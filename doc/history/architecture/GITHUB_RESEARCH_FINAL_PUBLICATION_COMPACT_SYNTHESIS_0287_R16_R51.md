# Publication finale et synthèse compacte — 0287 r16 r51

## Défaut observé

Le livrable final SQL utilise le contrat historique `FinalSynthesisPacket`.
Sa projection durable contient une référence typée `synthesis_ref`, pas une copie
imbriquée de toute la synthèse. L'adaptateur de publication r16-r17 exigeait au
contraire `packet.synthesis` sous forme d'objet et échouait après la persistance
réussie du livrable.

## Décision

La projection durable n'est pas modifiée. L'adaptateur de frontière accepte explicitement deux formes versionnées : le paquet historique complet avec `packet.synthesis`, et le paquet compact avec `packet.synthesis_ref`. Pour la forme compacte, il :

1. relit la synthèse de liaison déjà corrélée au même paquet de travail ;
2. exige l'égalité exacte des `synthesis_ref` ;
3. exige que la synthèse source demeure non publiable et masque la provenance ;
4. exige les preuves de préparation finale portées par le plan SQL et les
   métadonnées de l'objet d'autorité ;
5. crée uniquement une copie en mémoire marquée prête pour le planificateur de
   publication déjà installé.

Ainsi, les objets persistés et leurs digests ne changent pas. Un redémarrage
reste un replay du même livrable, sans seconde révision créée pour ajouter un
champ redondant.

## Frontières conservées

- PostgreSQL reste l'autorité durable du livrable final.
- JSON reste une projection de frontière et non une file JSONL interne.
- Le Scheduler canonique unique reste l'autorité d'orchestration.
- Aucune mutation GitHub n'est déclenchée par cette adaptation pure.
- Les deux analyses spécialistes et la synthèse de liaison restent immuables.
