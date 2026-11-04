"""Regresiones de red nativa, privacidad del directorio e identidad del contenedor."""

import http.server
import json
import os
import stat
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from test_jobs import JobFixture
from videosia.job import JobError
from videosia.runner import child_environment, find_ffmpeg, inspect_container_image, render, verify_media


class NativeMediaPrivacyTests(unittest.TestCase):
    def test_dash_named_mp4_cannot_make_native_ffmpeg_http_request(self):
        """Real wheel FFmpeg rejects XML before a loopback HTTP receiver is contacted."""
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.skipTest("Requiere FFmpeg del host o el wheel ya instalado; no descarga herramientas")
        requests = []

        class Receiver(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Receiver)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                runtime = Path(temporary)
                malicious = runtime / "fake.mp4"
                malicious.write_text(
                    '<?xml version="1.0"?><MPD xmlns="urn:mpeg:dash:schema:mpd:2011" '
                    'type="static" mediaPresentationDuration="PT1S" minBufferTime="PT1S">'
                    '<Period><AdaptationSet mimeType="video/mp4"><Representation id="0" bandwidth="1">'
                    f'<BaseURL>http://127.0.0.1:{server.server_port}/must-not-be-requested.mp4</BaseURL>'
                    '</Representation></AdaptationSet></Period></MPD>', encoding="utf-8",
                )
                env = child_environment(runtime)
                env["IMAGEIO_FFMPEG_EXE"] = ffmpeg
                with self.assertRaises(JobError):
                    verify_media(malicious, runtime, env)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(requests, [])

    def test_both_host_media_tools_force_mov_and_local_protocols(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            probe = json.dumps({"streams": [{"codec_type": "video", "width": 1080, "height": 1920}],
                                "format": {"duration": "1"}})
            with patch("videosia.runner.find_ffmpeg", return_value="ffmpeg"), \
                 patch("videosia.runner.shutil.which", return_value="ffprobe"), \
                 patch("videosia.runner.run_logged", side_effect=["", probe]) as run:
                verify_media(runtime / "video.mp4", runtime, {})
            self.assertEqual(run.call_count, 2)
            for call in run.call_args_list:
                command = call.args[0]
                input_index = command.index("-i")
                self.assertLess(command.index("-protocol_whitelist"), input_index)
                self.assertEqual(command[command.index("-protocol_whitelist") + 1], "file,pipe")
                self.assertLess(command.index("-f"), input_index)
                self.assertEqual(command[command.index("-f") + 1], "mov")


class ExecutionPreflightTests(JobFixture):
    IMAGE_ID = "sha256:" + "b" * 64

    def test_missing_host_ffmpeg_prevents_engine_and_image_inspection(self):
        self.load()
        with patch("videosia.runner.find_ffmpeg", return_value=None), \
             patch("videosia.runner.build_command") as build, \
             patch("videosia.runner.run_logged") as run:
            path, manifest = render(self.path, root=self.root, container=True)
        self.assertTrue(path.is_file())
        self.assertEqual(manifest["status"], "failed")
        self.assertIn("FFmpeg en el host", manifest["error"])
        self.assertFalse(manifest["qa"]["passed"])
        build.assert_not_called()
        run.assert_not_called()

    @unittest.skipIf(os.name == "nt", "En Windows los permisos dependen de ACL, no de modo POSIX")
    def test_job_and_runtime_are_private_even_with_permissive_umask(self):
        self.load()
        previous_mask = os.umask(0)
        try:
            with patch("videosia.runner.find_ffmpeg", return_value=None):
                path, _manifest = render(self.path, root=self.root)
        finally:
            os.umask(previous_mask)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((path.parent / "runtime").stat().st_mode), 0o700)

    def test_image_inspection_failure_prevents_engine_run(self):
        self.load()
        with patch("videosia.runner.find_ffmpeg", return_value="fixture-ffmpeg"), \
             patch("videosia.runner.build_command") as build, \
             patch("videosia.runner.run_logged", side_effect=JobError("imagen no disponible")) as run:
            _path, manifest = render(self.path, root=self.root, container=True)
        self.assertEqual(manifest["status"], "failed")
        self.assertIsNone(manifest["engine"]["commit"])
        self.assertIsNone(manifest["engine"]["image_id"])
        run.assert_called_once()
        self.assertEqual(run.call_args.args[2], "image-inspect")
        build.assert_not_called()

    def test_invalid_image_identity_is_rejected(self):
        for value in ("videosia-mpt:local", "sha256:123", {"Id": self.IMAGE_ID}, None):
            with self.subTest(value=value), \
                 patch("videosia.runner.run_logged", return_value=json.dumps(value)), \
                 self.assertRaises(JobError):
                inspect_container_image(self.root, {})

    def test_container_runs_immutable_id_and_does_not_claim_checkout_as_source(self):
        self.load()
        calls = []

        def fake_run(command, runtime, stem, **_kwargs):
            calls.append((stem, command))
            if stem == "image-inspect":
                # The mutable tag could be moved now; docker run receives this exact identity.
                return json.dumps(self.IMAGE_ID)
            self.assertEqual(stem, "engine")
            video = runtime / "video.mp4"
            video.write_bytes(b"unit-test-fixture")
            return json.dumps({"failed": 0, "succeeded": 1, "total": 1, "tasks": [
                {"status": "succeeded", "result": {"videos": ["/runtime/video.mp4"]}}
            ]})

        with patch("videosia.runner.find_ffmpeg", return_value="fixture-ffmpeg"), \
             patch("videosia.runner.engine_commit", return_value="c" * 40), \
             patch("videosia.runner.engine_dirty", return_value=False), \
             patch("videosia.runner.run_logged", side_effect=fake_run), \
             patch("videosia.runner.verify_media", return_value={"decoded_video_and_audio": True}):
            _path, manifest = render(self.path, root=self.root, container=True)
        self.assertEqual(manifest["status"], "succeeded")
        self.assertEqual(calls[0][0], "image-inspect")
        self.assertIn("videosia-mpt:local", calls[0][1])
        self.assertIn(self.IMAGE_ID, calls[1][1])
        self.assertNotIn("videosia-mpt:local", calls[1][1])
        self.assertEqual(manifest["engine"]["image_id"], self.IMAGE_ID)
        self.assertEqual(manifest["engine"]["checkout_commit"], "c" * 40)
        self.assertIsNone(manifest["engine"]["commit"])
        self.assertIsNone(manifest["engine"]["source_revision"])
        self.assertFalse(manifest["publication_allowed"])


if __name__ == "__main__":
    unittest.main()
