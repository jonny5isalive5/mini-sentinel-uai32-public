#!/usr/bin/env python3
"""Regression tests for every exploit in the 04a43fd and 82bd1f independent audits.

Run after make + get_mnist.py + make dist. Every destructive fixture is an isolated copy.
"""
import gzip, hashlib, importlib.util, json, os, pathlib, re, shlex, shutil, struct
import subprocess, sys, tempfile, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent
RECORDS = []

class AuditRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="uai32-regression-")
        cls.base = pathlib.Path(cls.scratch.name)
        cls.sanitized = cls.base / "sanitized"
        subprocess.run([os.environ.get("CC", "cc"), "-std=c99", "-O1", "-g", "-ffp-contract=off",
                        "-fsanitize=address,undefined,float-cast-overflow", "-fno-sanitize-recover=all",
                        str(ROOT / "uai32.c"), "-lm", "-o", str(cls.sanitized)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()
        (ROOT / "work").mkdir(exist_ok=True)
        (ROOT / "work/regression-results.json").write_text(json.dumps(RECORDS, indent=2) + "\n")

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(dir=self.base))

    def invoke(self, args, *, cwd=None, input=None, env=None, fails=True):
        e = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "halt_on_error=1", **(env or {})}
        p = subprocess.run([str(a) for a in args], cwd=cwd or ROOT, env=e, input=input,
                           capture_output=True, text=True, timeout=90)
        RECORDS.append({"test": self.id(), "args": list(map(str, args)), "returncode": p.returncode,
                        "stdout": p.stdout, "stderr": p.stderr})
        self.assertNotRegex(p.stderr, r"AddressSanitizer:|runtime error:|UndefinedBehaviorSanitizer:")
        if fails:
            self.assertGreater(p.returncode, 0, p.stdout + p.stderr)
            self.assertNotIn("ALL CHECKS PASSED", p.stdout)
        else: self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def fixture(self):
        p = self.tmp / "fixture"; p.mkdir()
        for f in ROOT.iterdir():
            if f.is_file(): shutil.copy2(f, p / f.name)
        shutil.copytree(ROOT / "dist", p / "dist")
        (p / "data").symlink_to(ROOT / "data", target_is_directory=True)
        (p / "work").mkdir(); shutil.copy2(ROOT / "dist/mnist14.model", p / "work/mnist14.model")
        return p

    def test_numeric_arguments_reject_before_conversion(self):
        invalid = {0: ["nan", "inf", "-inf", "-1", "65536", "1.5", "8junk", ""],
                   1: ["nan", "inf", "-inf", "-1", "2147483647", "1.5", "1junk", ""],
                   2: ["nan", "inf", "-inf", "0", "-1", "1000001", "1e-999", "0.05junk", ""],
                   3: ["nan", "inf", "-inf", "-1", "4294967296", "99999999999999999999999", "1.5", "1junk", ""]}
        for exe in [ROOT / "uai32", self.sanitized]:
            for index, tokens in invalid.items():
                for token in tokens:
                    with self.subTest(exe=exe.name, argument=index, token=token):
                        m = self.tmp / "state.model"; original = (ROOT / "dist/iris.model").read_bytes(); m.write_bytes(original)
                        values = ["8", "1", "0.05", "1"]; values[index] = token
                        self.invoke([exe, "train", ROOT / "data/iris_train.txt", m, *values])
                        self.assertEqual(m.read_bytes(), original)

    def test_valid_numeric_boundaries(self):
        for seed in ["0", "1", "4294967295"]:
            m = self.tmp / (seed + ".model")
            self.invoke([ROOT / "uai32", "train", ROOT / "data/iris_train.txt", m, "8", "0", "0.05", seed], fails=False)
        self.invoke([ROOT / "uai32", "train", ROOT / "data/iris_train.txt", self.tmp / "new.model", "0", "0", "0.05"])

    def test_nonfinite_features_labels_and_out_of_range_labels(self):
        for exe in [ROOT / "uai32", self.sanitized]:
            for token in ["nan", "inf", "-inf", "1e30", "65535", "-1", "1.5", "1.00000001", "0junk"]:
                with self.subTest(exe=exe.name, label=token):
                    data = self.tmp / "label.txt"; data.write_text("5.1 3.5 1.4 0.2 " + token + "\n")
                    self.invoke([exe, "test", data, ROOT / "dist/iris.model"])
            for token in ["nan", "inf", "-inf", "1e999", "1junk"]:
                with self.subTest(exe=exe.name, feature=token):
                    data = self.tmp / "feature.txt"; data.write_text(token + " 3.5 1.4 0.2 0\n")
                    self.invoke([exe, "test", data, ROOT / "dist/iris.model"])

    def test_bad_model_headers_lengths_dimensions(self):
        original = (ROOT / "dist/iris.model").read_bytes()
        invalid = [b"x", b"\0" * len(original), original[:-1], original + b"trailing",
                   *(struct.pack("<4H", 0xA132, *d) for d in [(0,0,0), (0,1,1), (1,0,1), (1,1,0), (65535,65535,65535)])]
        for exe in [ROOT / "uai32", self.sanitized]:
            for i, blob in enumerate(invalid):
                with self.subTest(exe=exe.name, case=i):
                    m = self.tmp / "bad.model"; m.write_bytes(blob)
                    self.invoke([exe, "predict", m], input="1 0\n")
                    self.invoke([exe, "train", ROOT / "data/iris_train.txt", m, "0", "1", "0.01"])
                    self.assertEqual(m.read_bytes(), blob)

    def test_nonfinite_loaded_parameters_cannot_evaluate_or_overwrite(self):
        original = (ROOT / "dist/iris.model").read_bytes()
        # mean, scale, W1 and W2; both NaN and infinity, plus a negative scale.
        for offset, width in [(8,4), (24,4), (40,2), (120,2)]:
            for bits in ([0x7fc00000,0x7f800000,0xff800000] if width==4 else [0x7fc0,0x7f80,0xff80]):
                for exe in [ROOT / "uai32", self.sanitized]:
                    with self.subTest(offset=offset, bits=bits, exe=exe.name):
                        b=bytearray(original); struct.pack_into("<I" if width==4 else "<H",b,offset,bits)
                        m=self.tmp/"bad.model"; m.write_bytes(b)
                        self.invoke([exe,"test",ROOT/"data/iris_test.txt",m])
                        self.invoke([exe,"train",ROOT/"data/iris_train.txt",m,"0","1","0.01"])
                        self.assertEqual(m.read_bytes(),b)
        b=bytearray(original); struct.pack_into("<f",b,24,-1); m=self.tmp/"negative.model"; m.write_bytes(b)
        self.invoke([self.sanitized,"test",ROOT/"data/iris_test.txt",m])

    def test_reference_checker_rejects_each_evaluation_fault(self):
        for fault in ["loss", "nan", "inf", "exit", "accuracy"]:
            with self.subTest(fault=fault):
                p=self.tmp/fault; p.mkdir()
                script = ("#!/usr/bin/env python3\nimport subprocess,sys\n"
                          f"r=subprocess.run([{str(ROOT/'uai32')!r},*sys.argv[1:]],capture_output=True,text=True)\n"
                          "s=r.stdout\nif sys.argv[1]=='test':\n"
                          f" fault={fault!r}\n"
                          " if fault in ('loss','nan','inf'): s=s.replace(s.split()[2],{'loss':'12345.0000','nan':'nan','inf':'inf'}[fault],1)\n"
                          " if fault=='accuracy': s=s.replace('298/300 = 99.3%','0/300 = 0.0%')\n"
                          " if fault=='exit': r.returncode=7\n"
                          "print(s,end='');sys.stderr.write(r.stderr);sys.exit(r.returncode)\n")
                (p/'uai32').write_text(script); (p/'uai32').chmod(0o755)
                r=self.invoke([sys.executable,ROOT/'refcheck.py',ROOT/'dist/spirals.model',ROOT/'data/spirals_test.txt'],cwd=p)
                self.assertNotRegex(r.stdout,r"(?m)^AGREE$")

    def test_verifier_rejects_missing_corrupt_and_invalid_mnist(self):
        original=(ROOT/'dist/mnist14.model').read_bytes()
        blobs=[None,b'x',b'\0'*len(original),struct.pack('<4H',0xa132,0,0,0),original[:-1],original+b'trailing']
        p=self.fixture()
        for location in ['work','dist']:
            for blob in blobs:
                with self.subTest(location=location,case='missing' if blob is None else len(blob)):
                    target=p/location/'mnist14.model'
                    if blob is None: target.unlink(missing_ok=True)
                    else: target.write_bytes(blob)
                    self.invoke(['sh','verify.sh'],cwd=p)
                    target.write_bytes(original)

    def test_verifier_requires_checksum_and_mnist_evaluation(self):
        p=self.fixture(); manifest=p/'dist/SHA256SUMS'; original=manifest.read_bytes()
        manifest.write_text('0'*64+'  uai32\n'); self.invoke(['sh','verify.sh'],cwd=p); manifest.write_bytes(original)
        # Valid-format model with all zero weights: format/size alone must not pass.
        model=p/'work/mnist14.model'; b=bytearray(model.read_bytes()); b[8+8*196:]=bytes(len(b)-8-8*196); model.write_bytes(b)
        self.invoke(['sh','verify.sh'],cwd=p)

    def test_verifier_never_skips_missing_dependencies_or_wrong_check_count(self):
        p=self.fixture(); tools=self.tmp/'tools'; tools.mkdir(); path=str(tools)+os.pathsep+os.environ['PATH']
        (tools/'python3').write_text('#!/bin/sh\nexit 1\n'); (tools/'python3').chmod(0o755)
        self.invoke(['sh','verify.sh'],cwd=p,env={'PATH':path}); (tools/'python3').unlink()
        (tools/'objcopy').write_text('#!/bin/sh\nexit 1\n'); (tools/'objcopy').chmod(0o755)
        self.invoke(['sh','verify.sh'],cwd=p,env={'PATH':path}); (tools/'objcopy').unlink()
        script=p/'verify.sh'; script.write_text(script.read_text().replace('EXPECTED=28','EXPECTED=29'))
        self.invoke(['sh','verify.sh'],cwd=p)

    def fake_training_exe(self, p, missing=False, size=None):
        script = ("#!/usr/bin/env python3\nimport pathlib,shutil,subprocess,sys\n"
                  "if sys.argv[1]=='train':\n p=pathlib.Path(sys.argv[3])\n"
                  f" if not ({missing!r} and p.name=='mnist14.model'): shutil.copyfile({str(ROOT/'dist')!r}+'/'+p.name,p)\n"
                  " sys.exit(0)\n"
                  f"sys.exit(subprocess.call([{str(ROOT/'uai32')!r},*sys.argv[1:]]))\n")
        if size: script += '#'*(size-len(script.encode()))
        (p/'uai32').write_text(script); (p/'uai32').chmod(0o755)

    def test_measure_and_dist_reject_missing_models(self):
        p=self.fixture(); self.fake_training_exe(p,missing=True)
        before=(p/'dist/SHA256SUMS').read_bytes()
        self.invoke(['sh','measure.sh'],cwd=p); self.invoke(['make','dist'],cwd=p)
        self.assertEqual((p/'dist/SHA256SUMS').read_bytes(),before)

    def test_measure_and_dist_reject_oversized_executable_and_combination(self):
        for size in [40000,28000]:
            with self.subTest(size=size):
                p=self.tmp/str(size); p.mkdir()
                for name in ['Makefile','measure.sh','check_artifacts.py','uai32.c']: shutil.copy2(ROOT/name,p/name)
                shutil.copytree(ROOT/'dist',p/'dist'); (p/'data').symlink_to(ROOT/'data',target_is_directory=True)
                self.fake_training_exe(p,size=size); before=(p/'dist/SHA256SUMS').read_bytes()
                self.invoke(['sh','measure.sh'],cwd=p); self.invoke(['make','dist'],cwd=p)
                self.assertEqual((p/'dist/SHA256SUMS').read_bytes(),before)

    def test_measure_and_dist_reject_missing_mnist_data(self):
        p=self.fixture(); (p/'data').unlink(); shutil.copytree(ROOT/'data',p/'data',ignore=shutil.ignore_patterns('mnist*','*.gz'))
        before=(p/'dist/SHA256SUMS').read_bytes()
        self.invoke(['sh','measure.sh'],cwd=p); self.invoke(['make','dist'],cwd=p)
        self.assertEqual((p/'dist/SHA256SUMS').read_bytes(),before)

    def mnist_module(self):
        spec=importlib.util.spec_from_file_location('mnist_under_test',ROOT/'get_mnist.py')
        m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.OUT=str(self.tmp/'cache'); pathlib.Path(m.OUT).mkdir(); return m

    def test_mnist_source_hashes_and_authentic_cache(self):
        m=self.mnist_module()
        for name in m.HASHES:
            raw=m.checked_archive(ROOT/'data'/name,name)
            self.assertTrue(raw)
        X,y=m.decode(m.checked_archive(ROOT/'data/train-images-idx3-ubyte.gz','train-images-idx3-ubyte.gz'),
                     m.checked_archive(ROOT/'data/train-labels-idx1-ubyte.gz','train-labels-idx1-ubyte.gz'),60000)
        self.assertEqual(len(X),len(y)); self.assertEqual(len(y),60000)

    def test_mnist_decode_rejects_magic_dimensions_counts_and_payload(self):
        m=self.mnist_module(); images=struct.pack('>4I',2051,3,28,28)+bytes(3*28*28); labels=struct.pack('>2I',2049,3)+bytes([0,1,2])
        self.assertEqual(len(m.decode(images,labels,3)[1]),3)
        invalid=[(b'',labels),(images,b''),(struct.pack('>4I',0,3,28,28)+images[16:],labels),
                 (struct.pack('>4I',2051,3,14,56)+images[16:],labels),
                 (images,struct.pack('>2I',0,3)+labels[8:]),(images,struct.pack('>2I',2049,99)+labels[8:]),
                 (images,labels[:-1]),(images[:-1],labels),(images+b'x',labels),(images,labels+b'x'),
                 (images,labels[:8]+bytes([0,1,10]))]
        for i,(a,b) in enumerate(invalid):
            with self.subTest(case=i),self.assertRaises(ValueError): m.decode(a,b,3)
        with self.assertRaises(ValueError): m.decode(images,labels,60000)

    def test_mnist_malformed_cache_and_download_fail_nonzero(self):
        p=self.tmp/'badcache'; (p/'data').mkdir(parents=True); shutil.copy2(ROOT/'get_mnist.py',p/'get_mnist.py')
        for prefix in ['train','t10k']:
            (p/'data'/f'{prefix}-images-idx3-ubyte.gz').write_bytes(gzip.compress(struct.pack('>4I',2051,3,28,28)+bytes(3*28*28)))
            (p/'data'/f'{prefix}-labels-idx1-ubyte.gz').write_bytes(gzip.compress(struct.pack('>2I',2049,3)+bytes([0,1])))
        self.invoke([sys.executable,'get_mnist.py'],cwd=p)
        self.assertFalse((p/'data/mnist14_train.txt').exists())
        m=self.mnist_module()
        def invalid_download(url,target): pathlib.Path(target).write_bytes(b'not MNIST')
        with mock.patch.object(m.urllib.request,'urlretrieve',invalid_download), self.assertRaises(SystemExit): m.fetch('train-images-idx3-ubyte.gz')
        self.assertFalse((pathlib.Path(m.OUT)/'train-images-idx3-ubyte.gz').exists())
        self.assertFalse((pathlib.Path(m.OUT)/'train-images-idx3-ubyte.gz.part').exists())
        script=(f"import importlib.util,pathlib; s=importlib.util.spec_from_file_location('m',{str(ROOT/'get_mnist.py')!r}); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.OUT={str(self.tmp/'download-cli')!r}; "
                "m.urllib.request.urlretrieve=lambda url,target:pathlib.Path(target).write_bytes(b'bad'); m.main(False)")
        self.invoke([sys.executable,'-c',script])

    def test_normalisation_range_overflow_fails_closed(self):
        # Finite inputs whose range exceeds FLT_MAX used to give scale = 1/inf = 0 silently (feature dropped).
        data = self.tmp / 'range.txt'; data.write_text('3e38 0\n-3e38 1\n')
        for exe in [ROOT / 'uai32', self.sanitized]:
            with self.subTest(exe=exe.name):
                m = self.tmp / 'range.model'; m.unlink(missing_ok=True)
                p = self.invoke([exe, 'train', data, m, '4', '1', '0.05'])
                self.assertIn('feature range overflows', p.stderr); self.assertFalse(m.exists())
        data.write_text('1.7e38 0\n-1.7e38 1\n')   # the widest range that still fits in a float trains normally
        m = self.tmp / 'wide.model'; self.invoke([ROOT / 'uai32', 'train', data, m, '4', '1', '0.05'], fails=False)
        self.assertTrue(m.exists())

    def test_dist_publication_failure_preserves_previous_dist(self):
        p = self.fixture(); self.fake_training_exe(p)      # measurement succeeds instantly with the committed models
        tools = self.tmp / 'tools'; tools.mkdir(); real_mv = shutil.which('mv')
        (tools / 'mv').write_text('#!/bin/sh\ncase "$1" in work/stage.*) echo "injected publication failure" >&2; exit 1;; esac\n'
                                  f'exec {real_mv} "$@"\n')
        (tools / 'mv').chmod(0o755); env = {'PATH': str(tools) + os.pathsep + os.environ['PATH']}
        before = {f.name: f.read_bytes() for f in (p / 'dist').iterdir()}
        r = self.invoke(['make', 'dist'], cwd=p, env=env)
        self.assertIn('restoring the previous dist/', r.stderr)
        self.assertEqual({f.name: f.read_bytes() for f in (p / 'dist').iterdir()}, before)
        self.assertEqual([x.name for x in (p / 'work').glob('stage.*')], [])
        self.assertEqual([x.name for x in (p / 'work').glob('previous-dist.*')], [])
        self.invoke(['make', 'dist'], cwd=p, fails=False)   # without the injected failure publication completes
        self.assertEqual(sorted(f.name for f in (p / 'dist').iterdir()), sorted(before))
        self.assertEqual([x.name for x in (p / 'work').glob('previous-dist.*')], [])

    def test_iris_caveat_and_full_verification_count_are_documented(self):
        readme=(ROOT/'README.md').read_text()
        self.assertNotIn('30 unseen flowers',readme)
        self.assertIn('one iris test row',readme)
        self.assertIn('28',readme)

if __name__=='__main__': unittest.main(verbosity=2)
