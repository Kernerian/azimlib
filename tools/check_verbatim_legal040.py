"""Check staged publication whitespace with exact, audited legal exceptions.

Exceptions affect whitespace only. Original legal payloads, staged payloads and
worktree payloads must all match the frozen release Git objects and SHA-256.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE_SHA = '50b467e252afe314645c031629ed1729007b267c'
PAGES_ATTRIBUTES_SHA256 = 'd72b21a03e33e37cdf723ba5fb1b65a1a50c0cf71675d62284d97abf95668d8b'
LEGAL_HASHES = {
    'licenses/AMSFonts.txt': 'aa783fdd47e92743bafe79277ac4067d20339344dc5b64a09c2d0f869b2999dc',
    'licenses/LPPL-1.3c.txt': '3d262cdf34dafa6955f703c634a8c238ec44109bc8dd6ef34fb7aa54809f7e66',
}
# Enumerated release payload paths; no directory, suffix or wildcard exemption.
PUBLICATION_COPIES = {
    '0.4.0/licenses/AMSFonts.txt': 'licenses/AMSFonts.txt',
    '0.4.0/licenses/LPPL-1.3c.txt': 'licenses/LPPL-1.3c.txt',
    'stable/licenses/AMSFonts.txt': 'licenses/AMSFonts.txt',
    'stable/licenses/LPPL-1.3c.txt': 'licenses/LPPL-1.3c.txt',
    'dev/licenses/AMSFonts.txt': 'licenses/AMSFonts.txt',
    'dev/licenses/LPPL-1.3c.txt': 'licenses/LPPL-1.3c.txt',
}


def git(repository, *args):
    return subprocess.run(['git', *args], cwd=repository, capture_output=True)


def blob(repository, spec):
    result = git(repository, 'show', spec)
    if result.returncode:
        raise AssertionError('Required legal Git object is missing: ' + spec)
    return result.stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(repository, source_repository):
    repository = Path(repository).resolve()
    source_repository = Path(source_repository).resolve()
    # Keep the existing Pages attribute policy intact: an unregistered license
    # cannot acquire another whitespace bypass through a new attribute file.
    attrs = repository / '.gitattributes'
    if (not attrs.is_file() or attrs.is_symlink() or
            digest(attrs.read_bytes()) != PAGES_ATTRIBUTES_SHA256 or
            blob(repository, ':.gitattributes') != attrs.read_bytes()):
        raise AssertionError('Publication attribute policy changed; explicit review required')
    tracked = git(repository, 'ls-files', '-z').stdout.decode('utf8').split('\0')
    if any(p != '.gitattributes' and p.endswith('/.gitattributes') for p in tracked):
        raise AssertionError('Unreviewed nested attributes cannot bypass whitespace validation')
    info = git(repository, 'rev-parse', '--git-path', 'info/attributes').stdout.decode().strip()
    info_path = Path(info) if Path(info).is_absolute() else repository / info
    if info_path.exists() and info_path.read_bytes().strip():
        raise AssertionError('Local attribute overrides cannot bypass publication validation')
    originals = {}
    for source, expected in LEGAL_HASHES.items():
        raw = blob(source_repository, SOURCE_SHA + ':' + source)
        if digest(raw) != expected:
            raise AssertionError('Frozen legal provenance/hash mismatch: ' + source)
        originals[source] = raw
    verified = []
    for relative, source in PUBLICATION_COPIES.items():
        path = repository / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(repository):
            raise AssertionError('Required verbatim legal copy is missing or linked: ' + relative)
        mode = git(repository, 'ls-files', '--stage', '--', relative).stdout.split(maxsplit=1)
        if not mode or mode[0] != b'100644':
            raise AssertionError('Legal copy must be a staged ordinary file: ' + relative)
        staged = blob(repository, ':' + relative)
        actual = path.read_bytes()
        if staged != originals[source] or actual != staged or digest(actual) != LEGAL_HASHES[source]:
            raise AssertionError('Verbatim legal payload changed; new audit required: ' + relative)
        verified.append(dict(path=relative, source=source, sha256=digest(actual)))
    # Mandatory normal Git check for all other paths, including unregistered
    # license files. Only the six already integrity-checked files are excluded.
    command = ['diff', '--cached', '--check', '--', '.',
               *[':(top,literal,exclude)' + path for path in PUBLICATION_COPIES]]
    result = git(repository, *command)
    if result.returncode:
        raise AssertionError('Non-verbatim whitespace validation failed:\n' +
                             (result.stdout + result.stderr).decode('utf8', errors='replace'))
    return dict(passed=True, release_source_sha=SOURCE_SHA, whitespace_check='git diff --cached --check',
                legal_exceptions=verified, provenance_verified=True,
                staged_and_worktree_bytes_verified=True, generic_exceptions=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--source-repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.repository, args.source_repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, indent=2))
