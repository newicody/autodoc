# Roadmap de développement — parcours d'une requête GitHub jusqu'au retour Git

Cette roadmap est l'axe de développement de MissiPy. Elle décrit un seul parcours fonctionnel, depuis une nouvelle entrée sur un board GitHub jusqu'à la livraison finale dans Git. Les rapports opérationnels périodiques constituent un second flux Git permanent, distinct du livrable de la requête.

Les étapes peuvent nécessiter plusieurs patches intermédiaires. Une étape n'est déclarée terminée qu'après raccordement et validation du parcours concerné. Le manuel sera construit progressivement : un chapitre par étape effectivement terminée.

## Invariants d'architecture

- Le Scheduler est l'unique autorité d'admission, de sélection, de priorité et d'orchestration des tâches.
- Le Scheduler ne possède pas une connaissance omnisciente ou automatiquement actualisée de tous les systèmes. Chaque composant est responsable de son état et peut transmettre, à la demande, les informations utiles au Scheduler.
- Les informations communicables comprennent la disponibilité, les capacités, les réservations, les compétences, les interfaces, l'état des communications et les statistiques d'utilisation.
- Les statistiques décrivent séparément l'utilisation des composants et l'évolution des recherches/cellules.
- Les mécanismes de sécurité et de politique prévus doivent encadrer les demandes, les communications, l'admission et les mutations. Ils sont réutilisés ; aucun système de sécurité parallèle n'est créé.
- PostgreSQL est l'autorité durable. Qdrant est une projection de recherche/rappel reconstructible ; il ne remplace pas PostgreSQL.
- Les laboratoires et spécialistes sont des capacités appelées par les handlers sous l'autorité du Scheduler. Ils ne possèdent pas de Scheduler, queue, bus, registre ou orchestrateur parallèle.
- Les laboratoires peuvent collaborer en échangeant des résultats et en lisant les données persistées dans PostgreSQL. Ces données peuvent être moins fraîches que l'état courant d'un autre laboratoire ; leur date, version et provenance doivent rester explicites.
- EventBus, Cell Lens, PassiveSupervisor et VisPy sont des mécanismes d'observation, pas des autorités de décision.
- La charge physique et la capacité logique du Scheduler restent distinctes. Une mesure CPU/GPU/RAM ne permet pas de déduire une capacité d'admission.
- La présence d'un module, d'un contrat ou d'un adaptateur ne prouve pas que le flux complet est raccordé ou exploitable.\n- Pour les échanges locaux de données volumineuses, l'orientation retenue est un canal de contrôle `AF_UNIX / SOCK_SEQPACKET` et des buffers mémoire `memfd` dont les descripteurs sont transmis par `SCM_RIGHTS`. Ces buffers constituent des points d'entrée/sortie de données du Scheduler ; ils ne sont ni un bus ni une autorité d'orchestration.\n- Le cycle de vie des espaces mémoire (création, attachement/montage, détachement/démontage, fermeture/libération et contrôle des accès ou « vannes ») relève de modules dédiés, distincts du Scheduler et du transport. Aucun canal gRPC général n'est retenu dans ce périmètre ; les autres interfaces spécialisées restent hors du chantier immédiat.

## 01. Entrée Projects, cadrage Copilot et premier artefact

**Déclencheur initial actuellement décrit par le bundle :** ouverture d'une Issue `[Recherche]` dans `newicody/projects` (`issues.opened`). La carte ProjectV2 est la surface de classement et de suivi ; sa création ne vaut pas admission d'une tâche par le Scheduler.

Composants :
- GitHub Issues et ProjectV2
- Formulaires et workflow du bundle Projects
- Copilot
- Artefact initial de cadrage
- Réponse de cohérence du serveur
- Artefact reformulé par Copilot
- Réconciliateur de configuration ProjectV2
- Futur installateur complet du mode Projects

Le cadrage initial suit exactement cette séquence, sans boucle :

```text
Nouvelle Issue de recherche
    → Copilot dégrossit la demande
    → Artefact initial : forme du rapport scientifique attendu
    → Serveur examine la cohérence, les données, capacités et contraintes
    → Une réponse structurée du serveur
    → Copilot reformule une demande précise
    → Publication de l'artefact reformulé
```

