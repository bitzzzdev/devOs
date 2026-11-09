# RMX3231 boot strategy

Status: an ARM64 initramfs has been built as a local artifact. No modified Android boot image has been assembled, booted, or flashed.

## Stock A.119 boot components

The exact A.119 `boot.img` has Android boot header v2, 2,048-byte pages, an ARM64 kernel, a gzip ramdisk, and a DTB field encoded as a one-entry Android DT table. The inner FDT is the generic `sprd,sc9863a` base tree. The separate `dtbo.img` has six entries. Entry 0 matches `RMX3231-overlay.dts`, and that overlay sets `androidboot.dtbo_idx=0`.

The boot image's embedded kernel config enables initramfs, gzip ramdisk decompression, ELF and script execution, proc, sysfs, tmpfs, and the usermode-helper mechanism. It disables devtmpfs. The built initramfs therefore provides static `/dev/console`, `/dev/null`, `/dev/tty`, and `/dev/zero` nodes, mounts proc/sysfs and volatile tmpfs filesystems, and runs `mdev -s`. It does not mount the phone's persistent partitions.

## Candidate strategy

For a future boot candidate, retain the A.119 kernel, base DTB wrapper, and exact RMX3231 DTBO. Replace only the Android ramdisk with the DEVos initramfs. This preserves the known device-specific kernel and board description while limiting the first userspace to an interactive console.

Changing the ramdisk changes the boot image covered by the stock AVB metadata. The bootloader lock and AVB enforcement state are unknown. A modified image may be rejected or cause another boot failure. The image will not be assembled into a flashable artifact until the original bootloader state and a usable recovery route are known.

## Recovery evidence

The original A.119 ZIP includes a full PAC package, FDL loader binaries, and `ResearchDownload.exe` inside `ResearchDownload.zip`. The included downloader is a Windows executable. The presence of these files makes exact-build stock restoration a plausible recovery route, but it has not been verified on this phone, its BootROM/download mode, or the user's available computer and drivers.

The workspace has no `adb`, `fastboot`, or `lsusb` tools, so no device connection, bootloader state, or live partition information was established. Until these facts are known, do not try a modified image or PAC operation. The phone has not been changed by this project.

## Local build artifact

Run `python3 scripts/build_initramfs.py` to create `builds/devos-rmx3231-initramfs.cpio.gz`. The binary uses Debian's statically linked ARM64 BusyBox package pinned by version and SHA-256 in the script. The CPIO and gzip structure were inspected after building. Hardware boot remains unverified.
