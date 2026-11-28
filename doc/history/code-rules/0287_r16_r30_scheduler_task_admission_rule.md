# Règle r16-r30 — admission pure des tâches Scheduler

1. Le planificateur ne modifie jamais SchedulerTask, un budget, un inventaire ou
   une ressource réelle.
2. Le budget global de commande borne au minimum les étapes Scheduler, les
   visites de spécialistes et la durée totale.
3. Le budget de tâche doit être corrélé à `task_ref` et porter exactement le
   même `max_attempts` que la tâche.
4. Le profil de ressources est résolu avant l’admission depuis le descripteur du
   handler ; r16-r30 ne crée aucun registre global implicite.
5. La priorité effective est calculée par politique explicite. Le vieillissement
   empêche la famine sans dépasser la priorité maximale autorisée.
6. Le backoff est entier, déterministe et borné. Aucun hasard ou horloge cachée
   n’est consulté.
7. Une admission produit seulement une réservation proposée et digestée. Elle
   n’ouvre ni SQL, Qdrant, OpenVINO, `/dev/shm`, ControlProxy ou laboratoire.
8. Le Scheduler vivant applique seul le plan, réalise les transitions et
   persiste les effets via les ports autorisés.
9. Aucun JSON ou JSONL interne n’est une autorité. JSON reste réservé aux
   frontières externes telles que GitHub.
10. EventBus, PassiveSupervisor et VisPy observent les décisions sans les
    influencer.
