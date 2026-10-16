# Reproduce the exact claim

Use a disposable directory. Preserve the frozen `dist/` and audit archive before rebuilding.
Commands below run from `uai32/` unless a different directory is stated. The documented artifact is an
x86-64 Linux ELF; Windows needs a compatible Linux environment such as WSL. No native Windows,
macOS, ARM or bare-metal result is claimed.

## 1. Obtain and verify this publication copy

Use the checkout or source archive supplied with this publication. From its root, run `python -B verify_publication.py`, then enter `uai32/` for the remaining commands. Do not fetch the private historical repository or assume that its original commit exists in this fresh history.

The original audited implementation is identified by `3e924e600ef6b65eff9f00668cb283b259930049`. That is a provenance identifier, not a public checkout instruction. Computational source and dist/ artifacts are unchanged. Documentation and publication evidence may differ; their exact hashes and redactions are in the root publication provenance. No experiments were run while preparing this copy.

## 2. Check the committed artifact identity before rebuilding

```sh
(cd dist && sha256sum -c SHA256SUMS)
sha256sum dist/SHA256SUMS
wc -c dist/uai32 dist/mnist14.model
readelf -l dist/uai32
readelf -d dist/uai32
```

All five artifact checksums must be OK. The manifest itself must hash to
`036f3894d7155b71c5c46acafbceb5eac411979d3305a83f9f73ce85f39d75a9`.
Expected sizes: **9,188** and **21,468**, sum **30,656**, spare **2,112**.
Count file contents using `wc -c`, not filesystem block allocation or compressed archive size.
Inspect the ELF interpreter and NEEDED libraries; the claim excludes host libc, libm and the loader.
[EVIDENCE.md](EVIDENCE.md) lists the full hashes and the original audit archive checksum.

## 3. Prepare the verification environment and data

Required: an x86-64 Linux host, C compiler, GNU make/binutils (`ld`, `objcopy`, `readelf`), POSIX shell,
Python 3 with NumPy, SHA-256 tools, and ordinary GNU tools including awk, sed, sort, uniq, comm,
cmp, od, cut, grep, wc and mktemp. Full checks require `objcopy --strip-section-headers` support
(the recorded binutils version is 2.42) and GCC sanitizer support for AddressSanitizer,
UndefinedBehaviorSanitizer and float-cast-overflow. Missing dependencies are failures, not skips.

For Python dependencies, an optional local virtual environment keeps system packages unchanged:

```sh
python3 -m venv ../verification-env
. ../verification-env/bin/activate
python3 -m pip install numpy
mkdir -p work/reproduction-logs
uname -a > work/reproduction-logs/host.txt
cc --version > work/reproduction-logs/compiler.txt
ld --version > work/reproduction-logs/linker.txt
ldd --version > work/reproduction-logs/libc.txt
python3 --version > work/reproduction-logs/python.txt
python3 -c 'import numpy; print(numpy.__version__)' > work/reproduction-logs/numpy.txt
python3 get_mnist.py
```

The downloader validates SHA-256 for all four original compressed MNIST archives, then validates IDX
magic, dimensions, exact counts/lengths, image-label agreement and labels. It writes 60,000 training
rows and 10,000 test rows. Default preprocessing averages each 2×2 block, rounds to an integer, and
converts 28×28 images to 14×14 features. Do not use `--full` for this claim. NumPy does not run in
the C classifier; it is needed for dataset preparation and numerical verification.

## 4. Evaluate the frozen executable/model pair

```sh
python3 check_artifacts.py dist --manifest --data data
./dist/uai32 test data/mnist14_test.txt dist/mnist14.model
```

Expected MNIST output:

```text
test loss 0.0766  accuracy 9781/10000 = 97.8%
```

The exact count gives 97.81%; the program displays one decimal place. The committed executable
requires a compatible host dynamic loader and libraries. Record loading failures rather than changing
the frozen executable to make it run.

## 5. Rebuild, retrain into scratch, and run all gates

Run this block in a shell that stops on errors; it saves full outputs and does not hide a failing status
behind a logging pipeline:

```sh
set -eu
mkdir -p work/reproduction-logs
make > work/reproduction-logs/build.log 2>&1
make measure > work/reproduction-logs/measure.log 2>&1
make test > work/reproduction-logs/regressions.log 2>&1
make verify > work/reproduction-logs/verify.log 2>&1
cat work/reproduction-logs/measure.log
cat work/reproduction-logs/regressions.log
cat work/reproduction-logs/verify.log
(cd dist && sha256sum -c SHA256SUMS)
```

`make measure` starts fresh model files in `work/`, including MNIST 196-48-10, seed 1, 12 epochs at
0.01 then 4 continued epochs at 0.002. `make test` runs the 18 existing regression groups with
sanitizers. `make verify` requires the prepared MNIST scratch model and finishes with
**ALL CHECKS PASSED (28/28)** only if every mandatory check succeeds. Read the full logs and retain
their exit statuses. This block preserves the committed `dist/`.

