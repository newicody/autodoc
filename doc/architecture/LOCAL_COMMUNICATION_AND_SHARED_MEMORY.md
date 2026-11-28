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

## Mécanisme de routes et cycle d'ouverture/fermeture déjà présent dans le dépôt

Les travaux historiques ont déjà posé le vocabulaire et plusieurs briques de ce mécanisme. Il faut les réutiliser et les raccorder, pas créer un second système.

### Surfaces et responsabilités retrouvées

- **ControlFS** (module 'runtime.controlfs_manifest') porte l'état déclaratif des routes souhaitées : manifestes sous 'desired/routes/<route_id>/'. Le Scheduler écrit cet état après autorisation ; ce n'est ni le canal de données ni la mémoire partagée elle-même.
- **ControlProxyPump** (fonction 'runtime.controlproxy_pump.tick_controlproxy') exécute un tick synchrone explicite. Il compare l'état désiré et l'état actif, puis matérialise les routes manquantes. Ce n'est pas un service résident : pas de watcher, d'inotify, de boucle permanente ou de daemon.
- **ActiveRouteMaterializer** (fonction 'runtime.controlproxy_active_routes.materialize_active_route') crée le fichier de route mmap et écrit le manifeste et le statut actifs dans ControlFS.
- **RouteDevShmRuntime** (module 'runtime.route_dev_shm_runtime') valide le point de placement explicite sous '/dev/shm', vérifie le tmpfs et prépare le répertoire runtime. Il refuse le fallback implicite.
- **RouteLease** (module 'runtime.controlproxy_route_lease') conserve l'état d'accès d'une route : 'not_leased → leased → active → draining → closed'. Il représente l'état de la réservation et de l'ouverture logique ; il ne constitue pas à lui seul une révocation au niveau du noyau.
- **RouteGenerationLifecycle** (module 'runtime.route_generation_lifecycle') formalise le cycle 'candidate → active → draining → closed → cleanup'. Le nettoyage supprime les fichiers d'une génération seulement après son état 'closed'.
- **RouteRuntimeManager** (module 'runtime.route_runtime_manager') expose ces opérations de génération derrière une façade runtime unique. Il ne décide ni de la politique ni de l'admission.
- **RouteProxyReconciler** (module 'runtime.routeproxy_reconciler') compare les routes souhaitées et actives et produit un plan 'create/delete/update/noop'. Il est explicitement en mode dry-run : il ne monte rien, ne démonte rien et ne surveille pas ControlFS.
- **RouteProxyFlowControlContract** (module 'context.route_proxy_flow_control_contract') décrit des baux, permissions d'écriture, états de zones, clôtures de génération et signaux de pression. Son constructeur de paquet est déclaratif et ne touche pas lui-même à '/dev/shm'.

### Ce que le runtime courant fait réellement

Le chemin Scheduler/ControlProxy historique actuellement présent passe par :

```text
demande de route déjà autorisée par Scheduler
  → ControlProxySchedulerAdapter
  → manifeste désiré ControlFS
  → SchedulerRouteAdapter / SchedulerRouteHandshake
  → ControlProxyPump (tick explicite)
  → ActiveRouteMaterializer
  → fichier mmap ring.bin sous le runtime root
  → manifeste + statut actifs ControlFS
  → acquisition / activation du RouteLease
```

Le retrait logique suit les transitions de bail et de génération, puis le nettoyage des fichiers d'une génération fermée. Le pump courant ne traite pas les actions 'update' et 'delete' : il les reporte explicitement au chemin de génération/drain/cleanup.

### Écarts à ne pas masquer

Les éléments suivants ne sont pas démontrés comme achevés dans le runtime courant :

1. 'RouteProxyReconciler' n'est pas un daemon passif qui surveille ControlFS ; il ne fait qu'un plan à la demande.
2. Le pump matérialise des routes manquantes, mais ne réalise pas le cycle complet d'update/delete.
3. Les transitions 'RouteLease' écrivent un état JSON ; elles ne prouvent pas à elles seules que tous les accès concurrents sont bloqués ou révoqués au niveau du transport.
4. Le chemin Scheduler/ControlProxy historique utilise 'ActiveRouteMaterializer', tandis que 'RouteRuntimeManager' expose le cycle plus récent par générations. Leur raccordement complet dans une seule composition runtime doit être vérifié ; leur coexistence dans le dépôt ne prouve pas qu'ils forment déjà un seul parcours.
5. Le transport mmap présent est un prototype de fichiers à slots fixes. Le module 'mmap_fixed_slot_route' le décrit comme file-backed et single-process, sans garantie de sûreté interprocessus.
6. Aucun usage de 'memfd_create', de transmission 'SCM_RIGHTS' ou de socket 'AF_UNIX / SOCK_SEQPACKET' n'a été retrouvé dans les chemins runtime examinés. Le choix memfd décrit plus haut reste donc une cible à implémenter, et non le transport actuellement fourni.

Dans cette architecture, « ouvrir/fermer une vanne » désigne l'autorisation et le cycle de vie d'une route d'accès. Les opérations existantes de matérialisation et de nettoyage ne doivent pas être présentées comme des appels système Linux 'mount(2)' / 'umount(2)'. Si un montage de namespace ou de système de fichiers est réellement requis ultérieurement, il devra rester sous la responsabilité du module système spécialisé, distinct du Scheduler, de ControlFS et du transport.

### Suite de raccordement

La suite doit rapprocher les responsabilités déjà présentes : demande autorisée du Scheduler, état désiré ControlFS, matérialisation passive de route, bail/permission d'accès, drainage, fermeture et nettoyage. Il faut notamment choisir et raccorder le chemin de génération comme cycle de vie canonique, sans créer un autre manager, watcher, bus ou ordonnanceur. L'implémentation memfd/SCM_RIGHTS sera intégrée à ce chemin de données lorsque ses contrats et ses garanties de propriété, de durée de vie et de révocation seront définis.
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
