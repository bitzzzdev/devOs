# Root filesystem

No DEVos root filesystem has been built. The target can run an AArch64 kernel; the stock Android build uses a 32-bit application ABI. Choose the first rootfs ABI after booting a non-destructive Linux test image and verifying basic userspace execution.

The first rootfs should be an initramfs with a shell, device management, logging, and a recovery path. Add package management, Python, Git, Node.js, SSH, and a touchscreen selector after kernel boot and persistent storage are proven.
