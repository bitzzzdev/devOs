import gzip
import tempfile
import unittest
from pathlib import Path

from scripts.build_boot_image import cpio_names
from scripts.build_initramfs import build_archive, package_busybox, PACKAGE_NAME


class TestInitramfs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package_path = Path("rootfs/cache") / PACKAGE_NAME
        cls.assertTrue(
            cls.package_path.exists(),
            f"Cached BusyBox package must exist at {cls.package_path}",
        )
        cls.busybox = package_busybox(cls.package_path)

    def test_build_archive_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "test-initramfs.cpio.gz"
            init_bytes = Path("rootfs/init").read_bytes()
            build_archive(
                self.busybox,
                init_bytes,
                output,
                rootfs_dir=Path("rootfs"),
                stock_ramdisk=b"test-stock-ramdisk-bytes",
            )
            self.assertTrue(output.exists())
            decompressed = gzip.decompress(output.read_bytes())
            names = cpio_names(decompressed)

            expected_entries = {
                "init",
                "bin/busybox",
                "etc/devos.conf",
                "sbin/devos-mode-vps",
                "sbin/devos-mode-router",
                "sbin/devos-mode-dual",
                "sbin/devos-mode-android",
                "stock_ramdisk.cpio.gz",
                "dev/console",
                "dev/null",
            }
            for entry in expected_entries:
                self.assertIn(entry, names, f"Expected entry missing: {entry}")


if __name__ == "__main__":
    unittest.main()
