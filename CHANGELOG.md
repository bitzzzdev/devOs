# Changelog

All notable changes to DEVos are listed here.

## [Unreleased]

## [0.1.0] - 2026-11-10

### Added
- Added an interactive multi-boot selector in `rootfs/init` with support for four operational modes: Pocket VPS, Wi-Fi Router, Dual Mode, and Regular Barebones (Stock Android).
- Added dedicated mode execution scripts in `rootfs/sbin/`: `devos-mode-vps`, `devos-mode-router`, `devos-mode-dual`, and `devos-mode-android`.
- Added stock Android ramdisk embedding and root handover in Barebones mode, preserving camera, microphone, cellular telephony, mobile data, and Wi-Fi functionality while keeping dynamic partitions on `super.img` untouched for UPI banking compatibility.
- Added `scripts/build_flashable_package.py` to produce a single-file flashable ISO installer (`builds/devos-rmx3231-installer.iso`) and flashable ZIP bundle (`builds/devos-rmx3231-flashable.zip`) containing automated fastboot flasher scripts for Linux, macOS, and Windows.
- Updated the boot candidate workflow in `.github/workflows/build-boot-candidate.yml` to package and upload the single-file flashable installer ISO and ZIP artifacts.
- Added an automated test suite in `tests/` covering shell script syntax, initramfs entry verification, and flashable package generation.
- Added documentation for the multi-boot architecture and network configurations in `docs/multiboot-modes.md`.
- Added a manually triggered workflow that downloads a caller-supplied,
  checksum-verified A.119 BOOT image, builds the full candidate, verifies its
  AVB signature, and uploads short-lived artifacts without storing firmware.
- Added a beginner guide to verify the A.119 firmware and build the local boot candidate, with an explicit no-flash status until device recovery is verified.
- Assembled a local 64 MiB A.119 boot-image candidate with a self-verified custom AVB signature.
- Initial RMX3231 development workspace and hardware-source research.
- Pinned Realme kernel source for the RMX3231 and SC9863A platform.
- Recorded the A.119 PAC partition table and inspected the boot image, ARM64 kernel, first-stage fstab, ramdisk, DTBO header, and AVB metadata.
- Added a reproducible ARM64 BusyBox initramfs builder and Android boot image inspector.
- Added a PAC inventory tool that can read an embedded PAC from the stock ZIP without extracting the multi-gigabyte package first.
- Matched DTBO entry 0 to the RMX3231 overlay and extracted the base DTB from the boot image's single-entry DT table.
- Added a GitHub Actions workflow that builds and checks the initramfs archive.
- Licensed original DEVos-authored code under PolyForm Noncommercial 1.0.0 with a required attribution notice and documented third-party license boundaries.

### Changed
- Firmware intake now targets the user's confirmed A.119 build.
- Stage 1 firmware download and ZIP CRC verification completed. The original package remains in temporary storage because it is larger than the available workspace volume.
