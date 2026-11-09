# RMX3231 A.119 firmware intake and analysis

Status: the user confirmed A.119 as the previously installed build. The matching package was downloaded from a Realme-owned host, its ZIP integrity test passed, and the PAC package and boot components were inspected. Nothing has been flashed to the phone.

## Source and integrity

| Field | Result |
| --- | --- |
| Device / product | Realme C11 2021, RMX3231 |
| User-confirmed build | `RMX3231_11.A.119` |
| Region | India-capable package; the PAC itself lists project codes 20780, 20781, 20782, 21673, 216F1 and 216F2, without an explicit country label |
| Filename | `RMX3231_11.A.119_202310110952.zip` |
| Download URL | <https://rms01.realme.net/sw/RMX3231_11.A.119_202310110952.zip> |
| Download host | `rms01.realme.net` (Realme domain; URL was discovered through a third-party firmware index) |
| ZIP size | 3,539,802,433 bytes |
| SHA-256 | `640d925183ecef3b267883f3266fd5e0aa3b20590e5fecaa2088de8f76973f57` |
| ZIP verification | `unzip -tq` completed with `No errors detected in compressed data` |
| Realme-published checksum | None located. The ZIP SHA-256 above is locally computed, not a vendor-published digest. |
| HTTP metadata | `Content-Type: application/zip`; `Accept-Ranges: bytes`; last modified `2023-10-31`; ETag recorded during download: `6e70526c76517a776873626b4e785757616d64553235654c566b524b-563` |
| Local source path | `/tmp/DEVos-firmware/RMX3231_11.A.119_202310110952.zip` |

The ZIP contains 12 entries and expands to 6,398,846,162 bytes. The main payload is `cp_sign/SHARKL3_R11/RMX3231-user-native_SHARKL3_R11.pac`, 6,301,038,358 bytes expanded and 3,481,352,838 bytes compressed. The PAC header reports format `BP_R2.0.1`, product and alias `RMX3231`, firmware `RMX3231_11.A.119_202310110952`, 49 entries, and PAC magic `0xfffafffa`. `version_info.txt` states platform `SC9863A`, project `20780`, and compile time `2023-10-11 09:52:10`. Its embedded SHA-256 is metadata from the package and does not match the locally computed ZIP digest; it is not treated as the ZIP checksum.

The package was found through a third-party index, but the binary came directly from a Realme-owned domain. This establishes the host and package identity, not a cryptographic Realme signature verification. The package has passed ZIP CRC validation; PAC-internal CRC values were read but not recomputed, and a vendor signature chain has not been independently authenticated.

## Storage and preserved files

The workspace filesystem cannot hold the 3.54 GB original ZIP. The downloaded archive remains under `/tmp/DEVos-firmware/`, outside Git. To fit the 5 GiB super image within temporary disk space, the extracted PAC working copy was reshaped in place into `super.img`; the original ZIP remains unchanged and can recreate the PAC. Small analysis outputs are under `firmware/extracted/`; `.gitignore` excludes proprietary firmware and extracted files. Do not delete the temporary original archive if it is still needed for follow-up analysis.

## PAC partition inventory

The complete 49-entry PAC table, including entry IDs, filenames, byte sizes, offsets, and PAC flags, is recorded in [pac-partitions.tsv](pac-partitions.tsv). Key findings:

| Category | PAC entries / observations |
| --- | --- |
| Boot | `BOOT` (`boot.img`, 67,108,864 bytes), `DTBO` (`dtbo.img`, 8,388,608 bytes), `VBMETA` and system/vendor/product vbmeta images |
| Dynamic partitions | `Super` (`super.img`, 5,242,880,000 bytes). Its liblp metadata is version 10.2 with the Virtual A/B flag; logical system, system_ext, vendor, and product partitions are declared. The `_a` partitions have data; corresponding `_b` entries are empty. Sizes are recorded in [super-logical-partitions.tsv](super-logical-partitions.tsv). |
| Modem and connectivity | `Modem_LTE`, `Modem_WCN`, `DSP_LTE_GGE`, `DSP_LTE_LTE`, `DFS`, `NV_LTE`, `Modem_LTE_DELTANV`, `GPS_BD`, and `GPS_GL` |
| Device data and security | `Persist`, `ProdNV`, `Odmko`, `Socko`, `Trustos`, `Teecfg`, `SML`, bootloader stages, and signed vbmeta components. These are device-sensitive or boot-chain components and are not DEVos replacement candidates. |
| Other | `My_preload`, cache/userdata templates, logo images, six OCDT/project configuration blobs, FDL loaders, and PAC operations such as erase/phase-check entries. |
| Recovery | No standalone `recovery.img`, `vendor_boot.img`, or `init_boot.img` entry appears in the PAC table. Recovery-related init files and fstab variants are present in the boot ramdisk. The ZIP contains a Windows-only `ResearchDownload.exe` tool and FDL/PAC files; this is a possible stock-recovery route, not a verified route for this currently boot-looping phone. |
| Partition map | The PAC is a flashing package, not a GPT dump. It does not establish physical partition boundaries or sizes. Those still require a read-only device-side partition query or authoritative partition map. |

