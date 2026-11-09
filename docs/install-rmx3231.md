# Installing DEVos on the Realme C11 2021

## Read this before you start

DEVos is not ready to install on an RMX3231. The project has a locally built boot image candidate, but it has not been booted on a phone. It starts only a small BusyBox Linux console. It does not yet provide persistent storage, SSH, cellular data, a Wi-Fi hotspot, or the touchscreen mode selector.

The phone reported for this project is already boot-looping. Its current bootloader state, live partition sizes, and a working stock recovery route have not been checked. The image uses a local AVB key instead of Realme's key, and the phone's response to that image is unknown. A wrong boot image or an attempted unlock could make recovery harder or erase user data. For these reasons, this guide does not include a flash or unlock command. Building the candidate on a computer is safe; installing it on the phone is not currently a supported step.

Do not use an RMX3235 or RMX2185 image. Do not erase, format, or write any phone partition while following this guide.

## What you can do now

You can prepare and verify the development image on a Linux computer. A Linux environment is required for these commands. Windows users can run them in WSL2. Keep at least 4 GB free for the firmware ZIP, plus room for the repository and build files. The PAC parser streams the large firmware member and writes only the selected BOOT image, so this guide does not require extracting the full 6 GB PAC to disk.

You will need:

- This DEVos repository, including its kernel submodule.
- The exact stock package `RMX3231_11.A.119_202310110952.zip`, matching the build the user reported.
- Python 3, Git, OpenSSL, and the standard `unzip` and `sha256sum` tools.
- Network access for the build scripts to fetch pinned, checksum-verified build inputs.

The A.119 package was downloaded from a Realme-owned host and passed ZIP CRC validation. Realme did not publish a checksum in the source we found. Its locally calculated SHA-256 is recorded in [the firmware inventory](../firmware/inventory/stage-1-2.md). CRC validation detects archive corruption, but does not authenticate the package as a vendor signature would.

## 1. Get the source and firmware

Clone the repository and its kernel submodule:

```sh
git clone --recurse-submodules https://github.com/bitzzdev/DEVos.git
cd DEVos
```

If you already cloned it without submodules, initialize them:

```sh
git submodule update --init --recursive
```

The original firmware package is not stored in Git. Save your exact A.119 ZIP as `firmware/original/RMX3231_11.A.119_202310110952.zip` if your disk has room. The package URL and verification record are in the inventory. The local build environment used for project analysis stored the ZIP under `/tmp/DEVos-firmware/` because the repository filesystem was too small. If you keep it elsewhere, use that path in the extraction command below.

Check the archive before extraction:

```sh
unzip -tq firmware/original/RMX3231_11.A.119_202310110952.zip
sha256sum firmware/original/RMX3231_11.A.119_202310110952.zip
```

The expected SHA-256 for the package inspected by this project is:

```text
640d925183ecef3b267883f3266fd5e0aa3b20590e5fecaa2088de8f76973f57
```

If your file's hash differs, stop and check the file's source and filename before continuing. This digest is a locally computed comparison value, not a checksum published by Realme.

## 2. Extract the RMX3231 BOOT image

Run this from the repository root. The parser reads the PAC member from inside the ZIP and extracts only its `BOOT` entry:

```sh
python3 scripts/inspect_pac.py \
  firmware/original/RMX3231_11.A.119_202310110952.zip \
  --member cp_sign/SHARKL3_R11/RMX3231-user-native_SHARKL3_R11.pac \
  --extract-id BOOT \
  --extract-dir firmware/extracted/boot \
  --inventory /tmp/rmx3231-a119-pac-partitions.tsv
```

If the ZIP is stored somewhere else, replace only the first path. Confirm that the extracted image is the expected A.119 file:

```sh
sha256sum firmware/extracted/boot/boot.img
```

Expected BOOT image SHA-256:

```text
5a77b4405cfa5b5399d7b3f1822ba57bcf4e386232ef7aab1bf7b39e6159f51e
```

Do not substitute a BOOT image from another build or model. The project inventory explains the PAC contents and the limits of what the package proves.

## 3. Build the local candidate

Build the small ARM64 BusyBox initramfs, then assemble the image:

```sh
python3 scripts/build_initramfs.py
python3 scripts/build_boot_image.py
```

