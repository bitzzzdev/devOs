import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_flashable_package import build_package, file_sha256


class TestFlashablePackage(unittest.TestCase):
    def test_build_package_iso_and_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dummy_boot = temp_path / "boot.img"
            dummy_boot.write_bytes(b"\x00" * 1024 * 64)

            iso_path = temp_path / "installer.iso"
            zip_path = temp_path / "installer.zip"

            summary = build_package(dummy_boot, iso_path, zip_path)

            self.assertTrue(iso_path.exists())
            self.assertTrue(zip_path.exists())
            self.assertEqual(summary["iso_package"], str(iso_path))
            self.assertEqual(summary["zip_package"], str(zip_path))

            # Inspect ZIP contents
            with zipfile.ZipFile(zip_path, "r") as archive:
                names = set(archive.namelist())
                expected = {
                    "boot.img",
                    "flash.sh",
                    "flash.bat",
                    "README.txt",
                    "manifest.json",
                    "checksums.sha256",
                }
                self.assertTrue(expected.issubset(names))

                manifest_data = json.loads(archive.read("manifest.json").decode("utf-8"))
                self.assertEqual(manifest_data["target_device"], "Realme C11 2021 (RMX3231)")
                self.assertIn("4", manifest_data["boot_modes"])


if __name__ == "__main__":
    unittest.main()
