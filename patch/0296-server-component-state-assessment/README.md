# 0296 — État propre des composants et évaluation scientifique serveur

## Base et portée
- Branche : `docs/unification-027x`
- Base : `23e38d250949a25e321bada21e334f59b2c720c1`
- Ajoute un contrat d'instantané d'état, un agrégateur scientifique et un port injecté dans la composition/runtime OpenRC existante.

## Modifications
- `missipy.server.component_state_snapshot.v1` : disponibilité, collecte, fraîcheur, communication, capacités, réservations, interfaces, statistiques d'utilisation, données, représentations, contraintes, erreurs et provenance.
- Agrégateur d'évaluation qui conserve les sources/dates et dégrade la cohérence en cas d'état partiel, inconnu, périmé, indisponible ou en erreur.
- Séparation stricte des statistiques d'utilisation, de la télémétrie matérielle et de la capacité logique Scheduler.
- Fournisseur d'état optionnel, injecté par la fabrique de composants déjà utilisée par le runtime installé.
- Adaptateur de publication serveur étendu pour recevoir des instantanés typés et les transformer en réponse corrélée à l'artefact initial.
- Documentation d'architecture et roadmap mises à jour.

## Limites
Le fournisseur concret doit être implémenté par la fabrique de composants installée.
Le traitement serveur vivant doit appeler l'évaluation lorsque l'artefact initial
arrive, puis lancer l'adaptateur de publication. Ce patch n'ajoute pas de poller,
de manager, de registre, d'EventBus ou de Scheduler. Il ne raccorde pas encore
le déclenchement Git initial ni l'activation obligatoire de la chaîne dans
l'admission ProjectV2 `En cours`.

## Validation
Tests de contrat, d'agrégation et d'injection runtime ajoutés. Non exécutés ici.
Aucune admission ni exécution de laboratoire déclenchée.
