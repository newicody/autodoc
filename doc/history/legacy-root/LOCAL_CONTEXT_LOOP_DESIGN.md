# Phase 5.12 — Local context loop design

La Phase 5.12 définit la boucle locale qui doit relier les artefacts E5 de la
Phase 4, l'intake explicite du `ContextEngine` et la décision humaine, sans
encore introduire de daemon, de serveur, de stockage persistant ou d'API GitHub.

Elle ne crée pas de nouvelle surface d'exécution. Elle décrit uniquement le
contrat d'orchestration futur que la CLI locale 5.13 pourra implémenter.

## But

Le but est de rendre explicite le cycle suivant :

```text
question ou demande locale
-> recherche E5 / artifact-dir Phase 4
-> intake explicite ContextEngine
-> status/report
-> décision humaine
-> relance, rejet, archivage, promotion future ou fusion future
```

Cette boucle reste volontairement manuelle. Elle prépare le serveur local futur,
mais elle ne le crée pas.

## Entrées

Une boucle locale peut démarrer depuis plusieurs entrées, mais 5.12 ne les
implémente pas encore :

```text
question libre
requête E5 déjà formulée
artifact-dir Phase 4 existant
source locale future
SourceCandidate future
```

Dans l'état actuel, l'entrée la plus stable est l'`artifact-dir` produit par la
commande E5 existante.

## Artefacts attendus

La boucle locale consomme l'ensemble déterministe déjà stabilisé :

```text
report.json
context.json
consumed_context.json
prompt.json
```

Ces fichiers sont lus par `E5RuntimeArtifactDirectoryLoader`, transformés par le
runtime local E5, attachés à un `InferenceContext`, puis exposés via le
`ContextEngine`.

## Étapes de boucle

### 1. Produire ou sélectionner un artifact-dir

La production de l'artifact-dir reste hors `ContextEngine`. Elle appartient à la
couche `inference/` et à la CLI E5 existante.

```text
./tools/e5.py search ... --artifact-dir /tmp/autodoc_e5_dry_run
```

### 2. Charger les artefacts

La lecture est concentrée dans la bordure IO dédiée :

```text
E5RuntimeArtifactDirectoryLoader
```

Aucune autre couche ne doit relire directement les quatre fichiers JSON.

### 3. Construire le runtime E5 local

Le runtime construit un statut et un `InferenceContext` sans relancer le modèle :

```text
E5LocalContextRuntime
```

### 4. Attacher explicitement au ContextEngine

L'intake est volontaire :

```text
ContextEngine.attach_e5_artifact_dir(...)
ContextEngine.attach_e5_runtime_context(...)
```

Aucun autoload n'est autorisé.

### 5. Inspecter le statut

La boucle produit une projection passive :

```text
E5ContextEngineStatus
```

Cette projection peut être affichée ou écrite en JSON par la CLI existante 5.9.

### 6. Décider humainement

La décision n'est pas encore codée en 5.12. Elle est simplement nommée afin de
préparer `SourceCandidate` :

```text
relancer
rejeter
archiver
promouvoir
fusionner
```

## Non-objectifs

```text
pas de nouvelle CLI en 5.12
pas de serveur
pas de daemon
pas de watcher fichier
pas de polling
pas de réseau
pas d'API GitHub
pas de token
pas de Qdrant
pas de base persistante
pas de LLM de réponse
pas d'appel OpenVINO caché
```

## Contrat de frontière

La boucle locale ne doit pas mélanger production, consommation et décision :

```text
inference/ produit les artefacts
context/ les charge et les attache
ContextEngine expose le contexte courant
CLI affiche ou écrit les rapports
humain valide la prochaine action
```

## Préparation de la Phase 5.13

La Phase 5.13 pourra ajouter une CLI mince qui orchestre les appels existants.
Elle devra rester une façade, pas un nouveau moteur.

Exemple cible non implémenté en 5.12 :

```bash
PYTHONPATH=src python3 -m context.local_context_loop \
  --artifact-dir /tmp/autodoc_e5_dry_run \
  --report-file /tmp/autodoc_loop.json
```

La commande devra s'appuyer sur les contrats existants au lieu de dupliquer la
logique de loader, runtime, attachment ou status.

## Impact architectural

5.12 confirme que le serveur local futur et GitHub doivent se placer au-dessus
de cette boucle, pas à l'intérieur du moteur E5 ni dans le Scheduler.

```text
GitHub future / SourceCandidate future
-> boucle locale contrôlée
-> artifact-dir / ContextEngine intake
-> statut / rapport
-> validation humaine
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.12 formalise une boucle locale documentaire sans nouvelle règle de programmation.
```
