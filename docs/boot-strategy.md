# RMX3231 boot strategy

Status: an ARM64 initramfs has been assembled into a local, unsigned Android boot-image candidate. It has not been booted or flashed. The device is already boot-looping from an earlier attempt, and its current bootloader state and recovery route are unknown.

## Stock A.119 boot components

The exact A.119 `boot.img` has Android boot header v2, 2,048-byte pages, an ARM64 kernel, a gzip ramdisk, and a DTB field encoded as a one-entry Android DT table. The inner FDT is the generic `sprd,sc9863a` base tree. The separate `dtbo.img` has six entries. Entry 0 matches `RMX3231-overlay.dts`, and that overlay sets `androidboot.dtbo_idx=0`.

The boot image's embedded kernel config enables initramfs, gzip ramdisk decompression, ELF and script execution, proc, sysfs, tmpfs, and the usermode-helper mechanism. It disables devtmpfs. The built initramfs therefore provides static `/dev/console`, `/dev/null`, `/dev/tty`, and `/dev/zero` nodes, mounts proc/sysfs and volatile tmpfs filesystems, and runs `mdev -s`. It does not mount the phone's persistent partitions.

## Candidate strategy

`python3 scripts/build_boot_image.py` retains the A.119 kernel, complete base DTB wrapper, boot header parameters, and the separate DTBO partition unchanged. It replaces the Android ramdisk with the DEVos initramfs and recalculates the Android v2 legacy ID using the format in AOSP `mkbootimg.py` ([source](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/mkbootimg.py)). The result is padded with zeroes to the 64 MiB BOOT entry size in the A.119 PAC. This preserves the known device-specific kernel and board description while limiting the first userspace to an interactive console.

The output is an unsigned candidate, not a verified flashable release. The stock boot image has an AVB footer pointing to signed vbmeta at the end of the 64 MiB image. Changing the ramdisk invalidates that signature, so the builder removes both the old AVB footer and its vbmeta block and zeroes the remaining partition area. It cannot create a replacement signature trusted by Realme's boot chain. The bootloader lock and AVB enforcement state are unknown; a modified image may be rejected or cause another boot failure. The package's partition size also does not confirm the phone's current live partition size. Do not flash this candidate until the device state and a complete recovery route are established.

The local build produced `builds/devos-rmx3231-a119-boot-unsigned.img` with SHA-256 `b76171d797d43ff6d849536408536c5e01baa8fc4013d7fa53fd931714309494`. The image was parsed again with `scripts/inspect_android_boot.py`; its header reports v2, 2,048-byte pages, and the expected kernel, initramfs, and DTB sizes. The extracted kernel and DTB wrapper hashes match the source components. No AVB footer or vbmeta remains. Hardware boot and bootloader acceptance are not verified.

## Recovery evidence

The original A.119 ZIP includes a full PAC package, FDL loader binaries, and `ResearchDownload.exe` inside `ResearchDownload.zip`. The included downloader is a Windows executable. The presence of these files makes exact-build stock restoration a plausible recovery route, but it has not been verified on this phone, its BootROM/download mode, or the user's available computer and drivers.

The workspace has no `adb`, `fastboot`, or `lsusb` tools, so no device connection, bootloader state, or live partition information was established. Until these facts are known, do not try a modified image or PAC operation. The phone has not been changed by this project.

## Local build artifact

Run `python3 scripts/build_initramfs.py` and then `python3 scripts/build_boot_image.py` to create the initramfs and unsigned boot-image candidate. The second command requires the locally extracted stock A.119 image at `firmware/extracted/boot/boot.img`; source firmware and generated artifacts are excluded from Git. The initramfs uses Debian's statically linked ARM64 BusyBox package pinned by version and SHA-256 in the script. The candidate has not been booted on hardware.
