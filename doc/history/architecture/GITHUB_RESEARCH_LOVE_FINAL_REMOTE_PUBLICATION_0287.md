# Publication contrôlée du livrable final vers Issue et ProjectV2

## But

Cette unité relie le livrable durable r16-r16 au mécanisme de publication déjà
présent :

```text
livrable final SQL relu exactement
+ synthèse de liaison r16-r15
→ validation de la lignée
→ adaptation au contrat r12/r13 existant
→ plan déterministe
→ commentaire Issue marqué
→ projection d’un champ ProjectV2
→ prévisualisation par défaut
→ exécution sous verrous
→ relecture distante exacte
```

## Réutilisation

Aucun nouveau client GitHub n’est créé. L’unité réutilise :

- `plan_love_final_deliverable_publication`;
- `execute_love_final_deliverable_remote_publication`;
- `verify_love_final_deliverable_publication_readback`;
- `GitHubCliFinalDeliverablePublicationAdapter`, via l’outil existant
  `tools/publish_love_final_deliverable_0287.py`.

Le nouveau plan place le plan canonique sous la clé `publication_plan`.
L’analyseur de l’outil existant accepte déjà cette enveloppe.

## Lignée validée

La préparation vérifie :

- résultat SQL r16-r16 valide et `persisted`;
- relecture SQL finale confirmée;
- paquet final marqué `final_publication_ready=true`;
- provenance spécialiste masquée sur la surface finale;
- digest de liaison identique à r16-r15;
- références des deux analyses identiques;
- objet, artefact, paquet et révision conformes au reçu SQL;
- destination exacte `github:<repository>#<issue_number>`;
- absence de publication distante déjà déclarée.

## Plan Issue

Le commentaire utilise le marqueur déterministe existant :

```text
autodoc:final-deliverable:<digest>
```

L’exécuteur distingue :

- création;
- rejeu identique;
- collision si le même marqueur porte un autre corps.

## Projection ProjectV2

Une valeur concise est projetée dans le champ explicitement résolu, par défaut
`Résumé` :

```text
Livrable final prêt — <titre> — <artifact_ref>
```

Le champ, l’item et la valeur sont relus exactement après mutation.

## Verrous

La mutation exige simultanément :

```text
--execute
operator_decision = approve
AUTODOC_REMOTE_MUTATION_ALLOWED=true
AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
AUTODOC_PROJECT_PROJECTION_ALLOWED=true
--confirm-plan-digest <digest exact>
```

La prévisualisation reste le comportement par défaut.

## Rejeu et exécution partielle

Le commentaire est créé avant la projection ProjectV2. Si la seconde mutation
échoue, le résultat indique `partial`. Un rejeu relit le commentaire marqué,
le reconnaît comme identique, puis reprend seulement la projection manquante.

La publication n’est confirmée qu’après relecture exacte des deux surfaces.

## Utilisation opérationnelle

Préparer le plan :

```bash
python tools/plan_github_research_love_final_publication_0287.py \
  --final-deliverable /tmp/r16-r16-final.json \
  --liaison /tmp/r16-r15-liaison.json \
  --repository newicody/projects \
  --issue-number 15 \
  --policy-decision-id policy:github-love-final-15 \
  --operator-decision approve \
  --project-item-id '<PROJECT_ITEM_ID>' \
  --project-field-ref '<RESUME_FIELD_ID>' \
  --project-field-name 'Résumé' \
  --output /tmp/r16-r17-publication-plan.json
```

Prévisualiser avec l’adaptateur existant :

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/r16-r17-publication-plan.json \
  --operator-decision approve \
  --format json
```

Exécuter ensuite avec le digest lu dans la prévisualisation et les trois
variables d’autorisation.

## Frontières

Cette unité ne modifie ni SQL, ni Qdrant, ni Scheduler, ni laboratoire. Elle
n’introduit aucun transport parallèle et conserve l’adaptateur `gh` existant.
