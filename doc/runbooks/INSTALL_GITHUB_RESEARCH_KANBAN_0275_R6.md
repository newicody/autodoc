# Installation du Kanban de recherche GitHub — préparation 0275-r6

## Portée

Cette procédure configure manuellement le dépôt de gestion
`newicody/projects` et le GitHub Project associé.

0275-r6 n'installe aucun watcher, service OpenRC ou mutation GitHub. Les
déclenchements réels par changement de colonne seront ajoutés par les patchs
0275-r7 à 0275-r12.

## 1. Sauvegarder l'existant

Avant nettoyage, relever :

- le nom du Project ;
- les vues existantes ;
- les champs existants ;
- les automatisations actives ;
- le numéro du Project ;
- l'URL du dépôt `newicody/projects`.

Ne supprimer aucune issue.

## 2. Nettoyer les anciennes vues

Dans le GitHub Project :

1. ouvrir chaque vue technique créée pendant les essais ;
2. supprimer les vues qui exposent `AutodocStage`, `Laboratory`, `Decision`,
   `Qdrant`, `SQL`, `Scheduler` ou une phase serveur ;
3. conserver provisoirement une vue Table non filtrée pour ne perdre aucun
   élément pendant la migration.

## 3. Nettoyer les champs

Conserver les champs natifs GitHub.

Créer ou renommer deux champs personnalisés seulement.

### Champ `Status`

Type :

```text
Single select
```

Valeurs, dans cet ordre :

```text
Recherche
En cours
Terminé
Développement
Production
Drop
```

### Champ `Thème`

Pour permettre des thèmes libres, préférer un champ texte si l'interface du
Project permet de grouper la vue Board par ce champ.

Si le Board courant ne permet le groupement que par sélection unique, utiliser
temporairement un champ `Single select` avec seulement les thèmes réellement
utiles. Ajouter les thèmes au fil des besoins, sans taxonomie serveur.

Le champ reste facultatif.

Supprimer ou masquer des vues les anciens champs techniques. Ne les supprimer
définitivement qu'après vérification qu'aucune donnée humaine utile n'y réside.

## 4. Créer la vue principale

Créer une vue :

```text
Nom         : Recherches
Disposition : Board
Colonnes    : Status
Groupement  : Thème
```

Afficher au minimum :

- titre ;
- personnes assignées ;
- labels si utilisés ;
- date de mise à jour.

Ne pas afficher les champs techniques du serveur.

## 5. Créer les vues complémentaires

### `Résultats`

```text
Disposition : Table
Filtre      : Status = Terminé
```

### `Sans thème`

Créer une vue sans groupement. Filtrer sur les tickets dont `Thème` est vide
si l'interface le permet.

### `Historique`

```text
Disposition : Table
Filtre      : Status = Terminé OU Étape = Drop
```

## 6. Configurer l'ajout automatique

Dans les workflows intégrés du Project, conserver ou créer l'auto-ajout des
issues provenant de :

```text
newicody/projects
```

Une nouvelle issue doit être ajoutée au Project sans lancer immédiatement une
recherche.

Définir sa valeur initiale `Status` à une valeur non déclenchante si GitHub
l'exige. Tant que le champ ne propose pas de colonne Brouillon, laisser
l'élément sans valeur puis le déplacer manuellement vers `Recherche`,
`Développement` ou `Production` au moment voulu.

## 7. Ne pas activer encore les déclenchements de colonnes

Le workflow actuel peut encore réagir à `issues.opened` ou `issues.edited`.

Avant utilisation opérationnelle, 0275-r7 devra le remplacer par un workflow
contrôlé. Jusqu'à ce patch :

- ne pas considérer le déplacement de carte comme connecté au serveur ;
- ne pas ajouter de token d'écriture ;
- ne pas installer de service OpenRC ;
- ne pas contourner le garde-fou interdisant l'ingestion de `newicody/autodoc`.

## 8. Préparer un ticket de test

Créer une issue dans `newicody/projects` :

```text
Titre :
Test du modèle de recherche durable

Corps :
## Question d'origine

Vérifier que le ticket conserve la même identité sur plusieurs cycles.

## Contexte et paramètres actuels

Premier cadrage du test.

## Recherches liées

- aucune

## Médias et documents

- aucun

## Inférence externe

- [ ] Lancer également une inférence sur un moteur externe

## Exclusions pour le prochain cycle

- [ ] Exclure le résultat du cycle précédent
- [ ] Exclure les anciens commentaires
- [ ] Exclure les anciennes pièces jointes
- [ ] Exclure les recherches liées
- [ ] Exclure les résultats d'inférence externe
- [ ] Condenser les anciens cycles
- [ ] Utiliser un contexte minimal
```

Attribuer éventuellement un `Thème`, puis déplacer la carte entre les colonnes
pour vérifier uniquement le rendu visuel du Board.

## 9. Critères de réussite de l'installation préparatoire

```text
repository_management = newicody/projects
development_repository = newicody/autodoc
project_has_field_Status = true
project_has_optional_field_Theme = true
board_columns_match_contract = true
board_can_group_by_theme = true
technical_server_fields_hidden = true
new_issue_auto_added = true
column_trigger_runtime_installed = false
github_write_token_required = false
openrc_service_installed = false
```

## 10. Application du patch Autodoc

Depuis `/home/eric/projet/git/autodoc` :

```bash
unzip -o /mnt/data/0275-r6-github_research_kanban_operator_model.zip

python apply_patch_queue.py \
  --patch 0275-r6-github_research_kanban_operator_model \
  --dry-run \
  --allow-dirty
```

Après un dry-run vert :

```bash
python apply_patch_queue.py \
  --patch 0275-r6-github_research_kanban_operator_model \
  --commit \
  --allow-dirty
```

Validation :

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_github_research_kanban_operator_model_0275_r6_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules

PYTHONPATH=src:. python -m pytest -q
```

Arrêter la série au premier échec. Ne pas appliquer 0275-r7 avant validation
complète de 0275-r6.
