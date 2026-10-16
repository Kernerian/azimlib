"""Release-publication legal integrity and whitespace contracts."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_verbatim_legal040 import SOURCE_SHA, PUBLICATION_COPIES, blob, check


class VerbatimLegalGate(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.source = Path(os.environ.get('AZIMLIB_AUDITED_SOURCE_REPOSITORY', ROOT))
        subprocess.run(['git', 'init', '--quiet', str(self.repo)], check=True)
        subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=self.repo, check=True)
        (self.repo / '.gitattributes').write_bytes(b'''# Preserve the reviewed publication payload bytes on every platform.
* -text
# CR is part of a CRLF line ending; retain the default text whitespace checks.
* whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol
# Binary exports have format-defined offsets, streams and embedded legal notices.
*.pdf binary
*.png binary
*.gif binary
*.ico binary
*.jpg binary
*.jpeg binary
*.woff binary
*.woff2 binary
*.ttf binary
*.otf binary
''')
        for relative, source in PUBLICATION_COPIES.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob(self.source, SOURCE_SHA + ':' + source))
        self.stage()

    def stage(self):
        subprocess.run(['git', 'add', '--all'], cwd=self.repo, check=True, capture_output=True)

    def test_invalid_normal_file_whitespace_is_blocked(self):
        (self.repo / 'normal.py').write_bytes(b'value = 1  \n')
        self.stage()
        with self.assertRaisesRegex(AssertionError, 'whitespace'):
            check(self.repo, self.source)

    def test_original_approved_legal_whitespace_is_accepted(self):
        raw = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=self.repo, capture_output=True)
        self.assertNotEqual(raw.returncode, 0)
        proof = check(self.repo, self.source)
        self.assertTrue(proof['passed'])
        self.assertEqual(len(proof['legal_exceptions']), 6)

    def test_changed_license_hash_is_blocked(self):
        path = self.repo / 'stable/licenses/LPPL-1.3c.txt'
        path.write_bytes(path.read_bytes().rstrip() + b'\n')
        self.stage()
        with self.assertRaisesRegex(AssertionError, 'new audit required'):
            check(self.repo, self.source)

    def test_uncatalogued_license_cannot_use_exception(self):
        path = self.repo / 'stable/licenses/Unregistered.txt'
        path.write_bytes(b'Unregistered legal payload  \n')
        self.stage()
        with self.assertRaisesRegex(AssertionError, 'whitespace'):
            check(self.repo, self.source)

    def test_missing_approved_copy_is_blocked(self):
        (self.repo / 'dev/licenses/AMSFonts.txt').unlink()
        self.stage()
        with self.assertRaisesRegex(AssertionError, 'missing'):
            check(self.repo, self.source)

    def test_unstaged_legal_change_is_blocked(self):
        path = self.repo / '0.4.0/licenses/AMSFonts.txt'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(AssertionError, 'new audit required'):
            check(self.repo, self.source)

    def test_new_attribute_bypass_is_blocked(self):
        path = self.repo / 'stable/licenses/.gitattributes'
        path.write_bytes(b'* -whitespace\n')
        self.stage()
        with self.assertRaisesRegex(AssertionError, 'nested attributes'):
            check(self.repo, self.source)


if __name__ == '__main__':
    unittest.main()
