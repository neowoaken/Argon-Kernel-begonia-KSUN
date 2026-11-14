#!/bin/bash
# Build the begonia KernelSU-Next kernel.
# Usage: wsl_build.sh [defconfig|kernel|clean]
set -euo pipefail

KDIR="${KDIR:-/home/kali/kernel_xiaomi_mt6785}"
TOOLS="${TOOLS:-/home/kali/toolchains}"
OUT="${OUT:-out}"
JOBS="${JOBS:-$(nproc)}"

export PATH="$TOOLS/clang-r383902/bin:$TOOLS/gcc49/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export ARCH=arm64
export SUBARCH=arm64
export KBUILD_BUILD_USER=begonia
export KBUILD_BUILD_HOST=ksu-build
export KBUILD_BUILD_VERSION=1

MAKE_ARGS=(
  -C "$KDIR" O="$OUT"
  ARCH=arm64
  CC=clang
  CLANG_TRIPLE=aarch64-linux-gnu-
  CROSS_COMPILE=aarch64-linux-android-
  LD=ld.lld
  NM=llvm-nm
  OBJCOPY=llvm-objcopy
  AR=llvm-ar
  STRIP=llvm-strip
)

case "${1:-kernel}" in
  defconfig)
    make "${MAKE_ARGS[@]}" begonia_user_defconfig
    ;;
  kernel)
    make "${MAKE_ARGS[@]}" -j"$JOBS" Image.gz-dtb
    ;;
  clean)
    make "${MAKE_ARGS[@]}" clean
    ;;
  *)
    echo "unknown target: $1" >&2
    exit 2
    ;;
esac
