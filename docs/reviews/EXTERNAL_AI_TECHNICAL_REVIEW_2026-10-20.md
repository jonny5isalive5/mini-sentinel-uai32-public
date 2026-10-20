# External AI Technical Review — Sentovara µAI-32 (`mini-sentinel-uai32-public`)

**Date:** 20 October 2026.
**Reviewer:** Claude Opus (Anthropic).
**Disclosure:** Anthropic's Claude Fable previously contributed to Mini Sentinel's
development. Claude Opus was not involved in that development and conducted a
separate, hands-on examination of the published repository.
**Scope:** Reproduction of bundled demonstrations, model-size verification, source
inspection and publication integrity checks.
**Limitation:** The reported MNIST accuracy of 97.81% was not independently reproduced.
**Commit reviewed:** `6476d7d7b0a3cb64194a92c40b00846e4bb71ca6` (public publication copy).

This is a hands-on reproduction and code read of the *locally verifiable* parts of
the repository. It is **not** a formal certification and does not supersede the
project's own recorded audit.

---

## Method

A shallow clone of the public repository was compiled and exercised in an isolated
Linux container (gcc 13, x86-64). The following were performed:

1. Read of the complete source (`uai32/uai32.c`, 257 lines) and the project
   documentation.
2. Compilation of the source and execution of the three committed demonstration
   models against their committed test data.
3. An arithmetic check of the MNIST model's on-disk size against the documented
   format.
4. A structural load test of the committed MNIST model.
5. Execution of the repository's own `verify_publication.py` hash/manifest check.

No network access to external datasets was used, and no attempt was made to push,
modify, or otherwise alter the repository.

---

## What reproduced

| Check | Result |
|---|---|
| Source compiles cleanly (`gcc -O2 -lm`) | **Yes** |
| `dist/iris.model` on `data/iris_test.txt` | **29/30 = 96.7%** (matches README) |
| `dist/spirals.model` on `data/spirals_test.txt` | **298/300 = 99.3%** (matches README) |
| `dist/rings.model` on `data/rings_test.txt` | **300/300 = 100%** (matches README) |
| Committed executable size (`dist/uai32`) | **9,188 bytes** (matches claim) |
| Committed MNIST model size (`dist/mnist14.model`) | **21,468 bytes** (matches claim) |
| MNIST model structural validity | Loads as 196→48→10; emits 10 normalised probabilities |
| `verify_publication.py` (file set + hashes + archives) | **PASS** — 44 files, 49 archive members |

**Model-size arithmetic (independently recomputed):** for the MNIST model
(NI=196, NH=48, NO=10) the format stores `mean[196]` and `scale[196]` as float32
(392 × 4 = 1,568 bytes), the remaining 9,946 parameters as bfloat16
(9,946 × 2 = 19,892 bytes), plus an 8-byte header — total **21,468 bytes**,
matching the committed file exactly.

---

## What was not independently verified

- **The headline MNIST accuracy (9,781/10,000 = 97.81%).** The MNIST dataset is
  deliberately not redistributed in the repository (a licensing decision stated in
  the documentation), and no external dataset was fetched for this review. The
  committed model is of the claimed size and correct architecture, and loads and
  runs, but the accuracy figure itself rests on the project's own recorded audit
  and has **not** been re-measured here. An independent party obtaining MNIST from
  the documented upstream and running `make measure` is the outstanding step to
  confirm this number first-hand.
- **Byte-identical rebuilds across toolchains.** The documentation explicitly makes
  no such claim; executable size is toolchain-dependent. Not tested here.

---

## Code observations

The implementation is clean, readable, and defensively written for its size. Noted
positives:

- Numerically stable softmax via log-sum-exp; finite-value guards on activations,
  parameters, and inputs; integer-label and column-count validation on data load.
- bfloat16 weight storage (top 16 bits of the float32, round-to-nearest-even) halves
  the model file at negligible accuracy cost, while normalisation statistics are kept
  at full float32 — an appropriate precision split.
- He-uniform initialisation, feature normalisation, ReLU hidden layer, and
  save/reload-and-continue training are all present and correct.

Minor, non-blocking notes:

- `frand()` casts the `unsigned` RNG state to `(int)` before scaling, which is
  implementation-defined on overflow. It behaves as intended on the target
  platform, but scaling the unsigned value directly would be strictly portable.
- The reported MNIST accuracy is measured on the standard public test set, which —
  as the documentation acknowledges — is not a never-consulted development holdout.
- No weight regularisation is used; at this scale (48 hidden units on 14×14 inputs)
  this is a reasonable choice and unlikely to materially affect the result.

---

## Conclusion

Within the scope defined above, the repository's locally checkable claims hold:
the code builds and runs, the three bundled demonstration models reproduce their
stated accuracies exactly, the executable and MNIST model match their claimed sizes,
the model-size accounting is arithmetically correct, and the publication hash
manifest passes. The documentation is notably careful about scope, exclusions, and
known limitations, and does not overstate the result.

The single remaining gap between "verified here" and "fully independently
confirmed" is the MNIST accuracy figure, which requires obtaining the dataset and
re-running the measurement. Closing that one step would place the entire headline
claim on independently reproduced footing.

*This review covers only what is stated above and is offered without warranty. It
reflects the reviewed commit and may not apply to later changes.*
