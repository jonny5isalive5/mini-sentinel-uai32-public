#!/usr/bin/env python3
"""Independent check of uai32's maths, in numpy (no C code involved).

  python3 refcheck.py MODEL DATA        1. re-implements inference from the documented file format and
                                           prints accuracy/loss to compare with `uai32 test DATA MODEL`
                                        2. compares one C SGD step against the analytic gradient of
                                           softmax cross-entropy (needs ./uai32 in the same directory)
Exit status 0 if both agree, 1 otherwise.
"""
import os, subprocess, sys, tempfile, re, math
import numpy as np

def load(path):
    b = open(path, "rb").read()
    magic, ni, nh, no = np.frombuffer(b[:8], "<u2")
    assert magic == 0xA132, "bad magic"
    stats = np.frombuffer(b[8:8 + 8 * ni], "<f4").astype(np.float64)          # mean, scale as float32
    w = np.frombuffer(b[8 + 8 * ni:], "<u2").astype(np.uint32) << 16          # bfloat16 -> float32 bits
    w = w.view("<f4").astype(np.float64)
    assert w.size == nh * (ni + 1) + no * (nh + 1), "file size does not match header"
    W1 = w[:nh * (ni + 1)].reshape(nh, ni + 1); W2 = w[nh * (ni + 1):].reshape(no, nh + 1)
    return stats[:ni], stats[ni:], W1, W2

def forward(x, mean, scale, W1, W2):
    xn = (x - mean) * scale
    h = np.maximum(W1[:, :-1] @ xn + W1[:, -1], 0)
    z = W2[:, :-1] @ h + W2[:, -1]
    lse = z.max() + np.log(np.exp(z - z.max()).sum())
    return xn, h, z, lse

def main(model, data):
    mean, scale, W1, W2 = load(model)
    rows = np.loadtxt(data, ndmin=2); X, y = rows[:, :-1], rows[:, -1].astype(int)
    ok = loss = 0.0
    for xi, yi in zip(X, y):
        _, _, z, lse = forward(xi, mean, scale, W1, W2)
        ok += z.argmax() == yi; loss += lse - z[yi]
    print(f"numpy: loss {loss / len(y):.4f}  accuracy {int(ok)}/{len(y)} = {100 * ok / len(y):.1f}%")
    evaluation = subprocess.run(["./uai32", "test", data, model], capture_output=True, text=True)
    c = evaluation.stdout.strip()
    print("c:    ", c)
    match = re.fullmatch(r"test loss (\S+)  accuracy (\d+)/(\d+) = (\S+)%", c)
    same = evaluation.returncode == 0 and match is not None
    if same:
        closs, correct, count, accuracy = match.groups()
        closs, accuracy = float(closs), float(accuracy)
        same = (math.isfinite(closs) and math.isfinite(accuracy)
                and int(correct) == int(ok) and int(count) == len(y)
                and accuracy == float(f"{100 * ok / len(y):.1f}")
                and abs(closs - loss / len(y)) <= 0.0001)
    if not same:
        print("DISAGREE: evaluation status, accuracy or loss"); return 1
    # Gradient check: one SGD step on one example with a tiny rate, compared with the analytic gradient.
    xi = X[0]; xn, h, z, lse = forward(xi, mean, scale, W1, W2)
    lr, yi = 0.5, (int(z.argmax()) + 1) % len(z)   # a wrong label and a big rate: the update must dwarf bfloat16 rounding
    p = np.exp(z - lse); dz = p; dz[yi] -= 1
    gW2 = np.outer(dz, np.append(h, 1)); gW1 = np.outer((W2[:, :-1].T @ dz) * (h > 0), np.append(xn, 1))
    with tempfile.TemporaryDirectory() as d:
        one, m2 = os.path.join(d, "one.txt"), os.path.join(d, "m.model")
        np.savetxt(one, [np.append(xi, yi)], fmt="%.8g")
        open(m2, "wb").write(open(model, "rb").read())
        subprocess.run(["./uai32", "train", one, m2, "0", "1", str(lr)], capture_output=True, check=True)
        _, _, W1b, W2b = load(m2)
    # The C program rounds weights to bfloat16 when saving (relative error up to 2^-8), so judge only the
    # weights whose update is at least 16x that noise; for them (step - gradient)/gradient must be small.
    for name, before, after, g in (("W1", W1, W1b, gW1), ("W2", W2, W2b, gW2)):
        step = (before - after) / lr; big = np.abs(g) * lr > np.abs(after) * 2 ** -4 + 1e-6
        err = (np.abs(step[big] - g[big]) / np.abs(g[big])).max() if big.any() else 1.0
        print(f"gradient {name}: {int(big.sum())} weights checked, max relative error {err:.3g}")
        same &= big.any() and err < 0.1
    print("AGREE" if same else "DISAGREE"); return 0 if same else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
