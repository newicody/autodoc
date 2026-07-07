# Patch queue traces

This directory stores generated patch-queue snapshots used during Autodoc/MissiPy development.

These patch directories are kept intentionally at repository root because they help
humans and AI agents understand the development sequence, design intent, local
experiments, failed applications, manual corrections, and validation history.

Important rule:

- `patch/` is a historical development trace.
- Git commits are the canonical source of truth.
- A `patch.diff` may not always be replayable after manual fixes.
- When a patch was corrected manually, the final tracked source files and the
  corresponding Git commit take precedence.
- Do not treat generated patch snapshots as runtime data.
- Do not store user artifacts, fetched GitHub artifacts, photos, audio, video,
  PDFs, archives, or dataset contents here.
- Server/user data belongs in the configured server dataset, not in this repository.

Recommended reading order for AI agents:

1. Read `doc/code-rules/code_rule.md`.
2. Read relevant `doc/code-rules/016x_*.md`.
3. Read `doc/architecture/*.md`.
4. Read `doc/CHANGELOG_*.md`.
5. Inspect the corresponding `patch/016x-*` directory as historical context.
6. Prefer tracked source files and Git history when patch snapshots disagree
   with final code.
