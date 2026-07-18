# Conservation de l'intention de recherche

## Problème

Le constructeur générique de demande autoritative connaît l'Issue GitHub mais ne
doit pas devenir responsable des choix de workflow propres à `newicody/projects`.
Le workflow contrôlé possède pourtant trois informations nécessaires au serveur :

```text
requested_status
request_mode
parent_event_ref
```

## Solution

Une étape explicite, exécutée immédiatement après la construction de la demande,
valide l'événement contrôlé puis ajoute ces valeurs dans le dictionnaire
`metadata` déjà prévu par le schéma v1.

```text
Issue lue
→ événement contrôlé
→ demande autoritative générique
→ enrichissement de provenance
→ avis Copilot
→ manifeste
→ artefacts
```

L'enrichissement refuse :

- un dépôt différent ;
- un numéro d'Issue différent ;
- un statut ou un mode inconnu ;
- une valeur de métadonnée déjà présente mais contradictoire.

## Frontières

Cette unité ne modifie pas le constructeur générique et ne touche ni au
Scheduler, ni au laboratoire, ni à SQL, ni à Qdrant. Elle ne décide pas encore
si une demande est admissible : elle fournit seulement une provenance explicite
et vérifiée à l'unité suivante.
