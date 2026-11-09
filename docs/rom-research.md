# Open-source ROM and Linux source review

## Finding

No released, device-tested native Linux image for RMX3231 was found in the sources reviewed. Recent community posts claim Android GSIs, including ArrowOS or LineageOS-based images, can run on RMX3231, but they do not identify a source-built exact-model release with reproducible hardware results. The /e/OS Treble compatibility list records RMX3231 as `arm_binder64 A/B`; that is generic Android ABI metadata, not a verified ROM image or a native Linux port. DEVos will use the device's Linux kernel and hardware description as source material, not use an Android system image as its operating system.

## Device-specific LineageOS material

The public [`lineage_device_lineage_rmx3231` tree](https://github.com/depesh1977/lineage_device_lineage_rmx3231) is an Android device configuration. Its `BoardConfig.mk` targets 32-bit ARM userspace, uses 64-bit Binder, describes A/B virtual A/B and dynamic partitions, and forces a prebuilt kernel. The repository has no published ROM releases and no root license file. It is useful as a source of Android boot metadata, but it is not a native Linux port or a verified installable ROM.

The related [firmware dump repository](https://github.com/depesh1977/dump_lineage_rmx3231) contains a device tree and stock firmware dump artifacts. Its README identifies an older RMX3231 firmware build, not the A.119 package currently being analyzed. Do not assume its prebuilt kernel, DTBO, or vendor files match A.119 without comparing them.

## LineageOS 21 GSI report

The [Narzo 50i and C11 2021 guide](https://github.com/fam007e/narzo-50i-lineage) labels both RMX3235 and RMX3231 as targets, but its own tested-device statement names only RMX3235 running A.63. Recent [community GSI reports](https://www.reddit.com/r/CustomROMsGuide/comments/1vnypnp/rmx3231_realme_c11_2021_installing_a_gsi_and_ubl/) remain anecdotal and do not prove that a published build works on this handset. Their procedures and bootloader-change claims are not being followed. No Android image is suitable as the DEVos userspace.

The GSI is Android userspace and depends on Android's init, Binder, HALs, and vendor compatibility. It cannot serve as DEVos's native Linux userspace.

## Source chosen for DEVos

Use Realme's public [C11 2021 and Narzo 50i Android R kernel source](https://github.com/realme-kernel-opensource/realme_C11-2021_Narzo-50i-AndroidR-kernel-source), pinned in `kernel/realme/sc9863a`. It is Linux 4.14.193 and contains `RMX3231-overlay.dts`, `sc9863a.dtsi`, the board family DTS, and the `sprd_sharkl3_defconfig`. This is the strongest device-specific starting point found for a native Linux boot path.

## References

- [Realme kernel source commit](https://github.com/realme-kernel-opensource/realme_C11-2021_Narzo-50i-AndroidR-kernel-source/commit/654351b0286746330f4a9ca958b2685e6485ec8d)
- [RMX3231 overlay in that source](https://github.com/realme-kernel-opensource/realme_C11-2021_Narzo-50i-AndroidR-kernel-source/blob/654351b0286746330f4a9ca958b2685e6485ec8d/arch/arm64/boot/dts/sprd/RMX3231-overlay.dts)
- [Upstream Linux SC9863A device tree](https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/sprd/sc9863a.dtsi)
- [Upstream Linux SP9863A 1H10 board description](https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/sprd/sp9863a-1h10.dts)
- [/e/OS Treble compatibility list](https://community.e.foundation/t/device-support-project-treble/19645), which records the Android ABI and slot model but not a working RMX3231 ROM build
