#!/bin/sh
# verify.sh -- evidence that uAI-32 meets every requirement of the Sentovara challenge.
# Every check prints PASS or FAIL with the numbers behind it; the exit status is non-zero if any check fails.
# Full verification requires python3+numpy, GNU objcopy and prepared MNIST data/models. No checks are optional.
set -eu
cd "$(dirname "$0")"
LIMIT=32768; W=work; FAIL=0; CHECKS=0; EXPECTED=28
mkdir -p $W; cd $W && rm -f iris0.model iris.model iris_again.model spirals.model rings.model scrambled.model copy.model more.model twin *.txt *.out; cd ..
size() { wc -c < "$1" | tr -d ' '; }
acc()  { output=$(./uai32 test "$1" "$2") || return 1; printf '%s\n' "$output" | awk -F'= ' '{print $2+0}'; }
check() { CHECKS=$((CHECKS + 1)); if [ "$1" -eq 1 ]; then echo "PASS  $2"; else echo "FAIL  $2"; FAIL=1; fi; }
ge() { awk "BEGIN{exit !($1 >= $2)}"; }   # float compare: ge A B

echo "== 0. build from source"
make -s uai32 uai32.elf || { echo "FAIL  build"; exit 1; }
python3 -c 'import numpy' || { echo "FAIL  numpy is required"; exit 1; }
python3 check_artifacts.py work --exe ./uai32 --mnist
python3 check_artifacts.py dist --manifest
check 1 "committed artifacts have valid formats, sizes and SHA-256 checksums"
EXE=$(size uai32)
check $((EXE <= LIMIT)) "executable is $EXE bytes (limit $LIMIT)"
S1=$(sha256sum uai32 | cut -c1-16); make -s -B uai32 > /dev/null; S2=$(sha256sum uai32 | cut -c1-16)
check $([ "$S1" = "$S2" ] && echo 1 || echo 0) "building twice gives the same bytes (sha256 $S1...)"
if objcopy --strip-section-headers uai32.elf $W/twin; then
    check $(cmp -s $W/twin uai32 && echo 1 || echo 0) "uai32 is exactly uai32.elf ($(size uai32.elf) bytes) minus the ELF section header table"
else check 0 "section-header identity check could not run"; fi

echo "== 1. it learns: the same program, before and after training (iris, 4-8-3)"
./uai32 train data/iris_train.txt $W/iris0.model 8 0 0.05 1 > /dev/null   # 0 epochs = random initial weights, saved
./uai32 train data/iris_train.txt $W/iris.model  8 60 0.05 1 > $W/iris_train.out
A0=$(acc data/iris_test.txt $W/iris0.model); A1=$(acc data/iris_test.txt $W/iris.model)
check $(ge "$A1" 90 && ge "$A1" "$A0 + 20" && echo 1 || echo 0) "held-out accuracy went from $A0% (untrained) to $A1% (after 60 epochs)"
L1=$(sed -n '2p' $W/iris_train.out | awk '{print $5}'); L2=$(tail -1 $W/iris_train.out | awk '{print $5}')   # "epoch 1/60  train loss L ..." 
check $(ge "$L1" "$L2 * 2" && echo 1 || echo 0) "training loss fell from $L1 (epoch 1) to $L2 (epoch 60)"
T1=$(tail -1 $W/iris_train.out | awk -F'= ' '{print $2+0}'); T2=$(acc data/iris_train.txt $W/iris.model)
check $([ "$T1" = "$T2" ] && echo 1 || echo 0) "the reloaded bfloat16 model scores the same on the training set as the in-memory float32 one ($T1%)"

echo "== 2. it alters internal state: the saved weights change"
if [ -s $W/iris0.model ] && [ -s $W/iris.model ] && ! cmp -s $W/iris0.model $W/iris.model; then check 1 "model file changed (same size: $(size $W/iris0.model) -> $(size $W/iris.model) bytes)"; else check 0 "model bytes changed"; fi

