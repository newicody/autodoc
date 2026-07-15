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
