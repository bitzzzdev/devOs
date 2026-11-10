#!/usr/bin/env python3
"""Build a single-file flashable installer ISO and ZIP package for DEVos."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


README_TEXT = """DEVos Realme C11 2021 (RMX3231) Single-File Flashable Installer
================================================================

This package contains the DEVos multi-boot candidate image and flashing
scripts for the Realme C11 2021 (model RMX3231, Unisoc SC9863A SoC).

PACKAGE CONTENTS:
-----------------
  boot.img          - 64 MiB custom-key AVB-signed multi-boot candidate
  flash.sh          - Automated one-command fastboot flasher (Linux/macOS)
  flash.bat         - Automated one-command fastboot flasher (Windows)
  manifest.json     - Build details, partition targets, and hardware spec
  checksums.sha256  - Cryptographic verification digests
  README.txt        - This instruction document

BOOT MODES AVAILABLE AFTER FLASHING:
------------------------------------
When your device powers on, the DEVos Multi-Boot Selector appears on the
boot console screen with four selectable modes:

  [1] Pocket VPS (Headless Linux micro-server)
      - USB gadget network (RNDIS/CDC-Ethernet) with IP 192.168.7.2
      - DHCP server automatically leases 192.168.7.1 to the connected host PC
      - Dropbear SSH and shell daemon listening on port 22

  [2] Wi-Fi Router (AP Hotspot & Gateway NAT)
      - Configures Wi-Fi AP interface with IP 192.168.43.1
      - Built-in DHCP and DNS service for connected Wi-Fi devices
      - IPv4 packet forwarding and iptables firewall NAT routing

  [3] Dual Mode (Pocket VPS + Wi-Fi Router combined)
      - Concurrently runs both the Wi-Fi AP router and Pocket VPS server
      - Access the Linux environment from Wi-Fi (192.168.43.1) or USB (192.168.7.2)
      - Wi-Fi clients receive full gateway internet routing

  [4] Regular Barebones (Stock Android System)
      - Boots normal stock Android userspace
      - All phone hardware active: camera, microphone, touchscreen, audio,
        cellular telephony (calling and SMS), 4G LTE data, and Wi-Fi
      - Leaves stock system and vendor partitions unmodified on super
      - Best possible compatibility for regular phone use and UPI payment apps

HOW TO FLASH:
-------------
Prerequisites:
  1. An unlocked bootloader on your Realme C11 2021.
  2. Android platform-tools (fastboot) installed on your computer.

Flashing on Linux or macOS:
  1. Put the phone into Fastboot mode:
     Power off completely, then hold Volume Down + Power until Fastboot appears.
  2. Connect the phone to your computer via USB cable.
  3. Run the flasher script:
     chmod +x flash.sh && ./flash.sh

Flashing on Windows:
  1. Put the phone into Fastboot mode.
  2. Connect via USB cable.
  3. Double-click flash.bat (or run flash.bat from Command Prompt).

Manual fastboot command:
  fastboot flash boot boot.img
  fastboot reboot

RECOVERY NOTICE:
----------------
This is a development candidate. If you need to revert to stock firmware,
flash the original stock A.119 BOOT partition image using fastboot:
  fastboot flash boot original_stock_boot.img
or restore using the Realme PAC download tool (ResearchDownload).
"""

FLASH_SH = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOT_IMG="${SCRIPT_DIR}/boot.img"

echo "========================================================="
echo "   DEVos Realme C11 2021 (RMX3231) Fastboot Installer   "
echo "========================================================="
echo ""

if [ ! -f "$BOOT_IMG" ]; then
    echo "Error: boot.img not found in ${SCRIPT_DIR}"
    exit 1
fi

if ! command -v fastboot >/dev/null 2>&1; then
    echo "Error: 'fastboot' command was not found in PATH."
    echo "Please install Android platform-tools before running this script."
    echo "Debian/Ubuntu: sudo apt-get install android-tools-fastboot"
    echo "Fedora:        sudo dnf install android-tools"
    echo "macOS:         brew install android-platform-tools"
    exit 1
fi

echo "Verifying device connection in fastboot mode..."
DEVICES=$(fastboot devices)
if [ -z "$DEVICES" ]; then
    echo "No device detected. Put device into Fastboot mode:"
    echo "  1. Turn off phone completely."
    echo "  2. Hold Volume Down + Power button until Fastboot screen shows."
    echo "  3. Connect phone to computer via USB."
    echo ""
    echo "Waiting for device..."
    fastboot wait-for-device 2>/dev/null || true
fi

echo "Connected fastboot device:"
fastboot devices

echo ""
echo "Flashing DEVos multi-boot candidate to 'boot' partition..."
fastboot flash boot "$BOOT_IMG"

echo ""
echo "Flashing succeeded. Rebooting device..."
fastboot reboot

echo ""
echo "========================================================="
echo "Device reboot initiated."
echo "Upon boot, use the DEVos Multi-Boot Selector:"
echo "  [1] Pocket VPS          - Linux server (SSH/RNDIS)"
echo "  [2] Wi-Fi Router        - AP hotspot with DHCP/NAT"
echo "  [3] Dual Mode           - Pocket VPS + Wi-Fi Router"
echo "  [4] Regular Barebones   - Normal Android (camera/mic/calls)"
echo "========================================================="
"""

