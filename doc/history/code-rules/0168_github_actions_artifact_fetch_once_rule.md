# 0168 code rule — GitHub Actions artifact fetch once

0168 implements a read-only GitHub Actions artifact fetch. GitHub Actions
artifacts remain the source system and the server dataset configured by 0167 is
the local storage authority.

Required invariants:

- read-only GitHub Actions artifact fetch
- GitHub Actions artifacts remain the source system
- server dataset configured by 0167
- calls 0167 server dataset sync
- conversion starts only after raw sync
- VisPy observes the sync result
- does not publish GitHub results
- no remote mutation
- no SQL/qdrant write
- no user data in the development repository

The fetch tool may use read-only HTTP GET requests to GitHub Actions REST API
endpoints. It must not dispatch workflows, change issues, change Projects,
comment on GitHub, delete artifacts, or publish result artifacts.
