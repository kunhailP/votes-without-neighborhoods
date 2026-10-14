"""Build and verify a review ZIP: python paper/review_package.py OUT.zip [--working-tree].

Default: committed files. --working-tree includes tracked and unignored new
replication files, allowing review of a locally revised paper before committing.
Private submission documents are never replication inputs.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
TOP = {'README.md', 'LICENSE', 'CITATION.cff', 'Makefile', 'requirements.txt', 'pyproject.toml', '.env.example'}
DIRS = {'vwn', 'analysis', 'build', 'data', 'results', 'paper', 'tests', 'docs'}
REQUIRED = {'README.md', 'Makefile', 'requirements.txt', 'vwn/lp.py',
            'paper/build/manuscript.pdf', 'paper/build/appendix.pdf',
            'paper/build/manuscript.docx', 'paper/build/appendix.docx'}


def included(name):
    p = PurePosixPath(name)
    if name == '.env.example':
        return True
    if name not in TOP and p.parts[0] not in DIRS:
        return False
    if any(part.startswith('.') or part in {'__pycache__', 'submission', 'private'} for part in p.parts):
        return False
    return not (name.endswith(('.pyc', '_pdf.md', '_docx.md')) or name == 'docs/submission_preparation.md')


def sources(working_tree):
    if working_tree:
        names = subprocess.check_output(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
        ).decode().split('\0')
        return {name: (ROOT / name).read_bytes() for name in sorted(set(names))
                if name and included(name) and (ROOT / name).is_file()}
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD'], cwd=ROOT).returncode:
        sys.exit('Uncommitted changes: commit first or explicitly use --working-tree.')
    raw = subprocess.check_output(['git', 'archive', '--format=zip', 'HEAD'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return {name: archive.read(name) for name in archive.namelist()
                if not name.endswith('/') and included(name)}


def check_identifiers(name, data, identifiers=(), commits=False):
    """Inspect uncompressed text; report the location, never a credential value."""
    if any(marker.lower() in data.lower() for marker in identifiers):
        raise ValueError(f'Repository identifier in {name}')
    credential = rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)'
    if re.search(credential, data):
        raise ValueError(f'Possible credential in {name}')
    if commits and re.search(rb'\b[0-9a-f]{40}\b', data):
        raise ValueError(f'Possible commit identifier in {name}')


def check(files, identifiers=()):
    missing = REQUIRED - files.keys()
    if missing:
        raise ValueError(f'Missing required files: {sorted(missing)}')
    for directory in ['data/', 'results/', 'analysis/', 'tests/']:
        if not any(name.startswith(directory) for name in files):
            raise ValueError(f'Empty replication directory: {directory}')
    for name, data in files.items():
        if name.endswith('.docx'):
            with zipfile.ZipFile(io.BytesIO(data)) as doc:
                core = ET.fromstring(doc.read('docProps/core.xml'))
                for element in core:
                    if element.tag.rsplit('}', 1)[-1] in {'creator', 'lastModifiedBy'} and (element.text or '').strip():
                        raise ValueError(f'Author metadata in {name}')
                for part in doc.namelist():
                    if part.startswith('word/comments'):
                        raise ValueError(f'Comment part in {name}')
                    if part.endswith(('.xml', '.rels')):
                        content = doc.read(part)
                        check_identifiers(f'{name}:{part}', content, identifiers)
                        if part.startswith('word/') and part.endswith('.xml'):
                            root = ET.fromstring(content)
                            if any(e.tag.rsplit('}', 1)[-1] in {'ins', 'del', 'moveFrom', 'moveTo'} for e in root.iter()):
                                raise ValueError(f'Tracked changes in {name}:{part}')
        check_identifiers(name, data, identifiers,
                          commits=name.endswith(('.md', '.py', '.txt', '.json', '.cff', '.toml')))


def remove_empty_comments(data):
    """Remove inert template comment parts; leave real comments for check() to reject."""
    with zipfile.ZipFile(io.BytesIO(data)) as document:
        parts = {name: document.read(name) for name in document.namelist()}
        empty = set()
        for name, content in parts.items():
            if name.startswith('word/comments') and name.endswith('.xml'):
                root = ET.fromstring(content)
                if root.tag.rsplit('}', 1)[-1] == 'comments' and not len(root) and not ''.join(root.itertext()).strip():
                    empty.add(name)
        references = rb'<(?:\w+:)?comment(?:Reference|RangeStart|RangeEnd)\b'
        if not empty or any(re.search(references, content) for name, content in parts.items()
                            if name.startswith('word/') and name.endswith('.xml')):
            return data
        for name, content in list(parts.items()):
            if name == '[Content_Types].xml' or name.endswith('.rels'):
                root = ET.fromstring(content)
                changed = False
                for element in list(root):
                    if name == '[Content_Types].xml':
                        target = element.get('PartName', '').lstrip('/')
                    else:
                        base = str(PurePosixPath(name).parent.parent)
                        target = element.get('Target', '')
                        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(base, target))
                    if target in empty:
                        root.remove(element)
                        changed = True
                if changed:
                    parts[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as cleaned:
            for entry in document.infolist():
                if entry.filename not in empty:
                    cleaned.writestr(entry, parts[entry.filename])
        return output.getvalue()


def build(out, working_tree=False):
    files = sources(working_tree)
    files = {name: remove_empty_comments(data) if name.endswith('.docx') else data
             for name, data in files.items()}
    if 'paper/build/BUILD_INFO.txt' in files:
        files['paper/build/BUILD_INFO.txt'] = b''.join(
            line for line in files['paper/build/BUILD_INFO.txt'].splitlines(True)
            if not line.startswith(b'commit:'))
    remote = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=ROOT,
                            capture_output=True, check=False).stdout.strip()
    owner = re.split(rb'[:/]', remote)[-2] if remote else b''
    check(files, identifiers=(owner,) if owner else ())
    manifest = {
        'source': 'working tree' if working_tree else 'committed files',
        'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())}}
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(out.suffix + '.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                archive.writestr('replication/' + name, data)
            archive.writestr('replication/REVIEW_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
        with zipfile.ZipFile(temporary) as archive:
            if archive.comment or archive.testzip():
                raise ValueError('Invalid archive or nonempty ZIP comment')
            for name, entry in manifest['files'].items():
                data = archive.read('replication/' + name)
                if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                    raise ValueError(f'Manifest mismatch: {name}')
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'wrote and verified {out} ({len(files)} files plus manifest; {out.stat().st_size:,} bytes)')


def verify(path):
    """Check the received review archive without requiring a Git checkout."""
    with zipfile.ZipFile(path) as archive:
        if archive.comment or archive.testzip():
            raise ValueError('Invalid archive or nonempty ZIP comment')
        manifest_name = 'replication/REVIEW_MANIFEST.json'
        manifest = json.loads(archive.read(manifest_name))
        entries = manifest['files']
        expected = {'replication/' + name for name in entries} | {manifest_name}
        if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
            raise ValueError('Archive file list differs from manifest')
        files = {}
        for name, entry in entries.items():
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or not included(name):
                raise ValueError(f'Invalid replication path: {name}')
            data = archive.read('replication/' + name)
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError(f'Manifest mismatch: {name}')
            files[name] = data
        check(files)
    print(f'verified {path} ({len(files)} files plus manifest)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--working-tree', action='store_true')
    mode.add_argument('--verify', action='store_true', help='verify an existing ZIP without Git')
    args = parser.parse_args()
    if args.verify:
        verify(args.output)
    else:
        build(args.output, args.working_tree)
