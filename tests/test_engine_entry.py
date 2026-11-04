"""Pruebas reales del bootstrap en procesos separados, sin motor ni red externa."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENTRY = Path(__file__).resolve().parent.parent / "videosia" / "engine_entry.py"


class EngineEntryTests(unittest.TestCase):
    def execute(self, source):
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "fixture.py"
            script.write_text(source, encoding="utf-8")
            return subprocess.run([sys.executable, "-I", str(ENTRY), str(script)],
                                  capture_output=True, text=True, encoding="utf-8", timeout=10,
                                  cwd=temporary, check=False)

    def test_connect_is_blocked_before_any_connection(self):
        result = self.execute(
            "import socket\n"
            "with socket.socket() as connection:\n"
            "    try:\n"
            "        connection.connect(('127.0.0.1', 9))\n"
            "    except PermissionError as error:\n"
            "        assert '127.0.0.1' not in str(error)\n"
            "        print('connection-blocked')\n"
            "    else:\n"
            "        raise AssertionError('audit guard did not reject connect')\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "connection-blocked")

    def test_dns_and_bind_are_blocked(self):
        result = self.execute(
            "import socket\n"
            "blocked = 0\n"
            "for operation in [lambda: socket.getaddrinfo('127.0.0.1', 9),\n"
            "                  lambda: socket.gethostbyname('127.0.0.1'),\n"
            "                  lambda: socket.socket().bind(('127.0.0.1', 0))]:\n"
            "    try:\n"
            "        operation()\n"
            "    except PermissionError:\n"
            "        blocked += 1\n"
            "assert blocked == 3\n"
            "print('network-blocked')\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "network-blocked")

    def test_file_only_script_and_arguments_continue_to_work(self):
        result = self.execute(
            "from pathlib import Path\n"
            "import sys\n"
            "Path('proof.txt').write_text('local-only', encoding='utf-8')\n"
            "assert Path('proof.txt').read_text(encoding='utf-8') == 'local-only'\n"
            "assert sys.argv[0].endswith('fixture.py')\n"
            "print('file-ok')\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "file-ok")


if __name__ == "__main__":
    unittest.main()
