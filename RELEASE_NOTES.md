# v0.1.0

First public release: environment byte accounting, NUL-delimited stdin argument
analysis, approximate pointer overhead, ARG_MAX pressure labels, Linux per-string
limit warning, JSON, --check and --hide-names. No command execution or repairs.

Local verification: syntax, 12 unit/CLI tests and the documented NUL pipe.
CI matrix: macOS/Linux with Python 3.9 and 3.13.

The executable asset is the same standard-library-only Python source as the repo.
Requires Python 3.9+. BELOW_ESTIMATE is not a guarantee of successful exec.
No user-outcome evidence has been measured for this release.
