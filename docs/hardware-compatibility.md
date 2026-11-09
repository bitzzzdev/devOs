# RMX3231 hardware compatibility

This report records evidence that affects a native Linux port. It does not claim that DEVos boots or that any peripheral works under Linux.

## Architecture and userspace ABI

Realme's kernel source builds the platform as `arm64`. Its SC9863A board DTS describes eight Cortex-A55 cores with ARMv8 compatibility. The A.119 vendor build properties report only `armeabi-v7a,armeabi` and an empty 64-bit ABI list. The community Android device configuration also sets `TARGET_ARCH := arm`, `TARGET_CPU_ABI := armeabi-v7a`, `TARGET_CPU_ABI2 := armeabi`, and 64-bit Binder.

The CPU and kernel support AArch64, while the stock Android userspace ABI is 32-bit ARM. Those are different facts. DEVos can target AArch64 userspace, but that choice still needs an on-device boot and libc smoke test. An ARMv7 userspace remains a fallback if the first Linux environment exposes a compatibility issue.

## Kernel and device description

The pinned Realme source is Linux 4.14.193. It contains:

- `arch/arm64/boot/dts/sprd/RMX3231-overlay.dts`
- `arch/arm64/boot/dts/sprd/RMX3235-overlay.dts`
- `arch/arm64/boot/dts/sprd/sp9863a-1h10_go-overlay.dts`
- `arch/arm64/boot/dts/sprd/sc9863a.dtsi`
- `arch/arm64/configs/sprd_sharkl3_defconfig`

The RMX3231 overlay identifies the board as `sprd,sp9863a-1h10-go` and lists multiple display panel variants. The kernel source Makefile builds RMX3231 and RMX3235 overlays against the SC9863A base DTB. This is exact-model support in the vendor kernel tree, but it is Android-vendor kernel code, not proof of mainline support.

The A.119 package confirms a boot image header v2, 2 KiB kernel pages, a separate DTBO image, and logical `system`, `vendor`, `product`, and `system_ext` partitions in the first-stage fstab. The fstab uses `slotselect` and identifies Virtual A/B. The PAC's 5 GiB `super.img` metadata confirms the four logical partitions and shows populated `_a` entries with empty `_b` entries. This is not a physical partition map and does not reveal the phone's live slot.

## Mainline Linux

Upstream Linux has an SC9863A SoC description and an SP9863A 1H10 board description. The current upstream DTS directory reviewed did not include an RMX3231-specific overlay. Mainline SoC support therefore does not establish complete RMX3231 support. The Realme 4.14.193 tree is the better first kernel for testing display, input, storage, power, and boot-chain behavior.

## Hardware support still to establish

| Hardware | Current evidence | DEVos status |
| --- | --- | --- |
| CPU and memory | ARM64 kernel and SC9863A device tree in Realme source | Source support found; not boot tested |
| Display | Multiple panel includes and display nodes in RMX3231 overlay | Exact panel selection not matched to A.119 yet |
| Touchscreen | Device-specific drivers and panel nodes exist in vendor source | Controller and driver mapping pending firmware inspection |
| eMMC and partitions | A.119 liblp metadata declares a 5 GiB `super`, groups for A and B, and four logical partitions; only `_a` contains image extents. Boot fstab uses AVB and slot selection. | Logical metadata inspected; physical GPT and live slot state still unknown |
| Wi-Fi and Bluetooth | Vendor image includes WCN service configuration, `hostapd`, and Wi-Fi supplicant service files | Firmware, chipset, kernel driver, and native Linux userspace path still unverified |
| Cellular modem | A.119 includes SC9600 modem/DSP firmware and Android Unisoc RIL/radio service configs | Firmware exists; Android RIL/HIDL dependency unresolved for native Linux |
| Charging, battery, thermal | Vendor overlay includes battery and thermal nodes | Must compare with stock DTBO and validate on device |
| USB | Device tree and Android USB init files exist | Linux gadget and OTG behavior not validated |

## Practical implications

The first DEVos milestone should reuse the matching stock kernel and its board DTB/DTBO while replacing Android init with a minimal Linux initramfs. A rebuilt kernel is a later step after compiling the exact source with the matching configuration and comparing its boot artifacts to A.119. Neither route is safe to flash until the current boot-loop cause and a recovery path are understood.

The vendor image confirms that modem and Wi-Fi operation are tied to Android service configuration, including Unisoc RIL, broadcast-radio/network services, WCN, hostapd, and supplicant. The stock vendor ABI is 32-bit ARM and its services expect Android init and HIDL/Binder. A native Linux service cannot use these components without a compatibility environment or a separate modem protocol implementation. Do not promise cellular data until the modem control path is identified.
