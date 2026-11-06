#!/usr/bin/env python3
"""Read-only PE/COFF and controller entrypoint gate for S07 A-case (NO SOLVER)."""
import argparse
import hashlib
import json
import struct
import sys
import os
import tempfile
from pathlib import Path

EXE = 'bin/openfast_x64_v353.exe'
DLL = 'CASES/U11p4_ETM_S04/Control/libdiscon.dll'
EXPECTED = {'exe': '0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a',
            'dll': '7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa'}


def u16(data, off):
    if off < 0 or off + 2 > len(data):
        raise ValueError('PE_TRUNCATED_U16')
    return struct.unpack_from('<H', data, off)[0]


def u32(data, off):
    if off < 0 or off + 4 > len(data):
        raise ValueError('PE_TRUNCATED_U32')
    return struct.unpack_from('<I', data, off)[0]


def pe_info(data):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('PE_MZ_MISSING')
    p = u32(data, 0x3c)
    if p < 64 or p + 24 > len(data) or data[p:p+4] != b'PE\0\0':
        raise ValueError('PE_SIGNATURE_INVALID')
    machine, nsec = u16(data, p+4), u16(data, p+6)
    optsize = u16(data, p+20)
    opt = p+24
    if machine != 0x8664 or u16(data, opt) != 0x20b:
        raise ValueError('PE_NOT_AMD64_PE32PLUS')
    if nsec < 1 or nsec > 96 or optsize < 120 or opt + optsize + nsec*40 > len(data):
        raise ValueError('PE_SECTION_TABLE_INVALID')
    secs = []
    for i in range(nsec):
        q = opt+optsize+i*40
        virtual_size, rva, raw_size, raw_ptr = struct.unpack_from('<IIII', data, q+8)
        if raw_ptr+raw_size > len(data):
            raise ValueError('PE_SECTION_RAW_OUT_OF_RANGE')
        secs.append((rva, max(virtual_size, raw_size), raw_ptr, raw_size))

    def offset(rva, length=1):
        for va, span, rp, rs in secs:
            if va <= rva and rva+length <= va+span and rva-va+length <= rs:
                return rp+(rva-va)
        raise ValueError('PE_RVA_UNMAPPED')

    exports = []
    exp_rva, exp_size = u32(data, opt+112), u32(data, opt+116)
    if exp_rva and exp_size:
        e = offset(exp_rva, 40)
        n = u32(data, e+24)
        names = u32(data, e+32)
        if n > 100000:
            raise ValueError('PE_EXPORT_COUNT_UNSAFE')
        for i in range(n):
            name_rva = u32(data, offset(names+i*4, 4))
            start = offset(name_rva)
            end = data.find(b'\0', start, min(len(data), start+256))
            if end < 0:
                raise ValueError('PE_EXPORT_STRING_INVALID')
            exports.append(data[start:end].decode('ascii', errors='strict'))
    return {'machine': 'AMD64', 'optional_header': 'PE32+', 'sections': nsec,
            'export_count': len(exports), 'discon_export': 'DISCON' in exports,
            'discon_case_variants': sorted(x for x in exports if 'discon' in x.lower())}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(receipt, exe, dll):
    if receipt.get('RUN', {}).get('executed') is not False or receipt.get('RUN', {}).get('openfast') != 0:
        raise ValueError('RECEIPT_NOT_STATIC')
    tab = receipt['TAB']['files']
    if receipt['TAB']['count'] != len(tab) or len(tab) != 20:
        raise ValueError('RECEIPT_COUNT_MISMATCH')
    for kind, path, key, file in [('exe', EXE, 'exe_sha256', exe), ('dll', DLL, None, dll)]:
        target = tab[path]
        expected = EXPECTED[kind]
        if target['sha256'] != expected or (key and receipt['SOURCE'][key] != expected):
            raise ValueError('SOURCE_RECEIPT_SHA_MISMATCH_'+kind)
        if not file.is_file() or file.stat().st_size != target['bytes'] or digest(file) != expected:
            raise ValueError('ACTUAL_BYTES_SHA_OR_SIZE_MISMATCH_'+kind)
    ei = pe_info(exe.read_bytes())
    di = pe_info(dll.read_bytes())
    if not di['discon_export']:
        raise ValueError('CONTROLLER_DISCON_EXPORT_MISSING')
    return {'SOURCE': {'exe_sha256': EXPECTED['exe'], 'dll_sha256': EXPECTED['dll']},
            'TAB': {'exe_pe': ei, 'dll_pe': di, 'manifest_files': len(tab)},
            'RUN': {'openfast': 0, 'abaqus': 0, 'type': 'static PE/ABI preflight'},
            'FIG': 'NONE', 'STANDARD': 'NOT_READ',
            'HOLD': 'No native initialization/version/banner/controller runtime ABI or 31-station OUTB'}



