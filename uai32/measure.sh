#!/bin/sh
# measure.sh -- the byte counts the challenge cares about.
# Trains the demo models from scratch into work/ (seconds; MNIST about 15 s when data/mnist14_train.txt
# exists, see get_mnist.py) and prints executable, model and combined sizes.
set -eu
cd "$(dirname "$0")"
LIMIT=32768
mkdir -p work
[ -x ./uai32 ] || make -s uai32
for n in iris spirals rings mnist14; do
    [ -s "data/${n}_train.txt" ] && [ -s "data/${n}_test.txt" ] || { echo "missing required dataset: $n" >&2; exit 1; }
done
size() { wc -c < "$1" | tr -d ' '; }
train() { rm -f "work/$1.model"; ./uai32 train "data/$1_train.txt" "work/$1.model" "$2" "$3" "$4" 1 > /dev/null; }
train iris     8  60 0.05
train spirals 32 500 0.05
train rings   16 200 0.05
train mnist14 48 12 0.01                     # 196-48-10: 12 epochs at 0.01, then 4 more at 0.002
./uai32 train data/mnist14_train.txt work/mnist14.model 0 4 0.002 > /dev/null
python3 check_artifacts.py work --exe ./uai32 --data data
EXE=$(size uai32)
printf '%-10s %10s %10s %10s   %s\n' model exe-bytes model-bytes combined "limit $LIMIT"
for n in iris spirals rings mnist14; do
    m=work/$n.model; [ -s "$m" ] || { echo "missing required model: $n" >&2; exit 1; }
    s=$(size "$m"); c=$((EXE + s))
    [ "$c" -le "$LIMIT" ] || { echo "$n OVER by $((c - LIMIT))" >&2; exit 1; }
    v="OK ($((LIMIT - c)) spare)"
    printf '%-10s %10d %10d %10d   %s\n' "$n" "$EXE" "$s" "$c" "$v"
done
