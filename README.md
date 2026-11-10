# DEVos

DEVos is an early native Linux pocket-server project for the Realme C11 2021 (RMX3231). It is not an Android ROM or launcher.

## Current state

The device-specific Realme Linux 4.14.193 kernel source is available as a pinned Git submodule. The user's A.119 stock package was downloaded from a Realme firmware host, passed ZIP CRC validation, and its PAC and boot components were inspected. A small ARM64 BusyBox initramfs has been assembled with the stock kernel and base DTB into a 64 MiB custom-key AVB-signed Android boot-image candidate. It has not been booted on the phone. The source package remains in temporary storage because it exceeds available workspace space. No phone partitions have been changed.

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

This repository contains source and an untested boot-image candidate, not a verified bootable DEVos release. Read the [RMX3231 installation guide](docs/install-rmx3231.md) before preparing a local build. It explains the firmware checks, build steps, and why flashing is not currently supported.

To reproduce the local candidate and generate the flashable installer package, first extract the exact RMX3231 A.119 `BOOT` partition image as described in the [installation guide](docs/install-rmx3231.md), then run:

```sh
python3 scripts/build_initramfs.py
python3 scripts/build_boot_image.py
python3 scripts/build_flashable_package.py
```

The build downloads a pinned AOSP `avbtool.py` and creates a local RSA-4096 signing key if one is not already present. It produces a self-verified AVB image signed by that local key, embeds the stock Android ramdisk for barebones fallback, and packages the result into a single-file flashable installer ISO (devos-rmx3231-installer.iso) and flashable ZIP (devos-rmx3231-flashable.zip) under the builds directory. The Realme root vbmeta pins a different key for `boot`, so standard AVB semantics require an unlocked bootloader to tolerate the key mismatch. RMX3231 bootloader acceptance and the recovery route are unknown. Do not flash it yet, and never share the private key. Clone the kernel source with `git submodule update --init --recursive`, then read [the firmware inventory](firmware/inventory/stage-1-2.md), [ROM research](docs/rom-research.md), [hardware compatibility](docs/hardware-compatibility.md), [boot strategy](docs/boot-strategy.md), and [multi-boot operational modes](docs/multiboot-modes.md), and the [troubleshooting guide](docs/troubleshooting.md) before making device changes. Local firmware downloads, signing keys, and generated images are excluded from Git.

## Multi-boot operating modes

When booted on hardware, the DEVos early initramfs displays an interactive multi-boot selector offering four operating modes:

1. **Pocket VPS**: Headless Linux server with USB gadget networking (RNDIS/CDC-Ethernet, device IP `192.168.7.2`, host `192.168.7.1`), DHCP server, and SSH daemon.
2. **Wi-Fi Router**: Wireless access point (`192.168.43.1`), DHCP server pool, DNS service, and IPv4 NAT packet forwarding.
3. **Dual Mode**: Combines Pocket VPS and Wi-Fi Router, allowing simultaneous access over USB and Wi-Fi.
4. **Regular Barebones**: Hands control over to the stock Android first-stage init. Loads full stock Android where all device hardware functions normally, including camera, microphone, cellular phone calls and SMS, 4G mobile data, and Wi-Fi. Because stock system and vendor partitions on `super.img` remain untouched, UPI banking applications have the highest degree of compatibility.

See [docs/multiboot-modes.md](docs/multiboot-modes.md) for full network parameters and mode specifications.

## Development status

The current inventory identifies the boot image, kernel, ramdisk, DTBO, AVB metadata, modem payload entries, and a 5 GiB dynamic-partition super image. DTBO entry 0 matches the RMX3231 vendor overlay and its `androidboot.dtbo_idx=0` selection. The local candidate retains the stock kernel and DTB wrapper, replaces the ramdisk, adds a locally signed AVB hash descriptor, and pads to the A.119 package's 64 MiB BOOT entry size. Its key differs from the Realme key pinned in root vbmeta. The package size does not confirm the phone's current live partition size. Nothing in this repository is an installation guide.

GitHub Actions builds and inspects the minimal initramfs on pushes and pull requests. Local build instructions are in [rootfs/README.md](rootfs/README.md), and the current boot constraints are in [the boot strategy](docs/boot-strategy.md).

The **Build DEVos boot candidate** workflow can assemble the full image on demand.
It requires a URL and SHA-256 digest for an exact, device-matched A.119 BOOT
image, keeps that proprietary input out of the repository, builds the multi-boot
candidate with embedded stock Android ramdisk, packages the single-file flashable
installer ISO and ZIP, and uploads the build artifacts. A successful workflow run
proves image assembly and local AVB verification, not that the phone accepts or boots the image.

The upstream kernel source's optional tools read `LOG_FILE`, `PERF_EXEC_PATH`, `READELF`, `SPHINX_CONF`, `SUDO_GID`, `SUDO_UID`, `SUDO_USER`, and `USER`. The downloaded AOSP AVB tool optionally reads `AVB_INVOCATION_LOGFILE`. These are controls for those upstream utilities, not DEVos configuration; DEVos does not set them. See [kernel tool notes](kernel/README.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## License and support

Original DEVos source code by `bitzzdev` is licensed under [PolyForm Noncommercial 1.0.0](LICENSE). Copies and derivatives must retain the license and its required attribution notice, and commercial use of that original code is not permitted by the license. This is source-available software, not OSI-defined open source, because the license restricts commercial use. The [Open Source Initiative's definition](https://opensource.org/osd) requires use for any field of endeavor.

Third-party materials keep their own licenses. In particular, the Realme kernel submodule remains GPL-2.0 under its upstream `COPYING` file; this project license cannot prohibit commercial use of that code. Proprietary A.119 firmware and extracted vendor binaries are excluded from Git and have no redistribution permission established here.
