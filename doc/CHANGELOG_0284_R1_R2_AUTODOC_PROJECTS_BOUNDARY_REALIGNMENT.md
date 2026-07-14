# Changelog — 0284-r1-r2 Autodoc / Projects boundary realignment

## Removed

- active controlled-research workflow from the Autodoc `.github/` surface;
- active research, theme and transversal Project-management Issue forms from
  the Autodoc `.github/` surface.

## Clarified

- Autodoc has no project-management mode;
- ProjectV2 is an external connector and workflow surface;
- `templates/github/projects-repository/` is the copy source for
  `newicody/projects`;
- reusable GitHub helpers may remain in Autodoc without becoming active Autodoc
  project workflows.

## Deferred

- split of query-only and outbound workflow-dispatch configuration;
- migration of stale `autodoc-ideas` references;
- Copilot fields and ProjectV2 views, which must be implemented in the copied
  Projects repository bundle rather than as an Autodoc runtime mode.
