#!/usr/bin/env python3
"""Build a small, reproducible ARM64 DEVos initramfs from Debian BusyBox."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import shutil
import struct
import tarfile
import urllib.request
from pathlib import Path


PACKAGE_NAME = "busybox-static_1.37.0-6+b9_arm64.deb"
PACKAGE_URL = (
    "https://deb.debian.org/debian/pool/main/b/busybox/" + PACKAGE_NAME
)
PACKAGE_SHA256 = "c833be48abfa16bc19c4966ec93e289ff1ce5d2f1476cad3a57bd105378cd15c"
SOURCE_DATE_EPOCH = 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_package(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        try:
            request = urllib.request.Request(
                PACKAGE_URL, headers={"User-Agent": "DEVos-initramfs-builder/1"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                with temporary.open("wb") as output:
                    shutil.copyfileobj(response, output)
            temporary.replace(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    actual = sha256(path)
    if actual != PACKAGE_SHA256:
        raise ValueError(
            f"BusyBox package checksum mismatch: expected {PACKAGE_SHA256}, "
            f"received {actual}"
        )


def package_busybox(package: Path) -> bytes:
    data = package.read_bytes()
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("BusyBox package is not a Debian ar archive")

    offset = 8
    while offset + 60 <= len(data):
        header = data[offset : offset + 60]
        if header[58:60] != b"`\n":
            raise ValueError("Invalid Debian ar member header")
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58].decode("ascii").strip())
        offset += 60
        member = data[offset : offset + size]
        if len(member) != size:
            raise ValueError("Truncated Debian ar member")
        if name == "data.tar.xz":
            with tarfile.open(fileobj=io.BytesIO(member), mode="r:xz") as archive:
                for item in archive.getmembers():
                    if item.name.lstrip("./") == "usr/bin/busybox" and item.isfile():
                        stream = archive.extractfile(item)
                        if stream is None:
                            break
                        return stream.read()
            raise ValueError("BusyBox binary is missing from data.tar.xz")
        offset += size + (size & 1)
    raise ValueError("Debian package has no data.tar.xz member")


def check_arm64_static(binary: bytes) -> None:
    if len(binary) < 64 or binary[:4] != b"\x7fELF":
        raise ValueError("BusyBox is not an ELF binary")
    if binary[4:6] != b"\x02\x01":
        raise ValueError("BusyBox must be a little-endian ELF64 binary")
    machine = struct.unpack_from("<H", binary, 18)[0]
    if machine != 183:
        raise ValueError(f"BusyBox ELF machine is {machine}, expected AArch64 (183)")
    phoff = struct.unpack_from("<Q", binary, 32)[0]
    phentsize, phnum = struct.unpack_from("<HH", binary, 54)
    for index in range(phnum):
        kind = struct.unpack_from("<I", binary, phoff + index * phentsize)[0]
        if kind == 3:
            raise ValueError("BusyBox has a PT_INTERP segment; a static binary is required")


def newc_entry(
    name: str,
    inode: int,
    mode: int,
    data: bytes = b"",
    device: tuple[int, int] = (0, 0),
    modified: int = SOURCE_DATE_EPOCH,
) -> bytes:
    encoded_name = name.encode("utf-8") + b"\0"
    fields = (
        inode,
        mode,
        0,
        0,
        1,
        modified,
        len(data),
        0,
        0,
        device[0],
        device[1],
        len(encoded_name),
        0,
    )
    result = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in fields)
    result += encoded_name
    result += b"\0" * ((-len(result)) % 4)
    result += data
    result += b"\0" * ((-len(result)) % 4)
    return result


def build_archive(busybox: bytes, init: bytes, output: Path) -> None:
    entries: list[tuple[str, int, bytes, tuple[int, int]]] = []
    directories = (
        "bin", "dev", "dev/pts", "dev/shm", "proc", "run", "sbin", "sys", "tmp"
    )
    for directory in directories:
        entries.append((directory, 0o040755, b"", (0, 0)))

    entries.append(("bin/busybox", 0o100755, busybox, (0, 0)))
    entries.append(("init", 0o100755, init, (0, 0)))

    for applet in ("cat", "mkdir", "mount", "mdev", "reboot", "sh", "uname"):
        entries.append((f"bin/{applet}", 0o120777, b"busybox", (0, 0)))
    entries.append(("sbin/mdev", 0o120777, b"../bin/busybox", (0, 0)))

    for name, major, minor, mode in (
        ("console", 5, 1, 0o020600),
        ("null", 1, 3, 0o020666),
        ("tty", 5, 0, 0o020666),
        ("zero", 1, 5, 0o020666),
    ):
        entries.append((f"dev/{name}", mode, b"", (major, minor)))

    archive = bytearray()
    for inode, (name, mode, data, device) in enumerate(
        sorted(entries, key=lambda entry: entry[0]), start=1
    ):
        archive.extend(newc_entry(name, inode, mode, data, device))
    archive.extend(newc_entry("TRAILER!!!", len(entries) + 1, 0, b""))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=stream, compresslevel=9, mtime=0
        ) as compressed:
            compressed.write(archive)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        type=Path,
        default=Path("rootfs/cache") / PACKAGE_NAME,
        help="cached Debian arm64 BusyBox package path",
    )
    parser.add_argument(
        "--init", type=Path, default=Path("rootfs/init"), help="init script path"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("builds/devos-rmx3231-initramfs.cpio.gz"),
        help="compressed initramfs output path",
    )
    args = parser.parse_args()

    download_package(args.package)
    busybox = package_busybox(args.package)
    check_arm64_static(busybox)
    build_archive(busybox, args.init.read_bytes(), args.output)
    print(f"Built {args.output} ({args.output.stat().st_size} bytes)")
    print(f"BusyBox SHA-256: {hashlib.sha256(busybox).hexdigest()}")
    print(f"Initramfs SHA-256: {sha256(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
