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

## Publication v2 sur le board et l’Issue

La preview `missipy.github.copilot_advisory_publication_preview.v2` est construite
uniquement après validation de la corrélation et des digests des trois artefacts.

Sur ProjectV2, les quatre champs analytiques sont rendus dans `Avis Copilot`.
Le statut `Copilot`, la date, la référence d’artefact et le cycle sont également
projetés. Le chemin v2 ne fabrique pas de route ni de confiance, ne modifie
pas les champs historiques correspondants et relit exactement les cinq champs
écrits après la mutation.

Sur l’Issue source, un commentaire Markdown distinct utilise un marqueur v2, un
plan digest déterministe, une détection de collision et un readback immédiat.
La demande reste l’autorité et Copilot reste consultatif.

## Mode opératoire contrôlé `0287-r7-r6`

Construire la preview v2 à partir des trois artefacts corrélés :

```bash
python scripts/build_copilot_advisory_v2_publication_preview.py \
  --advisory out/copilot_advisory.json \
  --request out/authoritative_request.json \
  --manifest out/dual_artifact_manifest.json \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --output out/copilot_advisory_publication_preview_v2.json
```

Prévisualiser la projection ProjectV2 :

```bash
python scripts/project_copilot_advisory_v2_fields.py \
  --preview out/copilot_advisory_publication_preview_v2.json \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --policy-decision-id "$POLICY_DECISION_ID" \
  --operator-decision approve \
  --updated-date "$(date -I)" \
  --format json
```

L’exécution distante exige les verrous existants :

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true
```

Relancer avec `--execute` et le `--confirm-plan-digest` exact. Le chemin v2
remplit `Avis Copilot`, conserve les champs v1 `Route Copilot` et
`Confiance Copilot`, puis relit les cinq champs réellement écrits.

La publication du commentaire sur l’Issue source reste exécutée depuis le
checkout `newicody/autodoc`. Construire d’abord le plan :

```bash
PYTHONPATH=src:. python \
  tools/publish_github_copilot_advisory_v2_issue_comment_0287.py \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --preview out/copilot_advisory_publication_preview_v2.json \
  --policy-decision-id "$POLICY_DECISION_ID" \
  --operator-decision approve \
  --format json | tee /tmp/copilot-v2-issue-plan.json
```

Extraire `plan.plan_digest`, puis activer le verrou de publication Issue :

```bash
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
```

Relancer la même commande avec `--execute` et le
`--confirm-plan-digest` exact. L’adapter relit le commentaire créé, refuse les
collisions et transforme un replay strictement identique en no-op.
