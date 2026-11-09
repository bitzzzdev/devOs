#!/usr/bin/env python3
"""Assemble an unsigned RMX3231 A.119 boot-image candidate.

This tool only creates a local image. It does not communicate with a device.
The stock AVB footer cannot authenticate a ramdisk changed by DEVos, so the
candidate is padded to the source partition size with zeroes and contains no
AVB footer or vbmeta image.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path


BOOT_MAGIC = b"ANDROID!"
AVB_FOOTER_MAGIC = b"AVBf"
AVB_VBMETA_MAGIC = b"AVB0"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DT_TABLE_MAGIC = b"\xd7\xb7\xab\x1e"
EXPECTED_KERNEL_SHA256 = "3bb948118add707f795cbced28c043657aed732ea72c17c99ed71d95e321ceec"
EXPECTED_BASE_DTB_SHA256 = "3042c329c3f877c6d96c3b2f8e7e8166dd8d65dbbeddbf8f7aa93be668b3301d"
EXPECTED_PARTITION_SIZE = 67_108_864


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cpio_names(data: bytes) -> set[str]:
    names: set[str] = set()
    offset = 0
    while offset + 110 <= len(data):
        header = data[offset : offset + 110]
        if header[:6] != b"070701":
            raise ValueError("initramfs is not a newc CPIO archive")
        fields = [int(header[i : i + 8], 16) for i in range(6, 110, 8)]
        file_size, name_size = fields[6], fields[11]
        offset += 110
        if name_size < 1 or offset + name_size > len(data):
            raise ValueError("initramfs has an invalid CPIO filename")
        name = data[offset : offset + name_size - 1].decode("utf-8")
        offset = align(offset + name_size, 4)
        if offset + file_size > len(data):
            raise ValueError(f"initramfs entry {name!r} exceeds the archive")
        offset = align(offset + file_size, 4)
        if name == "TRAILER!!!":
            return names
        names.add(name)
    raise ValueError("initramfs has no CPIO trailer")


def inspect_stock(image: bytes) -> dict[str, object]:
    if len(image) != EXPECTED_PARTITION_SIZE:
        raise ValueError(
            f"stock boot image is {len(image)} bytes; expected the A.119 "
            f"{EXPECTED_PARTITION_SIZE}-byte BOOT partition image"
        )
    if image[:8] != BOOT_MAGIC:
        raise ValueError("stock input does not start with Android boot magic")

    fields = struct.unpack_from("<10I", image, 8)
    kernel_size, _, ramdisk_size, _, second_size, _, _, page_size, version, _ = fields
    if version != 2 or page_size != 2048:
        raise ValueError("expected the A.119 Android boot header v2, 2048-byte pages")
    if second_size:
        raise ValueError("unexpected second-stage bootloader component")

    recovery_size, recovery_offset, header_size = struct.unpack_from("<IQI", image, 1632)
    dtb_size, _ = struct.unpack_from("<IQ", image, 1648)
    if recovery_size or recovery_offset or header_size != 1660 or not dtb_size:
        raise ValueError("unexpected A.119 recovery-DTBO or header-v2 layout")

    kernel_offset = page_size
    ramdisk_offset = kernel_offset + align(kernel_size, page_size)
    dtb_offset = ramdisk_offset + align(ramdisk_size, page_size)
    end = dtb_offset + dtb_size
    if end > len(image):
        raise ValueError("boot image component range exceeds source image")
    kernel = image[kernel_offset : kernel_offset + kernel_size]
    stock_ramdisk = image[ramdisk_offset : ramdisk_offset + ramdisk_size]
    dtb_wrapper = image[dtb_offset:end]
    if sha256(kernel) != EXPECTED_KERNEL_SHA256:
        raise ValueError("stock kernel does not match the recorded A.119 RMX3231 kernel")
    if not stock_ramdisk.startswith(b"\x1f\x8b"):
        raise ValueError("stock ramdisk is not gzip-compressed")

    if dtb_wrapper.startswith(FDT_MAGIC):
        base_dtb = dtb_wrapper
    elif dtb_wrapper.startswith(DT_TABLE_MAGIC) and len(dtb_wrapper) >= 32:
        _, total, header_len, entry_len, count, entries_offset, _, _ = struct.unpack_from(
            ">8I", dtb_wrapper
        )
        if count != 1 or header_len < 32 or entry_len < 32:
            raise ValueError("expected the one-entry A.119 base-DTB table")
        if total > len(dtb_wrapper) or entries_offset + entry_len > total:
            raise ValueError("invalid A.119 DTB table bounds")
        tree_size, tree_offset = struct.unpack_from(">2I", dtb_wrapper, entries_offset)
        if tree_offset + tree_size > total:
            raise ValueError("A.119 base DTB exceeds its table")
        base_dtb = dtb_wrapper[tree_offset : tree_offset + tree_size]
    else:
        raise ValueError("stock boot image has an unknown DTB wrapper")
    if sha256(base_dtb) != EXPECTED_BASE_DTB_SHA256:
        raise ValueError("base DTB does not match the recorded A.119 image")
    expected_id = android_legacy_id(
        [kernel, stock_ramdisk, b"", b"", dtb_wrapper]
    )
    if image[576:608] != expected_id:
        raise ValueError("stock boot header ID does not match its A.119 components")

    footer = image[-64:]
    magic, major, minor, original_size, vbmeta_offset, vbmeta_size, reserved = struct.unpack(
        "!4s2L3Q28s", footer
    )
    if magic != AVB_FOOTER_MAGIC or (major, minor) != (1, 0):
        raise ValueError("stock image does not have the expected AVB 1.0 footer")
    if reserved != bytes(28) or vbmeta_offset + vbmeta_size > len(image) - 64:
        raise ValueError("stock AVB footer fields are invalid")
    if image[vbmeta_offset : vbmeta_offset + 4] != AVB_VBMETA_MAGIC:
        raise ValueError("stock AVB footer does not point to a vbmeta image")

    return {
        "kernel": kernel,
        "ramdisk": stock_ramdisk,
        "dtb_wrapper": dtb_wrapper,
        "kernel_size": kernel_size,
        "ramdisk_size": ramdisk_size,
        "dtb_size": dtb_size,
        "page_size": page_size,
        "original_image_size": original_size,
        "vbmeta_offset": vbmeta_offset,
        "vbmeta_size": vbmeta_size,
    }


def android_legacy_id(parts: list[bytes]) -> bytes:
    digest = hashlib.sha1()
    for part in parts:
        digest.update(part)
        digest.update(struct.pack("<I", len(part)))
    return digest.digest() + bytes(12)


def build(stock_path: Path, initramfs_path: Path, output_path: Path) -> dict[str, object]:
    stock = stock_path.read_bytes()
    info = inspect_stock(stock)
    ramdisk = initramfs_path.read_bytes()
    archive = gzip.decompress(ramdisk)
    names = cpio_names(archive)
    if "init" not in names or "bin/busybox" not in names:
        raise ValueError("initramfs must contain init and bin/busybox")

    kernel = info["kernel"]
    dtb_wrapper = info["dtb_wrapper"]
    page_size = int(info["page_size"])
    header = bytearray(stock[:page_size])
    struct.pack_into("<I", header, 16, len(ramdisk))
    header[576:608] = android_legacy_id([kernel, ramdisk, b"", b"", dtb_wrapper])

    payload = bytearray(header)
    payload.extend(kernel)
    payload.extend(bytes(align(len(payload), page_size) - len(payload)))
    payload.extend(ramdisk)
    payload.extend(bytes(align(len(payload), page_size) - len(payload)))
    payload.extend(dtb_wrapper)
    if len(payload) > EXPECTED_PARTITION_SIZE:
        raise ValueError("assembled boot image exceeds the source BOOT partition size")

    # Pad the complete partition image so an old footer cannot remain at the
    # end if the output is later written as a full partition image.
    payload.extend(bytes(EXPECTED_PARTITION_SIZE - len(payload)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    result = {
        "device": "Realme C11 2021 RMX3231",
        "firmware": "RMX3231_11.A.119",
        "image_type": "Android boot header v2, unsigned DEVos candidate",
        "partition_size_bytes": len(payload),
        "output": str(output_path),
        "output_sha256": sha256(payload),
        "source_boot_sha256": sha256(stock),
        "kernel_sha256": sha256(kernel),
        "initramfs_sha256": sha256(ramdisk),
        "dtb_wrapper_sha256": sha256(dtb_wrapper),
        "boot_header_id_sha1": header[576:596].hex(),
        "stock_avb_footer_removed": True,
        "stock_vbmeta_removed": True,
        "remaining_partition_bytes_zero_padded": len(payload)
        - (len(header) + len(kernel) + len(ramdisk) + len(dtb_wrapper)),
        "device_boot_tested": False,
        "flash_authorized_or_performed": False,
        "warning": (
            "Unsigned candidate only. The stock AVB metadata was removed and "
            "cannot authenticate this changed ramdisk. Bootloader acceptance, "
            "live partition size, and recovery route are unverified. Do not "
            "flash until those are established."
        ),
    }
    metadata_path = output_path.with_suffix(output_path.suffix + ".json")
    metadata_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stock-boot",
        type=Path,
        default=Path("firmware/extracted/boot/boot.img"),
        help="preserved RMX3231 A.119 BOOT image extracted from PAC",
    )
    parser.add_argument(
        "--initramfs",
        type=Path,
        default=Path("builds/devos-rmx3231-initramfs.cpio.gz"),
        help="gzip-compressed ARM64 DEVos initramfs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("builds/devos-rmx3231-a119-boot-unsigned.img"),
        help="local 64 MiB unsigned boot-image candidate",
    )
    args = parser.parse_args()
    try:
        result = build(args.stock_boot, args.initramfs, args.output)
    except (OSError, ValueError, struct.error) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
