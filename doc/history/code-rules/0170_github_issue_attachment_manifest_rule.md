# 0170 GitHub issue attachment manifest rule

0170 introduces a reference-only attachment manifest for the external idea
repository workflow.

Required boundary:

- parse photo, audio, video, PDF, archive, and text attachment references
- GitHub issue attachment references only
- no GitHub API call
- no remote mutation
- GitHub Actions artifacts remain the source system
- no user artifacts in Autodoc repository
- store fetched files in the server dataset before conversion

The manifest may contain URLs and metadata. It must not contain downloaded user
files or runtime dataset contents.