No PAC entry or image for `vendor.img`, `odm.img`, or `system_ext.img` exists as a standalone file. Those logical partitions were extracted read-only from `super.img`; the 2.88 GiB `system_a` image was not copied because available workspace capacity is limited. The `vendor_a`, `system_ext_a`, and `product_a` files are ext4 images. `vendor_a` contains Android 11 vendor build properties for RMX3231, a 32-bit ARM ABI list with no 64-bit ABI, Unisoc RIL and radio services, Wi-Fi supplicant/hostapd service configs, display composer/allocator, health, USB, sensors, power, and thermal services. These depend on Android init and HIDL/Binder libraries; this is not a standalone Linux modem or Wi-Fi stack. Vendor firmware files include several touchscreen firmware variants and calibration/configuration data, so they cannot safely be treated as generic device files.

Standalone LTE modem and DSP/co-processor blobs were extracted to the ignored `firmware/extracted/modem/` directory. NV, delta-NV, ProdNV, persist, and calibration-specific PAC entries were not extracted. `firmware/inventory/extracted-sha256.txt` records local hashes for extracted artifacts. None of these binaries is tracked by Git.

## Boot image inspection

`boot.img` is an Android boot image with header version 2, 2,048-byte page size, 20,221,968-byte ARM64 kernel, 8,998,681-byte gzip ramdisk, and an 86,252-byte DTB field. The DTB field is a one-entry Android DT table wrapper; its inner 86,188-byte FDT is the base tree with model `Spreadtrum SC9863A SoC` and compatible `sprd,sc9863a`. The image is 64 MiB, with unused padding after its payloads. The boot command line begins `console=ttyS1,115200n8 androidboot.selinux=permissive buildvariant=user`.

The embedded kernel identifies itself as Linux `4.14.193+-ab453`, built with Android clang 11 for ARM64 on 2023-10-11. The gzip ramdisk integrity test passed. Its `first_stage_ramdisk/fstab.RMX3231` mounts logical ext4 system, system_ext, vendor, and product partitions read-only with AVB and first-stage mount flags. `file` recognizes the extracted kernel as an ARM64 Linux boot `Image`. The separate DTBO header uses magic `0xd7b7ab1e`, a 2,048-byte page size, and six entries. Entry 0 matches the RMX3231 overlay selected by the stock boot arguments; the exact panel revision in this handset remains unknown. All extracted VBMETA files begin with the AVB `AVB0` magic.

The boot image was parsed with `scripts/inspect_android_boot.py`, which extracts the kernel, ramdisk, and nested base DTB and writes a JSON inventory. The gzip ramdisk integrity test passed. The boot image layout follows Android's published v2 header structure.

The `super.img` uses the Android liblp metadata format: version 10.2, 256-byte header, Virtual A/B flag set, 4,096-byte logical block size, three metadata slots, and one 5 GiB `super` block device. The logical group table has `group_unisoc_a` and `group_unisoc_b`, each with a 5,238,685,696-byte maximum. The current image metadata maps only the `_a` partition names to data extents; `_b` sizes are zero. These are stock image metadata facts and do not establish the phone's live slot or physical GPT state.

## DTBO match to the RMX3231 kernel source

