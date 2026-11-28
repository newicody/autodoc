# Lanceur opérationnel du cycle complet GitHub

## But

Le lanceur r16-r20 transforme la composition r16-r19 en commande exploitable
sans reconstruire les infrastructures existantes.

Il réutilise :

- le rapport du fetch GitHub Actions;
- le chargeur local des trois artefacts;
- une fabrique de runtime déjà installée;
- la lease process-locale existante;
- le lecteur Qdrant de référence fourni par le runtime;
- la composition r16-r19;
- l’adaptateur `gh` de publication r16-r17;
- la clôture SQL r16-r18.

## Deux commandes et aucun recalcul

### Préparation

```text
fetch-cycle-report
+ run-id
+ runtime factory
+ reference-point reader factory
→ chargement des trois artefacts
→ acquisition des ports existants
→ exécution locale r16-r19
→ fermeture de la lease
→ prepared.json
→ publication_plan_digest
```

Aucune mutation Issue ou ProjectV2 n’est effectuée.

### Finalisation

```text
prepared.json
+ digest exact confirmé
+ runtime factory
+ trois verrous d’environnement
→ reconstruction du plan typé depuis le JSON
→ adaptateur gh existant
→ publication et readback
→ preuve SQL r16-r18
→ cycle_status=closed
```

Les analyses, projections, rappel, synthèse et livrable final ne sont pas
recalculés pendant `complete`.

## Injection du runtime

Le paramètre :

```text
--runtime-factory module:function
```

charge une fonction conforme à `ImportedActionsRuntimeFactory`. Cette fabrique
doit retourner les ports existants ou une `ImportedActionsRuntimeLease`.

Le lanceur ne crée donc aucun :

- Scheduler;
- Dispatcher;
- EventBus;
- magasin PostgreSQL;
- client Qdrant;
- runtime OpenVINO;
- laboratoire.

Le paramètre :

```text
--reference-point-reader-factory module:function
```

retourne le lecteur déjà lié à la collection Qdrant réelle.

## Chargement des artefacts

Le lanceur réutilise les fonctions du chargeur
`assemble_fetched_github_research_admissibility_0287.py` :

- validation du rapport de fetch;
- sélection exacte du `run_id`;
- résolution du rapport de scan et de l’état local;
- refus des liens symboliques;
- contrôle de taille;
- chargement exact de :
  - `authoritative_request.json`;
  - `copilot_advisory.json`;
  - `dual_artifact_manifest.json`.

## Fichiers de résultat

Le rapport `prepare` contient :

- le `ready_run`;
- tous les stages sérialisables;
- le livrable final SQL;
- le plan de publication;
- le digest à confirmer;
- le reçu de fermeture de la lease.

Le rapport `complete` contient :

- la publication distante relue;
- la preuve SQL;
- la révision de clôture;
- le reçu de fermeture du runtime.

Aucune valeur secrète n’est sérialisée.

## Frontière de sécurité

`complete` vérifie le digest avant même d’acquérir le runtime.

La mutation distante reste soumise à :

```text
AUTODOC_REMOTE_MUTATION_ALLOWED=true
AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
AUTODOC_PROJECT_PROJECTION_ALLOWED=true
operator_decision=approve
confirm_plan_digest=<digest exact>
```

## Limite volontaire

r16-r20 reçoit encore explicitement :

- `project_item_id`;
- `project_field_ref`;
- `project_field_name`.

La résolution automatique depuis l’Issue sera un durcissement séparé après le
premier cycle réel. Elle ne doit pas être ajoutée au lanceur en dupliquant les
requêtes ProjectV2 existantes.
