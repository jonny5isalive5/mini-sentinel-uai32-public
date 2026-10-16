# Evidence and provenance

## Audit identity and publication redactions

Original audited implementation: `3e924e600ef6b65eff9f00668cb283b259930049`. The original repository and history remain private; the new publication history does not contain that commit.

The [results JSON](evidence/audit-3e924e6-results.json) records the historical PASS for two remaining P2 findings and the release gates. This was an AI-assisted checking pass, not a third-party laboratory certification or a new audit of this publication.

The [publication evidence ZIP](evidence/audit-3e924e6-publication.zip) has 49 original member paths. Personal workspace locations and private origin references have been redacted in selected text members; source/artifact snapshots and numerical outcomes are preserved. The root publication provenance maps each original member hash to its publication hash. Original private archive SHA-256: `110fd5fa62c87d4324d0a71111aeb4f4d0f23406f7982dcc34663eefd268c734`.

Publication archive SHA-256: `1c05c151f5818558ba29b723a1792f2d57d8230fdc011e4d582b48f892f0448d`. Its [checksum file](evidence/audit-3e924e6-publication.sha256) applies only to this redacted archive. Use `python -B verify_publication.py` from the repository root to verify all publication bytes. Historical harness paths are illustrative aliases, not portable installation instructions; see [REPRODUCE.md](REPRODUCE.md).

| Recorded result | Evidence inside the ZIP |
|---|---|
| 28/28 mandatory checks under the pinned build | `logs/audit3-pinned-verify.log` |
| 18 regression groups; 222 recorded subprocess invocations; 92 sanitizer invocations | `logs/audit3-regressions.log`, `results/regression-results.json`, `audit-summary.json` |
| Committed MNIST pair: 9,781/10,000, loss 0.0766 | `logs/audit3-committed-score.log` |
| Byte-identical executable, four models and manifest; clean checkout | `harness/audit3-pinned-release-results.json`, `logs/audit3-pinned-dist.log` |
| Overflow rejects ±3e38; ±1.7e38 control succeeds | `results/focused-audit-results.json` |
| Final publication rename failure restores the preceding distribution | `results/focused-audit-results.json`, `harness/audit3-focused-probes.py` |
| Compiler/linker/libc package URLs, hashes and sizes | `toolchain/package-records.json`, `toolchain/linker-libc-package-records.json` |

The 222 figure counts recorded invocations from that run; it is not a promised fixed count of every
future run. PASS describes observed behavior within the audit scope, not proof that no defect exists.

## Artifact identity

These are the bytes committed at the audited SHA. Check `dist/SHA256SUMS` from inside `dist/` before
running or rebuilding. The manifest itself is hashed here to bind its identity as well.

| File | Bytes | SHA-256 |
|---|---:|---|
| `dist/uai32` | 9,188 | `996d73cba9676e8932206b9c80493becde6d04b6a57b70839999b0824c0186cb` |
| `dist/iris.model` | 174 | `2a859cf4edba8af4de4fa0a598dfc26280c3ecb914d298260c8846de1671fb48` |
| `dist/mnist14.model` | 21,468 | `24092e4006782550ac02a355d8e4d6bd24eb272a94993152fc159467cfc80c80` |
| `dist/rings.model` | 222 | `7e12bcb541bc8ce39117437458bbd40306f562722a668904fc03cb903b7fc834` |
| `dist/spirals.model` | 348 | `d9a5b4228c59479837c2c77f91a19e0ce7cb9c19561e4ff8f136e69c46bfbb82` |
| `dist/SHA256SUMS` | 387 | `036f3894d7155b71c5c46acafbceb5eac411979d3305a83f9f73ce85f39d75a9` |

The exact reproduction used GCC 13.3, binutils 2.42, and glibc 2.39 headers/startup objects, running
on the audit host with glibc 2.43. A GCC 15.2 / binutils 2.46 / glibc 2.43 native build was **9,140 bytes**
and passed its gates but is a different executable. Its hash in publication-failure probe records must
not be substituted for the **9,188-byte committed executable** identified above.

## What remains open

The archive is preserved evidence, not a hermetic build environment. Runtime libraries and every host
tool are not bundled. The existing numerical reference check covers inference and one SGD step above
bfloat16 rounding noise, not a formal proof of the complete program. Test coverage and source-hash checks
cannot prove the absence of hidden defects or historical benchmark tuning. These are challenge targets.