def native_reference_dll_load(dll):
    """Windows LoadLibrary + GetProcAddress only; NEVER call DISCON or OpenFAST.

    This checks the SHA-locked *reference* DLL, not the missing historical DLL.
    A successful OS load does not establish the controller calling convention,
    historical equivalence, or turbine physics.
    """
    dll = Path(dll)
    if (not dll.is_file() or dll.stat().st_size != 1122431 or
            digest(dll) != EXPECTED['dll']):
        raise ValueError('REFERENCE_DLL_REAL_BYTES_SHA_OR_SIZE_MISMATCH')
    pe = pe_info(dll.read_bytes())
    if not pe['discon_export'] or pe['machine'] != 'AMD64':
        raise ValueError('REFERENCE_DLL_STATIC_PE_OR_EXPORT_INVALID')
    if sys.platform != 'win32' or sys.maxsize <= 2**32:
        raise ValueError('WINDOWS_AMD64_NATIVE_LOADER_REQUIRED')
    import ctypes
    result = {
        'SOURCE': {'reference_dll_sha256': EXPECTED['dll'],
                   'reference_dll_bytes': 1122431},
        'READING_LEVEL': 'REAL_WINDOWS_OS_LOADER_REFERENCE_DLL_ONLY',
        'REF': 'T077 S07_A_NATIVE_BINARY_ABI_RECEIPT.json and A-case RUN card',
        'STANDARD': 'NOT_READ',
        'OFFICIAL': 'Windows OS LoadLibrary/GetProcAddress; not original DLL certification',
        'RUN': {'openfast': 0, 'discon_calls': 0, 'abaqus': 0,
                'type': 'Windows reference DLL load-only, NO SOLVER'},
        'FIG': 0,
        'TAB': {'pe': pe, 'loader': 'ctypes.WinDLL', 'export': 'DISCON'},
        'HOLD': 'Historical 36-case DLL absent; DISCON calling ABI and OpenFAST initialization NOT tested',
        'physical_pass': False, 'stages_passed': 0,
    }
    try:
        # Explicit DLL search scope; no calls into exported DISCON function.
        with os.add_dll_directory(str(dll.resolve().parent)):
            handle = ctypes.WinDLL(str(dll.resolve()))
            symbol = getattr(handle, 'DISCON')
            address = ctypes.cast(symbol, ctypes.c_void_p).value
        if not address:
            raise OSError('DISCON resolved to null address')
        result['status'] = 'PASS_REFERENCE_DLL_WINDOWS_LOAD_AND_EXPORT_ONLY'
        result['TAB']['symbol_address_nonzero'] = True
    except (OSError, AttributeError) as exc:
        result['status'] = 'HOLD_WINDOWS_REFERENCE_DLL_LOAD_OR_EXPORT'
        result['TAB']['symbol_address_nonzero'] = False
        result['failure'] = {'type': type(exc).__name__,
                             'winerror': getattr(exc, 'winerror', None),
                             'message': str(exc)}
    return result


def synthetic_pe(export='DISCON', machine=0x8664):
    b = bytearray(1024)
    b[:2] = b'MZ'
    struct.pack_into('<I', b, 0x3c, 128)
    b[128:132] = b'PE\0\0'
    struct.pack_into('<HH', b, 132, machine, 1)
    struct.pack_into('<H', b, 148, 240)
    opt = 152
    struct.pack_into('<H', b, opt, 0x20b)
    struct.pack_into('<II', b, opt+112, 0x1000, 40)
    sec = opt+240
    struct.pack_into('<IIII', b, sec+8, 512, 0x1000, 512, 512)
    struct.pack_into('<I', b, 512+24, 1)
    struct.pack_into('<I', b, 512+32, 0x1040)
    struct.pack_into('<I', b, 512+64, 0x1050)
    b[512+80:512+80+len(export)+1] = export.encode()+b'\0'
    return bytes(b)


def selftest():
    assert pe_info(synthetic_pe())['discon_export']
    assert not pe_info(synthetic_pe('NOT_DISCON'))['discon_export']
    for value, code in [(synthetic_pe(machine=0x14c), 'PE_NOT_AMD64_PE32PLUS'),
                        (b'not-a-pe', 'PE_MZ_MISSING'), (synthetic_pe()[:200], 'PE_SECTION_TABLE_INVALID')]:
        try:
            pe_info(value)
        except ValueError as exc:
            assert str(exc) == code, (str(exc), code)
        else:
            raise AssertionError('negative test was accepted: '+code)
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp)/'test.dll'
        file.write_bytes(synthetic_pe())
        assert len(digest(file)) == 64
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp)/'tampered_reference.dll'
        bad.write_bytes(synthetic_pe())
        try:
            native_reference_dll_load(bad)
        except ValueError as exc:
            assert str(exc) == 'REFERENCE_DLL_REAL_BYTES_SHA_OR_SIZE_MISMATCH'
        else:
            raise AssertionError('tampered native DLL source accepted')
    print('S07_NATIVE_BINARY_PE_SYNTHETIC_PASS: export, missing export, x86 reject, bad MZ, truncated sections, sha')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--native-load-only', action='store_true', help='Windows LoadLibrary only; NEVER invoke DISCON or OpenFAST')
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--exe', type=Path)
    ap.add_argument('--dll', type=Path)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.native_load_only:
        if a.receipt or a.exe or not a.dll:
            ap.error('--native-load-only requires only --dll (and optional --output)')
        result = native_reference_dll_load(a.dll)
        raw = json.dumps(result, sort_keys=True, indent=2)+'\\n'
        if a.output:
            if a.output.exists():
                raise ValueError('OUTPUT_OVERWRITE_FORBIDDEN')
            a.output.write_text(raw, encoding='utf-8')
        print('S07_WINDOWS_REFERENCE_DLL_LOAD_ONLY='+raw)
    elif a.receipt:
        if not a.exe or not a.dll:
            ap.error('--receipt requires --exe and --dll')
        result = audit(json.loads(a.receipt.read_text(encoding='utf-8')), a.exe, a.dll)
        raw = json.dumps(result, sort_keys=True, indent=2)+'\n'
        if a.output:
            if a.output.exists():
                raise ValueError('OUTPUT_OVERWRITE_FORBIDDEN')
            a.output.write_text(raw, encoding='utf-8')
        print('S07_NATIVE_BINARY_STATIC_GATE_PASS='+raw)
    elif not a.selftest:
        ap.error('specify --selftest, --receipt, or --native-load-only')


if __name__ == '__main__':
    main()
