# Copilot advisory v1/v2 intake compatibility

```text
copilot_advisory.json
        |
        v
schema dispatcher
  |                  |
  v                  v
v1 artifact       v2 first-opinion artifact
  |                  |
  +--------+---------+
           v
existing manifest digest/correlation validation
           v
existing read-only source-candidate intake
           v
request title/body only + advisory reference metadata
```

The dispatcher preserves both contracts. It does not normalize their analytical
content into a shared semantic model. Downstream projection remains a separate,
versioned step.
