# 0284-r5 — specialists/laboratories existing-chain smoke

Base attendue :

```text
0284-r2-portable-specialist-contract
0284-r3-specialist-laboratory-message-contract
0284-r4-specialist-laboratory-transfer-contract
```

Le patch exécute un `PortableSpecialistDescriptor` par le smoke 0274 déjà
existant, donc par le Scheduler, la queue, le Dispatcher, le handler et le
provider fictif déterministe déjà présents.

Après le retour du smoke existant, il projette le reçu réel du spécialiste en
une conversation typée `demand -> opinion`.

Il ne crée ni Scheduler, ni laboratoire, ni provider, ni transport, ni bus, ni
registre, ni CLI. Le transfert inter-laboratoires n'est pas simulé tant qu'un
second laboratoire réel n'existe pas.

Commit proposé :

```text
add-portable-specialist-existing-chain-smoke
```

Étape suivante :

```text
0284-r6-portable-specialist-real-memory-closure
```
