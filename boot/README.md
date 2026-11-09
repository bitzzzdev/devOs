# Boot work

The A.119 boot image has been parsed and its ARM64 kernel, ramdisk, and base DTB extracted. The separate DTBO entry selected for RMX3231 is identified. See [the boot strategy](../docs/boot-strategy.md) for image layout and recovery constraints.

The first Linux userspace is an ARM64 BusyBox initramfs. Its local CPIO/GZIP artifact is built with `python3 scripts/build_initramfs.py`. No modified Android boot image has been assembled or tested, and nothing has been flashed. The phone's bootloader and AVB state and a tested recovery route are still unknown.
