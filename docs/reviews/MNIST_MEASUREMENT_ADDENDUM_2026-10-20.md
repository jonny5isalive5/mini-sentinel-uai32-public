# MNIST measurement addendum — 20 October 2026

Codex evaluated the committed Sentovara uAI-32 executable and MNIST model from
jonny5isalive5/mini-sentinel-uai32-public at commit
6476d7d7b0a3cb64194a92c40b00846e4bb71ca6 on the owner's Windows PC using WSL.
The repository-documented MNIST test archives matched their pinned SHA-256 hashes;
the committed preprocessing produced all 10,000 test rows. The frozen-artifact
command returned 9,781/10,000 correct (97.81%), loss 0.0766, exit code 0.
No retraining was performed. This reproduces the reported MNIST accuracy for that
artifact pair. It supplements the existing review and does not change its attribution.

## Attribution and scope

This is a **SUBSEQUENT Codex reproduction**, performed after the
[external review by Claude Opus](EXTERNAL_AI_TECHNICAL_REVIEW_2026-10-20.md).
**Claude Opus did not test or independently reproduce the MNIST accuracy.** The
original review remains verbatim, including its historically accurate limitation.

The repository-pinned MNIST test archives passed SHA-256 and IDX format checks.
The direct frozen-artifact command, run from `uai32/`, was:

```sh
./dist/uai32 test data/mnist14_test.txt dist/mnist14.model
```

Raw program output (the program rounds accuracy to one decimal place):

```text
test loss 0.0766  accuracy 9781/10000 = 97.8%
```

The exact count gives **97.81%**. Exit code: **0**; stderr was empty.
Exactly one MNIST evaluation was executed, with no retraining or rebuild. This
verifies the frozen executable/model pair at the commit named above, not the full
retraining suite. `make measure` was not run because it retrains models.

This addendum is based on the owner's retained `OPTIONAL_ADDENDUM.txt`, checked
against `MEASUREMENT_REPORT.txt` and `measurement.stdout.txt`, dated 20 October 2026.
It adds a subsequent measurement record without changing the original review,
code, models, original publication hashes/manifests, or README.
