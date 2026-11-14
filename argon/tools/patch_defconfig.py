#!/usr/bin/env python3
"""Enable KernelSU-Next in the begonia defconfig (idempotent)."""
path = "arch/arm64/configs/begonia_user_defconfig"
with open(path, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

drop_prefixes = (
    "CONFIG_KSU", "# CONFIG_KSU",
    "CONFIG_TMPFS_XATTR", "# CONFIG_TMPFS_XATTR",
    "CONFIG_OVERLAY_FS_REDIRECT_DIR", "# CONFIG_OVERLAY_FS_REDIRECT_DIR",
    "CONFIG_LLVM_POLLY", "# CONFIG_LLVM_POLLY",
    "# KernelSU",
)
lines = [l for l in lines if not l.startswith(drop_prefixes)]
while lines and not lines[-1].strip():
    lines.pop()

lines += [
    "",
    "# KernelSU Next (non-GKI, manual hooks)",
    "CONFIG_KSU=y",
    "CONFIG_KSU_MANUAL_HOOK=y",
    "# CONFIG_KSU_KPROBES_HOOK is not set",
    "CONFIG_TMPFS_XATTR=y",
    "CONFIG_OVERLAY_FS_REDIRECT_DIR=y",
    "# CONFIG_LLVM_POLLY is not set",
    "",
]
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("defconfig updated")
