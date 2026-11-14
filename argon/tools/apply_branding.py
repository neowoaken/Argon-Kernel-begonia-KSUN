#!/usr/bin/env python3
"""Rebrand the tree as Argon Kernel (display strings only).

Deliberately does NOT touch CONFIG_LOCALVERSION / UTS_RELEASE: the vermagic
stays 4.14.357-openela-PoWeR so modules built for this tree keep loading.
Only runtime-reported strings change, so `uname -r` and Android Settings show
`4.14.357-openela-PoWeR-Argon` while VERMAGIC_STRING stays `-PoWeR`.

Changes:
  * init/version.c  - init_uts_ns.name.release gets a "-Argon" suffix
                      (this is what `uname -r`, /proc/version and Android
                      Settings report); linux_banner gets the same suffix
  * init/main.c     - print the Argon ASCII signature, manager version and
                      credits at boot
  * anykernel3/anykernel.sh - installer kernel.string + ASCII banner

Run from the kernel root (or set AK3 path via argv[1]).
"""
import os
import sys

MARK = "A R G O N   K E R N E L"
CREDITS = "@edis22ovner on XDA"
MANAGER = "KernelSU-Next manager v3.4.2"

BANNER = r'''
	pr_info("\n");
	pr_info("    _    ____   ____   ___  _   _\n");
	pr_info("   / \\  |  _ \\ / ___| / _ \\| \\ | |\n");
	pr_info("  / _ \\ | |_) | |  _ | | | |  \\| |\n");
	pr_info(" / ___ \\|  _ <| |_| | |_| | |\\  |\n");
	pr_info("/_/   \\_\\_| \\_\\\\____|\\___/|_| \\_|\n");
	pr_info("        A R G O N   K E R N E L\n");
	pr_info("  begonia | MT6785 | Linux 4.14.357\n");
	pr_info("  KernelSU-Next legacy (manual hooks)\n");
	pr_info("  KernelSU-Next manager v3.4.2\n");
	pr_info("  built by @edis22ovner on XDA\n");
	pr_info("  with the help of DeepSeek V4.1 Flash Free\n\n");
'''

# Banner written by earlier versions of this script; upgraded in place.
PREV_BANNER = r'''
	pr_info("\n");
	pr_info("    _    ____   ____   ___  _   _\n");
	pr_info("   / \\  |  _ \\ / ___| / _ \\| \\ | |\n");
	pr_info("  / _ \\ | |_) | |  _ | | | |  \\| |\n");
	pr_info(" / ___ \\|  _ <| |_| | |_| | |\\  |\n");
	pr_info("/_/   \\_\\_| \\_\\\\____|\\___/|_| \\_|\n");
	pr_info("        A R G O N   K E R N E L\n");
	pr_info("  begonia | MT6785 | Linux 4.14.357\n");
	pr_info("  KernelSU-Next legacy (manual hooks)\n");
	pr_info("  built by @edis22ovner on XDA\n");
	pr_info("  with the help of DeepSeek V4.1 Flash Free\n\n");
'''

OLD_BANNER = r'''
	pr_info("\n");
	pr_info("    _    ____   ____   ___  _   _\n");
	pr_info("   / \\  |  _ \\ / ___| / _ \\| \\ | |\n");
	pr_info("  / _ \\ | |_) | |  _ | | | |  \\| |\n");
	pr_info(" / ___ \\|  _ <| |_| | |_| | |\\  |\n");
	pr_info("/_/   \\_\\_| \\_\\\\____|\\___/|_| \\_|\n");
	pr_info("        A R G O N   K E R N E L\n");
	pr_info("  begonia | MT6785 | Linux 4.14.357\n");
	pr_info("  KernelSU-Next legacy (manual hooks)\n\n");
'''


def patch_version_c():
    path = "init/version.c"
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    old = '\tLINUX_COMPILE_HOST ") (" LINUX_COMPILER ") " UTS_VERSION "\\n";'
    new = '\tLINUX_COMPILE_HOST ") (" LINUX_COMPILER ") " UTS_VERSION " [Argon Kernel]\\n";'
    if new in src:
        print("already done %s" % path)
        return
    if old not in src:
        sys.exit("ERROR: %s: banner pattern not found" % path)
    src = src.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("patched      %s" % path)


def patch_uts_release():
    """Display-only "-Argon" suffix for the runtime UTS release string.

    UTS_RELEASE (from generated/utsrelease.h) is what VERMAGIC_STRING is built
    from, so leaving it alone keeps module loading working; only the value
    copied into init_uts_ns changes.
    """
    path = "init/version.c"
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    if '.release\t= UTS_RELEASE "-Argon",' in src:
        print("already done %s (uts release)" % path)
        return

    old = ".release\t= UTS_RELEASE,"
    if old not in src:
        sys.exit("ERROR: %s: .release line not found" % path)
    src = src.replace(old, '.release\t= UTS_RELEASE "-Argon",', 1)

    # Keep the dmesg banner in sync with uname -r.
    old_banner = '"Linux version " UTS_RELEASE " ("'
    if old_banner in src:
        src = src.replace(old_banner,
                          '"Linux version " UTS_RELEASE "-Argon" " ("', 1)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("patched      %s (uts release -Argon)" % path)


def patch_main_c():
    path = "init/main.c"
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if MANAGER in src:
        print("already done %s" % path)
        return
    if MARK in src:
        # Upgrade an older banner block (credits / no credits) in place.
        for block, label in ((PREV_BANNER, "manager line"),
                             (OLD_BANNER, "credits + manager line")):
            if block in src:
                src = src.replace(block, BANNER, 1)
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(src)
                print("patched      %s (%s)" % (path, label))
                return
        sys.exit("ERROR: %s: banner present but not the expected block" % path)
    old = '\tpr_notice("%s", linux_banner);\n'
    if old not in src:
        sys.exit("ERROR: %s: linux_banner call not found" % path)
    src = src.replace(old, old + BANNER, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("patched      %s" % path)


def patch_anykernel():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "anykernel3", "anykernel.sh")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        print("skip         %s (not found)" % path)
        return
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    out = []
    for line in lines:
        if line.startswith("kernel.string="):
            out.append("kernel.string=Argon Kernel 4.14.357 + KernelSU-Next legacy (manual hooks)")
        else:
            out.append(line)
    new = "\n".join(out) + ("\n" if src.endswith("\n") else "")
    if new != src:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("patched      %s (kernel.string)" % path)
    else:
        print("already done %s" % path)


def main():
    patch_version_c()
    patch_uts_release()
    patch_main_c()
    patch_anykernel()
    print("Argon Kernel branding applied")


if __name__ == "__main__":
    main()
