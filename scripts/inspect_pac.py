#!/usr/bin/env python3
"""Inventory a Unisoc PAC file or a PAC member inside a ZIP archive."""

from __future__ import annotations

import argparse
import contextlib
import struct
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterator


PAC_HEADER = struct.Struct("<44sII512s512sIIIIIII200sIII800sIHH")
FILE_HEADER = struct.Struct("<I512s512s504sIIIIIIII5I996s")


def text_field(value: bytes) -> str:
    return value.decode("utf-16le", errors="strict").rstrip("\0")


def read_exact(stream: BinaryIO, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ValueError(f"Expected {size} bytes, received {len(data)}")
    return data


def parse_pac(stream: BinaryIO, size: int) -> tuple[dict, list[dict]]:
    if size < PAC_HEADER.size:
        raise ValueError("Input is too small to contain a PAC header")
    values = PAC_HEADER.unpack(read_exact(stream, PAC_HEADER.size))
    version = text_field(values[0])
    if version not in ("BP_R1.0.0", "BP_R2.0.1"):
        raise ValueError(f"Unsupported PAC version {version!r}")
    declared_size = values[1] * 0x100000000 + values[2]
    if declared_size != size:
        raise ValueError(f"PAC declares {declared_size} bytes, input has {size}")

    count = values[5]
    table_offset = values[6]
    if table_offset < PAC_HEADER.size or table_offset + count * FILE_HEADER.size > size:
        raise ValueError("PAC partition table range is invalid")

    stream.seek(table_offset)
    entries = []
    for _ in range(count):
        fields = FILE_HEADER.unpack(read_exact(stream, FILE_HEADER.size))
        if fields[0] != FILE_HEADER.size:
            raise ValueError(f"Unknown PAC file header size {fields[0]}")
        partition_id = text_field(fields[1])
        filename = text_field(fields[2])
        image_size = fields[4] * 0x100000000 + fields[6]
        data_offset = fields[5] * 0x100000000 + fields[9]
        if image_size and (data_offset > size or image_size > size - data_offset):
            raise ValueError(f"PAC entry {filename!r} exceeds the input file")
        if filename and PurePosixPath(filename).name != filename:
            raise ValueError(f"Unsafe PAC filename {filename!r}")
        entries.append(
            {
                "partition_id": partition_id,
                "filename": filename,
                "byte_size": image_size,
                "data_offset": data_offset,
                "file_flag": fields[7],
                "check_flag": fields[8],
            }
        )
    metadata = {
        "version": version,
        "size": declared_size,
        "product": text_field(values[3]),
        "firmware": text_field(values[4]),
        "entry_count": count,
        "table_offset": table_offset,
        "magic": values[17],
        "crc1": values[18],
        "crc2": values[19],
    }
    return metadata, entries


@contextlib.contextmanager
def open_input(path: Path, member: str | None) -> Iterator[tuple[BinaryIO, int]]:
    if member is None:
        with path.open("rb") as stream:
            yield stream, path.stat().st_size
        return
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(member)
        with archive.open(info) as stream:
            yield stream, info.file_size


def write_inventory(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(
            "partition_id\tfilename\tbyte_size\tdata_offset\tfile_flag\tcheck_flag\n"
        )
        for entry in entries:
            stream.write(
                "\t".join(
                    str(entry[key])
                    for key in (
                        "partition_id",
                        "filename",
                        "byte_size",
                        "data_offset",
                        "file_flag",
                        "check_flag",
                    )
                )
                + "\n"
            )


def extract_entries(
    stream: BinaryIO, entries: list[dict], names: set[str], output: Path
) -> None:
    selected = [entry for entry in entries if entry["partition_id"] in names]
    found = {entry["partition_id"] for entry in selected}
    missing = names - found
    if missing:
        raise ValueError("Unknown partition IDs: " + ", ".join(sorted(missing)))

    output.mkdir(parents=True, exist_ok=True)
    for entry in sorted(selected, key=lambda item: item["data_offset"]):
        filename = entry["filename"]
        size = entry["byte_size"]
        if not filename or not size:
            raise ValueError(f"PAC entry {entry['partition_id']} has no image file")
        target = output / filename
        stream.seek(entry["data_offset"])
        remaining = size
        with target.open("wb") as destination:
            while remaining:
                block = stream.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError(f"Unexpected end while extracting {filename}")
                destination.write(block)
                remaining -= len(block)
        print(f"Extracted {entry['partition_id']}: {target} ({size} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="PAC file or containing ZIP file")
    parser.add_argument(
        "--member", help="PAC path inside input ZIP; omit for a standalone PAC"
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("firmware/inventory/pac-partitions.tsv"),
        help="output TSV inventory path",
    )
    parser.add_argument(
        "--extract-id",
        action="append",
        default=[],
        metavar="PARTITION_ID",
        help="extract a named PAC image; may be repeated",
    )
    parser.add_argument(
        "--extract-dir",
        type=Path,
        default=Path("firmware/extracted/pac"),
        help="directory for selected image files",
    )
    args = parser.parse_args()

    with open_input(args.input, args.member) as (stream, size):
        metadata, entries = parse_pac(stream, size)
        write_inventory(args.inventory, entries)
        print(
            f"PAC {metadata['product']} {metadata['firmware']}: "
            f"{metadata['entry_count']} entries, {metadata['size']} bytes, "
            f"magic 0x{metadata['magic']:08x}"
        )
        print(f"Inventory: {args.inventory}")
        if args.extract_id:
            extract_entries(
                stream, entries, set(args.extract_id), args.extract_dir
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
