#!/usr/bin/env python3
"""Keep the sched migration-cost tunable writable with SCHED_DEBUG=n.

kernel/sched/sched.h defines

    #ifdef CONFIG_SCHED_DEBUG
    # define const_debug __read_mostly
    #else
    # define const_debug const
    #endif

so with SCHED_DEBUG off (our tuning profile), fair.c's

    const_debug unsigned int sysctl_sched_migration_cost = 500000UL;

is a real const and lands in .rodata.  MTK perfmgr exposes
/proc/perfmgr/.../sched_migrate_cost_n, whose write handler stores
straight into that variable:

    sysctl_sched_migration_cost = data;

The vendor perfmgr daemon (NodeLooperThread) writes it a few seconds
after boot, which produced on Infinity-X Android 16:

    Unable to handle kernel write to read-only memory at virtual
    address ffffff9047b3e9e8
    pc : perfmgr_m_sched_migrate_cost_n_proc_write+0x40/0x70

The variable is a tunable (kernel/sysctl.c::sched_migration_cost_ns
writes it too whenever SCHED_DEBUG is on), so the fix is to keep the
storage writable instead of deleting the vendor proc node: switch the
definition to __read_mostly, which is exactly what const_debug expands
to with SCHED_DEBUG on.

Idempotent.  Run from the kernel root.
"""
import re
import sys

FAIR = "kernel/sched/fair.c"
SCHED_H = "kernel/sched/sched.h"
EAS = "drivers/misc/mediatek/performance/boost_ctrl/eas_ctrl/eas_ctrl.c"

DEF_RE = re.compile(
    r'^const_debug unsigned int sysctl_sched_migration_cost(\s*)= 500000UL;$',
    re.M)
NEW_DEF = (r'__read_mostly unsigned int sysctl_sched_migration_cost'
           r'\1= 500000UL;')

EXT_RE = re.compile(
    r'^extern const_debug unsigned int sysctl_sched_migration_cost;$', re.M)
NEW_EXT = 'extern __read_mostly unsigned int sysctl_sched_migration_cost;'


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    fair = read(FAIR)
    if 'const_debug unsigned int sysctl_sched_migration_cost' in fair:
        fair, n = DEF_RE.subn(NEW_DEF, fair)
        if n != 1:
            print("ERROR: %s: definition not matched (%d)" % (FAIR, n),
                  file=sys.stderr)
            return 1
        write(FAIR, fair)
        print("patched      %s (migration cost writable)" % FAIR)
    else:
        print("already done %s" % FAIR)

    hdr = read(SCHED_H)
    if 'extern const_debug unsigned int sysctl_sched_migration_cost;' in hdr:
        hdr, n = EXT_RE.subn(NEW_EXT, hdr)
        if n != 1:
            print("ERROR: %s: extern not matched (%d)" % (SCHED_H, n),
                  file=sys.stderr)
            return 1
        write(SCHED_H, hdr)
        print("patched      %s (matching extern)" % SCHED_H)
    else:
        print("already done %s" % SCHED_H)

    # Sanity: the vendor handler we are protecting must still exist, and it
    # must no longer be the only writer of a const object.
    if not re.search(r'sysctl_sched_migration_cost\s*=\s*data;', read(EAS)):
        print("WARNING: %s: perfmgr write handler not found" % EAS,
              file=sys.stderr)

    if 'const_debug unsigned int sysctl_sched_migration_cost' in read(FAIR):
        print("ERROR: %s still declares the tunable as const" % FAIR,
              file=sys.stderr)
        return 1

    print("perfmgr rodata-write fix applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
