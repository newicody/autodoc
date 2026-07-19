# Démarrage d’un cycle GitHub de recherche propre

## Objectif

Le cycle précédent contenait deux triplets complets sous un même `run_id`.
La cause opérationnelle à éviter est le cumul de plusieurs déclenchements pour
la même demande.

Le lanceur :

```text
tools/start_clean_github_research_cycle_0287.py
```

utilise uniquement l’événement `issues: opened`.

## Pourquoi l’ouverture d’Issue

Le workflow Projects existant transforme déjà cet événement en :

```text
requested_status = Recherche
request_mode = initial
parent_event_ref = ""
```

Une Issue conforme est donc plus sûre qu’un second `workflow_dispatch`.

## Forme obligatoire

Le titre commence par :

```text
[Recherche]
```

Le corps contient :

```text
### Question ou objectif
### Résultat attendu
```

Le lanceur ajoute un marqueur stable :

```html
<!-- autodoc-cycle-ref:<cycle-ref> -->
```

## Deux phases

### Plan

Le mode plan :

- ne contacte pas GitHub;
- calcule le SHA-256 du corps marqué;
- produit un digest de plan;
- ne crée aucune Issue ni aucun item.

### Exécution

Le mode exécution exige :

```text
AUTODOC_REMOTE_MUTATION_ALLOWED=true
AUTODOC_ISSUE_CREATION_ALLOWED=true
AUTODOC_PROJECT_PROJECTION_ALLOWED=true
```

et le digest exact du plan.

Il effectue ensuite :

```text
snapshot des runs issues existants
→ création de l’Issue
→ ajout au ProjectV2
→ découverte d’un unique nouveau run issues
→ attente de conclusion success
→ vérification d’exactement trois artefacts
```

## Arrêt de frontière

Le lanceur s’arrête avant :

- le fetch local;
- SQL;
- Qdrant;
- Scheduler;
- laboratoire;
- publication finale.

Le `run_id` produit devient l’entrée du fetch canonique local.

## Absence de double déclenchement

Aucun `workflow_dispatch` n’est envoyé. Si plusieurs nouveaux runs correspondent
malgré tout au titre créé, le cycle échoue fermé et conserve les identités
distantes déjà observées dans le rapport.
