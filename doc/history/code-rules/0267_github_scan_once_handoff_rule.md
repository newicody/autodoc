# Code rule 0267 - GitHub scan-once handoff

Required:

```text
GitHub scan-once handoff
local/server remains the authority
GitHub is a review/workflow surface
remote mutation is forbidden in 0267
scan-once means one local artifact envelope
```

Forbidden:

```text
GitHub API call
issue creation
project update
pull request creation
commit push
polling loop
runtime execution
new RuntimeManager
Scheduler.run modification
```

0268 may prepare OpenRC/launcher minimal readiness.
