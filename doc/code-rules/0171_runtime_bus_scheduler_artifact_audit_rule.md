# 0171 runtime bus/scheduler artifact audit rule

0171 locks the runtime integration boundary for GitHub artifact and server
dataset work.

Mandatory rules:

- Reuse existing event.bus/context.bus observation surfaces.
- Reuse the existing bus visualization adapter for VisPy/browser views.
- Reuse or extend existing scheduler route adapter/handler/handshake surfaces
  before adding any new runtime adapter.
- EventBus is observation-only.
- Events and bus facts are facts, not commands.
- Scheduler/policy/zone remain the authority.
- GitHub artifact/dataset tools must not create a parallel bus.
- GitHub artifact/dataset tools must not write directly to VisPy.
- Dataset-local observation files are audit/staging only, not the canonical
  VisPy integration path.
- Do not modify Scheduler.run() for artifact fetch or conversion planning.
- Do not store user artifacts, photos, audio, video, PDFs, archives, fetched
  GitHub artifacts, or dataset contents in the Autodoc repository.

The canonical next step after this audit is a bridge that maps GitHub
artifact/dataset outcomes to existing bus-compatible observation facts or
scheduler-addressable commands.
