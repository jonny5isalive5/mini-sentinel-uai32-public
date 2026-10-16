# Mini Sentinel — Sentovara µAI-32

A small trainable neural classifier in C. The recorded audited x86-64 Linux executable is **9,188 bytes**; its MNIST model is **21,468 bytes**, for **30,656 bytes combined**. The recorded result was **9,781/10,000 correct** on the standard MNIST test set after the documented preprocessing.

These are historical results, not a new validation. The size claim excludes host libraries, operating system, RAM, datasets and tooling. This is not a language model, a general-intelligence result or a production safety certification. The Iris record includes a duplicated train/test row.

## Contents

- [Project guide](uai32/README.md): source, use, measurements and limitations.
- [Reproduction guide](uai32/release/REPRODUCE.md): current package checks and toolchain requirements.
- [Evidence](uai32/release/EVIDENCE.md): preserved audit outcomes and the explicitly redacted archive.
- [Publication provenance](PUBLICATION_PROVENANCE.json): original and publication hashes, including every archive member.

The executable, all models, data, computational source and tests are unchanged. Documentation has been updated and personal workspace paths/private session references removed from publication evidence. Redacted files are not described as original bytes. The untouched originals and full development history remain private. This repository starts a fresh history; old commits and tags are not imported.

## Verify without running an experiment

```sh
python -B verify_publication.py
```

This only checks local file and archive hashes; it does not run the model, train, download data or access credentials.

## Attribution and licence

Project direction and release stewardship: **Sentovara**. Recorded engineering contributors: **OpenAI GPT-5.6 Sol, Anthropic Fable 5.1 and OpenAI Codex**.

Project code and documentation retain [Apache-2.0](LICENSE) and the [NOTICE](NOTICE). [Third-party notices](uai32/release/THIRD_PARTY_NOTICES.md) retain the Iris attribution and CC BY 4.0 terms. No MNIST images, labels, source archives or generated dataset files are bundled; the original learned model remains. Upstream MNIST licensing uncertainty is unchanged, and Sentovara grants no MNIST dataset rights.
