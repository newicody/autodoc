# 0284-r1-r3 — GitHub project connector configuration split

This patch separates the read-only ProjectV2 configuration from the explicit
outbound `workflow_dispatch` configuration targeting `newicody/projects`.

It also adds the cumulative installation guide:

`templates/github/projects-repository/INSTALLATION.md`

The guide is intended to be updated by later Projects bundle phases.

Suggested commit:

`split-github-project-connector-configs`
