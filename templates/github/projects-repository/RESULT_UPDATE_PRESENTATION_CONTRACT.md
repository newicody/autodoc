# Contrat de présentation Résultat / UPDATE — 0275-r9

## Nature des issues

```text
[Recherche]     = action puis résultat courant sur la même issue
[Actualisation] = action séparée visant un résultat existant
[Groupe]        = référence de contexte sans traitement direct
```

## Références d'une recherche

```text
result_parent_ref
related_result_refs[]
group_refs[]
issue_refs[]
repository_sources[]
  repository
  revision
  paths[]
attachment_refs[]
external_links[]
parameters
context_mode
copilot_requested
```

`result_parent_ref` établit la filiation principale. Les
`related_result_refs[]` sont seulement des liens de contexte. Aucun contenu de
résultat n'est copié dans le formulaire et aucune carte supplémentaire n'est
créée dans le Board.

## Résultat courant

Après traitement réussi d'une issue `[Recherche]`, la même issue devient le
résultat courant.

Corps ou commentaire de publication attendu :

```markdown
## Résultat courant

Résultat serveur complet.

## Résumé opérationnel

Résumé court destiné à la carte du Board.

<details>
<summary>Avis Copilot</summary>

Avis Copilot complet.

</details>

<details>
<summary>Sources et provenance</summary>

Références exactes, révisions, chemins et artefacts.

</details>
```

Les champs Project reflètent le dernier état :

```text
Affichage = Résultat courant
Résumé
Avis Copilot
Serveur
Copilot
Dernière mise à jour
```

## Filiation

Lorsqu'un `result_parent_ref` est fourni :

```text
nouvelle issue résultat = Résultat courant
ancien résultat parent  = Historique
```

La publication et la relation GitHub seront ajoutées par une phase ultérieure.
0275-r9 verrouille seulement le contrat d'interface.

## Actualisation append-only

Une issue `[Actualisation]` cible un résultat existant. Elle ne crée pas de
nouveau parent et ne remplace aucun commentaire antérieur.

Le publisher futur ajoute un commentaire :

```markdown
## UPDATE — 2026-07-13 23:42 Europe/Paris

### Nouveaux paramètres

Paramètres fournis par l'utilisateur.

### Nouvelles références

Groupes, tickets, résultats liés, dépôts, révisions, chemins, pièces jointes
et liens ajoutés pour cette actualisation.

### Résultat serveur

Contenu complet de l'actualisation.

<details>
<summary>Avis Copilot de cette actualisation</summary>

Avis Copilot complet.

</details>

<details>
<summary>Artefacts et provenance</summary>

Références techniques et artefacts.

</details>
```

Le timestamp canonique est conservé en ISO 8601 UTC. L'affichage humain utilise
la date et l'heure `Europe/Paris`.

Après publication, les champs visibles du résultat cible sont actualisés avec
le dernier résumé et la date la plus récente. L'historique reste intact sous
forme de commentaires UPDATE successifs.

## Accessibilité

- titre explicite ;
- résumés courts lisibles sur la carte ;
- états Serveur et Copilot écrits en texte ;
- résultat complet accessible en cliquant sur la carte ;
- sections longues repliables ;
- aucune information portée uniquement par une couleur.

## Projection Copilot contrôlée — 0284-r1-r4

Le workflow producteur ne publie ni commentaire ni valeur ProjectV2. Après
validation opérateur :

```text
publication_preview 0281
→ commentaire d'Issue idempotent
→ projection du dernier état dans les champs Copilot
```

La projection ProjectV2 est un read-model consultatif. Elle ne peut pas écrire
les champs d'autorité locale :

```text
Résumé
Serveur
```

Les anciens avis restent dans les commentaires append-only. Les champs
`Avis Copilot`, `Route Copilot`, `Confiance Copilot`, `Copilot`, `Artefact` et
`Cycle` reflètent uniquement le dernier avis approuvé pour l'affichage.
