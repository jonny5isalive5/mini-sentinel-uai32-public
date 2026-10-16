# Disprove us

Our claim is public so it can be checked and challenged. Reproduce it, find the boundary where it fails,
or show a better comparable result. Reproducible negative results are useful contributions.

## The claim to attack

At `3e924e600ef6b65eff9f00668cb283b259930049`, the committed x86-64 Linux executable plus the complete saved MNIST model totals
**30,656 bytes** under a **32,768-byte** on-disk limit, with the documented host-library exclusions,
and scores **9,781/10,000 (97.81%)** on standard MNIST test images after 14×14 preprocessing.
The executable also trains, saves, reloads and continues learning. See the [README](../README.md)
for scope and [EVIDENCE.md](EVIDENCE.md) for artifact identities.

## Useful challenges

- **Accounting:** find omitted learned state, uncounted executable bytes or a dependency that exceeds
  the stated host-library exclusion. A static binary or RAM measurement is a useful alternative
  accounting exercise; report it with its own boundary.
- **Learning and evaluation:** show data leakage, incorrect preprocessing, a reference mismatch,
  hard-coded answers, misleading generalization claims or a failure to reach the recorded score.
- **Robustness:** provide malformed numeric input, model files, cached datasets or failure injection
  that exposes incorrect behavior, corruption or an unjustified PASS. Use disposable local files.
- **Reproduction:** demonstrate a checksum mismatch, an unexplained build difference, or a failed
  mandatory gate. Report the environment and unedited logs even if the cause is unknown.
- **Smaller comparable implementations:** include training as well as inference, all saved learned
  state and any implementation-specific dependencies, with the same exclusions. Report at least
  9,781/10,000 on the same preprocessed test set and give source, training recipe and exact artifacts.
  Label any different accuracy, task, preprocessing or dependency boundary so readers can compare it.

A smaller comparable program improves the result; it does not refute an optimality claim because we
make none. We do not claim to be the world's smallest AI.

## Submit a counterexample

Open an issue or propose a pull request in the repository hosting this publication copy. Keep any exploit demonstration
local to this program and attach the smallest input needed to reproduce it. Do not test unrelated services.

```text
Title: [uai32 challenge] short description
Category: accounting / evaluation / robustness / reproduction / smaller implementation
Target commit: 3e924e600ef6b65eff9f00668cb283b259930049
Executable SHA-256:
Model SHA-256:
OS / architecture / CPU:
Compiler / linker / libc / Python / NumPy versions:
Exact command(s), starting directory, environment overrides:
Minimal input or attached files and their hashes:
Expected behavior under the stated claim:
Actual output, stderr and exit status:
Counted executable + learned-state bytes:
Correct predictions / total test examples:
Does a fresh exact-SHA checkout reproduce it?
If comparing another implementation: source, training recipe, dependencies and scope differences:
```

Remove credentials and unrelated personal data from submissions. Public fixes should keep the original
counterexample and add a regression where appropriate. A changed implementation gets a new SHA and
new evidence; it must not inherit the old PASS automatically. This invitation promises no bounty,
reward or response deadline.
