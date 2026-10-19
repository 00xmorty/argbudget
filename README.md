# ArgBudget

A dependency-free, read-only byte-pressure report for “Argument list too long”.
Measures the environment that actually reached this Python process and optionally
NUL-delimited argument bytes. Does **not** execute the proposed command.

## Install / run

Requires Python 3.9+ on macOS or Linux. No pip packages.

```sh
git clone https://github.com/00xmorty/argbudget.git
cd argbudget
python3 argbudget
printf 'tool\000first argument\000second argument\000' | python3 argbudget --stdin0 --json --hide-names
```

Or download the `argbudget` asset from v0.1.0, inspect it, and run
`python3 argbudget --help`. No sudo or installation into system folders needed.
Include the executable name as argv[0] in stdin. Every item must end in NUL;
empty input means zero arguments, a single NUL means one empty argument.
Without `--stdin0`, arguments are explicitly **not measured**.
The pipe is data only; it never executes `tool`.

For a file-name workload, a bounded example (paths remain local):

```sh
find . -type f -print0 | python3 argbudget --stdin0 --json --hide-names
```

This counts filenames, not a complete command; add executable/options to your
own NUL stream for a complete estimate. Prefer stdin-capable tools or bounded
`xargs` batches rather than constructing enormous shell argument lists.

## Report / exits

- `environment_bytes`: raw key + '=' + value + NUL, measured in bytes.
- `argument_bytes`: each supplied byte string plus its final NUL.
- `pointer_estimate_bytes`: process pointer size times entry counts plus two terminators.
- `estimated_total_bytes`: those three components, not an exact kernel budget.
- `BELOW_ESTIMATE`, `NEAR_LIMIT` (80%+), `OVER_ESTIMATE` (100%+ or Linux single-string limit).
- Linux checks a 32-page per-string limit separately; this can fail even below ARG_MAX.
- `execution_guaranteed` is always false.
- Default exits 0 on a valid report, 2 on invalid input/unavailable limits.
  `--check` exits 1 for NEAR/OVER, 0 below; it is not a command-execution test.
- `--version` prints the version; `--hide-names` suppresses even environment key names.

## Safety

No target execution, subprocesses, networking, telemetry, configuration writes,
cleanup, sudo, or environment modifications. Values and supplied argument contents
are never printed. Normal environment **names** are printed unless `--hide-names`
is used; names can themselves reveal sensitive context. Nonstandard names are
hidden. Inspect reports manually before sharing; byte counts may also be sensitive.
Do not unset security/build variables blindly or disable sandboxing to clear an error.
Input is bounded to 16 MiB; report errors do not echo the input or OS paths.

## Limitations

A diagnostic estimate, not a promise an `exec` succeeds: OS-specific overhead,
alignment, interpreter-added arguments, stack limits, executable paths, and wrappers
can change effective limits. Pointer accounting is deliberately approximate on macOS.
Only the current environment is visible, not variables Xcode/a later wrapper adds.
No permission, interpreter, sandbox or executable validation is performed. Python
itself cannot start if its launch environment already exceeds the kernel limit.
No automatic repair and no popularity, user-success or market-demand claim.

Technical references: `man execve`, `man xargs`,
[Linux execve manual](https://man7.org/linux/man-pages/man2/execve.2.html),
[Apple execve manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html).

## Development

```sh
python3 -m py_compile argbudget
python3 -m unittest discover -s tests -v
```

CI exercises the tests and actual NUL-pipe usage on macOS and Linux, Python 3.9/3.13.
MIT license. Please share only synthetic/reviewed reproductions in issues.
