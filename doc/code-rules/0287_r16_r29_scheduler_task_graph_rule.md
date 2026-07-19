# Règle — graphe de tâches Scheduler 0287 r16-r29

## Construction

- Construire un graphe immuable par commande.
- Exiger des `task_ref` uniques et une seule `command_ref`.
- Vérifier toute référence de dépendance, barrière et branche.
- Détecter les cycles avant toute admission du graphe.

## Readiness

- Le plan de readiness reste pur et déterministe.
- Ne jamais promouvoir une tâche dont une dépendance, une barrière ou une porte de branche est bloquée.
- Ordonner les candidats par priorité effective décroissante, date de création puis `task_ref`.
- Produire une nouvelle version de graphe et des transitions typées lorsque des tâches deviennent `ready`.

## Autorité

La décision appartient au Scheduler. Le modèle ne persiste rien. PostgreSQL sera l'autorité durable des graphes, tâches et transitions. Les dictionnaires locaux utilisés pour indexer les objets ne sont pas des autorités et ne franchissent aucune frontière.

## Effets de bord interdits

- Ne pas appeler le Dispatcher ou un handler.
- Ne pas publier sur EventBus.
- Ne pas ouvrir PostgreSQL, Qdrant ou OpenVINO.
- Ne pas manipuler ControlProxy ou `/dev/shm`.
- Ne pas démarrer de Scheduler, laboratoire ou spécialiste.
- Ne pas écrire JSON ou JSONL.
- Ne pas afficher de texte automatiquement.
