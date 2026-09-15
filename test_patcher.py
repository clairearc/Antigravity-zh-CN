import hashlib
import json
from pathlib import Path
import struct
import shutil
import tempfile
import unittest
from unittest.mock import patch
import patcher


class PatcherTests(unittest.TestCase):
    def setUp(self):
        self.closed = patch.object(patcher, 'require_closed')
        self.closed.start()
        self.addCleanup(self.closed.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.app = self.root / 'installed'
        self.resources = self.app / 'resources'
        self.resources.mkdir(parents=True)
        self.archive = self.resources / 'app.asar'
        self.archive.write_bytes(b'original archive')
        self.bundle = self.root / 'bundle'
        (self.bundle / 'app').mkdir(parents=True)
        (self.bundle / 'app/package.json').write_text('{}')
        self.manifest = {'version': patcher.VERSION, 'backup_name': patcher.BACKUP,
                         'source_sha256': patcher.sha(self.archive), 'unpacked_sha256': {},
                         'files': {'package.json': patcher.sha(self.bundle / 'app/package.json')}}
        (self.bundle / 'manifest.json').write_text(json.dumps(self.manifest))

    def tearDown(self):
        # Temporary test paths may intentionally exceed MAX_PATH.
        shutil.rmtree(patcher.extended_path(self.root))
        self.temp.cleanup()

    def test_install_restore_exact_original(self):
        patcher.install(self.app, self.bundle)
        self.assertFalse(self.archive.exists())
        patcher.restore(self.app)
        self.assertEqual(self.archive.read_bytes(), b'original archive')
        self.assertFalse((self.resources / 'app').exists())

    def test_restore_preserves_official_update(self):
        patcher.install(self.app, self.bundle)
        self.archive.write_bytes(b'new official version')
        patcher.restore(self.app)
        self.assertEqual(self.archive.read_bytes(), b'new official version')
        self.assertEqual((self.resources / patcher.BACKUP).read_bytes(), b'original archive')

    def test_refuse_changed_source_and_corrupt_bundle(self):
        self.archive.write_bytes(b'updated')
        with self.assertRaises(ValueError):
            patcher.install(self.app, self.bundle)
        self.assertFalse((self.resources / 'app').exists())
        (self.bundle / 'app/package.json').write_text('changed')
        with self.assertRaises(ValueError):
            patcher.verify_bundle(self.bundle)

    def test_refuse_duplicate_install(self):
        patcher.install(self.app, self.bundle)
        with self.assertRaises(FileExistsError):
            patcher.install(self.app, self.bundle)

    def test_corrupt_backup_cannot_restore(self):
        patcher.install(self.app, self.bundle)
        (self.resources / patcher.BACKUP).write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            patcher.restore(self.app)
        self.assertTrue((self.resources / 'app').exists())

    def test_rename_failure_leaves_original_active(self):
        original = Path.rename
        def fail_archive(source, target):
            if source.name == 'app.asar':
                raise PermissionError('Simulated locked original')
            return original(source, target)
        with patch.object(Path, 'rename', fail_archive):
            with self.assertRaises(PermissionError):
                patcher.install(self.app, self.bundle)
        self.assertEqual(self.archive.read_bytes(), b'original archive')
        self.assertFalse((self.resources / 'app').exists())

    def write_asar(self, files, data=b''):
        header = json.dumps({'files': files}).encode()
        padding = b'\0' * (-len(header) % 4)
        size = 8 + len(header) + len(padding)
        self.archive.write_bytes(struct.pack('<4I', 4, size, size - 4, len(header)) + header + padding + data)

    def test_asar_packed_and_external_integrity(self):
        self.write_asar({'one': {'size': 3, 'offset': '0'}, 'two': {'size': 3, 'unpacked': True}}, b'abc')
        external = Path(str(self.archive) + '.unpacked')
        external.mkdir()
        (external / 'two').write_bytes(b'xyz')
        asar = patcher.Asar(self.archive)
        self.assertEqual(asar.read('one'), b'abc')
        self.assertEqual(asar.read('two'), b'xyz')
        (external / 'two').write_bytes(b'x')
        with self.assertRaises(ValueError):
            asar.read('two')

    def test_windows_long_staging_path(self):
        relative = 'node_modules/' + ('long-directory/' * 12) + 'long-file-name.md'
        target = patcher.extended_path(self.bundle / 'app' / relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'long path resource')
        self.manifest['files'][relative] = patcher.sha(target)
        (self.bundle / 'manifest.json').write_text(json.dumps(self.manifest))
        patcher.install(self.app, self.bundle)
        self.assertEqual(patcher.extended_path(self.resources / 'app' / relative).read_bytes(), b'long path resource')
        patcher.restore(self.app)

    def test_asar_rejects_traversal_and_truncation(self):
        self.write_asar({'../outside': {'size': 0, 'offset': '0'}})
        with self.assertRaises(ValueError):
            patcher.Asar(self.archive)
        self.write_asar({'one': {'size': 100, 'offset': '0'}}, b'x')
        with self.assertRaises(ValueError):
            patcher.Asar(self.archive).read('one')


if __name__ == '__main__':
    unittest.main()