FLASH_BAT = """@echo off
setlocal
set SCRIPT_DIR=%~dp0
set BOOT_IMG=%SCRIPT_DIR%boot.img

echo =========================================================
echo    DEVos Realme C11 2021 (RMX3231) Fastboot Installer   
echo =========================================================
echo.

if not exist "%BOOT_IMG%" (
    echo Error: boot.img was not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

where fastboot >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: 'fastboot' command was not found in PATH.
    echo Please install Android platform-tools and add fastboot to PATH.
    pause
    exit /b 1
)

echo Checking for connected fastboot device...
fastboot devices
echo.

echo Flashing DEVos multi-boot image to boot partition...
fastboot flash boot "%BOOT_IMG%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Flashing failed. Please check USB cable and bootloader unlock status.
    pause
    exit /b 1
)

echo.
echo Flashing complete. Rebooting device...
fastboot reboot

echo.
echo =========================================================
echo Device rebooted.
echo Multi-Boot Selector Options:
echo   [1] Pocket VPS
echo   [2] Wi-Fi Router
echo   [3] Dual Mode (VPS + Router)
echo   [4] Regular Barebones (Stock Android)
echo =========================================================
pause
"""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def find_iso_tool() -> str | None:
    for tool in ("genisoimage", "mkisofs", "xorrisofs"):
        if shutil.which(tool):
            return tool
    return None


def build_package(
    boot_image: Path,
    output_iso: Path,
    output_zip: Path,
    volume_label: str = "DEVOS_RMX3231",
) -> dict[str, object]:
    if not boot_image.exists():
        raise FileNotFoundError(f"Boot image candidate not found: {boot_image}")

    boot_sha256 = file_sha256(boot_image)
    output_iso.parent.mkdir(parents=True, exist_ok=True)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="devos-flashable-") as temp_dir:
        staging = Path(temp_dir) / "payload"
        staging.mkdir(parents=True, exist_ok=True)

        # Copy boot.img
        shutil.copyfile(boot_image, staging / "boot.img")

        # Write flasher scripts and documentation
        flash_sh_path = staging / "flash.sh"
        flash_sh_path.write_text(FLASH_SH, encoding="utf-8")
        flash_sh_path.chmod(0o755)

        flash_bat_path = staging / "flash.bat"
        flash_bat_path.write_text(FLASH_BAT, encoding="utf-8")

        readme_path = staging / "README.txt"
        readme_path.write_text(README_TEXT, encoding="utf-8")

        manifest = {
            "name": "DEVos Single-File Flashable Package",
            "target_device": "Realme C11 2021 (RMX3231)",
            "soc": "Unisoc SC9863A",
            "kernel_version": "4.14.193",
            "boot_partition_size": boot_image.stat().st_size,
            "boot_image_sha256": boot_sha256,
            "boot_modes": {
                "1": "Pocket VPS (Linux micro-server, USB-RNDIS, SSH)",
                "2": "Wi-Fi Router (AP hotspot, DHCP gateway, NAT routing)",
                "3": "Dual Mode (Pocket VPS + Wi-Fi Router combined)",
                "4": "Regular Barebones (Stock Android, camera/mic/cell phone)",
            },
            "default_mode": 4,
            "boot_timeout_seconds": 5,
        }
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Generate checksums file
        checksums_lines = []
        for item in sorted(staging.iterdir()):
            if item.is_file():
                checksums_lines.append(f"{file_sha256(item)}  {item.name}\n")
        (staging / "checksums.sha256").write_text("".join(checksums_lines), encoding="utf-8")

        # 1. Build ZIP package
        with zipfile.ZipFile(
            output_zip, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for item in sorted(staging.iterdir()):
                if item.is_file():
                    archive.write(item, arcname=item.name)

        # 2. Build ISO image
        iso_tool = find_iso_tool()
        if iso_tool:
            cmd = [
                iso_tool,
                "-o",
                str(output_iso),
                "-V",
                volume_label[:32],
                "-r",
                "-J",
                str(staging),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"{iso_tool} failed to build ISO: {result.stderr}"
                )
        else:
            raise RuntimeError(
                "Neither genisoimage, mkisofs, nor xorrisofs is available to create ISO."
            )

    iso_sha256 = file_sha256(output_iso)
    zip_sha256 = file_sha256(output_zip)

    # Write companion sha256 files
    output_iso.with_suffix(output_iso.suffix + ".sha256").write_text(
        f"{iso_sha256}  {output_iso.name}\n", encoding="utf-8"
    )
    output_zip.with_suffix(output_zip.suffix + ".sha256").write_text(
        f"{zip_sha256}  {output_zip.name}\n", encoding="utf-8"
    )

    return {
        "boot_image": str(boot_image),
        "boot_sha256": boot_sha256,
        "iso_package": str(output_iso),
        "iso_size": output_iso.stat().st_size,
        "iso_sha256": iso_sha256,
        "zip_package": str(output_zip),
        "zip_size": output_zip.stat().st_size,
        "zip_sha256": zip_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--boot-image",
        type=Path,
        default=Path("builds/devos-rmx3231-a119-boot-custom-avb.img"),
        help="AVB-signed multi-boot candidate boot image",
    )
    parser.add_argument(
        "--output-iso",
        type=Path,
        default=Path("builds/devos-rmx3231-installer.iso"),
        help="output flashable ISO installer path",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=Path("builds/devos-rmx3231-flashable.zip"),
        help="output flashable ZIP archive path",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="DEVOS_RMX3231",
        help="ISO volume label (max 32 chars)",
    )
    args = parser.parse_args()

    try:
        summary = build_package(
            args.boot_image,
            args.output_iso,
            args.output_zip,
            volume_label=args.label,
        )
    except Exception as error:
        parser.error(str(error))

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
