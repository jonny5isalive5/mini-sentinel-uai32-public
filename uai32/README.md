# Sentovara µAI-32

**AI engineering contributors**\
OpenAI GPT-5.6 Sol\
Anthropic Fable 5.1\
OpenAI Codex

**Project direction and release stewardship**\
Sentovara

µAI-32 was developed through collaborative human direction and AI-assisted engineering, implementation, adversarial review, verification, and release preparation.

A trainable neural classifier in plain C, with its executable and saved learned state under 32,768 bytes.
It trains by stochastic gradient descent, saves and reloads its weights, and supports inference and continued training.

**Historical audit: 7 October 2026.** This is a privacy-reviewed publication copy; see [publication notes](../PUBLICATION_NOTES.md). The audited implementation is
`3e924e600ef6b65eff9f00668cb283b259930049` (private historical reference) from PR #2 (private historical reference).
This documentation and license overlay is a separate change; the PASS applies to that exact audited commit.

## Claim

The committed x86-64 Linux executable is **9,188 bytes** and its saved MNIST model is **21,468 bytes**:
**30,656 bytes combined**, with **2,112 bytes** remaining under the 32,768-byte limit.
That executable/model pair correctly classifies **9,781 of the standard 10,000 MNIST test images (97.81%)**
after the documented 28×28 to 14×14 preprocessing. The printed loss is **0.0766**.

## Scope and accounting

Count the complete executable file plus one complete saved model file, including the model header,
normalization statistics, weights and biases. This is an **on-disk file-size claim** for the identified
artifacts on a host that supplies `libc.so.6`, `libm.so.6` and the ELF dynamic loader.
Those host libraries, the operating system, RAM, datasets, compiler, verification tools, source,
documentation and archive/checksum metadata are excluded. These exclusions are part of the claim.
The executable includes training as well as inference. All four demonstration models are alternatives;
the MNIST claim counts its one model, not the entire release download.

## Evidence

The original focused audit reports **PASS**, **28/28 mandatory verification checks**, **18 regression
groups** and **222 recorded subprocess invocations**, including sanitizer checks. It records exact
toolchain reproduction of the executable, all four models and the checksum manifest.
The [evidence index](release/EVIDENCE.md) links those results, the redacted publication archive and separate original/publication hashes.
These are recorded audit results; release preparation is not a new independent certification.

## Known limits

This is a one-hidden-layer classifier, not a language model or proof of general intelligence.
There is no claim of being the world's smallest AI, of bare-metal operation, of a 32 KiB RAM footprint,
or of universal accuracy or byte-identical builds across environments. The standard MNIST test set is
a public benchmark; the audit does not establish a never-consulted development holdout. One iris test
row duplicates a training row. The size-oriented executable omits several hardening features.
See [release notes](release/RELEASE_NOTES.md) and the detailed limits below.

## Reproduce

Start with the [exact-SHA reproduction guide](release/REPRODUCE.md). Verify the committed checksums
before rebuilding; train into scratch files before any optional `make dist`. A full pass requires every
prerequisite and all 28 checks. Failures must be reported, never converted into skipped checks.

## Disprove us

Reproduce the result. Challenge the accounting or dependencies. Find data leakage, incorrect learning,
invalid-input behavior or a reproducible test failure. Build a smaller comparable implementation.
The [Disprove us challenge](release/CHALLENGE.md) gives the reporting format and comparison rules.
Bring commands, inputs, hashes and results so others can check the counterexample.

## License and release status

Project code and release documentation in `uai32/` are offered under [Apache-2.0](LICENSE).
Datasets retain their own terms; see [attribution and third-party notices](release/THIRD_PARTY_NOTICES.md).

**MNIST licensing note:** This release does not redistribute MNIST images, labels, source archives,
or generated dataset files. Reproduction requires users to obtain MNIST separately from the documented
upstream mirrors and comply with whatever terms apply to that dataset. Sentovara does not grant any
rights in MNIST and does not make an independent claim about its upstream licence.

This branch prepares a reviewable release package. It does not merge PR #2, create a release tag or publish
a GitHub release.

## Recorded demonstration results

