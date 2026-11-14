#!/bin/bash
# Integrate KernelSU-Next v3.2.0-legacy into the begonia kernel tree.
# Run from the kernel root (or set KDIR), on Linux/WSL.
set -euo pipefail

KDIR="${KDIR:-$(pwd)}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
# Default: legacy branch at UAPI 5, matching the released v3.4.2 manager.
# "legacy" = branch tip (UAPI 6, needs an unreleased manager).
# Use KSU_TAG=v3.2.0-legacy for the older tested pair.
KSU_TAG="${KSU_TAG:-legacy-3.4.2}"

cd "$KDIR"
[ -d drivers ] || { echo "not a kernel tree: $KDIR" >&2; exit 1; }

# 1. KernelSU-Next source at the newest 4.14-compatible revision.
#    v3.4.1/v3.4.2 kernel-side dropped manual hooks and require KPROBES, so
#    they cannot be used on this tree.
case "$KSU_TAG" in
  legacy-3.4.2) KSU_REF=465490a2 ;;      # legacy, UAPI 5 == manager 3.4.2
  legacy)       KSU_REF=origin/legacy ;;  # tip, UAPI 6 (unreleased manager)
  *)            KSU_REF="$KSU_TAG" ;;
esac
if [ ! -d KernelSU-Next/.git ]; then
  git clone https://github.com/KernelSU-Next/KernelSU-Next.git KernelSU-Next
fi
git -C KernelSU-Next fetch --tags --force
git -C KernelSU-Next checkout -f "$KSU_REF"

# 2. Wire it into drivers/.
ln -sfn ../KernelSU-Next/kernel drivers/kernelsu
grep -q 'kernelsu' drivers/Makefile || printf '\nobj-$(CONFIG_KSU) += kernelsu/\n' >> drivers/Makefile
grep -q 'drivers/kernelsu/Kconfig' drivers/Kconfig || \
  sed -i '/^endmenu/i source "drivers/kernelsu/Kconfig"' drivers/Kconfig

# 3. In-tree manual hooks + defconfig + toolchain build fixes.
python3 "$TOOLS/apply_manual_hooks.py"
python3 "$TOOLS/patch_defconfig.py"
python3 "$TOOLS/apply_tuning.py"
# Tuning turns SCHED_DEBUG off, which makes sched tunables const; the MTK
# perfmgr proc handler writes one of them and oopses at boot if it is rodata.
python3 "$TOOLS/apply_perfmgr_fix.py"
python3 "$TOOLS/apply_branding.py"
python3 "$TOOLS/fix_build_flags.py"

echo
echo "KernelSU-Next $KSU_TAG integrated in $KDIR"
echo "Next: $TOOLS/wsl_build.sh defconfig && $TOOLS/wsl_build.sh kernel"
