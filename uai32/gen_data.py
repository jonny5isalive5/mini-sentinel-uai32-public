#!/usr/bin/env python3
"""Generate the small datasets that ship with uAI-32 (deterministic, numpy only).

  python3 gen_data.py            writes data/*.txt

Datasets
  iris      Fisher's iris flowers (UCI, 150 rows, 4 features, 3 classes) from data/iris.data,
            shuffled with a fixed seed and split 120 train / 30 test.
  spirals   two interleaved spirals (2 features, 2 classes), 600 train / 300 test, noise 0.05.
            Not linearly separable: a model has to learn a curved boundary to generalise.
  rings     three concentric rings (2 features, 3 classes), 600 train / 300 test.
Every file: one example per line, features then the integer class label.
"""
import os, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")

def write(name, X, y):
    with open(os.path.join(OUT, name), "w") as f:
        for row, lab in zip(X, y):
            f.write(" ".join(f"{v:.4f}" for v in row) + f" {int(lab)}\n")
    print(f"{name}: {len(y)} rows, {X.shape[1]} features, {int(y.max()) + 1} classes")

def split(X, y, n_test, rng):
    order = rng.permutation(len(y))
    X, y = X[order], y[order]
    return (X[n_test:], y[n_test:]), (X[:n_test], y[:n_test])

def iris(rng):
    names = {"Iris-setosa": 0, "Iris-versicolor": 1, "Iris-virginica": 2}
    rows = [l.strip().split(",") for l in open(os.path.join(OUT, "iris.data")) if l.strip()]
    X = np.array([[float(v) for v in r[:4]] for r in rows])
    y = np.array([names[r[4]] for r in rows])
    (Xa, ya), (Xb, yb) = split(X, y, 30, rng)
    write("iris_train.txt", Xa, ya); write("iris_test.txt", Xb, yb)

def spirals(rng, n=900):
    per = n // 2
    t = np.sqrt(rng.uniform(0, 1, per)) * 3 * np.pi + 0.5
    pts, labs = [], []
    for c in range(2):
        a = t + c * np.pi
        r = t / (3 * np.pi + 0.5)
        pts.append(np.stack([r * np.cos(a), r * np.sin(a)], 1) + rng.normal(0, 0.05, (per, 2)))
        labs.append(np.full(per, c))
    X, y = np.concatenate(pts), np.concatenate(labs)
    (Xa, ya), (Xb, yb) = split(X, y, 300, rng)
    write("spirals_train.txt", Xa, ya); write("spirals_test.txt", Xb, yb)

def rings(rng, n=900):
    per = n // 3
    pts, labs = [], []
    for c in range(3):
        a = rng.uniform(0, 2 * np.pi, per)
        r = 0.3 + 0.35 * c + rng.normal(0, 0.05, per)
        pts.append(np.stack([r * np.cos(a), r * np.sin(a)], 1))
        labs.append(np.full(per, c))
    X, y = np.concatenate(pts), np.concatenate(labs)
    (Xa, ya), (Xb, yb) = split(X, y, 300, rng)
    write("rings_train.txt", Xa, ya); write("rings_test.txt", Xb, yb)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(32)
    iris(rng); spirals(rng); rings(rng)
