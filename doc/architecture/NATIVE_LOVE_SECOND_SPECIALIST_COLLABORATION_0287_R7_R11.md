# Native love second-specialist collaboration — 0287-r7-r11

## Runtime composition

```text
existing Scheduler
  -> LABORATORY_VISIT_REQUEST
  -> existing Dispatcher
  -> collaborative love handler
  -> collaborative native provider
      -> r10 first provider for specialist 1
      -> r11 relational handler for specialist 2
```

The collaborative provider supports both specialist identities but does not own
their order. It upgrades the single r10 Scheduler-owned registration in place;
no second registry entry is created. A caller receives the first Scheduler receipt, creates a canonical
artifact reference, prepares the continuation, registers the authorized runtime
inputs, then submits a second visit through the same Scheduler.

## Conversation

```text
sequence 0: demand to specialist 1
sequence 1: completion + concept/affect artifact
sequence 2: continued demand to specialist 2
sequence 3: completion + relational-dynamics artifact
```

The second demand carries `parent_visit_ref`,
`continuation_of_message_ref`, the exact source artifact and one stable
conversation/correlation identity.

## Non-goals

- no direct specialist-to-specialist invocation;
- no automatic follow-up scheduling;
- no global synthesis;
- no durable storage;
- no OpenVINO model invocation;
- no Qdrant projection;
- no GitHub publication.