Copilot identifie en particulier les représentations scientifiques nécessaires à un rapport complet : données attendues, mesures, analyses, visualisations, preuves, comparaisons et structure du livrable. Le serveur retravaille cette proposition au regard de ses capacités et contraintes réelles, puis répond une seule fois. Copilot tient compte de cette réponse et publie la demande précise. Aucun ping-pong de clarification récursif n'est prévu.

Cette séquence de cadrage n'est pas le lancement de l'exécution. Le lancement d'un cycle reste la transition ProjectV2 vers `En cours`, issue d'une intention opérateur (`Recherche`, `Développement` ou `Production`) et traitée par le dispatch idempotent existant. L'ouverture de l'Issue et la transition `En cours` ont donc des rôles différents : cadrer, puis demander l'exécution.

Le mode Projects doit conserver les cartes durables, les vues, les champs, les thèmes et l'historique append-only des cycles déjà définis. Un installateur idempotent, simple et complet devra installer ou réconcilier formulaires, workflows, champs, options et vues, vérifier les permissions et secrets attendus sans jamais versionner les secrets, et produire un compte rendu vérifiable. Le réconciliateur de configuration existant ne doit pas être présenté comme cet installateur complet.

En parallèle, le serveur prépare et publie périodiquement dans le dépôt Git un rapport de fonctionnement et d'utilisation. Ce flux est indépendant du cadrage Copilot et du livrable scientifique.

**Résultat attendu :** une recherche durable configurée dans Projects, un cadrage initial effectué en un seul échange serveur/Copilot et un artefact précis publié, sans admission implicite d'une tâche.

**Avancement 0293 :** le contrat typé du cadrage scientifique initial est ajouté (`missipy.github.copilot_advisory.v2` → `missipy.github.server_scientific_framing_response.v1` → `missipy.github.copilot_refined_research_request.v1`). Les validations de corrélation, de digest, de provenance et de non-autorité sont définies. Ce patch ne fournit pas encore le producteur de la réponse serveur, le second appel Copilot, la persistance append-only ni leur raccordement au workflow ; l'étape 01 reste donc ouverte.

**Avancement 0294 :** le canal de transport est maintenant formalisé séparément du contenu scientifique : trois artefacts append-only dans `newicody/projects`, publiés par commits/push Git et reliés par références et digests (`copilot-initial` → `server-response` → `copilot-refined`). Le contrat interdit l'écrasement d'un chemin, distingue rejeu identique et collision, et fixe l'absence de RPC, de boucle de clarification et d'autorisation d'exécution. Il ne réalise pas encore les producteurs/publishers Git, le workflow `push` de reformulation ni la récupération serveur ; l'étape 01 reste ouverte. Le séparateur d'identité du contrat 0293 a également été corrigé.

**Avancement 0295 :** le workflow initial publie maintenant l'avis Copilot v2 dans Git avec un secret d'écriture limité ; un workflow séparé réagit uniquement au push de `server-response.json` et publie la reformulation Copilot une seule fois. Les adaptateurs de récupération/publication Git sont ajoutés. Le serveur dispose d'un adaptateur pour publier sa réponse à partir d'une évaluation JSON vérifiée, et l'assembleur d'admissibilité peut exiger la chaîne complète puis intégrer la reformulation comme indication non autoritative au work package existant. Ce raccordement est disponible en option CLI, pas encore activé dans le parcours vivant `En cours`. L'adaptateur serveur ne collecte pas lui-même l'état des composants : son alimentation par les interfaces réelles et son appel dans le traitement serveur restent à raccorder. Les workflows et le secret doivent encore être installés dans `newicody/projects` et le parcours de bout en bout validé. L'étape 01 reste ouverte.

**Avancement 0296 :** un contrat d'instantané d'état propre à chaque composant (`missipy.server.component_state_snapshot.v1`) et un agrégateur d'évaluation scientifique sont ajoutés. Ils conservent disponibilité, fraîcheur, état de communication, capacités, réservations, interfaces, statistiques d'utilisation, données et provenance. Les états inconnus, partiels et périmés ne sont pas transformés en zéros ; les statistiques d'utilisation restent distinctes de la capacité logique du Scheduler et des mesures matérielles. Le runtime installé peut recevoir un fournisseur d'instantanés injecté et produire l'évaluation utilisée par l'adaptateur de réponse Git. Le fournisseur concret doit encore être implémenté par la fabrique de composants installée, puis appelé par le traitement Git serveur lorsqu'un artefact initial arrive. Aucun poller, registre, manager ou orchestrateur parallèle n'est ajouté. L'étape 01 reste ouverte.