| model (trained by `make measure`) | executable | model file | **combined** | held-out accuracy |
|---|---:|---:|---:|---|
| iris (4 features, 3 classes, 8 hidden)        | 9,188 B | 174 B    | **9,362 B**  | 96.7% on 30 held-out rows; one has duplicate features in training |
| spirals (2 features, 2 classes, 32 hidden)    | 9,188 B | 348 B    | **9,536 B**  | 99.3% on 300 unseen points |
| rings (2 features, 3 classes, 16 hidden)      | 9,188 B | 222 B    | **9,410 B**  | 100% on 300 unseen points |
| MNIST digits 14×14 (196 features, 10 classes, 48 hidden) | 9,188 B | 21,468 B | **30,656 B** | **9,781/10,000 = 97.81%** (printed as 97.8%) |

Limit: 32,768 bytes. Worst case above leaves 2,112 bytes spare. Sizes are from `gcc 13.3 / binutils 2.42 / glibc 2.39, x86-64 Linux`;
run `make measure` to get them on your machine. The exact files measured are committed in `dist/` with `SHA256SUMS`.

## Local command reference (use a disposable checkout; full prerequisites in the reproduction guide)

```sh
make                 # builds ./uai32 and ./uai32.elf; byte size depends on the toolchain
python3 get_mnist.py # downloads and validates the four pinned MNIST source archives
make measure         # trains all four models into work/; preserves the committed dist/
make test            # audit exploit regressions; requires sanitizer support in the compiler
make verify          # exactly 28 mandatory checks; missing prerequisites cause failure
```

The whole interface is three verbs:

```sh
$ ./uai32 train data/iris_train.txt iris.model 8 60 0.05 1      # HIDDEN EPOCHS RATE SEED
new model: 4 inputs, 8 hidden, 3 classes, 75 parameters
epoch 1/60  train loss 0.5715  accuracy 109/120 = 90.8%
...
epoch 60/60  train loss 0.0802  accuracy 116/120 = 96.7%

$ ./uai32 test data/iris_test.txt iris.model                     # 30 flowers held out from training
test loss 0.0794  accuracy 29/30 = 96.7%

$ head -3 data/iris_test.txt | ./uai32 predict iris.model        # class, then probability of each class
0 0.999 0.001 0.000
1 0.001 0.998 0.001
1 0.001 0.912 0.087

$ ./uai32 train data/iris_train.txt iris.model 0 20 0.01         # file exists -> reload and keep learning
continuing: 4 inputs, 8 hidden, 3 classes
```

For the digits: `python3 get_mnist.py` downloads MNIST (11 MB) and writes it as text, then `make measure` trains
196-48-10 for 12 epochs at rate 0.01 plus 4 epochs at 0.002 (about 15 s) and `./uai32 test data/mnist14_test.txt work/mnist14.model` reports the accuracy.

## What `make verify` checks

| requirement | evidence (all printed by `verify.sh`) |
|---|---|
| learns from examples | iris held-out accuracy 53% with the random initial weights (saved after 0 epochs) → 96.7% after 60 epochs; training loss 0.57 → 0.08 |
| alters internal state | the 174-byte model file before and after training differs (`cmp`) |
| evaluates examples outside the training split | spirals/rings train/test rows are disjoint (checked); the UCI iris file contains duplicate flowers, so one iris test row has a verbatim twin in training: iris 96.7%, spirals 99.3%, rings 100% on the test files |
| ...and not by accident | **control**: trained on the spirals with scrambled labels it scores 47% on the real test set (chance = 50%) |
| saves what it learned | `train` writes the model file; `test`/`predict` are separate processes that only have that file |
| reloads it and continues inference | a copy of the model file, read by a fresh process, gives byte-identical predictions, 99.3% correct |
| continues training | `train` on an existing file prints `continuing`, changes the weights and keeps learning (100 more epochs at a lower rate) |
| numerical reference agreement | `refcheck.py` (NumPy) independently computes inference and compares it with the C output: exact correct/total counts and displayed accuracy, finite loss within 0.0001; one C SGD step agrees with the analytic gradient within 10% relative error for weights whose updates exceed bfloat16 rounding noise |
| the build is honest | building twice gives identical bytes; `uai32` is byte-for-byte `uai32.elf` minus the section header table (`objcopy --strip-section-headers`) |
| reproducible | two runs with the same data and seed write byte-identical model files |
| size limit | executable + each model ≤ 32,768 bytes, numbers printed; each model file's size equals the formula computed from its own header |

