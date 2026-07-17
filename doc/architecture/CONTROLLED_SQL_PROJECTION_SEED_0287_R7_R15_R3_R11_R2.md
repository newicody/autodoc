# Controlled SQL projection seed

```text
context-revision:love-base (accepted, immutable)
                    |
                    v
context-revision:love-live-projection-probe-v1 (accepted)
                    |
                    +-- active --> context-object:love-live-projection-probe-v1
```

The object owns the authoritative title, body and content digest. The child
revision makes the object eligible for the existing projection probe. This unit
has no Qdrant or OpenVINO effect.
