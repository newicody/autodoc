# Phase 4.12-r2 — audit de style code_rule préservé

## Résumé

La première proposition 4.12 a trop réécrit `doc/code_rule.md` et a donné trop de place à l'idée d'outillage CLI hors kernel.
Cette révision r2 corrige la trajectoire : l'ancien `doc/code_rule.md` reste le socle normatif.

La Phase 4.12-r2 ajoute seulement un addendum court pour appliquer les règles existantes aux phases E5 4.2 → 4.11.

## Décision de doctrine

Les outils CLI E5 ne sont pas une exception à la philosophie du noyau.
Ils sont des adaptateurs temporaires dont le cœur doit déjà être écrit comme un futur composant pilotable par événement.

Règle retenue :

```text
CLI -> intention typée -> politiques explicites -> use-case testable -> résultat immuable -> IO isolée
```

Cette règle dérive directement de l'ancien `doc/code_rule.md` : composants indépendants, intentions, politiques explicites, déterminisme, observabilité et structures rejouables.

## Dettes reprises sur 4.2 → 4.11

| Dette | Correction 4.12-r2 |
|---|---|
| `argparse.Namespace` utilisé comme contrat interne | conversion en `Command` dataclasses à la frontière CLI |
| seuils et limites dispersés | `Policy` dataclasses explicites |
| écriture JSON rapport dupliquée | `src/inference/report_io.py` |
| risque d'une zone CLI écrite en Python classique | addendum `code_rule.md` : la CLI reste un adaptateur temporaire, pas une exception |
| oubli possible de `code_rule.md` en phase future | champ `code_rule_review` obligatoire dans les rapports |

## Zones réalignées

- Build corpus E5 : `E5BuildCommand` + `E5SourceSelectionPolicy`.
- Search corpus E5 : `E5SearchCommand` + `E5SearchPolicy` + `E5SearchRenderPolicy`.
- Rebuild sûr : `E5RebuildCommand` + `E5DiagnosticGatePolicy` + `E5SearchValidationPolicy`.
- Inspect corpus : `E5InspectCommand` + `E5DiagnosticGatePolicy`.
- Rapports JSON : `JsonReportWritePolicy` + writer atomique centralisé.

## Ce qui a été corrigé par rapport à la 4.12 rejetée

- L'ancien `doc/code_rule.md` est conservé comme base.
- Les sections historiques `Micro-Kernel Coopératif IA`, `Contrat d'un composant`, `Instrumentation native` et `État actuel du modèle après Phase 2.6` restent présentes.
- La notion `Outillage CLI hors kernel` est retirée.
- Le addendum dit explicitement que les CLI ne sont pas une exception à la philosophie du noyau.
- Les tests de règles vérifient désormais que l'identité kernel est conservée.

## Limites

- Le Scheduler n'est pas modifié.
- Aucun EventBus/Scheduler n'est introduit dans les outils de développement.
- Les outils restent des CLI, mais leur cœur est réaligné pour pouvoir devenir des handlers/use-cases pilotables par événement.
- Les tests complets doivent être exécutés dans le dépôt local complet.

## code_rule

```text
code_rule_review: done
code_rule_update_required: true
reason: ajout court d'application E5 sans réécriture de la philosophie initiale
```
