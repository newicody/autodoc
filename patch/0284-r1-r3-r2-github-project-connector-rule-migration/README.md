# 0284-r1-r3-r2 — GitHub project connector rule migration

Correctif de reprise à appliquer sur le worktree sale laissé par l'échec de
`0284-r1-r3-r1-github-project-connector-config-split-alignment`.

Ce patch ne réapplique pas les configurations. Il migre seulement les règles
historiques 0272/0275 vers la séparation déjà présente :

- `config/github_project_v2_query_only.example.ini` reste query-only ;
- `config/github_projects_workflow_dispatch.example.ini` porte le dispatch ;
- les deux autorisations distantes restent à `false` dans l'exemple ;
- les références actives visent `newicody/projects`.

Le commit produit par `apply_patch_queue.py --allow-dirty` inclura également les
modifications de r3 déjà appliquées avant l'échec des tests.

Suggested commit: `split-github-project-connector-configs`