## 02. Communication à la demande et état propre des composants

**Avancement 0296 :** le contrat d'instantané et l'agrégateur scientifique établissent la forme des informations fournies par les composants. Le raccordement au runtime passe par un fournisseur injecté par la composition installée ; chaque composant reste responsable de ses propres observations. Le registre déclaratif 0242 et le plan de registre Scheduler 0257 ne sont pas transformés en sources d'état dynamique ni en autorités omniscientes.

**Objectif :** permettre au Scheduler d'interroger les composants sans leur imposer un registre central omniscient.

Composants :
- Scheduler
- Composants interrogés
- Interfaces de communication
- ControlProxy, lorsque le transport l'exige
- Message Journal, lorsque la traçabilité du transport l'exige

À la demande du Scheduler, chaque composant peut transmettre les informations qu'il détient sur son propre fonctionnement :

- disponibilité et état de préparation ;
- capacités et limites ;
- capacités déjà réservées ou engagées ;
- compétences et types de traitement supportés ;
- interfaces et modes de communication ;
- état des échanges, erreurs, délais et fraîcheur des informations ;
- statistiques d'utilisation et résultats opérationnels.

Le Scheduler ne suppose pas qu'une information est connue si le composant ne l'a pas fournie. Une information absente, inconnue ou périmée reste explicitement inconnue ou périmée.

Le serveur peut agréger les informations reçues pour ses rapports opérationnels et pour sa réponse unique de cohérence au cadrage initial Copilot, sans transformer cette agrégation en autorité concurrente du Scheduler. Cette réponse doit distinguer les capacités vérifiées, les limites, les données manquantes et les représentations scientifiques réalisables ; elle ne déclenche pas l'exécution.

Le canal local de référence pour ce périmètre est `AF_UNIX / SOCK_SEQPACKET` : les messages courts transportent les demandes, réponses, références et métadonnées. Les gros volumes sont placés dans des buffers `memfd`, et les descripteurs sont transmis par `SCM_RIGHTS`. Ces buffers fournissent les points d'entrée/sortie de données du Scheduler. Les autres interfaces de communication spécialisées ne sont pas exclues, mais leur gestion n'est pas requise dans ce chantier. Le cycle de vie et le contrôle des accès aux espaces mémoire sont délégués aux modules dédiés qui pilotent les ouvertures/fermetures (« vannes »). Voir [Communication locale et espaces mémoire partagés](architecture/LOCAL_COMMUNICATION_AND_SHARED_MEMORY.md).\n\n**Résultat attendu :** chaque composant expose une interface de réponse exploitable ; le Scheduler peut demander les informations nécessaires au moment où il en a besoin, et les données volumineuses disposent de points d'entrée/sortie partagés sous contrôle.

## 03. Sécurité, politiques et autorisations

**Objectif :** intégrer les mécanismes de sécurité prévus au parcours réel.

Composants :
- Policy Engine
- Policy Engine Runtime
- Policy Contracts
- Admission Control
- Authorized Adapters
- Audit et Provenance

Les règles de sécurité encadrent les opérations selon les contrats et frontières déjà prévus : accès aux systèmes, opérations permises, admission, lecture, proposition, approbation et mutation externe.

Cette étape doit auditer et raccorder les mécanismes présents dans le dépôt. Elle ne doit pas inventer une seconde autorité de permissions ni permettre à Copilot, à un laboratoire ou à un handler de contourner le Scheduler et les contrôles d'accès.

**Résultat attendu :** chaque opération sensible passe par les contrôles prévus et laisse les traces nécessaires.

## 04. Admission et distribution par le Scheduler

**Objectif :** transformer la demande en tâches exécutables et les affecter sous l'autorité unique du Scheduler.

Composants :
- PostgreSQL
- Scheduler
- Task Admission
- Task Graph
- Handler Catalog
- Dispatcher
- Handler Factory