The DTBO v0 table has six entries. Entry 0 identifies the board as `sprd,sp9863a-1h10-go` and includes the `oppo, device_info` and Jadard touchscreen properties present in Realme's `RMX3231-overlay.dts`. That DTS sets `androidboot.hardware=RMX3231 androidboot.dtbo_idx=0`. Entry 1 has the same SoC family string but matches the sibling RMX3235 overlay, while entries 2 to 5 describe other SP9863A board variants. This makes entry 0 the exact stock overlay selected for RMX3231 A.119; it does not prove which panel hardware revision is in this individual phone.

The exact A.119 kernel includes IKCONFIG. Extracting it with the matching kernel source's `scripts/extract-ikconfig` confirmed `CONFIG_BLK_DEV_INITRD=y`, `CONFIG_RD_GZIP=y`, `CONFIG_BINFMT_ELF=y`, `CONFIG_BINFMT_SCRIPT=y`, `CONFIG_PROC_FS=y`, `CONFIG_SYSFS=y`, `CONFIG_TMPFS=y`, `CONFIG_UEVENT_HELPER=y`, and `# CONFIG_DEVTMPFS is not set`. The `CONFIG_UEVENT_HELPER_PATH` is empty. These facts shaped the initial ramdisk: static console/null device nodes, proc and sysfs mounts, then a one-time `mdev -s` scan. It has not been boot tested.

Extracted analysis files (all ignored by Git):

- `firmware/extracted/boot/boot.img`
- `firmware/extracted/boot/kernel.bin`
- `firmware/extracted/boot/ramdisk.img`
- `firmware/extracted/boot/base.dtb`
- `firmware/extracted/boot/dtbo.img`
- `firmware/extracted/super/vendor_a.img`, `system_ext_a.img`, and `product_a.img`
- Selected standalone LTE modem and DSP/co-processor firmware in `firmware/extracted/modem/`
- VBMETA images and the small project configuration/OCDT files

The individual image SHA-256 digests are available by running `sha256sum firmware/extracted/boot/*` locally. Do not publish or flash these images as DEVos artifacts.

## Archive contents outside the PAC

The ZIP also includes `ResearchDownload.zip` (39,078,392 bytes), PAC configuration files, and standalone copies of the SC9860/Unisoc modem, DSP, and co-processor firmware. Their presence confirms vendor modem firmware is available, but does not make Android RIL or vendor services usable from a native Linux system. The modem interface, calibration dependencies, and legal redistribution status remain to be investigated.

## Stage status and next steps

- Stage 1: complete for exact A.119 package identity, direct Realme-host download, local SHA-256, and ZIP CRC verification. Vendor-published checksum/signature verification is still unavailable.
- Stage 2: PAC and boot analysis underway. The full PAC table, boot payload, super metadata, three logical ext4 images, vendor services, six DTBO entries, and selected modem/DSP blobs are inventoried. The larger `system_a` image, panel revision match, and full vendor service/library dependency mapping remain outstanding.
- Build milestone: a small ARM64 BusyBox initramfs was generated and its compressed CPIO structure was inspected. It is not a boot image and has not been run on the phone.
- Stage 3: the Realme open-source kernel source and an RMX3231 community Android device tree have been located separately. The device-tree source does not turn this package into a Linux ROM.
- No operation has been performed on the phone. No image has been flashed, and no partition has been erased or formatted.

The next safe step is to build a boot-image candidate around the A.119 kernel and matched DTBO only after the current bootloader state and a complete stock recovery route are known. No ADB, fastboot, or USB inspection tools are installed in this workspace, so no device connection or bootloader state was established. Do not attempt a phone operation until recovery feasibility is established.

## Sources

- [Direct A.119 package on Realme's download host](https://rms01.realme.net/sw/RMX3231_11.A.119_202310110952.zip)
- [Realme India software update page](https://www.realme.com/in/support/software-update)
- [Third-party RMX3231 firmware index](https://realme.hqloader.in/firmware.php), used to identify the matching direct Realme-hosted file; it is not the source of the downloaded bytes
- [Open-source PAC extractor](https://github.com/bismoy-bot/PAC-Extractor), MIT-licensed Python parser inspected before use
- [Android liblp metadata format](https://android.googlesource.com/platform/system/core/+/refs/heads/main/fs_mgr/liblp/include/liblp/metadata_format.h)
- [Android boot image header format](https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/include/bootimg/bootimg.h)
