"""Version-locked, staged Windows localization. Python standard library only."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import uuid

VERSION = '2.15.1'
ROOT = Path(__file__).resolve().parent
MARKER = '.antigravity-zh-cn.json'
BACKUP = f'app.asar.zh-cn-{VERSION}.bak'
DEFAULT_APP = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'antigravity'


def sha(path):
    with extended_path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extended_path(path):
    """Avoid MAX_PATH when appending temporary staging directory names on Windows."""
    path = Path(path).resolve()
    text = str(path)
    if sys.platform == 'win32' and not text.startswith('\\\\?\\'):
        text = ('\\\\?\\UNC\\' + text[2:]) if text.startswith('\\\\') else ('\\\\?\\' + text)
    return Path(text)


class Asar:
    def __init__(self, path):
        self.path = extended_path(path)
        with self.path.open('rb') as stream:
            prefix = stream.read(16)
            if len(prefix) != 16:
                raise ValueError('Truncated ASAR prefix')
            magic, size, payload, length = struct.unpack('<4I', prefix)
            if magic != 4 or size < 8 or length > size - 8 or size > self.path.stat().st_size - 8:
                raise ValueError('Invalid ASAR header')
            self.header = json.loads(stream.read(length))
        self.base = 8 + size
        self.entries = {}
        self._walk(self.header['files'])

    def _walk(self, files, prefix=''):
        for name, node in files.items():
            if name in ('', '.', '..') or any(c in name for c in '/\\:'):
                raise ValueError('Unsafe ASAR filename')
            relative = prefix + name
            if 'files' in node:
                self._walk(node['files'], relative + '/')
            elif 'link' in node:
                raise ValueError('ASAR links require explicit support: ' + relative)
            else:
                self.entries[relative] = node

    def read(self, relative):
        node = self.entries[relative]
        size = int(node['size'])
        if size < 0:
            raise ValueError('Negative entry size')
        if node.get('unpacked'):
            unpacked_dir = self.path.parent / 'app.asar.unpacked'
            if not unpacked_dir.exists():
                unpacked_dir = Path(str(self.path) + '.unpacked')
            external = unpacked_dir / relative
            root = unpacked_dir.resolve()
            if not external.resolve().is_relative_to(root):
                raise ValueError('External resource escapes unpacked directory')
            data = external.read_bytes()
        else:
            offset = int(node['offset'])
            if offset < 0 or self.base + offset + size > self.path.stat().st_size:
                raise ValueError('Entry exceeds archive: ' + relative)
            with self.path.open('rb') as stream:
                stream.seek(self.base + offset)
                data = stream.read(size)
        if len(data) != size:
            raise ValueError('Truncated entry: ' + relative)
        integrity = node.get('integrity', {})
        if integrity.get('algorithm') == 'SHA256' and hashlib.sha256(data).hexdigest() != integrity.get('hash'):
            raise ValueError('Integrity mismatch: ' + relative)
        return data

    def package(self):
        return json.loads(self.read('package.json'))


def replace_required(path, before, after):
    text = path.read_text(encoding='utf-8')
    if text.count(before) != 1:
        raise ValueError('Expected exactly one patch anchor in ' + path.name + ': ' + before[:70])
    path.write_text(text.replace(before, after), encoding='utf-8', newline='\n')


MENU_MAP = {
    'File': '文件', 'Edit': '编辑', 'View': '视图', 'Window': '窗口', 'Help': '帮助',
    'New Window': '新建窗口', 'Close Window': '关闭窗口', 'Docs': '文档',
    'Undo': '撤销', 'Redo': '重做', 'Cut': '剪切', 'Copy': '复制', 'Paste': '粘贴',
    'Paste and Match Style': '粘贴并匹配样式', 'Select All': '全选', 'Delete': '删除',
    'Minimize': '最小化', 'Zoom': '缩放', 'Close': '关闭', 'Quit': '退出',
    'Reload': '重新加载', 'Force Reload': '强制重新加载', 'Actual Size': '实际大小',
    'Reset Zoom': '重置缩放', 'Zoom In': '放大', 'Zoom Out': '缩小',
    'Toggle Full Screen': '切换全屏', 'Toggle Developer Tools': '切换开发者工具',
}


def build(app_dir, destination):
    destination = extended_path(destination)
    archive = app_dir / 'resources' / 'app.asar'
    if not archive.exists():
        bak = app_dir / 'resources' / 'app.asar.official.bak'
        if bak.exists():
            archive = bak
        else:
            raise FileNotFoundError(f'Neither app.asar nor app.asar.official.bak found in {app_dir / "resources"}')
    asar = Asar(archive)
    package = asar.package()
    if package.get('name') != 'antigravity':
        raise ValueError(f'Expected package "antigravity", found "{package.get("name")}"')
    detected_version = package.get('version') or VERSION
    backup_name = f'app.asar.zh-cn-{detected_version}.bak'
    if destination.exists():
        raise FileExistsError('Build destination already exists: ' + str(destination))
    destination.mkdir(parents=True)
    output = destination / 'app'
    external_hashes = {}
    for relative, node in asar.entries.items():
        data = asar.read(relative)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if node.get('unpacked'):
            external_hashes[relative] = hashlib.sha256(data).hexdigest()
    translations = json.loads((ROOT / 'translations.json').read_text(encoding='utf-8'))
    if (ROOT / 'translations-2.13.json').exists():
        translations.update(json.loads((ROOT / 'translations-2.13.json').read_text(encoding='utf-8')))
    javascript = (ROOT / 'localization.js').read_text(encoding='utf-8')
    javascript = javascript.replace('/*__DICTIONARY__*/ {}', json.dumps(translations, ensure_ascii=False))
    preload = output / 'dist/preload.js'
    original = preload.read_text(encoding='utf-8')
    if "contextBridge.exposeInMainWorld('electronNative'" not in original:
        raise ValueError('Unexpected preload structure')
    preload.write_text(original + '\n;\n' + javascript, encoding='utf-8', newline='\n')
    (destination / 'localization.generated.js').write_text(javascript, encoding='utf-8', newline='\n')
    # Menu translation
    menu = output / 'dist/menu.js'
    replace_required(menu, '    electron_1.Menu.setApplicationMenu(menu);',
                     '    translateZhCNMenu(menu);\n    electron_1.Menu.setApplicationMenu(menu);')
    replace_required(menu, 'item.label === submenuLabel',
                     '(item.label === submenuLabel || item.label === zhCNMenuLabels[submenuLabel])')
    with menu.open('a', encoding='utf-8') as stream:
        stream.write('\nconst zhCNMenuLabels = ' + json.dumps(MENU_MAP, ensure_ascii=False) + ';\n'
                     'function translateZhCNMenu(menu) {\n'
                     '  for (const item of menu.items || []) {\n'
                     '    if (Object.hasOwn(zhCNMenuLabels, item.label)) item.label = zhCNMenuLabels[item.label];\n'
                     '    if (item.submenu) translateZhCNMenu(item.submenu);\n'
                     '  }\n}\n')
    main = output / 'dist/main.js'
    replace_required(main, "label: 'No agents running'", "label: '没有正在运行的智能体'")
    replace_required(main, 'label: `Open ${electron_1.app.getName()}`', 'label: `打开 ${electron_1.app.getName()}`')
    replace_required(main, "label: 'Quit'", "label: '退出'")
    tray = output / 'dist/tray.js'
    replace_required(tray,
                     "(count > 0 ? `${count}` : 'No') +\n                    ' agent' +\n                    (count === 1 ? '' : 's') +\n                    ' running'",
                     "(count > 0 ? `${count} 个智能体正在运行` : '没有正在运行的智能体')")
    replace_required(output / 'dist/loadingOverlay.js', '>Loading Antigravity<', '>正在加载 Antigravity<')
    wizard = output / 'dist/ideInstall/wizardHtml.js'
    if wizard.exists():
        wizard_text = wizard.read_text(encoding='utf-8')
        replacements = [
            ('<title>Welcome to Antigravity</title>', '<title>欢迎使用 Antigravity</title>'),
            ('Setting up…', '正在设置…'),
            ('<h1>Welcome to the new Antigravity!</h1>', '<h1>欢迎使用全新 Antigravity！</h1>'),
            ("Antigravity has been redesigned to put agents first with new capabilities. If you'd still like a code editor, you can download it as a separate app named <b>Antigravity IDE</b>.",
             'Antigravity 经过全新设计，以智能体为核心并提供全新能力。如果您仍需要代码编辑器，可单独下载名为 <b>Antigravity IDE</b> 的独立应用。'),
            ('<span>Download the Antigravity IDE</span>', '<span>下载 Antigravity IDE</span>'),
            ('<button class="btn-primary" id="btn-skip">Explore the new Antigravity</button>', '<button class="btn-primary" id="btn-skip">探索全新 Antigravity</button>')
        ]
        for src, dst in replacements:
            if src in wizard_text:
                wizard_text = wizard_text.replace(src, dst)
        wizard.write_text(wizard_text, encoding='utf-8', newline='\n')
    hashes = {p.relative_to(output).as_posix(): sha(p) for p in output.rglob('*') if p.is_file()}
    manifest = {
        'format': 1, 'version': detected_version, 'source_sha256': sha(archive),
        'backup_name': backup_name, 'unpacked_sha256': external_hashes, 'files': hashes,
        'translation_count': len(translations),
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'version': detected_version, 'files': len(hashes), 'unpacked_files': len(external_hashes),
                      'translations': len(translations), 'bundle': str(destination)}, ensure_ascii=False))


def verify_bundle(bundle):
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    bundle_version = manifest.get('version')
    expected_backup = manifest.get('backup_name', f'app.asar.zh-cn-{bundle_version}.bak')
    if not bundle_version or manifest.get('backup_name') != expected_backup:
        raise ValueError('Unsupported bundle manifest')
    root = extended_path(bundle / 'app')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(manifest['files']):
        raise ValueError('Bundle file set does not match manifest')
    for relative, expected in manifest['files'].items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or sha(target) != expected:
            raise ValueError('Bundle hash mismatch: ' + relative)
    return manifest


def require_closed():
    if sys.platform == 'win32':
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Antigravity.exe', '/FO', 'CSV', '/NH'],
                                capture_output=True, check=True)
        if b'antigravity.exe' in result.stdout.lower():
            raise RuntimeError('Exit Antigravity normally before installing/restoring. No processes were stopped.')


def install(app_dir, bundle):
    if sys.platform != 'win32':
        raise ValueError('This adaptation is validated for Windows only')
    require_closed()
    manifest = verify_bundle(bundle)
    target_version = manifest.get('version', VERSION)
    backup_name = manifest.get('backup_name', f'app.asar.zh-cn-{target_version}.bak')
    resources = extended_path(app_dir / 'resources')
    archive, app, backup = resources / 'app.asar', resources / 'app', resources / backup_name
    if backup.exists() or (resources / 'app.asar.disabled').exists():
        raise FileExistsError('Existing backup/disabled archive detected; restore or inspect before installing')
    if app.exists():
        shutil.rmtree(app)
    if sha(archive) != manifest['source_sha256']:
        raise ValueError('Official ASAR has changed. Rebuild against the current installation.')
    for relative, expected in manifest['unpacked_sha256'].items():
        source = resources / 'app.asar.unpacked' / relative
        if not source.resolve().is_relative_to((resources / 'app.asar.unpacked').resolve()) or sha(source) != expected:
            raise ValueError('Official external resource has changed: ' + relative)
    stage = resources / ('app.zh-cn-stage-' + uuid.uuid4().hex)
    try:
        shutil.copytree(extended_path(bundle / 'app'), stage)
    except BaseException:
        # This is the new UUID directory created by this invocation only.
        if stage.parent == resources and stage.exists() and not stage.is_symlink():
            shutil.rmtree(stage)
        raise
    # Verify the copy before switching Electron's app resolution.
    for relative, expected in manifest['files'].items():
        if sha(stage / relative) != expected:
            raise ValueError('Staging copy mismatch: ' + relative)
    (stage / MARKER).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    stage.rename(app)
    try:
        archive.rename(backup)
    except BaseException:
        app.rename(stage)
        raise
    print(f'Installed {target_version} zh-CN. Restart Antigravity when current work is finished. No processes were stopped.')
    print('Original archive: ' + str(backup))


def restore(app_dir):
    require_closed()
    resources = extended_path(app_dir / 'resources')
    app, archive = resources / 'app', resources / 'app.asar'
    if not app.exists() and archive.exists():
        print('Already original; nothing changed.')
        return
    manifest_file = app / MARKER
    if not manifest_file.exists():
        raise ValueError('Unrecognized patch marker')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    target_version = manifest.get('version', VERSION)
    backup_name = manifest.get('backup_name', f'app.asar.zh-cn-{target_version}.bak')
    backup = resources / backup_name
    if not backup.exists():
        for candidate in [resources / 'app.asar.official.bak', resources / BACKUP]:
            if candidate.exists():
                backup = candidate
                break
    if not backup.exists():
        raise FileNotFoundError(f'Original backup not found: {backup_name}')
    if sha(backup) != manifest['source_sha256']:
        raise ValueError('Original backup hash mismatch')
    preserved = resources / ('app.zh-cn-restored-' + uuid.uuid4().hex)
    app.rename(preserved)
    try:
        if not archive.exists():
            backup.rename(archive)
        # If an updater provided a new ASAR, retain that ASAR and the old backup.
    except BaseException:
        preserved.rename(app)
        raise
    print(f'Restored {target_version}. Existing official updates were preserved. Restart when convenient.')
    print('Patch preserved at: ' + str(preserved))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-dir', type=Path, default=DEFAULT_APP)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--build', type=Path, metavar='BUNDLE')
    actions.add_argument('--install', type=Path, metavar='BUNDLE')
    actions.add_argument('--verify', type=Path, metavar='BUNDLE')
    actions.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.build:
        build(args.app_dir.resolve(), args.build.resolve())
    elif args.install:
        install(args.app_dir.resolve(), args.install.resolve())
    elif args.verify:
        manifest = verify_bundle(args.verify.resolve())
        print('Verified ' + str(len(manifest['files'])) + ' files')
    else:
        restore(args.app_dir.resolve())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
