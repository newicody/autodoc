# Règle r16-r25 — commande Scheduler typée et autorité PostgreSQL

1. Manipuler une `GitHubResearchSchedulerCommand` dans le code métier, jamais un
   dictionnaire comme autorité interne.
2. Réserver JSON aux frontières GitHub et aux rapports temporaires.
3. Persister chaque sous-contrat dans des tables relationnelles normalisées ;
   interdire les colonnes JSON d'autorité.
4. Réutiliser la connexion de `LovePostgreSqlAuthorityBinding` ; ne pas ouvrir un
   second runtime, Scheduler, bus ou service.
5. Insérer le graphe de commande dans une transaction unique et rollbacker toute
   insertion partielle.
6. Accepter un rejeu exact sans duplication et refuser toute collision immuable.
7. Initialiser la commande à l'état `pending` sans la réclamer ni l'exécuter.
8. Conserver le Dispatcher hors de cette frontière ; il ne devient jamais une
   autorité d'orchestration.
