# RMX3231 Troubleshooting and Recovery Guide

## Known Issue: Unlocked Boot Loop at Splash Logo

### Symptom

During startup, the screen briefly prints a yellow or white bootloader warning:
```text
LOCK FLAG STATUS : UNLOCKED !!!
```
or
```text
WARNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!
```
The device then displays the white Realme logo with the "Powered by Android (Go Edition)" footer and continuously reboots after 10 to 15 seconds.

### Root Cause Analysis

This symptom confirms that hardware initialization succeeded through Stage 0 (BootROM), Stage 1 (SPL), and Stage 2 (U-Boot). The screen panel and backlight drivers initialized correctly to display `logo.bin`. The crash occurs after U-Boot jumps to the Linux kernel (`boot.img`) and Android first-stage init.

The reboot loop is triggered by one of four specific mechanisms:

1. **File-Based Encryption (FBE) and Android Rescue Party (Most Common)**:
   When the bootloader is unlocked, or when changing boot images, cryptographic encryption credentials stored in the secure TrustZone (`trustos`, `teecfg`, and `metadata` partitions) no longer match the existing encrypted `/data` filesystem. Android first-stage init fails to mount userdata and triggers the Android Rescue Party mechanism. After several failed reboot cycles, Rescue Party forces continuous reboots.

2. **AVB 2.0 and dm-verity Hash Mismatch**:
   Even though Unisoc U-Boot prints `SKIP VERIFY!`, Android first-stage init and kernel drivers enforce integrity checking on logical partitions (`system`, `vendor`, `product`). If `boot.img` or any system partition was modified without disabling verity verification on `vbmeta`, the kernel panics on signature failure and the hardware watchdog resets the phone.

3. **Virtual A/B Active Slot Flip**:
   The Realme C11 2021 uses Virtual A/B dynamic partitions. Factory stock packages populate only slot `_a` with partition extents; slot `_b` entries are unpopulated. If an interrupted fastboot command or OTA switched the active slot to `b`, the bootloader attempts to boot an empty slot and reboots immediately.

4. **Corrupted or Incompatible Boot Image**:
   Flashing a boot image from another model (such as the MediaTek Realme C11 RMX2185 or Narzo 50i RMX3235) or a generic patched image can fail to load the Unisoc display or power management drivers, triggering an immediate kernel panic.

---

## Hardware Key Combinations for RMX3231

The Realme C11 2021 uses a Unisoc SC9863A SoC with non-standard hardware key mappings. Use the following combinations:

| Mode | Key Combination | Action / Result |
| --- | --- | --- |
| Force Power Off | Hold **Power + Volume Down** for 10-15 seconds | Shuts down phone from a continuous reboot loop |
| Fastboot Mode | Hold **Volume Up + Power** from powered-off state | Reaches bootloader fastboot terminal |
| Stock Recovery | Hold **Volume Down + Power** from powered-off state | Reaches Android recovery menu for data formatting |
| Unisoc BROM Mode | Hold **Volume Down** while connecting USB cable to PC | Hardware download mode for SPD Upgrade Tool flashing |

---

## Resolution Steps

### Step 1: Break the Reboot Cycle

Do not attempt fastboot commands while the handset is actively rebooting.

1. Disconnect the USB cable.
2. Hold both **Power** and **Volume Down** simultaneously for 10 to 15 seconds until the screen goes completely dark.
3. Release the buttons immediately once the screen is off.

### Step 2: Enter Fastboot Mode and Inspect State

1. Hold the **Volume Up** button and press the **Power** button until the Fastboot text appears.
2. Connect the handset to your computer via USB.
3. Verify connection:
   ```sh
   fastboot devices
   ```
4. Query device partition and unlock variables:
   ```sh
   fastboot getvar unlocked
   fastboot getvar current-slot
   fastboot getvar product
   ```

### Step 3: Fix Active Slot Flip

If `current-slot` returns `b`, the device is attempting to boot from an empty slot. Switch back to slot A:

```sh
fastboot set_active a
fastboot reboot
```

If the phone boots successfully, the issue was an unpopulated slot. If it continues looping, proceed to Step 4.

### Step 4: Clear Encrypted Userdata (Fixes Rescue Party Loop)

If the active slot is already `a`, the boot loop is typically caused by an encrypted userdata mismatch resulting from the bootloader unlock.

Erase the userdata, cache, and metadata partitions:

```sh
fastboot erase userdata
fastboot erase cache
fastboot erase metadata
```

Alternatively, use the full wipe command:

```sh
fastboot -w
```

Then reboot:

```sh
fastboot reboot
```

*Note: The first startup after clearing userdata takes 3 to 5 minutes while Android rebuilds the filesystem structures.*

### Step 5: Restore Verified Boot Partition

If clearing userdata does not resolve the loop, the `boot` partition is damaged or failing verification.

Flash the verified stock A.119 `boot.img` or the DEVos candidate image:

```sh
fastboot flash boot boot.img
```

If testing custom boot images on Unisoc hardware, disable AVB verification flags on `vbmeta`:

```sh
fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img
```

Then reboot:

```sh
fastboot reboot
```

---

## Emergency Factory Restore via Unisoc BROM Mode

If the device cannot enter Fastboot mode, or if partitions inside `super.img` are damaged, Unisoc chipsets include a hardware BootROM download mode that cannot be overwritten by software.

### Requirements

- A Windows computer with Spreadtrum / Unisoc USB drivers installed.
- SPD Upgrade Tool or ResearchDownload.exe flasher.
- The official stock A.119 PAC firmware archive (`RMX3231-user-native_SHARKL3_R11.pac`).

### Flashing Procedure

1. Launch `SPD_Upgrade_Tool.exe`.
2. Click the **Load Packet** button (gear icon) and select the A.119 `.pac` file. Wait for the tool to unpack and verify the package.
3. Click the **Start Downloading** button (play arrow icon) to enter listening mode.
4. Ensure the phone is completely powered off.
5. Press and hold the **Volume Down** button (without touching the Power button).
6. While holding **Volume Down**, plug the USB cable into the computer.
7. The tool detects the Spreadtrum COM port, loads FDL1 and FDL2 into internal SRAM, and begins writing partitions. Release the Volume button once the progress bar moves.
8. When the progress bar turns green with a **Passed** message, disconnect the USB cable and power on the handset.
