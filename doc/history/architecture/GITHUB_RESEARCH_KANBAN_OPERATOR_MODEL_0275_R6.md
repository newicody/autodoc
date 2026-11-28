# Modèle opérateur du Kanban de recherche GitHub — 0275-r6

## Objet

Cette phase verrouille le modèle utilisateur du dépôt de gestion
`newicody/projects` et du GitHub Project personnel associé.

Le Project n'expose pas l'architecture interne d'Autodoc. Il sert uniquement à :

- créer et organiser des demandes ;
- déplacer des tickets entre des colonnes compréhensibles ;
- regrouper visuellement plusieurs tickets sous un thème facultatif ;
- relancer une recherche durable sur le même ticket ;
- lier d'autres recherches, documents, médias et sources ;
- demander facultativement une inférence externe ;
- réduire explicitement le contexte du prochain cycle sans effacer l'historique.

Cette phase est documentaire. Elle n'ajoute aucun runtime, handler, adapter,
manager, daemon, Scheduler, worker, backend, appel réseau ou mutation GitHub.

## Modèle utilisateur canonique

```text
ligne facultative = Thème
carte              = ticket de recherche durable
colonne            = Status et intention opérateur
cycle              = nouvelle exécution du même ticket
lien #issue        = autre recherche disponible comme contexte
case cochée        = exclusion explicite du prochain cycle
```

### Ticket durable

Un ticket représente une question ou un objectif durable. Il conserve la même
identité GitHub pendant toute son évolution.

Une relance ne crée pas automatiquement une nouvelle issue ou une sous-issue.
Elle crée un nouveau cycle local rattaché au même ticket.

```text
newicody/projects#18
├── cycle 1
├── cycle 2
├── cycle 3
└── cycle 4
```

L'identité de la question d'origine reste stable. Les paramètres, commentaires,
liens, médias et consignes du prochain cycle peuvent évoluer.

### Thème facultatif

Le champ Project `Thème` crée les groupes horizontaux du Board. Un thème peut
contenir plusieurs tickets indépendants.

Exemples :

```text
Chalouf
Architecture réseau
Modèles d'inférence
Documentation
Sans thème
```

Le thème est une organisation visuelle. Il ne crée pas une parenté entre les
tickets et ne sélectionne aucun laboratoire ou spécialiste.

Une recherche peut rester sans thème.

### Status

Le champ Project `Status` forme les colonnes du Board.

Valeurs retenues :

```text
Recherche
En cours
Terminé
Développement
Production
Drop
```

Sémantique :

- `Recherche` : demander un nouveau cycle de recherche sur le ticket ;
- `En cours` : le cycle a été pris en charge ;
- `Terminé` : le résultat courant est accepté ou conservé ;
- `Développement` : demander un cycle orienté conception ou implémentation ;
- `Production` : demander un cycle orienté préparation, validation ou livraison ;
- `Drop` : arrêter le traitement sans supprimer l'historique.

Les colonnes `Recherche`, `Développement` et `Production` sont des intentions
opérateur. Les autres colonnes décrivent un état et ne doivent pas créer seules
un nouveau cycle.

Une transition ne doit être traitée qu'une fois. Une carte laissée dans la même
colonne ne redéclenche rien.

## Cycles successifs

Un nouveau cycle reprend par défaut :

- la question d'origine ;
- les paramètres actuels ;
- les résultats des cycles précédents ;
- les commentaires pertinents ;
- les recherches liées ;
- les médias et pièces jointes ;
- les nouvelles consignes depuis le dernier cycle.

Le serveur attribue un numéro de cycle et conserve une filiation immuable :

```text
research_issue_ref
cycle_ref
cycle_number
previous_cycle_ref
requested_stage
ticket_revision_ref
```

GitHub reste l'interface opérateur. SQL reste l'autorité durable de l'historique
des cycles.

## Recherches liées

Un ticket peut citer d'autres recherches avec des références GitHub ou des URL.

```markdown
## Recherches liées

- #12
- #24
- https://github.com/newicody/projects/issues/41
```

Ces recherches deviennent des sources de contexte disponibles. Elles peuvent
appartenir à un autre thème. Un lien n'implique ni parenté, ni fusion, ni
changement de thème.

Le collecteur futur doit préserver la provenance de chaque référence.

## Médias et pièces jointes

Le ticket et ses commentaires peuvent contenir :

- images ;
- PDF ;
- fichiers texte ;
- archives ;
- audio ou vidéo ;
- URL externes.

L'artefact doit d'abord transporter des références typées et leur provenance.
Le téléchargement est soumis à une politique distincte de type, taille,
autorisation et intégrité. Aucun média n'est implicitement ingéré sans cette
politique.

## Inférence externe facultative

Le formulaire de ticket peut proposer :

```text
[ ] Lancer également une inférence sur un moteur externe
```

Cette case exprime uniquement une intention :

```text
external_inference_requested = true|false
```

Elle ne choisit pas directement un fournisseur, un modèle, un secret ou un
budget. Le serveur applique ensuite une politique explicite portant notamment
sur l'autorisation, la confidentialité, le coût, le modèle disponible et la
borne de ressources.

