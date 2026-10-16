#!/usr/bin/env python3
"""Download MNIST (70,000 handwritten digits) and write it in uAI-32's text format.

  python3 get_mnist.py            -> data/mnist14_train.txt (60,000 rows), data/mnist14_test.txt (10,000 rows)
  python3 get_mnist.py --full     -> data/mnist28_*.txt with all 784 pixels instead of 14x14

By default each 28x28 image is average-pooled 2x2 to 14x14 = 196 features (integers 0..255),
which keeps the text files and the training time small.  Files are not committed (see .gitignore).
Every archive, cached or freshly downloaded, must match its pinned SHA-256; the IDX magic numbers,
counts, dimensions, lengths and image/label agreement are validated; anything malformed exits non-zero.
Source: Yann LeCun / Corinna Cortes / Christopher Burges, MNIST database (CC BY-SA 3.0),
mirrored at storage.googleapis.com/cvdf-datasets/mnist/ and ossci-datasets.s3.amazonaws.com/mnist/.
"""
import gzip, os, struct, sys, urllib.request, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
MIRRORS = ["https://storage.googleapis.com/cvdf-datasets/mnist/", "https://ossci-datasets.s3.amazonaws.com/mnist/"]
FILES = {"train": ("train-images-idx3-ubyte.gz", "train-labels-idx1-ubyte.gz"),
         "test": ("t10k-images-idx3-ubyte.gz", "t10k-labels-idx1-ubyte.gz")}
HASHES = {"train-images-idx3-ubyte.gz": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",   # SHA-256
          "train-labels-idx1-ubyte.gz": "3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
          "t10k-images-idx3-ubyte.gz": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
          "t10k-labels-idx1-ubyte.gz": "f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6"}

def checked_archive(path, name):
    with open(path, "rb") as f:
        compressed = f.read()
    if hashlib.sha256(compressed).hexdigest() != HASHES[name]:
        raise ValueError("MNIST source hash mismatch: " + name)
    return gzip.decompress(compressed)

def fetch(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        for m in MIRRORS:
            try:
                print("downloading", m + name); urllib.request.urlretrieve(m + name, path + ".part")
                raw = checked_archive(path + ".part", name)
                os.replace(path + ".part", path); return raw
            except Exception as e:  # try the next mirror; a half-written file is never kept
                print("  failed:", e)
                if os.path.exists(path + ".part"): os.remove(path + ".part")
        else:
            sys.exit("could not download " + name)
    return checked_archive(path, name)

def decode(images, labels, count):
    if len(images) < 16 or len(labels) < 8:
        raise ValueError("truncated MNIST header")
    magic, n, h, w = struct.unpack(">IIII", images[:16])
    lm, ln = struct.unpack(">II", labels[:8])
    if (magic, n, h, w) != (2051, count, 28, 28) or (lm, ln) != (2049, count):
        raise ValueError("invalid MNIST magic, dimensions or image/label count")
    if len(images) != 16 + n * h * w or len(labels) != 8 + n:
        raise ValueError("wrong MNIST payload length or image/label count")
    X = np.frombuffer(images[16:], dtype=np.uint8).reshape(n, h, w)
    y = np.frombuffer(labels[8:], dtype=np.uint8)
    if np.any(y > 9): raise ValueError("MNIST label outside 0..9")
    return X, y

def main(full):
    os.makedirs(OUT, exist_ok=True)
    for split, (img, lab) in FILES.items():
        X, y = decode(fetch(img), fetch(lab), 60000 if split == "train" else 10000)
        n = len(y)
        if not full:  # 2x2 average pooling, 28x28 -> 14x14
            X = X.reshape(n, 14, 2, 14, 2).mean(axis=(2, 4)).round().astype(np.uint8)
        X = X.reshape(n, -1)
        name = f"mnist{28 if full else 14}_{split}.txt"
        with open(os.path.join(OUT, name), "w") as f:
            for row, lab in zip(X, y):
                f.write(" ".join(map(str, row.tolist())) + f" {lab}\n")
        print(f"{name}: {n} rows, {X.shape[1]} features")

if __name__ == "__main__":
    main("--full" in sys.argv)
