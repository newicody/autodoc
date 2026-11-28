# Noyau et Scheduler

Le package `src/kernel/` contient le Scheduler, Dispatcher, EventBus, PriorityQueue et Registry. Le Scheduler coordonne la boucle, la politique d'admission, la file, le dispatch et le ContextEngine. Les contrats d'événement, Scheduler, politique et télémétrie sont dans `src/contracts/`.

Le Scheduler est l'autorité unique d'admission et d'orchestration. PolicyEngine évalue les autorisations ; Dispatcher distribue ; handlers exécutent des capacités bornées et rendent leurs résultats. Les labs/spécialistes réutilisent cette chaîne.

Pour le parcours GitHub Projects, le cadrage Copilot initial (proposition de représentation scientifique, réponse de cohérence du serveur, reformulation Copilot) est consultatif et limité à un seul échange. Il ne crée pas une admission. Le dispatch d'exécution est déclenché séparément par la transition opérateur vers `En cours`. Une amélioration proposée après consultation des résultats Git constitue un nouveau cycle lié à la recherche d'origine et repasse par l'admission normale.

EventBus est observation-only : ni queue de commande ni ordonnanceur secondaire. Supervision et visualisation ne contrôlent pas le Scheduler.

## Entrées/sorties de données et communication locale

Pour les échanges locaux de données volumineuses, l'architecture retient un canal de contrôle `AF_UNIX / SOCK_SEQPACKET` et des espaces mémoire partagés `memfd`, dont les descripteurs sont transmis par `SCM_RIGHTS`. Les messages de contrôle portent les demandes, réponses, références et métadonnées ; les espaces `memfd` servent de buffers et de points d'entrée/sortie de données du Scheduler. Ils ne constituent ni un bus ni un mécanisme d'ordonnancement.

La création, l'attachement/montage, le détachement/démontage, la fermeture/libération et le contrôle des accès (« vannes ») sont confiés à des modules dédiés. Le Scheduler conserve l'autorité d'orchestration sans gérer lui-même ce cycle de vie. Aucun canal gRPC général n'est retenu dans ce périmètre ; les autres interfaces spécialisées ne sont pas à intégrer pour le moment. Cette orientation est une cible d'architecture et ne prouve pas que le transport est déjà implémenté. Voir [Communication locale et espaces mémoire partagés](LOCAL_COMMUNICATION_AND_SHARED_MEMORY.md).

Le noyau actuel est un micro-kernel coopératif ; ne pas lui attribuer le futur moteur de recherche adaptatif. Évolutions : graphe durable des tâches de recherche, transitions explicites, rapports de résultats/états, mesure de couverture/intérêt, reprise/idempotence, et charge logique calculée à partir des tâches/files/budgets du Scheduler.
