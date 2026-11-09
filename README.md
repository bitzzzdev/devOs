# DEVos

DEVos is an early native Linux pocket-server project for the Realme C11 2021 (RMX3231). It is not an Android ROM or launcher.

## Current state

The device-specific Realme Linux 4.14.193 kernel source is available as a pinned Git submodule. The user's A.119 stock package was downloaded from a Realme firmware host, passed ZIP CRC validation, and its PAC and boot components were inspected. A small ARM64 BusyBox initramfs has been assembled with the stock kernel and base DTB into a 64 MiB unsigned Android boot-image candidate. It has not been booted on the phone. The source package remains in temporary storage because it exceeds available workspace space. No phone partitions have been changed.

There is no verified, device-tested native Linux image for RMX3231 in the sources reviewed so far. The available LineageOS material is an Android device tree and a GSI guide whose end-to-end test was performed on RMX3235. See [ROM research](docs/rom-research.md) and [hardware compatibility](docs/hardware-compatibility.md).

## Project layout

- `boot/`: boot-image and initramfs work
- `device/realme/rmx3231/`: device-specific configuration
- `docs/`: compatibility findings, decisions and milestones
- `firmware/original/`: local stock packages, excluded from Git
- `firmware/extracted/`: local extraction output, excluded from Git
- `firmware/inventory/`: package and partition inventory
- `kernel/realme/sc9863a/`: Realme kernel source submodule
- `rootfs/`: DEVos Linux userspace
- `scripts/`: reproducible development tools

## Usage

This repository contains source and an untested boot-image candidate, not a verified bootable DEVos release. To reproduce the local candidate, first extract the exact RMX3231 A.119 `BOOT` partition image to `firmware/extracted/boot/boot.img`, then run:

```sh
python3 scripts/build_initramfs.py
python3 scripts/build_boot_image.py
```

The generated image is unsigned because the changed ramdisk cannot use Realme's stock AVB metadata. Its bootloader acceptance and recovery route are unknown. Do not flash it yet. Clone the kernel source with `git submodule update --init --recursive`, then read [the firmware inventory](firmware/inventory/stage-1-2.md), [ROM research](docs/rom-research.md), [hardware compatibility](docs/hardware-compatibility.md), and [boot strategy](docs/boot-strategy.md) before making device changes. Local firmware downloads and extracted images are excluded from Git.

## Development status

The current inventory identifies the boot image, kernel, ramdisk, DTBO, AVB metadata, modem payload entries, and a 5 GiB dynamic-partition super image. DTBO entry 0 matches the RMX3231 vendor overlay and its `androidboot.dtbo_idx=0` selection. The local candidate retains the stock kernel and DTB wrapper, replaces the ramdisk, removes the stale AVB footer and vbmeta, and zero-pads to the A.119 package's 64 MiB BOOT entry size. That package size does not confirm the phone's current live partition size. Nothing in this repository is an installation guide.

GitHub Actions builds and inspects the minimal initramfs on pushes and pull requests. Local build instructions are in [rootfs/README.md](rootfs/README.md), and the current boot constraints are in [the boot strategy](docs/boot-strategy.md).

## License and support

Original DEVos source code by `bitzzdev` is licensed under [PolyForm Noncommercial 1.0.0](LICENSE). Copies and derivatives must retain the license and its required attribution notice, and commercial use of that original code is not permitted by the license. This is source-available software, not OSI-defined open source, because the license restricts commercial use. The [Open Source Initiative's definition](https://opensource.org/osd) requires use for any field of endeavor.

Third-party materials keep their own licenses. In particular, the Realme kernel submodule remains GPL-2.0 under its upstream `COPYING` file; this project license cannot prohibit commercial use of that code. Proprietary A.119 firmware and extracted vendor binaries are excluded from Git and have no redistribution permission established here.
