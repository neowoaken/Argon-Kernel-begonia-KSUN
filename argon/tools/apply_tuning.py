#!/usr/bin/env python3
"""Apply the begonia performance + multi-Android support profile.

Idempotent: managed lines are removed and re-appended as one block.

  * Networking: BBR default congestion control, fq default qdisc.
  * Block: BFQ scheduler available (UFS keeps mq-deadline by default).
  * Timers: HZ=250 (vendor default; some MTK drivers assume it).
  * Debug: SCHED_DEBUG/SCHEDSTATS off (small, safe win).
  * Android 11/14/16: asserts binderfs, ashmem, ION, dm-verity/FEC,
    f2fs encryption, EROFS, userfaultfd, BPF. (All vendor defaults.)
  * zram: LZ4 default compressor (fast, built in).

Stability notes (kept conservative on purpose):
  * ARM64_LSE_ATOMICS stays off. The vendor defconfig disables it and
    enabling it on this MTK 4.14 tree caused crashes under load.
  * HZ stays 250 and -mtune stays cortex-a55; both are vendor defaults.
  * DEBUG_FS and SW_SYNC stay off: the vendor config has them off, and
    turning DEBUG_FS on activates Mali/display debugfs paths the stock
    kernel never runs.
  * sw_sync is not needed by Android; SYNC_FILE (sync_file fds) is what
    SurfaceFlinger/HWC use, and it is already enabled by the vendor config.

Run from the kernel root.
"""
import re
import sys

DEFCONFIG = "arch/arm64/configs/begonia_user_defconfig"

# Lines we own: dropped before appending the fresh block.
MANAGED = (
    r'CONFIG_DEFAULT_TCP_CONG',
    r'CONFIG_DEFAULT_NET_SCH',
    r'CONFIG_DEFAULT_(BIC|CUBIC|RENO|HTCP|HYBLA|VEGAS|WESTWOOD|VENO|DCTCP|CDG|BBR)',
    r'CONFIG_DEFAULT_(FQ|FQ_CODEL|CODEL|SFQ|PFIFO_FAST)',
    r'CONFIG_NET_SCH_DEFAULT',
    r'CONFIG_NET_SCH_FQ(_CODEL)?',
    r'CONFIG_IOSCHED_BFQ',
    r'CONFIG_ARM64_LSE_ATOMICS',
    r'CONFIG_SW_SYNC',
    r'CONFIG_DEBUG_FS',
    r'CONFIG_SCHED_DEBUG',
    r'CONFIG_SCHEDSTATS',
    r'CONFIG_HZ(_\d+)?',
    r'CONFIG_ANDROID_BINDER(FS|_IPC|_DEVICES)',
    r'CONFIG_ASHMEM',
    r'CONFIG_ION',
    r'CONFIG_DM_VERITY(_FEC)?',
    r'CONFIG_F2FS_FS_ENCRYPTION',
    r'CONFIG_INCREMENTAL_FS',
    r'CONFIG_EROFS_FS',
    r'CONFIG_USERFAULTFD',
    r'CONFIG_BPF_SYSCALL',
    r'CONFIG_CGROUP_BPF',
)

BLOCK = """
# begonia tuning profile (performance)
CONFIG_NET_SCH_DEFAULT=y
CONFIG_NET_SCH_FQ=y
CONFIG_NET_SCH_FQ_CODEL=y
CONFIG_DEFAULT_FQ=y
CONFIG_DEFAULT_BBR=y
CONFIG_IOSCHED_BFQ=y
# CONFIG_ARM64_LSE_ATOMICS is not set
# CONFIG_DEBUG_FS is not set
# CONFIG_SW_SYNC is not set
CONFIG_HZ_250=y
CONFIG_HZ=250
# CONFIG_SCHED_DEBUG is not set
# CONFIG_SCHEDSTATS is not set

# Android 11/14/16 compatibility
CONFIG_ANDROID_BINDER_IPC=y
CONFIG_ANDROID_BINDERFS=y
CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"
CONFIG_ASHMEM=y
CONFIG_ION=y
CONFIG_DM_VERITY=y
CONFIG_DM_VERITY_FEC=y
CONFIG_F2FS_FS_ENCRYPTION=y
CONFIG_INCREMENTAL_FS=y
CONFIG_EROFS_FS=y
CONFIG_USERFAULTFD=y
CONFIG_BPF_SYSCALL=y
CONFIG_CGROUP_BPF=y
"""


def main():
    with open(DEFCONFIG, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    pat = re.compile(r'^(?:# )?(?:%s)(?:=.*| is not set)$' % '|'.join(MANAGED))
    headers = ("# begonia tuning profile", "# Android 11/14/16 compatibility")
    lines = [l for l in lines if not pat.match(l) and not l.startswith(headers)]

    while lines and not lines[-1].strip():
        lines.pop()
    lines += BLOCK.rstrip("\n").splitlines()

    with open(DEFCONFIG, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # zram default compressor: lzo -> lz4 (CRYPTO_LZ4 is built in)
    zpath = "drivers/block/zram/zram_drv.c"
    with open(zpath, "r", encoding="utf-8") as f:
        zsrc = f.read()
    if 'default_compressor = "lzo"' in zsrc:
        zsrc = zsrc.replace('default_compressor = "lzo"',
                            'default_compressor = "lz4"', 1)
        with open(zpath, "w", encoding="utf-8", newline="\n") as f:
            f.write(zsrc)
        print("patched      %s (default compressor lz4)" % zpath)
    else:
        print("already done %s" % zpath)

    # Clang tuning: keep the vendor default (Cortex-A55 for both cpu and tune).
    # -mtune=cortex-a76 was tried and is deliberately reverted: it caused
    # instability on this tree, and tune-only changes are not worth a bootloop.
    mpath = "Makefile"
    with open(mpath, "r", encoding="utf-8") as f:
        msrc = f.read()
    a55 = "KBUILD_CFLAGS\t+= -mcpu=cortex-a55 -mtune=cortex-a55"
    a76 = "KBUILD_CFLAGS\t+= -mcpu=cortex-a55 -mtune=cortex-a76"
    if a76 in msrc:
        msrc = msrc.replace(a76, a55, 1)
        with open(mpath, "w", encoding="utf-8", newline="\n") as f:
            f.write(msrc)
        print("reverted     %s (mtune=cortex-a55)" % mpath)
    elif a55 in msrc:
        print("already done %s" % mpath)
    else:
        print("WARNING: %s: mtune line not found" % mpath, file=sys.stderr)

    print("tuning profile applied")


if __name__ == "__main__":
    main()
