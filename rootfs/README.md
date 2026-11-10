# Root filesystem

The first DEVos rootfs milestone is a minimal AArch64 initramfs. The A.119 stock kernel is ARM64 even though its Android vendor userspace advertises only ARMv7 ABIs.

## Build the initramfs

Run from the repository root:

```sh
python3 scripts/build_initramfs.py
```

The script downloads Debian's `busybox-static` 1.37.0-6+b9 ARM64 package when it is not cached, verifies its SHA-256, checks that its ELF is ARM64 and static, then creates `builds/devos-rmx3231-initramfs.cpio.gz`. The pinned package and checksum come from Debian's [Trixie package record](https://packages.debian.org/trixie/arm64/busybox-static/filelist) and official arm64 package index. Local downloads and build output are ignored by Git.

The initramfs has a static BusyBox shell, basic device nodes, proc/sysfs mounts, `mdev`, and an interactive shell on the boot console. It does not mount or write persistent partitions. The stock A.119 kernel config disables devtmpfs, so the archive supplies `/dev/console` and uses `mdev` to populate device nodes from sysfs.

The initramfs incorporates a multi-boot selector that offers four operational modes upon boot:
- Mode 1: Pocket VPS (headless Linux micro-server with SSH and USB-RNDIS)
- Mode 2: Wi-Fi Router (AP hotspot with DHCP gateway and NAT routing)
- Mode 3: Dual Mode (Pocket VPS and Wi-Fi Router combined)
- Mode 4: Regular Barebones (Stock Android system with all hardware active)

When Mode 4 is chosen, the initramfs unpacks the embedded stock Android ramdisk and performs a switch_root handover to the stock Android first-stage init, keeping the stock dynamic partitions untouched on super.img.

The archive has been built and its gzip and CPIO structure inspected. It has not been booted on hardware. After extracting the exact A.119 BOOT image to `firmware/extracted/boot/boot.img`, run `python3 scripts/build_boot_image.py` to assemble a custom-key AVB-signed 64 MiB Android boot-image candidate at `builds/devos-rmx3231-a119-boot-custom-avb.img`, and `python3 scripts/build_flashable_package.py` to create the single-file flashable ISO and ZIP installer bundles. The candidate retains the stock kernel and DTB wrapper and signs a hash descriptor for the changed boot image. AOSP AVB verification succeeds with the local development key, but that key differs from the Realme key pinned by root vbmeta. Device acceptance is unverified, and the build does not establish that this phone will boot the image.

## Deferred userspace

Add persistent storage, package management, Python, Git, Node.js, SSH, and a touchscreen selector after a non-destructive Linux boot and storage path are verified. The network mode also needs an independent solution for the Android-only modem and Wi-Fi vendor services found in A.119.