MNIST is mandatory for full verification: both `work/mnist14.model` and the committed `dist/mnist14.model`
must have the documented dimensions, exact length and finite parameters. The verifier checks every
committed artifact against `dist/SHA256SUMS` and evaluates MNIST in both the built and committed executables,
requiring at least 9,781 correct predictions out of exactly 10,000. No missing NumPy/objcopy check is skipped:
`ALL CHECKS PASSED (28/28)` is printed only after the fixed count succeeds. `refcheck.py` requires successful
C evaluation and compares accuracy and finite loss (absolute tolerance 0.0001 for the four-decimal output).
Its gradient check covers one example and the weights whose updates exceed bfloat16 rounding noise.

`make test` runs isolated regressions for corrupt/missing models and checksums, numeric conversions and
non-finite state under sanitizers, failed evaluation/loss comparison, missing/oversized distribution artifacts,
and malformed MNIST caches/downloads. Neither failed measurement nor failed packaging replaces `dist/`, and
if the final rename that publishes a new `dist/` fails, the previous `dist/` is put back (that failure is injected
by a regression test). A training set whose feature range overflows a float (for example 3e38 and -3e38) is
refused rather than silently normalised with scale 0.

## How it works (the whole thing is `uai32.c`)

* **Model.** A multilayer perceptron with one hidden layer: `inputs → NH ReLU units → NO softmax outputs`.
  Inputs are standardised with per-feature statistics learned from the training data (shift by the mean,
  scale by the range), and the statistics are stored in the model file as ordinary parameters.
* **Learning.** Plain stochastic gradient descent, one example at a time, with backpropagation of the
  cross-entropy gradient (`learn()` is 15 lines). The loss is computed in the stable log-sum-exp form.
  Examples are reshuffled every epoch with a seeded xorshift32 generator, so runs are deterministic.
  Weights start He-uniform (`±sqrt(6/fan_in)`), biases at zero.
* **Everything learned is one float array `P`:** `mean[NI] scale[NI] W1[NH][NI+1] W2[NO][NH+1]`
  (the last column of each matrix is the bias). Parameter count = `2·NI + NH·(NI+1) + NO·(NH+1)`.
* **Model file** = 8-byte header, the normalisation statistics as float32, then 2 bytes per weight, all little-endian:

  | bytes | content |
  |---|---|
  | 0–1 | magic `0xA132` |
  | 2–3, 4–5, 6–7 | `NI`, `NH`, `NO` as u16 |
  | 8 … 8+8·NI−1 | `mean[NI]`, `scale[NI]` as exact float32 (a rounded mean would shift every input) |
  | then | each weight as **bfloat16**: the top 16 bits of its IEEE-754 float, rounded to nearest even |

  bfloat16 keeps the float32 exponent and 7 explicit fraction bits (8 bits of precision including the implicit leading bit). It halves the file
  for a negligible accuracy cost (MNIST: 97.8% both ways) and loading is a 16-bit shift. Weights are
  trained in float32 and rounded only when saved. File size = `8 + 8·NI + 2·(NH·(NI+1) + NO·(NH+1))`.
* **Data format.** Text, one example per line: the features, then the integer label (`0,1,2,…`). The
  feature count comes from the first line, the class count from the largest label. `predict` reads the
  same rows from stdin and ignores extra numeric columns after the features, so a labelled file can be piped
  straight in (a non-numeric token anywhere in a row is an error).

## Executable layout and host-library exclusions

The executable is a normal dynamically linked ELF that uses the C library already on the machine
(`libc.so.6`, `libm.so.6`, the dynamic loader) for file I/O, formatting, elementary math and numeric parsing.
Those are the "operating-system libraries already provided" that the challenge excludes, as are the source,
the compiler and the datasets.

| part | bytes | what |
|---|---:|---|
| code (`.text`) | measured in `uai32.elf` | forward pass, backprop, validation, file format, data reader, CLI |
| dynamic linking tables (`.dynsym`, `.dynstr`, `.rela.dyn`, `.dynamic`, `.got`, version info) | measured in `uai32.elf` | libc/libm imports |
| strings (`.rodata`) | measured in `uai32.elf` | messages and formats |
| ELF + program headers, interpreter path, crt start-up code | ≈1,000 | |

