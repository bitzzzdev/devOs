#!/usr/bin/env python3
"""Inspect and extract Android boot image v0, v1, or v2 components."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


BOOT_MAGIC = b"ANDROID!"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DT_TABLE_MAGIC = b"\xd7\xb7\xab\x1e"


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract(data: bytes, offset: int, size: int, name: str, output: Path) -> dict:
    if size == 0:
        return {"size": 0, "sha256": None}
    end = offset + size
    if offset < 0 or end > len(data):
        raise ValueError(f"{name} range exceeds the boot image")
    component = data[offset:end]
    (output / name).write_bytes(component)
    return {"size": size, "sha256": digest(component)}


def unwrap_dtb(payload: bytes, output: Path) -> dict:
    if payload.startswith(FDT_MAGIC):
        tree = payload
        wrapper = "raw-fdt"
    elif payload.startswith(DT_TABLE_MAGIC):
        if len(payload) < 32:
            raise ValueError("DT table payload is shorter than its header")
        _, total, header_size, entry_size, count, entries_offset, _, _ = (
            struct.unpack_from(">8I", payload)
        )
        if total > len(payload) or header_size < 32 or entry_size < 32:
            raise ValueError("Invalid DT table header")
        if count != 1:
            raise ValueError(
                f"Expected one base DTB in boot image wrapper, found {count}"
            )
        entry = entries_offset
        if entry + entry_size > total:
            raise ValueError("DT table entry is outside the wrapper")
        tree_size, tree_offset = struct.unpack_from(">2I", payload, entry)
        if tree_offset + tree_size > total:
            raise ValueError("Base DTB is outside the DT table wrapper")
        tree = payload[tree_offset : tree_offset + tree_size]
        wrapper = "single-entry-dt-table"
    else:
        raise ValueError("Boot image DTB payload has an unknown format")

    if not tree.startswith(FDT_MAGIC) or len(tree) < 8:
        raise ValueError("Extracted DTB has no FDT header")
    fdt_size = struct.unpack_from(">I", tree, 4)[0]
    if fdt_size > len(tree):
        raise ValueError("FDT total size exceeds its payload")
    tree = tree[:fdt_size]
    (output / "base.dtb").write_bytes(tree)
    return {"wrapper": wrapper, "size": len(tree), "sha256": digest(tree)}


def inspect(image_path: Path, output: Path) -> dict:
    image = image_path.read_bytes()
    if len(image) < 44 or image[:8] != BOOT_MAGIC:
        raise ValueError("Input is not an Android boot image")

    fields = struct.unpack_from("<10I", image, 8)
    kernel_size, kernel_addr, ramdisk_size, ramdisk_addr = fields[:4]
    second_size, second_addr, tags_addr, page_size, version, os_version = fields[4:]
    if version not in (0, 1, 2):
        raise ValueError(f"Unsupported Android boot header version {version}")
    if page_size < 512 or page_size & (page_size - 1):
        raise ValueError(f"Invalid boot image page size {page_size}")

    output.mkdir(parents=True, exist_ok=True)
    kernel_offset = page_size
    ramdisk_offset = kernel_offset + align(kernel_size, page_size)
    second_offset = ramdisk_offset + align(ramdisk_size, page_size)
    recovery_size = 0
    recovery_offset = 0
    header_size = None
    dtb_size = 0
    dtb_addr = 0

    if version >= 1:
        if len(image) < 1648:
            raise ValueError("Boot image is too short for a v1 header")
        recovery_size = struct.unpack_from("<I", image, 1632)[0]
        recovery_offset = struct.unpack_from("<Q", image, 1636)[0]
        header_size = struct.unpack_from("<I", image, 1644)[0]
    if version >= 2:
        if len(image) < 1660:
            raise ValueError("Boot image is too short for a v2 header")
        dtb_size = struct.unpack_from("<I", image, 1648)[0]
        dtb_addr = struct.unpack_from("<Q", image, 1652)[0]

    recovery_data_offset = second_offset + align(second_size, page_size)
    dtb_offset = recovery_data_offset + align(recovery_size, page_size)

    components = {
        "kernel": extract(image, kernel_offset, kernel_size, "kernel.bin", output),
        "ramdisk": extract(image, ramdisk_offset, ramdisk_size, "ramdisk.img", output),
    }
    if second_size:
        components["second"] = extract(
            image, second_offset, second_size, "second.img", output
        )
    if recovery_size:
        components["recovery_dtbo"] = extract(
            image,
            recovery_offset or recovery_data_offset,
            recovery_size,
            "recovery_dtbo.img",
            output,
        )
    if dtb_size:
        if version < 2:
            raise ValueError("DTB payload requires Android boot header v2")
        dtb_end = dtb_offset + dtb_size
        if dtb_end > len(image):
            raise ValueError("DTB range exceeds the boot image")
        components["dtb"] = unwrap_dtb(image[dtb_offset:dtb_end], output)

    cmdline = image[64:576].split(b"\0", 1)[0].decode("ascii", "replace")
    extra_cmdline = image[608:1632].split(b"\0", 1)[0].decode("ascii", "replace")
    metadata = {
        "image": str(image_path),
        "image_size": len(image),
        "header_version": version,
        "header_size": header_size,
        "page_size": page_size,
        "kernel_address": kernel_addr,
        "ramdisk_address": ramdisk_addr,
        "second_address": second_addr,
        "tags_address": tags_addr,
        "recovery_dtbo_offset_field": recovery_offset,
        "dtb_address": dtb_addr,
        "os_version_field": os_version,
        "cmdline": " ".join(part for part in (cmdline, extra_cmdline) if part),
        "components": components,
    }
    (output / "boot-image.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Android boot.img path")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/extracted/boot"),
        help="directory for extracted components and metadata",
    )
    args = parser.parse_args()
    result = inspect(args.image, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
