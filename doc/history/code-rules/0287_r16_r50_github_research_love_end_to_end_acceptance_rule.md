# Règle 0287 r16-r50 — acceptation bout en bout

Une validation bout en bout ne doit jamais déduire la réussite de la seule
présence des modules ou de tests unitaires.

Elle doit relire des preuves produites par une exécution réelle et vérifier :

- le même `repository/issue_number/run_id` ;
- le triplet d'artefacts distinct ;
- les étapes locales ;
- le digest de publication ;
- la publication distante ;
- la preuve SQL de clôture ;
- le cycle de vie temporel des handlers.

La porte d'acceptation est une lecture. Elle ne crée aucun Scheduler, ne
déclenche aucun laboratoire et ne réalise aucune mutation distante.
