# RMX3231 boot strategy

Status: an ARM64 initramfs has been assembled into a local custom-key AVB-signed Android boot-image candidate. AOSP avbtool verifies its signature and image hash. It has not been booted or flashed. The device is already boot-looping from an earlier attempt, and its current bootloader state and recovery route are unknown.

## Stock A.119 boot components

The exact A.119 `boot.img` has Android boot header v2, 2,048-byte pages, an ARM64 kernel, a gzip ramdisk, and a DTB field encoded as a one-entry Android DT table. The inner FDT is the generic `sprd,sc9863a` base tree. The separate `dtbo.img` has six entries. Entry 0 matches `RMX3231-overlay.dts`, and that overlay sets `androidboot.dtbo_idx=0`.

The boot image's embedded kernel config enables initramfs, gzip ramdisk decompression, ELF and script execution, proc, sysfs, tmpfs, and the usermode-helper mechanism. It disables devtmpfs. The built initramfs therefore provides static `/dev/console`, `/dev/null`, `/dev/tty`, and `/dev/zero` nodes, mounts proc/sysfs and volatile tmpfs filesystems, and runs `mdev -s`. It does not mount the phone's persistent partitions.

## Candidate strategy

`python3 scripts/build_boot_image.py` retains the A.119 kernel, complete base DTB wrapper, boot header parameters, and the separate DTBO partition unchanged. It replaces the Android ramdisk with the DEVos initramfs and recalculates the Android v2 legacy ID using the format in AOSP `mkbootimg.py` ([source](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/mkbootimg.py)). A pinned AOSP `avbtool.py` then adds a SHA-256 hash descriptor and RSA-4096 signature with a local development key, pads the image and AVB footer to the 64 MiB BOOT entry size in the A.119 PAC, and verifies the result ([AVB source](https://android.googlesource.com/platform/external/avb/%2B/refs/heads/android11-release/README.md)). This preserves the known device-specific kernel and board description while limiting the first userspace to an interactive console.

The output has a cryptographically valid AVB signature, but it is not signed by Realme's key. The stock root vbmeta has a chain descriptor for `boot` that pins key SHA-1 `9405a8f24d5b71da4420fa3edc5a5bd2e7420446`. The local key has a different fingerprint, so a locked bootloader will reject it. AOSP AVB's unlocked mode permits verification and chained-key errors to be non-fatal ([AOSP AVB unlocked-mode specification](https://android.googlesource.com/platform/external/avb/%2B/android11-release/README.md)), but RMX3231's bootloader behavior is not established. The candidate also uses the A.119 package's 64 MiB BOOT size, which does not confirm the phone's live partition size. Do not flash it until the device state and a complete recovery route are established. The local private key is needed to reproduce this exact signed image; never commit or share it.

The local build produced `builds/devos-rmx3231-a119-boot-custom-avb.img` with SHA-256 `a6869b8533e0234d3063cd1e54cf66f9b447ebcd684e82c780b111341d7b6df7`. AOSP `avbtool verify_image` passed with the local RSA key. The image was parsed again with `scripts/inspect_android_boot.py`; its header reports v2, 2,048-byte pages, and the expected kernel, initramfs, and DTB sizes. The extracted kernel and DTB wrapper hashes match the source components. Hardware boot and bootloader acceptance are not verified.

## Recovery evidence

The original A.119 ZIP includes a full PAC package, FDL loader binaries, and `ResearchDownload.exe` inside `ResearchDownload.zip`. The included downloader is a Windows executable. The presence of these files makes exact-build stock restoration a plausible recovery route, but it has not been verified on this phone, its BootROM/download mode, or the user's available computer and drivers.

The workspace has no `adb`, `fastboot`, or `lsusb` tools, so no device connection, bootloader state, or live partition information was established. Until these facts are known, do not try a modified image or PAC operation. The phone has not been changed by this project.

## Multi-boot architecture and stock Android handover

The candidate initramfs incorporates a multi-boot selector capable of launching four runtime modes:
1. Pocket VPS (headless Linux server over USB-RNDIS)
2. Wi-Fi Router (AP hotspot, DHCP gateway, NAT routing)
3. Dual Mode (Pocket VPS and Wi-Fi Router combined)
4. Regular Barebones (Stock Android handover)

When Mode 4 (Regular Barebones) is chosen, the DEVos init process locates the stock Android first-stage initramfs (embedded inside the candidate boot image as `/stock_ramdisk.cpio.gz`), unpacks it to `/stock_root`, unmounts early DEVos virtual filesystems, and invokes `switch_root` to start `/init`.

Because the underlying dynamic partitions (`system`, `vendor`, `product`, `system_ext`) on `super.img` remain completely untouched, the stock Android system launches with all original vendor HALs, preserving complete hardware access for the camera, microphone, cellular voice and data, and Wi-Fi.

## Single-file flashable installer packaging

To simplify device installation, `scripts/build_flashable_package.py` packages the 64 MiB custom-key AVB candidate into a single-file flashable installer ISO (`builds/devos-rmx3231-installer.iso`) and flashable ZIP (`builds/devos-rmx3231-flashable.zip`).

The package contains:
- `boot.img`: The signed multi-boot candidate boot partition image.
- `flash.sh`: Automated fastboot flasher script for Linux and macOS.
- `flash.bat`: Automated fastboot flasher script for Windows.
- `manifest.json`: Machine-readable target device and image metadata.
- `checksums.sha256`: Cryptographic integrity digests.
- `README.txt`: Operational instructions for flashing and boot selection.

## Local build artifact

Run `python3 scripts/build_initramfs.py` and then `python3 scripts/build_boot_image.py` to create the initramfs and AVB-signed boot-image candidate. The second command requires the locally extracted stock A.119 image at `firmware/extracted/boot/boot.img`, OpenSSL, and network access to fetch the pinned AOSP AVB tool. It generates a local signing key if absent. Source firmware, private key, and generated artifacts are excluded from Git. The initramfs uses Debian's statically linked ARM64 BusyBox package pinned by version and SHA-256 in the script. The candidate has not been booted on hardware.