The first command downloads a pinned Debian ARM64 BusyBox package and checks its SHA-256. The second checks the stock boot image against the expected A.119 kernel and device tree, downloads a pinned AOSP AVB tool, and creates a local RSA signing key if one does not exist. It writes the candidate here:

```text
builds/devos-rmx3231-a119-boot-custom-avb.img
```

The private key is stored at `builds/keys/devos-avb-rsa4096.pem`. Keep it private and backed up if you need to reproduce the same signed image. It is ignored by Git and must never be uploaded or shared. The generated image and firmware are also excluded from Git, so cloning the repository alone does not provide a ready-made image.

Verify the image file hash:

```sh
sha256sum builds/devos-rmx3231-a119-boot-custom-avb.img
```

With the same source files and the same private key, the expected SHA-256 is:

```text
a6869b8533e0234d3063cd1e54cf66f9b447ebcd684e82c780b111341d7b6df7
```

If you generated a new key, the signed image hash will differ. The build metadata JSON next to the image records the inputs and verification results. The build script also asks AOSP `avbtool` to verify the image against the local key. This checks the image file, not whether the phone will accept or boot it.

On macOS, use `shasum -a 256 <file>` in place of `sha256sum`. In PowerShell, use `Get-FileHash <file> -Algorithm SHA256`.

## 4. Read-only phone checks, when the phone is accessible

These checks only read information. They do not unlock, erase, or flash the phone. Install Android [Platform Tools](https://developer.android.com/tools/releases/platform-tools) on the computer first. The commands below are generic Fastboot queries and have not been tested on this RMX3231 bootloader. Do not use a key combination or recovery procedure guessed from another Realme model just to reach this step.

If the phone is already in bootloader Fastboot and the computer recognizes it, run:

```sh
fastboot devices
fastboot getvar product
fastboot getvar unlocked
fastboot getvar is-userspace
fastboot getvar current-slot
fastboot getvar has-slot:boot
fastboot getvar partition-size:boot
```

Stop if the product is not confirmed as RMX3231, if Fastboot cannot identify the device, if a required value is missing or unclear, if `is-userspace` says `yes`, or if the boot partition size does not match the candidate. `is-userspace=yes` means Fastbootd, which is a different mode from bootloader Fastboot. An unknown-variable response is not proof of a safe state. Do not share output containing serial numbers or other identifiers publicly.

Even if every query returns an expected value, that is not permission or proof that flashing is safe. The current device is boot-looping, and this project has not demonstrated a complete stock recovery on this phone and computer. Do not try `fastboot boot`, `fastboot flash`, a PAC download operation, bootloader unlock, or any partition write. [AOSP documents that unlocking can wipe user data](https://source.android.com/docs/core/architecture/bootloader/locking_unlocking); the project has not established an unlock route for this model.

## What must be verified before installation instructions can be added

The maintainers need to establish all of the following on the actual RMX3231 and available recovery computer:

- The device can enter a known service or bootloader mode and is identified as RMX3231.
- Its current bootloader state, active slot, and live boot partition size are known from reliable read-only queries.
- A complete A.119 stock restore path using the exact device-matched package has been tested or independently verified, including the required host, drivers, and cable connection.
- The consequences for user data are known, and the owner has a verified backup where possible.
- The boot candidate's expected AVB behavior on this bootloader is known.
- A separate non-destructive boot test succeeds before any persistent partition write is considered.

Until these checks are documented, DEVos has no supported installation procedure. The most useful next step is to establish device detection and a verified stock recovery route without writing to the phone. See [the boot strategy](boot-strategy.md) for the evidence gathered so far and [hardware compatibility](hardware-compatibility.md) for the remaining Linux support work.

## Current image status

The candidate preserves the A.119 kernel and base device tree, but replaces Android's ramdisk with a minimal Linux initramfs. It is signed by a locally generated key. Realme's root vbmeta pins a different key for the boot chain, so the candidate cannot be assumed to boot while the bootloader is locked. RMX3231 acceptance of this custom-key image is unverified. The candidate has not been booted on hardware, and its 64 MiB size comes from the A.119 package, not from a live read of this phone's partition table.

The current milestone is a build artifact for controlled development, not an installable DEVos release. Check the project's [license](../LICENSE) before reusing its original code. Stock Realme firmware is proprietary and is not included in the repository.
