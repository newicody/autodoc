# Création des artefacts pour chaque nouvelle Issue de recherche

## Frontière

Le déclencheur automatique appartient uniquement au dépôt dédié
`newicody/projects`. Les vues ProjectV2 préparées classent et présentent les
Issues, mais elles ne constituent pas l'autorité du webhook `issues.opened`.

Le formulaire `Nouvelle recherche` fournit les marqueurs immédiatement disponibles :

```text
[Recherche] <titre>
### Question ou objectif
### Résultat attendu
```

Le préfixe est le marqueur principal. Les deux sections obligatoires permettent
de reconnaître une Issue issue du formulaire lorsque son titre a été édité avant
la création.

## Chemin

```text
Issue ouverte dans newicody/projects
→ préfixe [Recherche] ou sections obligatoires du formulaire
→ run Actions initial
→ authoritative_request propre à l'Issue
→ copilot_advisory requis pour le run automatique
→ manifeste et identité corrélés
→ trois artefacts attachés au run
→ premier commentaire Copilot publié par Projects
→ fetch local Autodoc
→ contrôle d'admissibilité
→ Scheduler puis laboratoire si admissible
```

## Isolation

La provenance d'un contenu repose au minimum sur :

```text
repository
issue_number
run_id
request_digest
advisory_digest
manifest_digest
```

Les artefacts ne sont jamais mutualisés entre deux Issues. Un nouveau run de la
même Issue produit une nouvelle génération attachée à ce run et ne remplace pas
les générations précédentes.

## Hors périmètre

Cette unité ne déclenche pas encore le laboratoire. Elle garantit seulement que
chaque nouvelle demande de recherche possède une génération GitHub complète que
le fetch canonique pourra ensuite évaluer.
