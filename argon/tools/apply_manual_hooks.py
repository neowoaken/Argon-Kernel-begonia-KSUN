#!/usr/bin/env python3
"""Insert KernelSU-Next v3.2.0-legacy manual hooks into a Linux 4.14 tree.

Adapted from the verified begonia 4.14 non-GKI hook set:
  fs/exec.c        do_execveat_common -> ksud + sucompat
  fs/open.c        faccessat          -> ksu_handle_faccessat
  fs/stat.c        vfs_statx          -> ksu_handle_stat
  fs/read_write.c  vfs_read           -> ksu_handle_vfs_read
  drivers/input/input.c input_handle_event -> ksu_handle_input_handle_event
  kernel/reboot.c  sys_reboot         -> ksu_handle_sys_reboot

Run from the kernel root: python3 tools/apply_manual_hooks.py
"""
import sys

def patch(path, replacements, marker):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    orig = src
    if marker in src:
        print("already done %s" % path)
        return
    for old, new in replacements:
        count = src.count(old)
        if count != 1:
            raise SystemExit("ERROR: %s: pattern matched %d times:\n%s" % (path, count, old[:300]))
        src = src.replace(old, new, 1)
    if marker not in src:
        raise SystemExit("ERROR: %s: marker missing after patch: %s" % (path, marker))
    if src != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("patched      %s" % path)
    else:
        print("already done %s" % path)

patch("fs/exec.c", [(
"""static int do_execveat_common(int fd, struct filename *filename,
			      struct user_arg_ptr argv,
			      struct user_arg_ptr envp,
			      int flags)
{
	return __do_execve_file(fd, filename, argv, envp, flags, NULL);
}""",
"""#ifdef CONFIG_KSU
/*
 * KernelSU-Next manual hooks.
 *  - ksud:     hijacks the first /system/bin/app_process exec to start ksud
 *  - sucompat: rewrites exec of /system/bin/su into KernelSU's own su
 * struct user_arg_ptr is local to this file, so declare the prototypes here.
 */
extern int ksu_handle_execveat_ksud(int *fd, struct filename **filename_ptr,
				    struct user_arg_ptr *argv,
				    struct user_arg_ptr *envp, int *flags);
extern int ksu_handle_execveat_sucompat(int *fd, struct filename **filename_ptr,
					void *argv, void *envp, int *flags);
#endif

static int do_execveat_common(int fd, struct filename *filename,
			      struct user_arg_ptr argv,
			      struct user_arg_ptr envp,
			      int flags)
{
#ifdef CONFIG_KSU
	ksu_handle_execveat_ksud(&fd, &filename, &argv, &envp, &flags);
	ksu_handle_execveat_sucompat(&fd, &filename, NULL, NULL, NULL);
#endif
	return __do_execve_file(fd, filename, argv, envp, flags, NULL);
}"""
)], marker="ksu_handle_execveat_ksud(&fd")

patch("fs/open.c", [(
"""/*
 * access() needs to use the real uid/gid, not the effective uid/gid.
 * We do this by temporarily clearing all FS-related capabilities and
 * switching the fsuid/fsgid around to the real ones.
 */
SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)""",
"""#ifdef CONFIG_KSU
/* KernelSU-Next manual hook (su-compat: makes access("/system/bin/su") work). */
extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user,
				int *mode, int *flags);
#endif

/*
 * access() needs to use the real uid/gid, not the effective uid/gid.
 * We do this by temporarily clearing all FS-related capabilities and
 * switching the fsuid/fsgid around to the real ones.
 */
SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)"""
), (
"""	int res;
	unsigned int lookup_flags = LOOKUP_FOLLOW;

	if (mode & ~S_IRWXO)	/* where's F_OK, X_OK, W_OK, R_OK? */""",
"""	int res;
	unsigned int lookup_flags = LOOKUP_FOLLOW;

#ifdef CONFIG_KSU
	ksu_handle_faccessat(&dfd, &filename, &mode, NULL);
#endif

	if (mode & ~S_IRWXO)	/* where's F_OK, X_OK, W_OK, R_OK? */"""
)], marker="ksu_handle_faccessat(&dfd")

patch("fs/stat.c", [(
"""int vfs_statx(int dfd, const char __user *filename, int flags,
	      struct kstat *stat, u32 request_mask)
{
	struct path path;
	int error = -EINVAL;
	unsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;

	if ((flags & ~(AT_SYMLINK_NOFOLLOW | AT_NO_AUTOMOUNT |""",
"""#ifdef CONFIG_KSU
/* KernelSU-Next manual hook (su-compat: makes stat("/system/bin/su") work). */
extern int ksu_handle_stat(int *dfd, const char __user **filename_user,
			   int *flags);
#endif

int vfs_statx(int dfd, const char __user *filename, int flags,
	      struct kstat *stat, u32 request_mask)
{
	struct path path;
	int error = -EINVAL;
	unsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;

#ifdef CONFIG_KSU
	ksu_handle_stat(&dfd, &filename, &flags);
#endif

	if ((flags & ~(AT_SYMLINK_NOFOLLOW | AT_NO_AUTOMOUNT |"""
)], marker="ksu_handle_stat(&dfd")

patch("fs/read_write.c", [(
"""ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
	ssize_t ret;

	if (!(file->f_mode & FMODE_READ))""",
"""#ifdef CONFIG_KSU
/*
 * KernelSU-Next manual hook: lets ksud replace the content of
 * /system/etc/init/atrace.rc during early boot.
 */
extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,
			       size_t *count_ptr, loff_t **pos);
#endif

ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
	ssize_t ret;

#ifdef CONFIG_KSU
	ksu_handle_vfs_read(&file, &buf, &count, &pos);
#endif

	if (!(file->f_mode & FMODE_READ))"""
)], marker="ksu_handle_vfs_read(&file")

patch("drivers/input/input.c", [(
"""static void input_handle_event(struct input_dev *dev,
			       unsigned int type, unsigned int code, int value)
{
	int disposition = input_get_disposition(dev, type, code, &value);
""",
"""#ifdef CONFIG_KSU
/* KernelSU-Next manual hook: volume-key safe-mode detection during boot. */
extern int ksu_handle_input_handle_event(unsigned int *type,
					 unsigned int *code, int *value);
#endif

static void input_handle_event(struct input_dev *dev,
			       unsigned int type, unsigned int code, int value)
{
	int disposition;

#ifdef CONFIG_KSU
	ksu_handle_input_handle_event(&type, &code, &value);
#endif

	disposition = input_get_disposition(dev, type, code, &value);
"""
)], marker="ksu_handle_input_handle_event(&type")

patch("kernel/reboot.c", [(
"""SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
		void __user *, arg)
{
	struct pid_namespace *pid_ns = task_active_pid_ns(current);
	char buffer[256];
	int ret = 0;
""",
"""#ifdef CONFIG_KSU
extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);
#endif

SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
		void __user *, arg)
{
	struct pid_namespace *pid_ns = task_active_pid_ns(current);
	char buffer[256];
	int ret = 0;

#ifdef CONFIG_KSU
	ksu_handle_sys_reboot(magic1, magic2, cmd, &arg);
#endif
"""
)], marker="ksu_handle_sys_reboot(magic1")

print("done")
