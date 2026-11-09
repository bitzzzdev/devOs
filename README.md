# DEVos

DEVos is an early native Linux pocket-server project for the Realme C11 2021 (RMX3231). It is not an Android ROM or launcher.

## Current state

The device-specific Realme Linux 4.14.193 kernel source is available as a pinned Git submodule. The A.119 stock package was downloaded from Realme's firmware host, passed ZIP CRC validation, and its PAC and boot components were inspected. The source package remains in temporary storage because it exceeds available workspace space. No DEVos image has been built or booted, and no phone partitions have been changed.

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

This repository currently contains research and source material, not a bootable DEVos image. Clone the kernel source with `git submodule update --init --recursive`, then read [the firmware inventory](firmware/inventory/stage-1-2.md), [ROM research](docs/rom-research.md), and [hardware compatibility](docs/hardware-compatibility.md) before making device changes. Local firmware downloads and extracted images are excluded from Git.

## Development status

The current inventory identifies the boot image, kernel, ramdisk, DTBO, AVB metadata, modem payload entries, and a 5 GiB dynamic-partition super image. The super image's internal logical partition table and full DTBO overlay data still need analysis. Nothing in this repository is an installation guide.

## License and support

The project license has not been selected. Do not assume that files from the stock firmware or third-party device trees may be redistributed. The Realme kernel source remains under its upstream license in the submodule.
