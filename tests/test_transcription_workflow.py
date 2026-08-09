import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "tw-social-short-video-editor" / "scripts"


class TranscriptionWorkflowTests(unittest.TestCase):
    def test_hash_cache_reuses_transcript_without_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            media = temp / "talking-head.mov"
            media.write_bytes(b"not-real-media-but-cache-is-valid")
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            cache = temp / "cache"
            cache.mkdir()
            payload = {
                "schema_version": 1,
                "source": {"name": media.name, "sha256": digest, "duration_s": 3.0},
                "provider": "faster-whisper",
                "model": "small",
                "segments": [{"start": 0.0, "end": 3.0, "text": "測試逐字稿"}],
                "words": [],
                "text": "測試逐字稿",
            }
            (cache / f"{digest}.faster-whisper.small.json").write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "transcribe_video.py"), str(media), "--cache-dir", str(cache)],
                check=True,
                capture_output=True,
                text=True,
            )
            status = json.loads(result.stdout)
            self.assertTrue(status["cache_hit"])
            self.assertEqual(status["provider"], "faster-whisper")

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is required")
    def test_cloud_provider_requires_file_specific_consent(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "speech.wav"
            with wave.open(str(audio), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                handle.writeframes(b"\x00\x00" * 1600)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "transcribe_video.py"), str(audio), "--provider", "openai"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 3)
            self.assertIn("--cloud-consent", result.stderr)

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is required")
    def test_local_provider_serializes_timed_words(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            package = temp / "faster_whisper"
            package.mkdir()
            package.joinpath("__init__.py").write_text(
                """
class Word:
    def __init__(self, start, end, word):
        self.start, self.end, self.word = start, end, word

class Segment:
    start, end, text = 0.0, 1.0, "測試成功"
    words = [Word(0.0, 0.5, "測試"), Word(0.5, 1.0, "成功")]

class Info:
    language, language_probability = "zh", 0.99

class WhisperModel:
    def __init__(self, *args, **kwargs):
        assert kwargs["local_files_only"] is True
    def transcribe(self, *args, **kwargs):
        return iter([Segment()]), Info()
""".strip(),
                encoding="utf-8",
            )
            audio = temp / "speech.wav"
            with wave.open(str(audio), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                handle.writeframes(b"\x00\x00" * 16000)
            output = temp / "transcript.json"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(temp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "transcribe_video.py"),
                    str(audio),
                    "--provider",
                    "local",
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "faster-whisper")
            self.assertEqual([item["text"] for item in payload["words"]], ["測試", "成功"])
            self.assertNotIn(str(temp), json.dumps(payload, ensure_ascii=False))

    def test_analyzer_finds_hook_and_drops_repeat(self):
        transcript = {
            "schema_version": 1,
            "source": {"name": "sample.mov", "sha256": "abc", "duration_s": 30.0},
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "今天要教大家安裝一個剪輯工具。"},
                {"start": 3.0, "end": 6.0, "text": "第一步先打開 GitHub。"},
                {"start": 6.0, "end": 9.0, "text": "第一步就是先打開 GitHub。"},
                {"start": 9.0, "end": 13.0, "text": "每次剪片都要重新教 AI 嗎？"},
                {"start": 13.0, "end": 17.0, "text": "其實設定一次之後就不用再重複。"},
                {"start": 17.0, "end": 21.0, "text": "接著複製網址並貼到工作區。"},
                {"start": 21.0, "end": 25.0, "text": "想拿到這套工具就留言剪片。"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source = temp / "transcript.json"
            output = temp / "story-plan.json"
            source.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "analyze_transcript.py"),
                    str(source),
                    "--output",
                    str(output),
                    "--target-seconds",
                    "20",
                    "--keyword",
                    "AI",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            plan = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(plan["hook"]["text"], "每次剪片都要重新教 AI 嗎？")
            repeated = [item for item in plan["segments"] if "repeated_idea" in item["flags"]]
            self.assertEqual(len(repeated), 1)
            self.assertEqual(repeated[0]["decision"], "drop")
            self.assertEqual(plan["edit_order"][0]["id"], plan["hook"]["id"])


if __name__ == "__main__":
    unittest.main()
