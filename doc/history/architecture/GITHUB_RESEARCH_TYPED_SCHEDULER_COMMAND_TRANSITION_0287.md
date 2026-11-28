# Transition vers une commande Scheduler typée — 0287 r16-r24-r1

## Décision

Le stockage JSONL introduit en r16-r24 n’est pas retenu comme chemin canonique
de la recherche GitHub. Il reste présent uniquement pour la compatibilité
historique du chemin 0179 et pour ne pas réécrire l’historique des patchs.

La CLI r16-r24 refuse désormais ce chemin par défaut. Son usage exige l’option
explicite `--allow-legacy-filesystem-handoff` et reste réservé aux contrôles de
compatibilité.

La chaîne cible devient :

```text
triplet GitHub JSON validé
-> intake autorisé
-> désérialisation à la frontière
-> GitHubResearchSchedulerCommand (classes immuables)
-> adaptateur PostgreSQL (unité suivante)
-> Scheduler canonique
-> handler laboratoire
```

## Modèle objet

L’héritage exprime uniquement la spécialisation réelle :

```text
SchedulerCommand
└── AuthorizedSchedulerCommand
    └── GitHubResearchSchedulerCommand
```

La commande compose des objets séparés :

- `SchedulerAuthorization` ;
- `GitHubResearchCorrelation` ;
- `GitHubResearchPayload` ;
- `ResearchExecutionBudget` ;
- `SchedulerRouteRequest`.

Les listes de contexte et de preuves deviennent des tuples validés. Le digest
de commande est calculé sur les champs typés avec un encodage longueur-valeur
stable ; il ne dépend pas d’une sérialisation JSON.

L’identité est déterministe : `issued_at` provient du
`SchedulerRouteRequest.requested_at` déjà autorisé, et non de l’heure à laquelle
un opérateur relance la commande de diagnostic. Un rejeu du même intake et du
même budget produit donc le même `command_ref` et le même digest.

## Budget borné

La recherche porte obligatoirement un `ResearchExecutionBudget` explicite :

- nombre maximal d’étapes Scheduler ;
- nombre maximal de visites de spécialistes ;
- durée murale maximale.

Le budget participe au digest. Toute modification du budget produit une autre
commande, explicitement traçable.

## Frontières

- JSON est accepté pour lire le rapport temporaire issu de GitHub.
- `to_mapping()` est uniquement une projection de test, de CLI ou d’audit.
- aucune file interne n’est écrite par le constructeur typé ;
- aucune écriture SQL n’est encore effectuée ;
- `GitHubResearchSchedulerCommandStore` fixe le port que l’adaptateur PostgreSQL
  devra implémenter ;
- Scheduler, Dispatcher, EventBus, ControlProxy et laboratoire ne sont pas
  appelés dans cette unité.

## Métaclasse

Aucune métaclasse n’est ajoutée dans cette transition : aucun registre dynamique
de types de commandes n’est encore nécessaire. Introduire une métaclasse ici
masquerait les contrats sans apporter de capacité. Une métaclasse ou un registre
ne pourra être ajouté que lorsque plusieurs types de commandes devront être
résolus dynamiquement par le noyau, avec collision de schéma contrôlée et tests
dédiés.

## Transition

Le chemin canonique r16-r24 est neutralisé sans supprimer le mécanisme historique
0179. L’unité suivante implémentera la persistance relationnelle et idempotente
du port PostgreSQL. Une unité ultérieure fera réclamer cette commande au
Scheduler local déjà actif.
