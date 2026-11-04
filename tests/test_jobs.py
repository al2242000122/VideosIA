"""Pruebas de contrato; no sustituyen un render real con el motor."""

import copy
import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from videosia.job import JobError, build_params, load_job, resolve_asset
from videosia.runner import build_command, child_environment, find_ffmpeg, render, resolve_video, write_config


class JobFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.audio = self.inputs / "narration.wav"
        with wave.open(str(self.audio), "wb") as destination:
            destination.setnchannels(1)
            destination.setsampwidth(2)
            destination.setframerate(8000)
            destination.writeframes(b"\0\0" * 8000)
        # Signature validation is separate from the engine's real image decode.
        (self.inputs / "card.png").write_bytes(b"\x89PNG\r\n\x1a\nunit-test-fixture")
        self.payload = {
            "title": "Prueba local", "script": "Texto de una prueba de contrato.",
            "audio": "narration.wav", "materials": ["card.png"],
            "rights_note": "Archivos de prueba generados en un directorio temporal.",
            "ai_disclosure": {"decision": "needs_review", "reason": "Pendiente de revisión humana."},
        }
        self.path = self.root / "job.json"

    def load(self, payload=None):
        self.path.write_text(json.dumps(self.payload if payload is None else payload), encoding="utf-8")
        return load_job(self.path, self.inputs)


class ValidationTests(JobFixture):
    def test_rejects_video_inputs_and_dash_spoofed_as_png(self):
        for filename in ("clip.mp4", "fake.png", "fake.jpeg"):
            with self.subTest(filename=filename):
                (self.inputs / filename).write_bytes(b'<?xml version="1.0"?><MPD></MPD>')
                payload = copy.deepcopy(self.payload)
                payload["materials"] = [filename]
                with self.assertRaises(JobError):
                    self.load(payload)

    def test_rejects_unpaired_surrogates_in_text_and_paths(self):
        for field in ("title", "script", "rights_note", "audio"):
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload[field] = "\ud800"
                with self.assertRaises(JobError):
                    self.load(payload)
        payload = copy.deepcopy(self.payload)
        payload["ai_disclosure"]["reason"] = "\udfff"
        with self.assertRaises(JobError):
            self.load(payload)

    def test_measures_pcm_duration(self):
        job = self.load()
        self.assertEqual(job["audio_duration_seconds"], 1)
        self.assertEqual(job["audio"], self.audio.resolve())

    def test_rejects_provider_or_command_fields(self):
        for field in ("video_source", "command", "output", "api_key", "AUTO_PUBLISH"):
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload[field] = "https://example.com"
                with self.assertRaises(JobError):
                    self.load(payload)

    def test_rejects_remote_absolute_traversal_and_windows_paths(self):
        for value in ("../secret.png", "/tmp/secret.png", "https://example.com/a.png",
                      "C:/secret.png", "C:secret.png", "\\\\server\\share\\secret.png", "folder\\card.png", "bad\x00.png"):
            with self.subTest(value=value), self.assertRaises(JobError):
                resolve_asset(value, self.inputs, {".png"})

    def test_rejects_symlink_escape(self):
        outside = self.root / "private.png"
        outside.write_bytes(b"private")
        link = self.inputs / "link.png"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("El sistema no permite crear symlinks sin privilegios")
        with self.assertRaises(JobError):
            resolve_asset("link.png", self.inputs, {".png"})

    def test_rejects_missing_empty_or_wrong_type_disclosure(self):
        for value in ({}, {"decision": [], "reason": "test"},
                      {"decision": "not_required", "reason": " "},
                      {"decision": "required", "reason": "test", "approved": True}):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["ai_disclosure"] = value
                with self.assertRaises(JobError):
                    self.load(payload)

    def test_rejects_invalid_wave_and_overlong_audio(self):
        self.audio.write_bytes(b"not a wav")
        with self.assertRaises(JobError):
            self.load()
        with wave.open(str(self.audio), "wb") as destination:
            destination.setnchannels(1)
            destination.setsampwidth(2)
            destination.setframerate(1)
            destination.writeframes(b"\0\0" * 301)
        with self.assertRaises(JobError):
            self.load()

    def test_requires_one_to_twenty_materials(self):
        for value in ([], ["card.png"] * 21, "card.png", None):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.payload)
                payload["materials"] = value
                with self.assertRaises(JobError):
                    self.load(payload)

    def test_rejects_oversized_json(self):
        self.path.write_text(" " * (64 * 1024 + 1), encoding="utf-8")
        with self.assertRaises(JobError):
            load_job(self.path, self.inputs)