The native compiler on your machine can produce different bytes. The recorded GCC 15.2 native build
was 9,140 bytes and passed; it was not the committed 9,188-byte executable. A functionally passing
build is not automatically byte-identical artifact reproduction. Use the next section for that claim.

## 6. Reconstruct the recorded exact build environment

The original audit used GCC 13.3, binutils 2.42, glibc 2.39 headers/startup objects and the existing
audit host's glibc 2.43 runtime. Exact `.deb` versions, download URLs, sizes and SHA-256 hashes are
inside the redacted publication evidence ZIP under `toolchain/`. The audit compiler used
`--sysroot`, a `-B` path to the extracted binutils, and fallback system include paths.
This was an isolated extracted toolchain, not a container or a fully hermetic runtime.

Copy the redacted `release/evidence/audit-3e924e6-publication.zip` to the repository root beside `uai32/`. From `uai32/`,
the following builds an isolated toolchain in the repository root; it installs no system packages.
It requires `dpkg-deb`, network access to the recorded URLs, compatible host compiler runtime
dependencies, and `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`. The exact package hashes must match.

```sh
set -eu
python3 - <<'PY'
import hashlib, json, pathlib, shutil, subprocess, urllib.request, zipfile
archive = pathlib.Path('../audit-3e924e6-publication.zip')
assert hashlib.sha256(archive.read_bytes()).hexdigest() == '1c05c151f5818558ba29b723a1792f2d57d8230fdc011e4d582b48f892f0448d'
tc = pathlib.Path('../repro-toolchain').resolve()
tc.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
    groups = [('toolchain/package-records.json', 'extracted'),
              ('toolchain/linker-libc-package-records.json', None)]
    for source, default_dest in groups:
        for record in json.loads(z.read(source)):
            name = record['url'].rsplit('/', 1)[1]
            package = tc / name
            if not package.exists():
                urllib.request.urlretrieve(record['url'], package)
            payload = package.read_bytes()
            assert len(payload) == record['bytes'], name
            assert hashlib.sha256(payload).hexdigest() == record['sha256'], name
            destination = default_dest or ('sysroot' if name.startswith('libc6') else 'binutils')
            target = tc / destination
            target.mkdir(exist_ok=True)
            subprocess.run(['dpkg-deb', '-x', str(package), str(target)], check=True)
for name, target in [('ld', 'x86_64-linux-gnu-ld.bfd'), ('as', 'x86_64-linux-gnu-as')]:
    link = tc / 'binutils/usr/bin' / name
    if not link.exists():
        link.symlink_to(target)
for name, target in [('lib', 'usr/lib'), ('lib64', 'usr/lib64')]:
    link = tc / 'sysroot' / name
    if not link.exists():
        link.symlink_to(target)
shutil.copy2('/usr/lib/x86_64-linux-gnu/libgcc_s.so.1', tc / 'sysroot/usr/lib/x86_64-linux-gnu/libgcc_s.so.1')
print(tc)
PY
TC=$(cd ../repro-toolchain && pwd)
export LD_LIBRARY_PATH="$TC/binutils/usr/lib/x86_64-linux-gnu"
export CC="$TC/extracted/usr/bin/x86_64-linux-gnu-gcc-13 --sysroot=$TC/sysroot -B$TC/binutils/usr/bin/ -idirafter /usr/include -idirafter /usr/include/x86_64-linux-gnu"
make -B
cmp uai32 dist/uai32
make measure
CC=cc make test
make verify
for n in iris mnist14 rings spirals; do cmp "work/$n.model" "dist/$n.model"; done
```

Use a scratch path without spaces for this compiler-command recipe. `cmp` must exit 0 for each file.
The regression harness expects `CC` to be a single executable path, so its invocation explicitly uses
the native `cc` for its sanitizer build. The original audit also used the native GCC 15.2 sanitizer
suite alongside the pinned executable reproduction; the extracted multi-argument `CC` command is for make.
The audit archive retains the original package extraction and build harnesses for method comparison.
A mismatch requires investigation, including host runtime math, include files and compiler dependencies;
do not replace a committed artifact or weaken a gate to call a different result identical.

## 7. Optional full distribution reproduction, only in a second disposable copy

`make dist` trains and validates a new distribution and then replaces `dist/`. `make clean` deletes
`dist/`. Neither belongs in the preserved baseline checkout. To test publication, first copy the whole
working `uai32/` tree into a new disposable directory, retaining your recorded compiler environment.
From that copy:

```sh
set -eu
cp -a dist frozen-dist
make dist
for n in uai32 iris.model mnist14.model rings.model spirals.model SHA256SUMS; do
    cmp "frozen-dist/$n" "dist/$n"
done
(cd dist && sha256sum -c SHA256SUMS)
```

Exact reproduction means every comparison exits 0. A native build on a different toolchain may
correctly pass its size/evaluation gates but fail byte comparison. Keep those two results separate.

## Report a result

Attach commit, environment versions, commands, raw logs, exit codes, executable/model hashes,
byte counts and exact correct/total predictions. Report any mandatory failure and any artifact
mismatch. [CHALLENGE.md](CHALLENGE.md) provides a counterexample template.