The `Makefile` gets there with ordinary flags, no hand-written assembly and no packer:
`-Os`, no unwind tables, no stack protector, no PIE, `-fno-plt` (calls go straight through the GOT),
`-fcf-protection=none`, `--gc-sections`, `--build-id=none`, `-z noseparate-code` (no page padding between
segments), `-s`, and `-z nosectionheader`, which leaves out the ELF *section header table* that only linkers
and debuggers read (about 1.8 KB; `ldd`, `readelf -l` and the kernel never look at it). `-ffp-contract=off`
forbids fused multiply-add contraction, reducing one source of numerical variation; it does not guarantee
identical model bytes across optimisation levels, CPUs or host libraries. `uai32.elf` is the
same link with the table kept, for `nm`/`objdump`; `verify.sh` proves the two are otherwise identical.
A default `gcc -O2 -s` build of the same source is about 18 KB.

## Datasets

* `data/iris.data` — Fisher's iris flowers, UCI Machine Learning Repository (150 rows, CC BY 4.0).
  `gen_data.py` shuffles it with a fixed seed into `iris_train.txt` (120) and `iris_test.txt` (30).
* `data/spirals_*.txt`, `data/rings_*.txt` — synthetic 2-D problems generated by `gen_data.py` (numpy,
  seeded). Spirals are the classic test of whether a model can learn a curved boundary rather than a line.
* MNIST (not committed, 11 MB): `get_mnist.py` downloads the four IDX files from the cvdf-datasets or
  ossci-datasets mirrors and average-pools each 28×28 image to 14×14 (196 integers 0–255), writing
  `data/mnist14_train.txt` (60,000 rows) and `data/mnist14_test.txt` (10,000 rows). `--full` keeps 28×28.
  Cached and newly downloaded archives must match the pinned SHA-256 source hashes; IDX magic, 28×28 dimensions,
  split counts, exact payload lengths, image/label agreement and labels 0..9 are checked before use.

## Honest limits

* One hidden layer, plain SGD with a constant rate per run: good for tabular data and small images, not a
  language model. Learning-rate decay is done by hand with a second, lower-rate `train` run on the same file.
* Sizes are u16, so at most 65,535 features, hidden units or classes, and at most 100 million parameters; the dataset is held in memory as floats. Labels are integers 0..65,534. HIDDEN is an integer 0..65,535 (0 is a continuation placeholder; a new model requires at least 1). EPOCHS is an integer 0..2,147,483,646; 0 saves initialization without training. SEED is an unsigned 32-bit decimal integer; 0 retains the original alias for seed 1. RATE must be finite, positive and at most 1,000,000.
* Invalid numeric tokens, non-finite loaded parameters, negative normalization scales, truncated/trailing model bytes and numeric overflow fail non-zero. Continued training restores saved bfloat16 weights and reseeds its shuffle; it is not an exact interrupted float32 training resume.
* Reproducibility is byte-exact on one machine; another libm may round `expf` differently, which changes
  low bits of the weights and potentially the accuracy. The gates must still pass.
* The text data format is slow for big data (loading the 28 MB MNIST file takes about half a second), chosen because it is the simplest to audit.
* `nm`/`objdump` want section headers, so inspect `uai32.elf`; it is the same link with the table kept.

## Files

| file | purpose |
|---|---|
| `uai32.c` | the program |
| `Makefile` | `make`, `make verify`, `make measure`, `make dist`, `make clean` |
| `refcheck.py` | numpy re-implementation of inference + gradient check of one SGD step |
| `verify.sh` | the evidence script |
| `measure.sh` | trains the demo models and prints the size table |
| `check_artifacts.py` | exact model format, finite state, size, checksum and evaluation gates shared by scripts |
| `regression_tests.py` | isolated regressions for the independently demonstrated audit exploits |
| `gen_data.py`, `get_mnist.py` | dataset generation / download |
| `data/` | iris, spirals, rings (train/test); MNIST text files appear here after `get_mnist.py` |
| `dist/` | the measured deliverable: `uai32` executable, four `.model` files, `SHA256SUMS` |
| `uai32.elf` (built, not committed) | the executable with section headers, for inspection |
