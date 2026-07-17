# 0284-r1-r3-r1 — GitHub Project connector config split alignment

Ce paquet remplace `0284-r1-r3-github-project-connector-config-split`, qui a
échoué avant application sur le script de dispatch local divergent.

Il porte l'ensemble de la phase r3 sans modifier ce script ni le test historique
0272. Le fichier de dispatch dédié doit être sélectionné explicitement avec
`--config`.

Commit proposé : `split-github-project-connector-configs`
