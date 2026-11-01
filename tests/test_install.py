import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readability_install', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
BUN = shutil.which('bun') or str(Path.home() / '.bun/bin' / ('bun.exe' if os.name == 'nt' else 'bun'))


def fixture(path, title=True):
    # Synthetic parser fixture only, not a circuit or authoring example.
    path.parent.mkdir(parents=True, exist_ok=True)
    block = '(title_block (title "Fixture") (date "2026-11-01") (rev "A"))' if title else ''
    path.write_text('(kicad_sch (version 20250114) (generator "test-fixture") (uuid "00000000-0000-4000-8000-000000000001") (paper "A4") ' + block + ')')


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='readability tests ')
        self.root = Path(self.tmp.name)
        self.home = self.root / 'user home'
        self.home.mkdir()
        self.env = dict(os.environ, PATH=str(Path(BUN).parent) + os.pathsep + os.environ.get('PATH', ''))

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, *args, code=0):
        r = subprocess.run([sys.executable, str(ROOT / 'install.py'), '--home', str(self.home), *map(str, args)], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stderr)
        return json.loads(r.stdout) if code == 0 else r

    def check(self, *args):
        return subprocess.run([sys.executable, str(self.home / '.local/share/backplane-schematic-readability/run.py'), *map(str, args)], env=self.env, capture_output=True, text=True)

    def test_fresh_install_and_project_registration(self):
        project = self.root / 'project'; project.mkdir()
        result = self.install('--project', project)
        for p in result['skills']:
            self.assertTrue(Path(p).is_file())
        for p in result['instructions']:
            self.assertEqual(Path(p).read_text().count(installer.BEGIN), 1)
        self.assertTrue(Path(result['shortcut']).is_file())
        skill = Path(result['skills'][0]).read_text()
        self.assertIn(str(self.home / '.local/share/backplane-schematic-readability/run.py'), skill)
        self.assertNotIn('{{SKILL_PATH}}', (project / 'AGENTS.md').read_text())

    def test_update_preserves_user_text_and_backups(self):
        p = self.home / '.codex/AGENTS.md';p.parent.mkdir(parents=True)
        p.write_text('Existing user instructions.\n')
        self.install()
        p.write_text(p.read_text() + '\nUser additions after install.\n')
        before = p.read_text()
        result = self.install()
        text = p.read_text()
        self.assertIn('Existing user instructions.', text)
        self.assertIn('User additions after install.', text)
        self.assertEqual(text.count(installer.BEGIN), 1)
        self.assertEqual(text, before)
        self.assertTrue(any(f.read_text() == before for f in Path(result['backup']).rglob('AGENTS.md')))

    def test_conflicting_skill_refused_before_global_writes(self):
        p=self.home / '.claude/skills/schematic-readability';p.mkdir(parents=True)
        (p/'SKILL.md').write_text('Unrelated local skill')
        self.install(code=2)
        self.assertEqual((p/'SKILL.md').read_text(),'Unrelated local skill')
        self.assertFalse((self.home/'.codex/AGENTS.md').exists())
        self.assertFalse((self.home/'.local/share/backplane-schematic-readability').exists())

    def test_malformed_instruction_block_refused_before_writes(self):
        p=self.home/'.codex/AGENTS.md';p.parent.mkdir(parents=True);p.write_text(installer.BEGIN)
        self.install(code=2)
        self.assertEqual(p.read_text(),installer.BEGIN)
        self.assertFalse((self.home/'.local/share/backplane-schematic-readability').exists())

    def test_nested_resolution_and_read_only_exit_modes(self):
        self.install()
        project=self.root/'project';project.mkdir()
        sch=project/'boards/device/device.kicad_sch';fixture(sch,title=False)
        (project/'.backplane.json').write_text(json.dumps({'project':'boards/device/device.kicad_pro'}))
        original=sch.read_bytes()
        d=self.check('--project',project,'--describe');self.assertEqual(d.returncode,0,d.stderr)
        self.assertEqual(Path(json.loads(d.stdout)['schematic']),sch.resolve())
        strict=self.check('--project',project);self.assertEqual(strict.returncode,1,strict.stderr)
        self.assertGreater(json.loads(strict.stdout)['error_count'],0)
        out=project/'build/schematic-readability'
        self.assertTrue(json.loads((out/'verification.json').read_text())['cad_unchanged'])
        diagnostic=self.check('--project',project,'--report-only');self.assertEqual(diagnostic.returncode,0,diagnostic.stderr)
        self.assertEqual(sch.read_bytes(),original)

    def test_clear_automated_findings_returns_zero(self):
        self.install();project=self.root/'project';project.mkdir();fixture(project/'clean.kicad_sch')
        r=self.check('--project',project);self.assertEqual(r.returncode,0,r.stderr)
        j=json.loads(r.stdout);self.assertEqual(j['error_count'],0)
        self.assertTrue(j['manual_visual_review_required'])

    def test_empty_and_ambiguous_project_refused(self):
        self.install();project=self.root/'project';project.mkdir()
        self.assertEqual(self.check('--project',project).returncode,2)
        fixture(project/'one.kicad_sch');fixture(project/'two.kicad_sch')
        self.assertEqual(self.check('--project',project).returncode,2)
        self.assertFalse((project/'build').exists())

    def test_missing_configured_schematic_has_no_fallback(self):
        self.install();project=self.root/'project';project.mkdir();fixture(project/'other.kicad_sch')
        (project/'.backplane.json').write_text('{"schematic":"missing.kicad_sch"}')
        self.assertEqual(self.check('--project',project).returncode,2)

    def test_pin_vendor_checksums(self):
        manifest=json.loads((ROOT/'runtime/provenance.json').read_text())
        for name,digest in manifest['vendor_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'runtime'/name).read_bytes()).hexdigest(),digest,name)


if __name__ == '__main__':
    unittest.main()
