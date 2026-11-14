# Argon Kernel for begonia (MT6785)

Kernel source for the Argon Kernel release published on XDA.

Base tree: [krispgece/kernel_xiaomi_mt6785](https://github.com/krispgece/kernel_xiaomi_mt6785)
Linux: 4.14.357 (openela) · Device: Xiaomi Redmi Note 8 Pro (begonia / begoniain)
Root: KernelSU-Next legacy `465490a2` (UAPI 5), manager v3.4.2

The branch containing the Argon changes documents every modification as a
normal git commit against `krispgece/begonia-16`, so `git diff` against the
upstream tip is the complete patch.

## What is changed

- KernelSU-Next integration with **manual in-tree hooks** (no kprobes):
  `fs/exec.c`, `fs/open.c`, `fs/stat.c`, `fs/read_write.c`,
  `drivers/input/input.c`, `kernel/reboot.c`
- `arch/arm64/configs/begonia_user_defconfig`: KSU, binderfs, ashmem, ION,
  dm-verity/FEC, F2FS encryption, EROFS, userfaultfd, BPF/cgroup-BPF,
  BBR + fq, BFQ, HZ 250, LZ4 zram, SCHED_DEBUG/SCHEDSTATS off
- Empty `CONFIG_SYSVIPC`-era leftovers and vendor debug knobs kept at vendor
  defaults (DEBUG_FS, SW_SYNC, LSE atomics off)
- `drivers/block/zram/zram_drv.c`: default compressor `lzo` -> `lz4`
- `kernel/sched/fair.c`, `kernel/sched/sched.h`: `sysctl_sched_migration_cost`
  is `__read_mostly` instead of `const_debug` so the vendor perfmgr proc node
  can write it with `CONFIG_SCHED_DEBUG=n` (fixes a boot crash)
- Branding: `init/version.c`, `init/main.c`, `anykernel3/anykernel.sh`
  (`-Argon` release suffix, ASCII banner, credits)

The scripts in `argon/tools/` are the exact ones used to produce the released
image; they are idempotent.

## Build

Toolchain used (AOSP Clang 11 + GCC 4.9 binutils):

- clang-r383902
- gcc49 arm64 binutils

Steps:

```sh
cd kernel_xiaomi_mt6785

# KernelSU-Next at the pinned revision (integrate.sh can also do this)
git clone https://github.com/KernelSU-Next/KernelSU-Next KernelSU-Next
git -C KernelSU-Next checkout 465490a2

# Hooks, defconfig, tuning, branding, perfmgr fix
./argon/tools/integrate.sh

# Build (expects clang/gcc under /home/kali/toolchains by default)
TOOLS=/path/to/toolchains ./argon/tools/wsl_build.sh defconfig
TOOLS=/path/to/toolchains ./argon/tools/wsl_build.sh kernel

# AnyKernel3 flashable ZIP
ZIPNAME=ArgonKernel-begonia-33314-uapi5-4.14.357-20261114 \
  ./argon/tools/package_ak3.sh
```

Output image: `out/arch/arm64/boot/Image.gz-dtb`.

`KernelSU-Next/` and `out/` are intentionally not tracked. `drivers/kernelsu`
is a symlink to `../KernelSU-Next/kernel`, created by `integrate.sh`.

## License

GPLv2, inherited from the Linux kernel and the base tree. KernelSU-Next is
distributed under its own GPLv2 license; see its repository.
