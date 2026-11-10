import subprocess
import unittest
from pathlib import Path


class TestScriptSyntax(unittest.TestCase):
    def test_rootfs_shell_scripts_syntax(self):
        rootfs_dir = Path("rootfs")
        scripts = [
            rootfs_dir / "init",
            rootfs_dir / "sbin/devos-mode-vps",
            rootfs_dir / "sbin/devos-mode-router",
            rootfs_dir / "sbin/devos-mode-dual",
            rootfs_dir / "sbin/devos-mode-android",
        ]
        for script in scripts:
            with self.subTest(script=script.name):
                self.assertTrue(script.exists(), f"Script missing: {script}")
                result = subprocess.run(
                    ["sh", "-n", str(script)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"Syntax error in {script}: {result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()
