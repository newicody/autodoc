# Changelog 0168 — GitHub Actions artifact fetch once

Added a read-only fetch tool for GitHub Actions artifacts. The tool can list
workflow runs, list artifacts for runs, download matching artifact ZIPs, extract
them into server staging, and invoke the existing 0167 dataset sync tool.

The implementation keeps conversion and inference out of the fetch phase. It
also supports a fixture mode for deterministic tests without network access.