Le Scheduler :
1. reçoit une demande ou une tâche durable ;
2. applique les politiques et contrôles d'admission ;
3. interroge les composants concernés pour obtenir leurs informations utiles ;
4. compare les compétences requises aux capacités annoncées ;
5. tient compte des réservations et des statistiques disponibles ;
6. décide de l'admission, de la priorité et de l'affectation ;
7. distribue la tâche au handler choisi.

Les composants décrivent leur état ; le Scheduler prend les décisions d'orchestration. Aucun registre ou orchestrateur parallèle n'est introduit.

**Résultat attendu :** une tâche admise et affectée à un handler compatible, avec une décision durable et traçable.

## 05. Exécution et communication entre composants

**Objectif :** exécuter les tâches, transmettre les demandes et récupérer les résultats ou les erreurs.

Composants :
- Dispatcher
- Handlers
- Handler Execution
- Step Runner
- Continuation Store
- Adaptateurs
- ControlProxy
- Runtime
- PostgreSQL

Flux attendu :

```text
Scheduler
    → Dispatcher
    → Handler
    → Adaptateur / interface
    → Système cible
    → Résultat ou erreur
    → Handler
    → PostgreSQL
    → Scheduler
```

Les échanges doivent rendre identifiables le destinataire, l'interface utilisée, l'état de transmission, le résultat, les erreurs, les délais et les possibilités de reprise. Pour les échanges locaux, le canal de contrôle `AF_UNIX / SOCK_SEQPACKET` transporte les messages courts et les descripteurs `memfd` via `SCM_RIGHTS` ; les espaces `memfd` servent de buffers de données et de points d'entrée/sortie du Scheduler. Les modules dédiés gèrent leur création, montage/attachement, démontage/détachement, libération et contrôle des accès (« vannes »). ControlProxy transporte les messages autorisés ; il ne choisit pas les tâches et ne prend aucune décision d'orchestration. Les autres interfaces spécialisées restent hors du périmètre immédiat, et aucun canal gRPC général n'est prévu.

**Résultat attendu :** les tâches peuvent être exécutées, suivies, persistées et reprises sans perdre l'autorité du Scheduler.

## 06. Recherche, contexte et collaboration des laboratoires

**Objectif :** faire travailler ensemble les capacités de recherche, les spécialistes et les laboratoires.

Composants :
- Context Engine
- PostgreSQL
- E5
- OpenVINO
- Qdrant
- Research Tools
- Laboratory Framework
- Laboratories
- Specialists
- Handler Catalog

Les laboratoires sont appelés par les handlers et collaborent au moyen de leurs interfaces et contrats. Ils peuvent partager des résultats par PostgreSQL : un laboratoire peut donc lire une version persistée qui n'est pas le tout dernier état en mémoire ou en cours de production chez un autre laboratoire.

Les échanges doivent conserver :
- l'identité de la donnée ;
- sa date et sa version ;
- sa provenance ;
- son état de fraîcheur ;
- les références permettant de retrouver la donnée durable.

La fraîcheur requise dépend de la tâche. Une donnée persistée plus ancienne peut être acceptable pour une synthèse ou une collaboration asynchrone ; elle ne doit pas être présentée comme l'état instantané d'un autre laboratoire.

PostgreSQL demeure l'autorité durable. Qdrant fournit une projection de recherche/rappel ; les éléments retenus sont réhydratés depuis SQL lorsque nécessaire. Le profil E5 canonique reste en 384 dimensions.

**Résultat attendu :** les laboratoires et spécialistes collaborent sans orchestrateur parallèle, avec une fraîcheur et une provenance explicites des données échangées.

## 07. Résultats, preuves et synthèse

**Objectif :** consolider les résultats produits pendant la recherche.

Composants :
- Evidence Aggregation
- Provenance
- Digest Deduplication
- Contradiction Detection
- Liaison Synthesis
- PostgreSQL
- Qdrant

Les résultats des handlers et des laboratoires sont rassemblés, reliés à leur provenance, dédupliqués et confrontés. Les preuves et décisions durables sont conservées dans PostgreSQL ; Qdrant peut en fournir une projection de rappel.

Le périmètre exact du passage obligatoire par chacun de ces composants reste à confirmer par l'audit des parcours existants. La roadmap ne présume pas que toutes les requêtes nécessitent systématiquement toutes les formes d'agrégation.

