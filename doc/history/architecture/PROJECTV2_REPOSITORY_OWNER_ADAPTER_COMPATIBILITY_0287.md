# Adaptateur ProjectV2 compatible `repositoryOwner`

## Défaut

L’adaptateur historique interrogeait en parallèle un utilisateur et
une organisation portant le même login. GitHub rejetait la branche
inexistante avant la résolution de la branche valide.

## Correction sans modifier l’adaptateur historique

`RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter` hérite de
`GitHubCliFinalDeliverablePublicationAdapter`.

Il surcharge uniquement `resolve_project_target()` avec une requête
read-only fondée sur :

```graphql
owner: repositoryOwner(login: $projectOwner)
```

Toutes les autres opérations restent héritées :

- lecture et création du commentaire Issue;
- lecture du champ ProjectV2;
- mutation contrôlée du champ;
- transport GitHub CLI;
- gestion du token;
- contrôle du résultat.

## Compatibilité du contrat pur

Le payload `owner` est normalisé en mémoire vers la forme historique
`user` ou `organization`, puis transmis au résolveur pur existant.
Aucun changement du contrat de domaine n’est nécessaire.

## Câblage

La variante est utilisée dans :

- la résolution read-only pendant `prepare`;
- la publication contrôlée pendant `complete`.

Le fichier exécutable historique reste inchangé et conserve son mode
`100755`.

## Frontières

- aucune seconde implémentation de transport;
- une seule requête owner-polymorphe;
- aucune tentative successive;
- aucune mutation pendant la résolution;
- publication distante toujours soumise au digest et aux gates.