## Réduction du contexte du prochain cycle

La règle par défaut est :

```text
tout élément historique reste disponible
```

L'utilisateur peut cocher des exclusions applicables uniquement au prochain
cycle.

Options globales prévues :

```text
[ ] Exclure le résultat du cycle précédent
[ ] Exclure les anciens commentaires
[ ] Exclure les anciennes pièces jointes
[ ] Exclure les recherches liées
[ ] Exclure les résultats d'inférence externe
[ ] Condenser les anciens cycles
[ ] Utiliser un contexte minimal
```

Des exclusions précises peuvent aussi viser :

- un cycle antérieur ;
- une recherche liée ;
- une pièce jointe ;
- un commentaire ou groupe de commentaires ;
- un résultat externe.

Une exclusion ne supprime rien. Elle ne modifie pas l'historique durable et ne
s'applique pas automatiquement au cycle suivant.

La question d'origine et la demande courante restent toujours identifiables,
même en mode minimal.

## Champs publics autorisés dans le Project

Le modèle minimal contient uniquement :

```text
Status
Thème
```

Les champs natifs GitHub restent utilisables, notamment le titre, les personnes
assignées, les labels, la date de mise à jour et le dépôt.

Les notions suivantes ne doivent pas être projetées dans l'interface publique :

- Scheduler ;
- laboratoire ;
- spécialiste ;
- SQL ;
- Qdrant ;
- OpenVINO ;
- backend ;
- route interne ;
- phase serveur ;
- état technique d'orchestration.

## Vue principale

Configuration canonique :

```text
Nom         : Recherches
Disposition : Board
Colonnes    : Status
Groupement  : Thème
```

Le groupement par `Thème` peut être désactivé dans une vue dédiée aux recherches
non orientées.

```text
                    Recherche  En cours  Terminé  Développement  Production  Drop
Chalouf             #12        #18       #9
Architecture réseau #31        #27                  #22
Sans thème          #52
```

## Vues complémentaires minimales

```text
Recherches
Résultats
Sans thème
Historique
```

- `Recherches` : Board principal, groupé par `Thème` ;
- `Résultats` : table filtrée sur `Status = Terminé` ;
- `Sans thème` : vue sans groupement ou filtrée sur thème vide ;
- `Historique` : table incluant `Terminé` et `Drop`.

Aucune vue ne doit refléter l'architecture interne du serveur.

## Frontière GitHub / serveur

```text
GitHub Project
→ interface humaine, cartes, colonnes, thèmes

Issue
→ question durable, paramètres, liens, médias, exclusions

GitHub Actions
→ artefact autoritatif et avis Copilot séparé

Serveur local
→ détection de transition, création du cycle, contexte effectif, traitement

SQL
→ autorité durable de l'historique

GitHub
→ restitution et synchronisation contrôlées, jamais autorité durable
```

## Déclenchements futurs

Les transitions visées sont :

```text
* -> Recherche      = nouveau cycle de recherche
* -> Développement  = nouveau cycle de développement
* -> Production     = nouveau cycle de production
* -> Drop           = arrêt sans nouveau cycle
```

La détection doit comparer l'état Project courant à un état local durable et
idempotent. Elle ne doit pas dépendre d'un label caché ni d'une modification
automatique à l'ouverture de l'issue.

## Réutilisation obligatoire

Les phases suivantes doivent auditer et réutiliser en priorité :

- le lecteur ProjectV2 query-only 0272 ;
- le diff de snapshots ProjectV2 0272 ;
- le handoff `SourceCandidate` existant ;
- les builders GitHub d'artefacts existants ;
- le fetch-once GitHub Actions existant ;
- le manifeste de pièces jointes et son fetch contrôlé ;
- les frontières Scheduler, Handler et Dispatcher existantes ;
- le store SQL et les surfaces de recall déjà validés.

Aucun nouveau manager, orchestrateur, Scheduler, EventBus, worker ou daemon ne
doit être introduit sans preuve qu'aucune surface existante ne convient.

## Séquence de migration avant reprise des laboratoires

```text
0275-r6  modèle opérateur et plan d'installation
0275-r7  bundle du dépôt newicody/projects : formulaire + workflow contrôlé
0275-r8  contrat autoritatif enrichi : cycles, liens, médias, exclusions
0275-r9  collecteur lecture seule : issue, commentaires, refs et pièces jointes
0275-r10 détecteur idempotent des transitions Status
0275-r11 déclenchement contrôlé, corrélation du run et récupération des artefacts
0275-r12 wrapper OpenRC réutilisant les surfaces existantes
0275-r13 restitution locale minimale et preview GitHub
0276     publication GitHub contrôlée et mutations gouvernées
0277     laboratoire Autodoc natif
0278     laboratoires externes
0279     première recherche complète, dont Chalouf peut être le cas pilote
```

Chaque patch reste atomique et validé avant le suivant.

## Revue de code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: phase documentaire conforme aux frontières existantes
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependencies_added: false
scheduler_modified: false
scheduler_run_modified: false
remote_mutation_added: false
```
