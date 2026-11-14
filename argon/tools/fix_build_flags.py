#!/usr/bin/env python3
"""Fix two build issues that appear with the pinned AOSP Clang 11 toolchain.

1. scripts/Makefile.extrawarn passes two warning flags that Clang 11 does not
   know, which makes every cc-option probe fail.
2. Makefile adds the same -mllvm option twice (duplicate
   CONFIG_INLINE_OPTIMIZATION block); LLVM aborts with
   "--unroll-threshold may only occur zero or one times".
"""
import sys

def replace_once(path, old, new):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if new in src:
        print("already done %s" % path)
        return
    if src.count(old) != 1:
        raise SystemExit("ERROR: %s: pattern matched %d times" % (path, src.count(old)))
    with open(path, "w", encoding="utf-8") as f:
        f.write(src.replace(old, new))
    print("patched      %s" % path)

replace_once("scripts/Makefile.extrawarn",
"""KBUILD_CFLAGS += -Wno-enum-compare-conditional
KBUILD_CFLAGS += -Wno-enum-enum-conversion""",
"""KBUILD_CFLAGS += $(call cc-option, -Wno-enum-compare-conditional)
KBUILD_CFLAGS += $(call cc-option, -Wno-enum-enum-conversion)""")

replace_once("Makefile",
"""ifdef CONFIG_INLINE_OPTIMIZATION
KBUILD_CFLAGS\t+= -mllvm -inline-threshold=2000
KBUILD_CFLAGS\t+= -mllvm -inlinehint-threshold=3000
KBUILD_CFLAGS   += -mllvm -unroll-threshold=1200
endif

ifdef CONFIG_INLINE_OPTIMIZATION
KBUILD_CFLAGS  += -mllvm -inline-threshold=1300""",
"""ifdef CONFIG_INLINE_OPTIMIZATION
KBUILD_CFLAGS  += -mllvm -inline-threshold=1300""")

print("build fixes applied")
