# Communication locale et espaces mémoire partagés

## Statut de cette décision

Ce document formalise une orientation d'architecture destinée aux développements futurs. Il ne certifie pas que le transport local, le transfert de descripteurs ou le cycle de vie des espaces mémoire sont déjà implémentés et raccordés dans le runtime courant.

Le périmètre immédiat est volontairement limité à la communication locale nécessaire au contrôle des échanges et au transfert de données volumineuses. D'autres interfaces de communication peuvent exister ou être ajoutées, mais elles ne sont pas à concevoir ni à intégrer dans ce chantier.

## Principe

Le Scheduler dispose de points d'entrée et de sortie pour les données échangées avec les composants. Pour les gros volumes, ces points s'appuient sur des espaces mémoire partagés qui servent de tampons (buffers) et évitent de transporter le contenu volumineux dans les messages de contrôle.

Le canal de contrôle et le canal de données sont deux usages complémentaires d'un même dispositif de communication locale :

- **Contrôle :** sockets locaux `AF_UNIX` de type `SOCK_SEQPACKET`. Ils transportent les demandes, réponses, ordres, références, métadonnées et petites charges utiles.
- **Données volumineuses :** espaces mémoire adossés à `memfd`. Le descripteur est transmis au destinataire par `SCM_RIGHTS` sur le canal de contrôle ; le contenu est ensuite lu ou écrit dans l'espace mémoire partagé.

Il n'est pas prévu de maintenir en parallèle un canal gRPC général. Les autres interfaces spécialisées ne sont pas exclues par cette décision ; elles restent simplement hors du périmètre immédiat.

## Rôle des espaces mémoire

Les espaces mémoire partagés sont des tampons d'échange et des points d'entrée/sortie de données pour le Scheduler :

1. un composant peut déposer un volume de données destiné au Scheduler ;
2. le Scheduler peut lire ce volume, le référencer dans le traitement et décider de son acheminement ;
3. le Scheduler peut mettre à disposition un volume que le composant destinataire pourra lire ;
4. les métadonnées et références nécessaires au suivi circulent sur le canal de contrôle, tandis que le contenu volumineux reste dans l'espace mémoire.

Ces espaces ne sont ni un bus, ni une file de tâches, ni un registre, ni un ordonnanceur secondaire. Ils ne prennent aucune décision d'admission ou de distribution. Le Scheduler reste l'autorité d'orchestration et chaque composant reste responsable de l'état et de la validité des données qu'il produit.

Les métadonnées associées devront permettre d'identifier au minimum le producteur, le destinataire ou la destination logique, le format, la taille, l'identité/version de la donnée, la provenance et les informations de fraîcheur utiles. Les modalités précises de validation et de synchronisation seront définies avec les contrats concernés.

## Cycle de vie et contrôle des accès

La création, le montage/attachement, le démontage/détachement et la libération des espaces mémoire relèvent de modules dédiés. Ils ne doivent pas être confondus avec le Scheduler ni avec le transport lui-même.

Ces modules de cycle de vie gèrent les mécanismes d'ouverture et de fermeture des accès — les « vannes » — selon les états, autorisations et conditions d'utilisation définis par l'architecture. Le Scheduler exprime le besoin d'échange dans le cadre de sa tâche ; il ne remplace pas ces modules spécialisés et ne manipule pas directement leur politique interne.

Le détail des états de vanne, des transitions, des règles de concurrence, des quotas, du nettoyage après erreur ou arrêt de processus et des garanties d'isolation reste à spécifier avant l'implémentation. Il faudra notamment éviter qu'un descripteur ou un espace mémoire reste accessible au-delà de sa durée d'autorisation.

## Séparation des responsabilités

- **Scheduler :** décide de l'admission, de l'affectation et du moment où les données sont nécessaires ; expose les points d'entrée/sortie logiques du traitement.
- **Canal local de contrôle :** transporte les messages courts et les descripteurs de mémoire.
- **Espaces `memfd` :** tamponnent les données volumineuses.
- **Modules de cycle de vie :** créent, attachent, détachent, ferment et libèrent les espaces ; contrôlent les vannes d'accès.
- **Composants producteurs/consommateurs :** restent propriétaires de leurs données, de leur format et de leur état de fraîcheur.
- **PostgreSQL :** conserve l'état métier durable et les références durables nécessaires ; un espace mémoire temporaire ne devient pas une autorité durable.

## Limites et points à valider avant implémentation

L'orientation `AF_UNIX / SOCK_SEQPACKET + memfd / SCM_RIGHTS` est une décision d'architecture, pas une preuve d'implémentation. L'audit et les développements futurs devront vérifier et définir :

- l'existence effective du transport dans le runtime installé et son raccordement aux composants ;
- les contrats de messages et de métadonnées des buffers ;
- les règles de propriété, durée de vie, partage et révocation des descripteurs ;
- la synchronisation entre producteur et consommateur ;
- les limites de taille, quotas et pression mémoire ;
- le nettoyage en cas d'échec, de timeout ou de terminaison d'un processus ;
- les contrôles d'accès, l'isolation et l'audit des ouvertures/fermetures ;
- l'intégration avec les interfaces de réponse des composants et les points d'entrée/sortie du Scheduler.

Aucune collecte omnisciente, aucun nouveau manager de communication, aucun bus parallèle et aucune autorité d'orchestration supplémentaire ne doivent être introduits pour réaliser ce mécanisme.
