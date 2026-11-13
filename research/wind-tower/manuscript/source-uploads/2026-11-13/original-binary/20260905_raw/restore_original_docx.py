#!/usr/bin/env python3
"""Restore the unmodified 2026-09-05 original DOCX from tracked Git binary chunks.

Needs only Python 3 standard library. Validates every chunk's SHA256 and
Git blob SHA1, then validates original full-file byte length, SHA256 and ZIP.
"""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path


def git_blob_sha(blob: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(blob)).encode('ascii') + b'\0' + blob).hexdigest()


def restore(root: Path, output_dir: Path) -> Path:
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['format'] == 'git-binary-chunks-v1'
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / manifest['original_filename']
    if dest.exists():
        raise FileExistsError(f'Refusing to overwrite existing file: {dest}')
    temp = dest.with_name(dest.name + '.part')
    if temp.exists():
        raise FileExistsError(f'Previous partial output exists: {temp}')
    h = hashlib.sha256()
    size = 0
    try:
        with temp.open('xb') as writer:
            for info in manifest['parts']:
                b = (root / info['filename']).read_bytes()
                if len(b) != info['size']:
                    raise ValueError(f"Size mismatch: {info['filename']}")
                if hashlib.sha256(b).hexdigest() != info['sha256']:
                    raise ValueError(f"SHA256 mismatch: {info['filename']}")
                if git_blob_sha(b) != info['git_blob_sha1']:
                    raise ValueError(f"Git SHA mismatch: {info['filename']}")
                writer.write(b)
                h.update(b)
                size += len(b)
        if size != manifest['original_size'] or h.hexdigest() != manifest['original_sha256']:
            raise ValueError('Whole DOCX original-size/SHA256 mismatch')
        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None:
                raise ValueError('DOCX ZIP CRC validation failed')
        temp.replace(dest)
    finally:
        if temp.exists():
            temp.unlink()
    return dest


if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else folder / 'recovered'
    file = restore(folder, output)
    print(f'VERIFIED_ORIGINAL_DOCX: {file}')