# Interface GitHub finale Résultats / Actualisations — 0275-r9

## Décision

Le Project présente deux surfaces principales :

```text
Résultats       = uniquement les résultats courants
Actions serveur = nouvelles recherches et actualisations
```

Les sources restent des références dans les formulaires et les issues. Elles
ne sont pas transformées en cartes du Board principal.

## Recherche

Une issue `[Recherche]` commence avec :

```text
Type = Recherche
Affichage = Action
```

Après publication réussie, la même issue devient :

```text
Affichage = Résultat courant
```

Cette transformation évite la création d'une issue de résultat supplémentaire.

Un résultat parent facultatif établit la filiation. Les résultats liés restent
des liens de contexte complémentaires.

## Actualisation

Une issue `[Actualisation]` reste une action séparée. Elle cible un résultat
existant et ajoute un commentaire UPDATE immuable avec :

```text
date et heure
nouveaux paramètres
nouvelles références
résultat serveur
avis Copilot
provenance
```

L'actualisation met à jour le résumé visible de la carte cible, sans réécrire
ni supprimer l'historique antérieur.

## Sources

```text
groupes
tickets
résultats liés par URL
dépôts
révisions
chemins internes
pièces jointes
liens externes
```

`newicody/autodoc` reste le dépôt source du logiciel et ne devient jamais une
source de connaissance à ingérer.

## Accessibilité

Les cartes montrent des états textuels et deux résumés courts. Le clic ouvre
le panneau de l'issue complète. Les sections longues sont repliables.

## Frontière

Cette phase modifie uniquement les templates, la documentation et les tests de
règles. La collecte, la publication, le reparentage, la mise à jour des champs
Project et la fermeture des issues restent différés.
