# Sentovara uAI-32 -- build, measure, verify.
#   make            build ./uai32 with the size-reducing flags (and ./uai32.elf, the same binary with section headers)
#   make measure    train the demo models into work/ and print the byte sizes that the challenge counts
#   make verify     run the full evidence script (builds first)
#   make dist       copy the measured deliverable (executable + trained models + checksums) into dist/
#   make clean
CC      ?= cc
PROG    := uai32
# Optimise for size, drop everything that is not code, and never fuse multiply-adds (keeps model bytes
# identical across optimisation levels and CPUs).  None of these change what the program computes.
CFLAGS  ?= -std=c99 -Os -Wall -Wextra -pedantic -ffp-contract=off -U_FORTIFY_SOURCE -fno-asynchronous-unwind-tables \
           -fno-stack-protector -fno-ident -fno-pie -fno-plt -fcf-protection=none -fno-math-errno \
           -ffunction-sections -fdata-sections
LDFLAGS ?= -s -no-pie
LDLIBS  ?= -lm
# GNU ld only: drop unused sections, bind at load time (needed by -fno-plt), and remove page-alignment
# padding and metadata that costs bytes on disk.
ifeq ($(shell uname -s),Linux)
LDFLAGS += -Wl,--gc-sections -Wl,-z,now -Wl,--build-id=none -Wl,-z,norelro -Wl,-z,noseparate-code \
           -Wl,--hash-style=gnu -Wl,-z,max-page-size=4096 -Wl,--no-eh-frame-hdr
endif
SHA256 := $(shell command -v sha256sum > /dev/null 2>&1 && echo sha256sum || echo "shasum -a 256")
# The section header table is only read by linkers and debuggers, never by the kernel or the dynamic
# loader.  binutils >= 2.41 can leave it out; older ones keep it (about 1.8 KB more).
NOSH := $(shell printf 'int main(){return 0;}' | $(CC) -x c - -o /dev/null -Wl,-z,nosectionheader 2>/dev/null && echo -Wl,-z,nosectionheader)

all: $(PROG) $(PROG).elf

$(PROG): uai32.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS) $(NOSH) $(LDLIBS)

$(PROG).elf: uai32.c                     # identical build with section headers, for nm/objdump/readelf -S
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

measure: $(PROG)
	@./measure.sh

verify: $(PROG) $(PROG).elf
	@./verify.sh

# The deliverable is assembled and validated in work/stage.*, then published by renaming.  The previous
# dist/ is set aside as work/previous-dist.<pid> first and put back if the final rename fails, so a failed
# publication never leaves dist/ missing or partial (regression_tests.py injects that failure).
dist: $(PROG)
	@./measure.sh > /dev/null
	@set -eu; stage=$$(mktemp -d work/stage.XXXXXX); old=work/previous-dist.$$$$; \
	  trap 'rm -rf "$$stage"' EXIT HUP INT TERM; \
	  cp $(PROG) "$$stage/"; \
	  for n in iris spirals rings mnist14; do cp "work/$$n.model" "$$stage/"; done; \
	  (cd "$$stage" && $(SHA256) uai32 iris.model mnist14.model rings.model spirals.model > SHA256SUMS); \
	  python3 check_artifacts.py "$$stage" --manifest --data data; \
	  rm -rf "$$old"; if [ -e dist ]; then mv dist "$$old"; fi; \
	  if ! mv "$$stage" dist; then \
	    echo "dist: publication failed; restoring the previous dist/" >&2; \
	    if [ -e "$$old" ]; then mv "$$old" dist; fi; exit 1; \
	  fi; \
	  rm -rf "$$old"; cat dist/SHA256SUMS; wc -c dist/uai32 dist/*.model

test: all
	python3 regression_tests.py

clean:
	rm -rf $(PROG) $(PROG).elf work dist

.PHONY: all measure verify dist test clean
