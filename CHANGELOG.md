# Changelog

All notable changes to DEVos are listed here.

## [Unreleased]

### Added
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
