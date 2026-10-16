#!/usr/bin/env python3
"""Fail-closed checks shared by verify.sh, measure.sh and the dist target."""
import argparse, hashlib, math, pathlib, re, struct, subprocess

MODELS = {"iris": (4, 8, 3), "spirals": (2, 32, 2), "rings": (2, 16, 3), "mnist14": (196, 48, 10)}
FILES = {"uai32", *(name + ".model" for name in MODELS)}

def model(path, dimensions):
    b = path.read_bytes()
    if len(b) < 8: raise ValueError("truncated model: " + str(path))
    magic, ni, nh, no = struct.unpack("<4H", b[:8])
    size = 8 + 8 * ni + 2 * (nh * (ni + 1) + no * (nh + 1))
    if magic != 0xA132 or (ni, nh, no) != dimensions or len(b) != size:
        raise ValueError("invalid model magic, dimensions or size: " + str(path))
    stats = struct.unpack("<" + "f" * (2 * ni), b[8:8 + 8 * ni])
    weights = (struct.unpack("<f", struct.pack("<I", w << 16))[0]
               for (w,) in struct.iter_unpack("<H", b[8 + 8 * ni:]))
    if not all(map(math.isfinite, stats)) or any(s < 0 for s in stats[ni:]) or not all(map(math.isfinite, weights)):
        raise ValueError("invalid model parameter: " + str(path))

def manifest(directory):
    records = {}
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        m = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.]+)", line)
        if not m or m[2] in records: raise ValueError("invalid checksum manifest")
        records[m[2]] = m[1]
    if set(records) != FILES: raise ValueError("incomplete checksum manifest")
    for name, digest in records.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError("artifact checksum mismatch: " + name)

def evaluate(exe, data, path, name):
    p = subprocess.run([str(exe.resolve()), "test", str(data / (name + "_test.txt")), str(path)], capture_output=True, text=True, check=True)
    m = re.fullmatch(r"test loss (\S+)  accuracy (\d+)/(\d+) = (\S+)%", p.stdout.strip())
    if not m: raise ValueError("invalid evaluation output")
    loss, correct, count, accuracy = float(m[1]), int(m[2]), int(m[3]), float(m[4])
    total, minimum = {"iris": (30, 27), "spirals": (300, 285), "rings": (300, 285), "mnist14": (10000, 9781)}[name]
    if not math.isfinite(loss) or not math.isfinite(accuracy) or count != total or correct < minimum or correct > count or accuracy != float(f"{100 * correct / count:.1f}"):
        raise ValueError("accuracy/loss/count criterion failed: " + name)
    print(name + ": " + p.stdout.strip())

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("directory", type=pathlib.Path)
    p.add_argument("--exe", type=pathlib.Path); p.add_argument("--manifest", action="store_true")
    p.add_argument("--mnist", action="store_true"); p.add_argument("--data", type=pathlib.Path); a = p.parse_args()
    exe = a.exe or a.directory / "uai32"
    if not exe.is_file() or exe.stat().st_size == 0: raise ValueError("missing executable")
    names = ["mnist14"] if a.mnist else MODELS
    for name in names:
        path = a.directory / (name + ".model"); model(path, MODELS[name])
        if exe.stat().st_size + path.stat().st_size > 32768: raise ValueError("size limit exceeded: " + name)
        if a.data: evaluate(exe, a.data, path, name)
    if a.manifest: manifest(a.directory)

if __name__ == "__main__": main()
