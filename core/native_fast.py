"""ctypes loader for optional AEGENTIX native fast-path library.

Build produces native/aegentix_fast.{dll,so,dylib}. If unavailable, callers
fall back to pure Python (correctness preserved; native is a perf offload).
"""
from __future__ import annotations
import ctypes, os, sys
from pathlib import Path
from typing import Optional

_LIB = None
_TRIED = False

def _load():
    global _LIB, _TRIED
    if _TRIED:
        return _LIB
    _TRIED = True
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / 'native' / 'aegentix_fast.dll',
        root / 'native' / ('libaegentix_fast.so' if sys.platform != 'win32' else 'aegentix_fast.dll'),
        root / 'native' / 'libaegentix_fast.dylib',
        root / 'aegentix_fast.dll',
    ]
    env = os.environ.get('AEGENTIX_FAST_LIB')
    if env:
        candidates.insert(0, Path(env))
    for c in candidates:
        try:
            if c.exists():
                lib = ctypes.CDLL(str(c))
                lib.aegx_checksum32.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                lib.aegx_checksum32.restype = ctypes.c_uint32
                lib.aegx_score_terms.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
                lib.aegx_score_terms.restype = ctypes.c_int32
                try:
                    lib.aegx_abi_version.argtypes = []
                    lib.aegx_abi_version.restype = ctypes.c_uint32
                except Exception:
                    pass
                _LIB = lib
                return _LIB
        except Exception:
            continue
    return None

def checksum32(data: bytes) -> Optional[int]:
    lib = _load()
    if not lib or data is None:
        return None
    try:
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        return int(lib.aegx_checksum32(ctypes.cast(buf, ctypes.c_void_p), ctypes.c_size_t(len(data))))
    except Exception:
        return None

def score_terms(hay: str, terms: list[str], exact: str = '') -> Optional[int]:
    lib = _load()
    if not lib:
        return None
    try:
        hb = (hay or '').encode('utf-8', 'ignore')
        tb = ('\n'.join(terms or [])).encode('utf-8', 'ignore')
        eb = (exact or '').encode('utf-8', 'ignore')
        return int(lib.aegx_score_terms(hb, len(hb), tb, len(tb), eb, len(eb)))
    except Exception:
        return None

def available() -> bool:
    return _load() is not None