echo "== 3. it generalises: accuracy on examples never seen in training"
D=$(sort data/spirals_train.txt data/spirals_test.txt data/rings_train.txt data/rings_test.txt | uniq -d | wc -l)
sort -u data/iris_train.txt > $W/a.txt; sort -u data/iris_test.txt > $W/b.txt; DI=$(comm -12 $W/a.txt $W/b.txt | wc -l | tr -d ' ')
check $((D == 0)) "no spirals/rings test row also appears in training ($DI iris test row is a verbatim duplicate of a training row: the UCI file itself has duplicate flowers)"
./uai32 train data/spirals_train.txt $W/spirals.model 32 500 0.05 1 > /dev/null
./uai32 train data/rings_train.txt   $W/rings.model   16 200 0.05 1 > /dev/null
S=$(acc data/spirals_test.txt $W/spirals.model); R=$(acc data/rings_test.txt $W/rings.model)
check $(ge "$A1" 90 && echo 1 || echo 0) "iris:    $A1% on 30 held-out flowers"
check $(ge "$S" 95 && echo 1 || echo 0)  "spirals: $S% on 300 unseen points (curved boundary, 2 classes)"
check $(ge "$R" 95 && echo 1 || echo 0)  "rings:   $R% on 300 unseen points (3 concentric classes)"
# Control: destroy the relationship between features and labels; the model must then fail on the test set.
awk '{ $NF = ($NF + NR) % 2; print }' data/spirals_train.txt > $W/spirals_scrambled.txt
./uai32 train $W/spirals_scrambled.txt $W/scrambled.model 32 500 0.05 1 > /dev/null
C=$(acc data/spirals_test.txt $W/scrambled.model)
check $(ge 65 "$C" && echo 1 || echo 0) "control: trained on scrambled labels it scores $C% (chance is 50%), so the skill comes from the data"

echo "== 4. it saves, reloads and keeps inferring"
cp $W/spirals.model $W/copy.model
./uai32 predict $W/spirals.model < data/spirals_test.txt > $W/p1.out
./uai32 predict $W/copy.model    < data/spirals_test.txt > $W/p2.out
awk '{print $NF}' data/spirals_test.txt > $W/labels.txt
P=$(awk 'NR==FNR{l[FNR]=$1; next} l[FNR]==$1{c++} END{printf "%.1f", 100*c/FNR}' $W/labels.txt $W/p1.out)
check $(cmp -s $W/p1.out $W/p2.out && echo 1 || echo 0) "a fresh process reading a copy of the model file gives identical predictions ($(wc -l < $W/p1.out) rows)"
check $(ge "$P" 95 && echo 1 || echo 0) "those predictions are $P% correct on the unseen rows"

echo "== 5. training can continue from the saved state"
cp $W/spirals.model $W/more.model
./uai32 train data/spirals_train.txt $W/more.model 0 100 0.01 > $W/cont.out    # file exists -> loads and continues
S2=$(acc data/spirals_test.txt $W/more.model)
check $(grep -q '^continuing' $W/cont.out && ! cmp -s $W/spirals.model $W/more.model && ge "$S2" 95 && echo 1 || echo 0) "reloaded, trained 100 more epochs at a lower rate: weights changed, $S2% held-out"

echo "== 6. reproducible: same data and seed give a byte-identical model"
./uai32 train data/iris_train.txt $W/iris_again.model 8 60 0.05 1 > /dev/null
check $(cmp -s $W/iris.model $W/iris_again.model && echo 1 || echo 0) "two training runs with seed 1 produce the same bytes"

echo "== 7. the maths, checked independently"
for n in iris spirals rings; do
    s=$(size $W/$n.model); p=$(od -An -tu2 -j2 -N6 $W/$n.model | awk '{print 8 + 8*$1 + 2*($2*($1+1) + $3*($2+1))}')
    check $((s == p)) "$n.model is $s bytes = 8 + 8*NI + 2*(NH*(NI+1) + NO*(NH+1)) from its own header"
done
python3 refcheck.py $W/spirals.model data/spirals_test.txt > $W/ref.out 2>&1
check $(grep -q '^AGREE' $W/ref.out && echo 1 || echo 0) "numpy re-implementation reproduces the C accuracy/loss and the backprop step matches the analytic gradient"
sed 's/^/      /' $W/ref.out | grep -E 'numpy|c:|gradient'
python3 check_artifacts.py work --exe ./uai32
check 1 "all four scratch models have the required dimensions, finite parameters and exact sizes"
python3 check_artifacts.py work --exe ./uai32 --mnist --data data
check 1 "scratch MNIST model loads and scores at least 9781/10000"
python3 check_artifacts.py dist --mnist --data data
check 1 "committed MNIST executable/model loads and scores at least 9781/10000"

echo "== 8. size: executable + saved learned state must be <= $LIMIT bytes"
for n in iris spirals rings; do
    s=$(size $W/$n.model); c=$((EXE + s))
    check $((c <= LIMIT)) "$n: $EXE + $s = $c bytes ($((LIMIT - c)) spare)"
done
s=$(size $W/mnist14.model); c=$((EXE + s)); check $((c <= LIMIT)) "mnist14: $EXE + $s = $c bytes ($((LIMIT - c)) spare)"

if [ "$FAIL" -eq 0 ] && [ "$CHECKS" -eq "$EXPECTED" ]; then
    echo "ALL CHECKS PASSED ($CHECKS/$EXPECTED)"
else
    echo "SOME CHECKS FAILED ($CHECKS/$EXPECTED)"; exit 1
fi
