# Changelog

All notable changes to DEVos are listed here.

## [Unreleased]

### Added
- Initial RMX3231 development workspace and hardware-source research.
- Pinned Realme kernel source for the RMX3231 and SC9863A platform.
- Recorded the A.119 PAC partition table and inspected the boot image, ARM64 kernel, first-stage fstab, ramdisk, DTBO header, and AVB metadata.

### Changed
- Firmware intake now targets the user's confirmed A.119 build.
- Stage 1 firmware download and ZIP CRC verification completed. The original package remains in temporary storage because it is larger than the available workspace volume.
