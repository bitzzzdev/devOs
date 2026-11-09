#!/usr/bin/env python3
"""Assemble a custom-key AVB-signed RMX3231 A.119 boot-image candidate.

This tool only creates a local image. It does not communicate with a device.
The stock AVB key cannot authenticate a ramdisk changed by DEVos. The image
uses a local key, so standard AVB requires an unlocked bootloader to tolerate
the chained-key mismatch.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


BOOT_MAGIC = b"ANDROID!"
AVB_FOOTER_MAGIC = b"AVBf"
AVB_VBMETA_MAGIC = b"AVB0"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DT_TABLE_MAGIC = b"\xd7\xb7\xab\x1e"
EXPECTED_KERNEL_SHA256 = "3bb948118add707f795cbced28c043657aed732ea72c17c99ed71d95e321ceec"
EXPECTED_BASE_DTB_SHA256 = "3042c329c3f877c6d96c3b2f8e7e8166dd8d65dbbeddbf8f7aa93be668b3301d"
EXPECTED_AVB_CHAIN_KEY_SHA1 = "9405a8f24d5b71da4420fa3edc5a5bd2e7420446"
EXPECTED_PARTITION_SIZE = 67_108_864
AVBTOOL_URL = (
    "https://android.googlesource.com/platform/external/avb/+/"
    "761178607206f4cb2af79ed9eec52d8cbd814adb/avbtool.py?format=TEXT"
)
AVBTOOL_SHA256 = "e5a664a38db623da00f080219bc0ee60a640a9dc4a872803616fae4938ac749b"


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


def ensure_avbtool(path: Path) -> None:
    if not path.exists():
        import base64

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        request = urllib.request.Request(
            AVBTOOL_URL, headers={"User-Agent": "DEVos-boot-builder/1"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                encoded = response.read()
            tool = base64.b64decode(encoded, validate=True)
            if sha256(tool) != AVBTOOL_SHA256:
                raise ValueError("downloaded AOSP avbtool.py checksum mismatch")
            temporary.write_bytes(tool)
            temporary.replace(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    if sha256(path.read_bytes()) != AVBTOOL_SHA256:
        raise ValueError(f"AOSP avbtool.py checksum mismatch: {path}")


def run_avbtool(tool: Path, *arguments: str) -> str:
    result = subprocess.run(
        [sys.executable, str(tool), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(
            f"AOSP avbtool failed ({result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def ensure_signing_key(key_path: Path) -> None:
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if not key_path.exists():
        temporary = key_path.with_suffix(key_path.suffix + ".part")
        try:
            result = subprocess.run(
                ["openssl", "genrsa", "-out", str(temporary), "4096"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                raise ValueError(
                    "openssl could not generate the local AVB key: "
                    f"{result.stderr.strip()}"
                )
            os.chmod(temporary, 0o600)
            temporary.replace(key_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    os.chmod(key_path, 0o600)
    result = subprocess.run(
        ["openssl", "rsa", "-in", str(key_path), "-check", "-noout"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"AVB signing key is not a valid RSA private key: {key_path}")


def build(
    stock_path: Path,
    initramfs_path: Path,
    output_path: Path,
    avbtool_path: Path,
    key_path: Path,
) -> dict[str, object]:
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
    if len(payload) >= EXPECTED_PARTITION_SIZE:
        raise ValueError("assembled boot image exceeds the source BOOT partition size")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ensure_avbtool(avbtool_path)
    ensure_signing_key(key_path)
    with tempfile.TemporaryDirectory(
        prefix="devos-boot-", dir=output_path.parent
    ) as temporary_dir:
        temporary_path = Path(temporary_dir)
        image_path = temporary_path / "boot.img"
        image_path.write_bytes(payload)
        salt = hashlib.sha256(
            b"DEVos RMX3231 A.119 boot AVB salt\0" + payload
        ).hexdigest()
        run_avbtool(
            avbtool_path,
            "add_hash_footer",
            "--image",
            str(image_path),
            "--partition_name",
            "boot",
            "--partition_size",
            str(EXPECTED_PARTITION_SIZE),
            "--key",
            str(key_path),
            "--algorithm",
            "SHA256_RSA4096",
            "--hash_algorithm",
            "sha256",
            "--salt",
            salt,
        )
        run_avbtool(
            avbtool_path,
            "verify_image",
            "--image",
            str(image_path),
            "--key",
            str(key_path),
        )
        info_output = run_avbtool(avbtool_path, "info_image", "--image", str(image_path))
        public_key_path = temporary_path / "devos-avb-public-key.bin"
        run_avbtool(
            avbtool_path,
            "extract_public_key",
            "--key",
            str(key_path),
            "--output",
            str(public_key_path),
        )
        public_key = public_key_path.read_bytes()
        public_key_sha1 = hashlib.sha1(public_key).hexdigest()
        if f"Public key (sha1):        {public_key_sha1}" not in info_output:
            raise ValueError("AVB image public key does not match the signing key")
        if image_path.stat().st_size != EXPECTED_PARTITION_SIZE:
            raise ValueError("AOSP avbtool output is not the expected partition size")
        temporary_output = output_path.with_suffix(output_path.suffix + ".part")
        temporary_public_key = output_path.with_suffix(
            output_path.suffix + ".avbpubkey.bin.part"
        )
        try:
            shutil.copyfile(image_path, temporary_output)
            shutil.copyfile(public_key_path, temporary_public_key)
            temporary_output.replace(output_path)
            temporary_public_key.replace(
                output_path.with_suffix(output_path.suffix + ".avbpubkey.bin")
            )
        except Exception:
            temporary_output.unlink(missing_ok=True)
            temporary_public_key.unlink(missing_ok=True)
            raise

    image_bytes = output_path.read_bytes()

    result = {
        "device": "Realme C11 2021 RMX3231",
        "firmware": "RMX3231_11.A.119",
        "image_type": "Android boot header v2, custom-key AVB-signed DEVos candidate",
        "partition_size_bytes": len(image_bytes),
        "output": str(output_path),
        "output_sha256": sha256(image_bytes),
        "source_boot_sha256": sha256(stock),
        "kernel_sha256": sha256(kernel),
        "initramfs_sha256": sha256(ramdisk),
        "dtb_wrapper_sha256": sha256(dtb_wrapper),
        "boot_header_id_sha1": header[576:596].hex(),
        "avb_algorithm": "SHA256_RSA4096",
        "avb_signature_self_verified": True,
        "avb_signing_key_sha1": public_key_sha1,
        "avb_signing_key_matches_realme_chain": (
            public_key_sha1 == EXPECTED_AVB_CHAIN_KEY_SHA1
        ),
        "avb_private_key_path": str(key_path),
        "avb_public_key_path": str(
            output_path.with_suffix(output_path.suffix + ".avbpubkey.bin")
        ),
        "standard_avb_unlocked_state_required": True,
        "device_boot_tested": False,
        "flash_authorized_or_performed": False,
        "warning": (
            "Cryptographically signed and self-verified with a local DEVos "
            "key, but the A.119 root vbmeta chains boot to a different Realme "
            "key. Standard AVB permits verification errors only when the "
            "bootloader is unlocked. RMX3231 bootloader acceptance, live "
            "partition size, and recovery route are unverified. Do not flash "
            "until those are established. Keep the private key secret."
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
        default=Path("builds/devos-rmx3231-a119-boot-custom-avb.img"),
        help="local 64 MiB custom-key AVB-signed boot-image candidate",
    )
    parser.add_argument(
        "--avbtool",
        type=Path,
        default=Path("rootfs/cache/avbtool.py"),
        help="AOSP avbtool.py cache path; downloaded at a pinned commit if absent",
    )
    parser.add_argument(
        "--avb-key",
        type=Path,
        default=Path("builds/keys/devos-avb-rsa4096.pem"),
        help="local RSA-4096 AVB private key; generated if absent, never upload it",
    )
    args = parser.parse_args()
    try:
        result = build(
            args.stock_boot,
            args.initramfs,
            args.output,
            args.avbtool,
            args.avb_key,
        )
    except (OSError, ValueError, struct.error, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