**Résultat attendu :** des résultats traçables et une synthèse exploitable, avec les contradictions et incertitudes conservées au lieu d'être masquées.

## 08. Recherche adaptative pilotée par le Scheduler

**Objectif :** permettre au Scheduler de faire évoluer le graphe de recherche selon les observations et les résultats.

Composants :
- Scheduler
- Task Graph
- Context Engine
- Research Statistics
- Cell Statistics
- Component Usage Statistics
- Resource Reservations
- PostgreSQL

Le Scheduler exploite les retours des tâches pour :
- mesurer couverture, fréquence, nouveauté, rendement et incertitude des cellules ;
- repérer les cellules ou régions sous-représentées ;
- réévaluer l'intérêt des branches de recherche ;
- réviser les priorités ;
- abandonner explicitement une branche devenue peu intéressante ;
- préserver les tâches indépendantes ;
- réaffecter les travaux selon les capacités et réservations disponibles.

Deux familles de statistiques restent distinctes :
- **statistiques de recherche/cellules** : couverture, fréquence, nouveauté, résultats, incertitude et évolution des branches ;
- **statistiques d'utilisation des composants** : tâches traitées, durée, occupation, attente, succès, échecs, indisponibilités et erreurs de communication.

Les décisions, justifications, états et possibilités de reprise sont persistés dans PostgreSQL. La charge logique est calculée à partir des tâches, files, budgets et réservations du Scheduler, et non déduite des seules mesures matérielles.

**Résultat attendu :** un graphe de recherche évolutif dont le Scheduler reste l'unique autorité.

## 09. Observation, statistiques et rapport opérationnel périodique

**Objectif :** observer le fonctionnement réel des composants et publier régulièrement leur état d'utilisation dans Git.

Composants :
- EventBus
- EventBus Cell Lens Bridge
- Cell Observation Journal
- Cell Snapshot
- Cell Lens
- PassiveSupervisor
- VisPy
- Hardware Collector
- Hardware Contracts
- Component Usage Statistics
- Operational Report
- Git Publisher

Les événements, états et statistiques peuvent alimenter l'observation et le rapport. EventBus, Cell Lens, PassiveSupervisor et VisPy restent passifs : ils ne commandent ni le Scheduler ni les composants.

Le rapport opérationnel doit notamment présenter :
- les composants actifs, prêts, occupés, indisponibles ou inconnus ;
- les capacités et réservations communiquées par les composants ;
- les statistiques d'utilisation et d'exécution ;
- les durées, attentes, succès, échecs et indisponibilités ;
- les erreurs et états de communication ;
- les observations matérielles, séparées de la charge logique du Scheduler ;
- les horodatages, la fraîcheur et les lacunes de collecte.

**Cadence cible :** le serveur pousse dans le dépôt Git un nouvel état de rapport toutes les 30 secondes. Ce flux périodique est indépendant des branches, commits et pull requests utilisés pour livrer le résultat d'une requête.

Les contrats HardwareSample et HardwareCell existent, mais ils ne constituent pas à eux seuls un collecteur matériel. Le collecteur et son raccordement restent à réaliser et à valider.

**Résultat attendu :** un historique Git périodique du fonctionnement et de l'utilisation du serveur, sans transformer les outils d'observation en contrôleurs.

## 10. Copilot contextualisé par l'état du système

**Objectif :** permettre à Copilot de produire des propositions et artefacts en tenant compte du contexte opérationnel disponible.

Composants :
- GitHub ProjectV2
- Copilot
- Server Routing Context
- Scheduler
- Task Graph
- Laboratories
- Specialists
- Research Statistics
- Component Usage Statistics
- Operational Report

Pendant le cadrage initial de l'étape 01, le serveur fournit une seule réponse structurée, bornée, datée et traçable à l'artefact Copilot. Elle précise notamment les représentations scientifiques réalisables, les données et outils disponibles, les capacités et réservations communiquées, les contraintes, les incertitudes et les lacunes. Copilot reformule alors la demande et clôt ce cadrage : aucun nouvel échange de clarification automatique n'est engagé.

Après publication du rapport scientifique dans Git, Copilot peut consulter les résultats et proposer une nouvelle itération d'amélioration. Cette proposition est un nouveau cycle de la même recherche durable (ou une actualisation liée selon le modèle Projects), conserve les références et l'historique des cycles précédents et repasse par les contrôles d'admission du Scheduler. Il s'agit d'une réaction aux résultats publiés, pas de la reprise du dialogue initial.

