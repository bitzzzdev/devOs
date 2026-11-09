# Boot work

The A.119 boot image has been parsed and its ARM64 kernel, ramdisk, and base DTB extracted. The separate DTBO entry selected for RMX3231 is identified. See [the boot strategy](../docs/boot-strategy.md) for image layout and recovery constraints.

The first Linux userspace is an ARM64 BusyBox initramfs. Build it with `python3 scripts/build_initramfs.py`, then assemble the unsigned Android boot-image candidate with `python3 scripts/build_boot_image.py`. The builder requires the exact A.119 BOOT image at `firmware/extracted/boot/boot.img`. It retains the stock kernel and complete base-DTB wrapper, updates the v2 legacy ID, replaces the ramdisk, removes the stock AVB footer and vbmeta, and writes a partition-sized 64 MiB result under ignored `builds/`.

The local candidate has not been booted. The phone's bootloader state, AVB policy, live partition size, and a tested recovery route are unknown. Do not flash it. The build output and its JSON metadata are excluded from Git along with the proprietary stock image.
