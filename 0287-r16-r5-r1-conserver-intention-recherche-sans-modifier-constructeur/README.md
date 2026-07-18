# 0287 r16-r5-r1 — conserver l'intention de recherche sans modifier le constructeur

## Objet

Le patch précédent modifiait directement
`templates/github/scripts/build_autodoc_authoritative_request.py` et ne pouvait
pas s'appliquer sur le checkout courant. Cette révision ne touche plus ce fichier.

Elle ajoute une étape explicite après la construction générique de la demande :

```text
construction authoritative_request
→ validation de l'événement contrôlé
→ ajout requested_status / request_mode / parent_event_ref dans metadata
→ Copilot
→ manifeste
```

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r16-r5-r1-conserver-intention-recherche-sans-modifier-constructeur \
  --commit \
  --push \
  --allow-dirty
```

Le patch r16-r5 précédent a échoué à `git apply --check`; il n'est donc pas à
annuler avant cette révision.

## Synchronisation de `newicody/projects`

Après réussite dans Autodoc, recopier le workflow et le nouveau script dans le
dépôt dédié :

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects

install -Dm644 \
  "$AUTODOC/templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml" \
  "$PROJECTS/.github/workflows/autodoc-controlled-research.yml"

install -Dm755 \
  "$AUTODOC/templates/github/projects-repository/scripts/enrich_authoritative_request_research_intention.py" \
  "$PROJECTS/scripts/enrich_authoritative_request_research_intention.py"
```

Le workflow exécute le script depuis le checkout `autodoc-runtime`; la copie du
script dans `newicody/projects` maintient néanmoins le bundle installé complet et
auditable.