Copilot reste consultatif. Il ne peut ni admettre une tâche, ni sélectionner un handler, ni modifier les priorités durables, ni lancer directement un laboratoire ou un processus. Le Scheduler conserve toutes les décisions d'exécution.

**Résultat attendu :** Copilot dispose d'un contexte réel et actualisé selon les informations disponibles, sans devenir une autorité d'orchestration.

## 11. Construction du livrable final

**Objectif :** assembler le résultat final de la requête à partir des résultats et preuves disponibles.

Composants :
- Evidence Aggregation
- Liaison Synthesis
- Final Deliverable
- Publication Evidence
- Publication Plan
- PostgreSQL

Le livrable conserve les références aux résultats, preuves, sources, versions et décisions qui le justifient. Il est préparé pour validation et publication.

**Résultat attendu :** un livrable durable, traçable et prêt à être soumis à la revue prévue.

## 12. Validation et retour final dans Git

**Objectif :** livrer le résultat de la requête dans le dépôt Git et reporter son état final sur le board.

Composants :
- Publication Plan
- Human Review
- Git Adapter
- Git Writer
- Git Branch
- Git Commit
- Pull Request
- GitHub ProjectV2
- PostgreSQL
- Scheduler

Flux attendu :

```text
Final Deliverable
    → Publication Plan
    → Human Review
    → Git Adapter
    → Git Writer
    → Branch / Commit / Pull Request
    → GitHub ProjectV2
    → État final durable
```

La validation humaine et les autorisations requises précèdent les mutations externes. Le retour dans GitHub ProjectV2 reflète l'état du travail ; PostgreSQL conserve l'état durable de la requête. Une proposition Copilot née de la consultation d'un résultat publié ouvre, si elle est retenue par l'opérateur, un nouveau cycle lié à la même recherche : elle ne contourne ni la transition opérateur requise ni l'admission du Scheduler.

Le Git Writer et le parcours complet de livraison doivent être démontrés de bout en bout. La présence d'un plan, d'un adaptateur ou d'un contrat de publication ne suffit pas à prouver que le résultat est effectivement livré.

**Résultat attendu :** le livrable est publié dans Git, et la requête dispose d'un état final traçable dans PostgreSQL et sur le board.

## Ordre de réalisation

1. Entrée Projects, cadrage Copilot en un échange, artefact précis, installation/réconciliation du mode Projects et définition du flux de rapport périodique.
2. Interfaces de communication à la demande et remontée des informations propres aux composants.
3. Raccordement des politiques, contrôles de sécurité et autorisations.
4. Admission, sélection et distribution des tâches par le Scheduler.
5. Exécution, communication, retours d'état et reprise durable.
6. Recherche, contexte et collaboration des laboratoires avec fraîcheur explicite des données.
7. Consolidation des résultats et des preuves, après confirmation du périmètre réellement nécessaire.
8. Recherche adaptative et statistiques de recherche/composants sous autorité du Scheduler.
9. Observation, collecte, statistiques et Git Push du rapport toutes les 30 secondes.
10. Contexte serveur consultatif de Copilot.
11. Construction du livrable final.
12. Validation, publication et retour final dans Git.

## Règle de clôture d'une étape et manuel

Une étape est clôturée lorsque :
- ses composants producteurs et consommateurs sont identifiés ;
- les interfaces et échanges sont raccordés ;
- les autorités et contrôles de sécurité sont respectés ;
- les états, erreurs, fraîcheurs et reprises sont traités ;
- les données durables et les statistiques nécessaires sont traçables ;
- le parcours est validé par des preuves adaptées.

Une étape finale peut regrouper plusieurs patches. Les patches intermédiaires ne créent pas de chapitre prématuré. Une fois l'étape validée, son chapitre est ajouté au manuel organisé dans le même ordre que le parcours d'une requête.

Les noms de composants de cette roadmap désignent des responsabilités logiques. Ils ne certifient pas que chaque responsabilité est déjà implémentée ou raccordée. L'état réel est établi par audit du code courant et par les preuves d'exécution, pas par la seule présence des noms dans ce document.
