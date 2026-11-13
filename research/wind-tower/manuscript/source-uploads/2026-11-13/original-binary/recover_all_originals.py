#!/usr/bin/env python3
"""Recover BOTH byte-identical thesis Word originals, entirely from GitHub checkout.

Usage:
  python research/wind-tower/manuscript/source-uploads/2026-11-13/original-binary/recover_all_originals.py
  python .../recover_all_originals.py /path/to/output

No internet access and no external packages are needed after Git checkout.
Checks original file SHA256, byte length, archive integrity, and input chunk Git SHAs.
"""
from __future__ import annotations
import base64
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def git_blob_sha(blob: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(blob)).encode('ascii') + b'\0' + blob).hexdigest()


def validate_word_file(path: Path, size: int, sha256: str) -> None:
    if path.stat().st_size != size:
        raise ValueError(f'Original byte length changed: {path}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != sha256:
        raise ValueError(f'Original SHA256 mismatch: {path}: {digest}')
    with zipfile.ZipFile(path) as z:
        fault = z.testzip()
        if fault:
            raise ValueError(f'Corrupt DOCX ZIP member: {fault}')
        if '[Content_Types].xml' not in z.namelist() or 'word/document.xml' not in z.namelist():
            raise ValueError('DOCX required XML entry missing')
    print(f'RESTORED_AND_VERIFIED {path.name} | {size} bytes | SHA256 {digest}')


def restore_20260827(out_dir: Path) -> Path:
    source = ROOT / '20260827'
    m = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    assert m['format'] == 'word-original-base64-v1'
    # Base64 parts are slices of the ONE original base64 stream, not independent base64 of bytes.
    encoded = []
    for p in m['parts']:
        file = source / Path(p['path']).name
        raw = file.read_bytes()
        if git_blob_sha(raw) != p['git_blob_sha']:
            raise ValueError(f'Git content mismatch: {file}')
        encoded.append(raw.decode('ascii'))
    joined = ''.join(encoded)
    if len(joined) != m['base64_length']:
        raise ValueError('Base64 length mismatch')
    docx = base64.b64decode(joined, validate=True)
    dest = out_dir / m['file_name']
    dest.write_bytes(docx)
    validate_word_file(dest, m['byte_length'], m['sha256'])
    return dest


def restore_native_chunks(out_dir: Path, subfolder: str) -> Path:
    source = ROOT / subfolder
    m = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    assert m['format'] == 'git-binary-chunks-v1'
    dest = out_dir / m['original_filename']
    with dest.open('wb') as f:
        for p in m['parts']:
            raw = (source / p['filename']).read_bytes()
            if len(raw) != p['size'] or hashlib.sha256(raw).hexdigest() != p['sha256']:
                raise ValueError(f'Part bytes mismatch: {p["filename"]}')
            if git_blob_sha(raw) != p['git_blob_sha1']:
                raise ValueError(f'Part Git blob mismatch: {p["filename"]}')
            f.write(raw)
    validate_word_file(dest, m['original_size'], m['original_sha256'])
    return dest


def main() -> None:
    dest = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'recovered-docx'
    dest.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite already recovered / user-owned files.
    for sub, namekey in [('20260827','file_name'),('20260905_raw','original_filename'),('20261113_refined','original_filename')]:
        name = json.loads((ROOT/sub/'manifest.json').read_text(encoding='utf-8'))[namekey]
        if (dest/name).exists():
            raise FileExistsError(f'Refusing overwrite: {dest/name}')
    restore_20260827(dest)
    restore_native_chunks(dest, '20260905_raw')
    restore_native_chunks(dest, '20261113_refined')
    print('ALL_THREE_THESIS_DOCX_RECOVERED_WITHOUT_ANY_CHAT_ATTACHMENTS')

if __name__ == '__main__':
    main()