class PrivacyTests(JobFixture):
    def test_ffmpeg_wheel_fallback_is_fixed_and_does_not_execute_python(self):
        binaries = self.root / ".venv" / "Lib" / "site-packages" / "imageio_ffmpeg" / "binaries"
        binaries.mkdir(parents=True)
        executable = binaries / "ffmpeg-win64-v1.exe"
        executable.write_bytes(b"fixture")
        with patch("videosia.runner.shutil.which", return_value=None):
            self.assertEqual(find_ffmpeg({}, self.root), str(executable.resolve()))

    def test_invalid_explicit_ffmpeg_path_is_not_silently_replaced(self):
        self.assertIsNone(find_ffmpeg({"IMAGEIO_FFMPEG_EXE": str(self.root / "missing.exe")}))

    def test_only_approved_local_pipeline_parameters(self):
        params = build_params(self.load(), self.inputs)
        self.assertEqual(params["video_source"], "local")
        self.assertEqual(params["custom_audio_file"], str(self.audio.resolve()))
        self.assertEqual(params["video_count"], 1)
        self.assertFalse(params["subtitle_enabled"])
        self.assertEqual(params["bgm_type"], "")
        self.assertEqual(params["voice_name"], "no-voice")
        self.assertEqual(params["video_script"], self.payload["script"])
        self.assertTrue(all(item["provider"] == "local" for item in params["video_materials"]))

    def test_child_never_inherits_provider_credentials_or_proxy(self):
        env = child_environment(self.root, {
            "PATH": "/tools", "SYSTEMROOT": "C:/Windows", "HOME": "/secret-home",
            "OPENAI_API_KEY": "secret", "AZURE_KEY": "secret", "HTTP_PROXY": "http://proxy",
            "PYTHONPATH": "/untrusted", "GITHUB_TOKEN": "secret",
        })
        for name in ("OPENAI_API_KEY", "AZURE_KEY", "HTTP_PROXY", "PYTHONPATH", "GITHUB_TOKEN"):
            self.assertNotIn(name, env)
        self.assertEqual(env["HOME"], str(self.root))
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(env["HF_HUB_DISABLE_TELEMETRY"], "1")
        self.assertEqual(env["DO_NOT_TRACK"], "1")
        self.assertEqual(env["LITELLM_LOCAL_MODEL_COST_MAP"], "True")
        self.assertEqual(env["AUTO_PUBLISH"], "false")

    def test_private_configuration_has_no_external_service_or_publication(self):
        write_config(self.root)
        import tomllib
        config = tomllib.loads((self.root / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["listen_host"], "127.0.0.1")
        self.assertGreaterEqual(len(config["app"]["api_key"]), 32)
        self.assertFalse(config["app"]["upload_post_enabled"])
        self.assertFalse(config["app"]["upload_post_auto_upload"])
        self.assertFalse(config["diagnostics"]["log_requests"])
        self.assertEqual(config["app"]["llm_provider"], "")

    def test_container_has_no_network_no_home_mount_and_no_published_ports(self):
        command = build_command(self.root, self.path, self.inputs, container=True, image_id="sha256:" + "a" * 64)
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--read-only", command)
        self.assertNotIn("-p", command)
        self.assertNotIn("--publish", command)
        mounts = [command[i + 1] for i, value in enumerate(command) if value == "--mount"]
        self.assertEqual(len(mounts), 2)
        self.assertTrue(any("target=/inputs,readonly" in value for value in mounts))
        self.assertIn("LITELLM_LOCAL_MODEL_COST_MAP=True", command)
        self.assertIn("HF_HUB_DISABLE_TELEMETRY=1", command)
        self.assertIn("DO_NOT_TRACK=1", command)
        self.assertIn("/opt/videosia-engine-entry.py", command)


class ResultsTests(JobFixture):
    def result(self, video):
        return {"failed": 0, "succeeded": 1, "total": 1, "tasks": [
            {"status": "succeeded", "result": {"videos": [str(video)]}}
        ]}

    def test_rejects_output_outside_runtime_and_missing_file(self):
        runtime = self.root / "runtime"
        runtime.mkdir()
        outside = self.root / "secret.mp4"
        outside.write_bytes(b"untrusted")
        with self.assertRaises(JobError):
            resolve_video(self.result(outside), runtime)
        with self.assertRaises(JobError):
            resolve_video(self.result(runtime / "missing.mp4"), runtime)

    def test_accepts_only_actual_owned_mp4(self):
        video = self.root / "render.mp4"
        video.write_bytes(b"test-result-not-real-mp4")
        self.assertEqual(resolve_video(self.result(video), self.root), video.resolve())

    def test_failed_run_has_manifest_and_never_authorizes_publication(self):
        self.load()
        with patch("videosia.runner.build_command", side_effect=JobError("motor no instalado")):
            path, manifest = render(self.path, root=self.root)
        self.assertTrue(path.is_file())
        self.assertEqual(manifest["status"], "failed")
        self.assertFalse(manifest["qa"]["passed"])
        self.assertFalse(manifest["publication_allowed"])
        self.assertFalse(manifest["AUTO_PUBLISH"])
        self.assertIsNone(manifest["human_approval"])

    def test_mock_success_keeps_editorial_and_publication_pending(self):
        self.load()

        def fake_run(command, runtime, stem, **kwargs):
            video = runtime / "video.mp4"
            video.write_bytes(b"unit-test-fixture")
            return json.dumps(self.result(video))

        with patch("videosia.runner.build_command", return_value=["mock-engine"]), \
             patch("videosia.runner.find_ffmpeg", return_value="fixture-ffmpeg"), \
             patch("videosia.runner.run_logged", side_effect=fake_run), \
             patch("videosia.runner.verify_media", return_value={"decoded_video_and_audio": True}):
            path, manifest = render(self.path, root=self.root)
        self.assertEqual(manifest["status"], "succeeded")
        self.assertFalse(manifest["publication_allowed"])
        self.assertEqual(manifest["editorial_review"], "pending")
        self.assertFalse(manifest["rights"]["reviewed"])
        self.assertEqual(manifest["execution"]["network_isolation"], "not_enforced")
        self.assertFalse(manifest["subtitles"]["present"])


if __name__ == "__main__":
    unittest.main()
