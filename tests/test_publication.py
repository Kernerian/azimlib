"""Publication invariants: palette origins, third-party notices and redaction."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import azimlib as azl
from azimlib.cycles import AZIM10, TAB10

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from publication_privacy import public_path, sanitize_text, findings


class PublicationTests(unittest.TestCase):
    def test_default_and_dark_cycles_have_documented_azimlib_origin(self):
        manifest = json.loads((Path(azl.__file__).parent / 'data/materials.json').read_text('utf-8'))
        self.assertEqual(tuple(manifest['azim10']['colors']), AZIM10)
        self.assertEqual(TAB10, AZIM10)
        with azl.rc_context():
            azl.rcdefaults()
            self.assertEqual(tuple(r['color'] for r in azl.rcParams['axes.prop_cycle']), AZIM10)
            fig, ax = azl.subplots()
            lines = [ax.plot([0, 1], [i, i + 1])[0] for i in range(11)]
            self.assertEqual(tuple(line.get_color() for line in lines[:10]), AZIM10)
            self.assertEqual(lines[10].get_color(), AZIM10[0])
            azl.close(fig)
        retired = set(manifest['retired_palette_fingerprints'])
        for values in [AZIM10, tuple(r['color'] for r in azl.style.library['dark_background']['axes.prop_cycle'])]:
            self.assertNotIn(hashlib.sha256(','.join(values).encode()).hexdigest(), retired)

    def test_colorbrewer_credit_and_complete_terms_are_preserved(self):
        self.assertIn('Cynthia', (ROOT / 'THIRD_PARTY_LICENSES.md').read_text('utf-8'))
        license_text = (ROOT / 'licenses/LicenseRef-ColorBrewer.txt').read_text('utf-8')
        self.assertIn('Pennsylvania State', license_text)
        self.assertIn('end-user documentation', license_text)
        self.assertIn('Apache License', (ROOT / 'licenses/Apache-2.0.txt').read_text('utf-8'))
        self.assertIn('Bitstream', (ROOT / 'src/azimlib/fonts/LICENSE_DEJAVU').read_text('utf-8'))

    def test_home_paths_are_redacted_on_windows_linux_and_macos(self):
        samples = ['C:' + '/Us' + 'ers/example/venv/Lib/site-packages/azimlib',
                   '/ho' + 'me/example/venv/lib/site-packages/azimlib',
                   '/Us' + 'ers/example/checkout/src/azimlib/__init__.py']
        for value in samples:
            with self.subTest(platform=value.split('/')[0]):
                self.assertTrue(findings(value.encode()))
                cleaned = sanitize_text(value)
                self.assertFalse(findings(cleaned.encode()))
                self.assertNotIn('/example/', cleaned)
                self.assertIn('azimlib', cleaned)
        self.assertIn('site-packages', public_path(samples[0]))

    def test_json_escaping_cannot_hide_personal_paths(self):
        value = ('C:' + '/Us' + 'ers/example/venv/Lib/site-packages/azimlib').replace('/', '\\')
        self.assertIn('personal-home-path', findings(json.dumps({'origin': value}).encode()))

    def test_technical_text_and_copyright_are_not_private_context(self):
        value = 'Copyright 2002 Cynthia Brewer. User-supplied GeoJSON. Pan changes axis limits.'
        self.assertEqual(sanitize_text(value), value)
        self.assertEqual(findings(value.encode()), [])

    def test_credential_patterns_and_conversation_quotes_are_detected(self):
        key = 'gh' + 'p_' + 'A' * 36
        quote = 'O ' + 'usuário ' + 'respondeu: conteúdo sintético'
        self.assertIn('credential-pattern', findings(key.encode()))
        self.assertIn('conversation-context', findings(quote.encode()))

    def test_offline_material_audit_verifies_assets_and_licenses(self):
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/audit_licenses.py')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])


if __name__ == '__main__':
    unittest.main()
