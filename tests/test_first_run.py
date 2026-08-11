import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "tw-social-short-video-editor" / "scripts"


class FirstRunTests(unittest.TestCase):
    def environment(self, home):
        environment = os.environ.copy()
        environment["TW_SHORT_VIDEO_HOME"] = str(home)
        return environment

    def test_profile_init_is_external_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "external-state"
            environment = self.environment(home)
            command = [sys.executable, str(SCRIPTS / "manage_creator_profile.py"), "init"]
            first = subprocess.run(command, check=True, capture_output=True, text=True, env=environment)
            payload = json.loads(first.stdout)
            profile = Path(payload["path"])
            self.assertTrue(profile.is_file())
            self.assertTrue(str(profile).startswith(str(home)))
            profile.write_text("我的自訂設定", encoding="utf-8")
            subprocess.run(command, check=True, capture_output=True, text=True, env=environment)
            self.assertEqual(profile.read_text(encoding="utf-8"), "我的自訂設定")

    def test_profile_export(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            environment = self.environment(temp / "state")
            subprocess.run(
                [sys.executable, str(SCRIPTS / "manage_creator_profile.py"), "init"],
                check=True, capture_output=True, text=True, env=environment,
            )
            destination = temp / "shared-profile.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "manage_creator_profile.py"), "export", str(destination)],
                check=True, capture_output=True, text=True, env=environment,
            )
            self.assertEqual(json.loads(result.stdout)["exported"], str(destination.resolve()))
            self.assertTrue(destination.is_file())

    def test_runtime_check_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "state"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "setup_runtime.py"), "--check"],
                check=True, capture_output=True, text=True, env=self.environment(home),
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["data_home"], str(home.resolve()))
            self.assertFalse(home.exists())

    def test_install_requires_single_confirmation_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "state"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "setup_runtime.py"), "--install"],
                capture_output=True, text=True, env=self.environment(home),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--confirm-local-downloads", result.stderr)
            self.assertFalse(home.exists())

    def test_install_dry_run_does_not_download(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "state"
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / "setup_runtime.py"), "--install",
                    "--confirm-local-downloads", "--dry-run",
                ],
                check=True, capture_output=True, text=True, env=self.environment(home),
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["will_download_model"], "small")
            self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
