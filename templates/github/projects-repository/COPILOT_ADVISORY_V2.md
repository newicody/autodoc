# Avis Copilot v2 : premier avis borné

Les nouveaux runs produisent `copilot_advisory.json` avec le schéma public
`missipy.github.copilot_advisory.v2`.

Les seuls champs d’analyse sont :

| Champ | Contenu |
|---|---|
| `concrete_objective` | objectif concret de la demande |
| `expected_result` | résultat attendu, distinct du simple sujet de l’Issue |
| `provided_constraints` | contraintes et éléments déjà fournis, sans invention |
| `success_criteria` | conditions de réussite observables et vérifiables |

Les références, empreintes, identifiants de corrélation et drapeaux de confiance
restent des métadonnées de provenance. Ils ne constituent pas une cinquième
analyse.

Les artefacts historiques `missipy.github.copilot_advisory.v1` restent lisibles
pendant la migration locale. Le workflow actif ne doit plus produire de v1 et
ne doit pas recopier ses anciens champs dans v2.

Copilot est consultatif : `trusted=false`, `usable_as_hint=true` et
`usable_as_authority=false`. Toute publication conserve le preview, la décision
opérateur explicite, les deux verrous de mutation, le `plan_digest` exact et le
readback décrits dans `COPILOT_ADVISORY_PUBLICATION.md`.


## Compatibilité d’intake locale

Le serveur local reconnaît explicitement les schémas v1 et v2 pendant la
migration. Il conserve chaque artefact dans sa forme publique d’origine. Ainsi,
aucun champ v1 n’est réinterprété comme objectif, résultat, contrainte ou critère
v2.
Le schéma v2 est validé strictement et tout champ analytique v1 ajouté à un
artefact v2 provoque un rejet fermé.

L’intake ne copie toujours aucun contenu Copilot dans la demande autoritative ou
le `SourceCandidate`. Il conserve seulement la référence, l’empreinte de réponse
et le nom du schéma comme métadonnées consultatives.


## Projection opérateur/laboratoire

Après validation par l’intake local, un artefact v2 devient une projection
consultative versionnée. La projection conserve uniquement :

- `concrete_objective` ;
- `expected_result` ;
- `provided_constraints` ;
- `success_criteria`.

Aucun champ v1 n’est créé, inféré ou renommé. Les références techniques sont
injectées dans l’orientation du laboratoire existant comme contexte
consultatif. Le Scheduler existant reste l’unique autorité d’orchestration.

La publication preview v2 est également distincte de la preview v1. À cette
étape, elle reste une preview locale sans mutation distante. Son rendu Markdown,
son plan digest et son exécution contrôlée sont câblés dans les étapes
suivantes.
