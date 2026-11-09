# Root filesystem

The first DEVos rootfs milestone is a minimal AArch64 initramfs. The A.119 stock kernel is ARM64 even though its Android vendor userspace advertises only ARMv7 ABIs.

## Build the initramfs

Run from the repository root:

```sh
python3 scripts/build_initramfs.py
```

The script downloads Debian's `busybox-static` 1.37.0-6+b9 ARM64 package when it is not cached, verifies its SHA-256, checks that its ELF is ARM64 and static, then creates `builds/devos-rmx3231-initramfs.cpio.gz`. The pinned package and checksum come from Debian's [Trixie package record](https://packages.debian.org/trixie/arm64/busybox-static/filelist) and official arm64 package index. Local downloads and build output are ignored by Git.

The initramfs has a static BusyBox shell, basic device nodes, proc/sysfs mounts, `mdev`, and an interactive shell on the boot console. It does not mount or write persistent partitions. The stock A.119 kernel config disables devtmpfs, so the archive supplies `/dev/console` and uses `mdev` to populate device nodes from sysfs.

The archive has been built and its gzip and CPIO structure inspected. It has not been booted on hardware. After extracting the exact A.119 BOOT image to `firmware/extracted/boot/boot.img`, run `python3 scripts/build_boot_image.py` to assemble an unsigned 64 MiB Android boot-image candidate at `builds/devos-rmx3231-a119-boot-unsigned.img`. The candidate retains the stock kernel and DTB wrapper but removes Realme's AVB footer and vbmeta because their signature does not cover the changed ramdisk. It does not establish that this phone's bootloader will accept the image.

## Deferred userspace

Add persistent storage, package management, Python, Git, Node.js, SSH, and a touchscreen selector after a non-destructive Linux boot and storage path are verified. The network mode also needs an independent solution for the Android-only modem and Wi-Fi vendor services found in A.119.
