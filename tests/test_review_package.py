"""Regression checks for the payload that is supplied to anonymous reviewers."""
import importlib.util
import io
from pathlib import Path
import zipfile

import pytest

spec = importlib.util.spec_from_file_location('review_package', Path(__file__).parents[1] / 'paper/review_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def payload():
    files = {name: b'example' for name in package.REQUIRED}
    files.update({'data/input.csv': b'x\n1\n', 'results/result.csv': b'y\n2\n',
                  'analysis/run.py': b'pass', 'tests/test_core.py': b'pass'})
    for name in list(files):
        if name.endswith('.docx'):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as doc:
                doc.writestr('docProps/core.xml', '<properties><creator/></properties>')
                doc.writestr('word/document.xml', '<document/>')
            files[name] = stream.getvalue()
    return files


def test_reject_missing_replication_input():
    files = payload()
    del files['data/input.csv']
    with pytest.raises(ValueError, match='Empty replication directory'):
        package.check(files)


@pytest.mark.parametrize('content', [b'Contact repository-owner', b'commit: ' + b'a' * 40])
def test_reject_repository_or_commit_identifier(content):
    files = payload()
    files['README.md'] = content
    with pytest.raises(ValueError, match='identifier'):
        package.check(files, identifiers=(b'repository-owner',))


@pytest.mark.parametrize('part, content', [
    ('docProps/core.xml', '<properties><creator>Author</creator></properties>'),
    ('word/comments.xml', '<comments/>'),
    ('word/document.xml', '<w:ins xmlns:w="urn:word"/>'),
])
def test_reject_word_identity_comments_and_changes(part, content):
    files = payload()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as doc:
        doc.writestr('docProps/core.xml', content if part == 'docProps/core.xml' else '<properties/>')
        doc.writestr('word/document.xml', content if part == 'word/document.xml' else '<document/>')
        if part == 'word/comments.xml':
            doc.writestr(part, content)
    files['paper/build/manuscript.docx'] = stream.getvalue()
    with pytest.raises(ValueError):
        package.check(files)


def test_working_tree_archive_has_matching_manifest_and_no_commit(tmp_path, monkeypatch):
    import hashlib
    import json
    files = payload()
    files['paper/build/BUILD_INFO.txt'] = b'commit: ' + b'b' * 40 + b'\nresults: checksum\n'
    monkeypatch.setattr(package, 'sources', lambda working_tree: files.copy())
    out = tmp_path / 'review.zip'
    package.build(out, working_tree=True)
    with zipfile.ZipFile(out) as archive:
        assert archive.comment == b''
        assert archive.testzip() is None
        assert b'commit:' not in archive.read('replication/paper/build/BUILD_INFO.txt')
        manifest = json.loads(archive.read('replication/REVIEW_MANIFEST.json'))
        assert manifest['source'] == 'working tree'
        for name, entry in manifest['files'].items():
            data = archive.read('replication/' + name)
            assert hashlib.sha256(data).hexdigest() == entry['sha256']
    package.verify(out)


def test_received_archive_rejects_changed_result(tmp_path, monkeypatch):
    monkeypatch.setattr(package, 'sources', lambda working_tree: payload())
    out = tmp_path / 'review.zip'
    package.build(out, working_tree=True)
    with zipfile.ZipFile(out) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    contents['replication/results/result.csv'] = b'y\n3\n'
    with zipfile.ZipFile(out, 'w') as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError, match='Manifest mismatch'):
        package.verify(out)


def test_environment_example_is_included_without_other_hidden_files():
    assert package.included('.env.example')
    assert not package.included('data/.env.example')
    assert not package.included('.env.backup')


@pytest.mark.parametrize('comment, removed', [('', True), ('<comment>Review text</comment>', False)])
def test_template_comment_cleanup_preserves_real_reviews(comment, removed):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as document:
        document.writestr('word/document.xml', '<document/>')
        document.writestr('word/comments.xml', f'<comments>{comment}</comments>')
        document.writestr('word/_rels/document.xml.rels',
                          '<Relationships><Relationship Target="comments.xml"/></Relationships>')
        document.writestr('[Content_Types].xml',
                          '<Types><Override PartName="/word/comments.xml"/></Types>')
    cleaned = package.remove_empty_comments(stream.getvalue())
    with zipfile.ZipFile(io.BytesIO(cleaned)) as document:
        assert ('word/comments.xml' not in document.namelist()) == removed
        assert (b'comments.xml' not in document.read('word/_rels/document.xml.rels')) == removed
        assert (b'comments.xml' not in document.read('[Content_Types].xml')) == removed
        assert document.read('word/document.xml') == b'<document/>'


@pytest.mark.parametrize('name', ['.env', '.git/config', 'paper/submission/title_page.docx',
                               'paper/private/cover_letter.docx', 'data/.env', 'logs/build.log',
                               'paper/build/manuscript_docx.md', 'docs/submission_preparation.md'])
def test_private_and_intermediate_files_excluded(name):
    assert not package.included(name)


@pytest.mark.parametrize('part, content, category', [
    ('word/header1.xml', '<header>repository-owner</header>', 'identifier'),
    ('word/_rels/document.xml.rels', '<Relationships><Link Target="https://github.com/repository-owner/paper"/></Relationships>', 'identifier'),
    ('word/footer1.xml', '<x:del xmlns:x="urn:word">old text</x:del>', 'Tracked changes'),
    ('word/footnotes.xml', '<notes>' + 'ghp_' + 'x' * 36 + '</notes>', 'credential'),
])
def test_reject_hidden_word_parts(part, content, category):
    files = payload()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as doc:
        doc.writestr('docProps/core.xml', '<properties/>')
        doc.writestr('word/document.xml', '<document/>')
        doc.writestr(part, content)
    files['paper/build/manuscript.docx'] = stream.getvalue()
    with pytest.raises(ValueError, match=category):
        package.check(files, identifiers=(b'repository-owner',))


def test_credential_error_does_not_echo_value():
    files = payload()
    credential = b'ghp_' + b'z' * 36
    files['data/request.json'] = credential
    with pytest.raises(ValueError, match='credential') as error:
        package.check(files)
    assert credential.decode() not in str(error.value)
