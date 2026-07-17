# 0235-r1 patch queue ignored runtime artifacts guard

Filters `.var` paths before patch queue commit staging so local runtime reports do not break `git add`.
