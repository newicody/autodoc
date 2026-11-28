# Readable Copilot publication wiring — 0287-r7-r15-r2-r4

The readable identity bundle is correlated with the v2 publication preview. The existing Issue renderer remains responsible for the analytical content; the existing ProjectV2 planner remains responsible for field identities and mutations.

The new composition adds:

- a readable Issue heading;
- the human Actions artifact name;
- an Actions run URL;
- a bounded `Artefact` locator containing title, URL and typed reference;
- one combined digest covering the Issue and ProjectV2 plans;
- replay detection on both surfaces.

The request remains authoritative. Copilot remains an untrusted, consultative hint. Preview and operator approval remain mandatory.
