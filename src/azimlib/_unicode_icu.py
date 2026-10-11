"""Small, independently written binding to ICU's public Unicode C APIs.

No ICU binary, source, data table or third-party binding is bundled here.
Offsets are converted explicitly from UTF-16 to Python code-point indices.
"""
import ctypes as C
import ctypes.util
from functools import lru_cache
import re
import sys


class UnicodeEngineError(RuntimeError):
    """The optional Unicode service is unavailable or rejected the input."""


@lru_cache(maxsize=1)
def _api():
    if sys.platform == 'win32':
        candidates = ('icu.dll', 'icuuc.dll')
    elif sys.platform == 'darwin':
        candidates = ('/usr/lib/libicucore.A.dylib', ctypes.util.find_library('icuuc'))
    else:
        candidates = (ctypes.util.find_library('icuuc'),)
    for name in filter(None, candidates):
        try:
            lib = C.CDLL(name, **({'winmode': 0x800} if sys.platform == 'win32' else {}))
            suffixes = [''] + ['_'+v for v in re.findall(r'\d+', name)]
            suffixes += ['_'+str(v) for v in range(100, 49, -1)]
            suffix = next(s for s in suffixes if hasattr(lib, 'u_getVersion'+s))
            def bind(name, args, result):
                fn = getattr(lib, name+suffix); fn.argtypes = args; fn.restype = result
                return fn
            p, i, b, u = C.c_void_p, C.c_int32, C.c_uint8, C.c_uint16
            result = dict(
                break_open=bind('ubrk_open', [i,C.c_char_p,C.POINTER(u),i,C.POINTER(i)], p),
                break_close=bind('ubrk_close', [p], None),
                first=bind('ubrk_first', [p], i), next=bind('ubrk_next', [p], i),
                script=bind('uscript_getScript', [i,C.POINTER(i)], i),
                script_name=bind('uscript_getShortName', [i], C.c_char_p),
                char_direction=bind('u_charDirection',[i],C.c_int),
                integer_property=bind('u_getIntPropertyValue',[i,C.c_int],i),
                paired_bracket=bind('u_getBidiPairedBracket',[i],i),
                version=bind('u_getVersion', [C.POINTER(b)], None), library=lib)
            result['unicode_version']=bind('u_getUnicodeVersion',[C.POINTER(b)],None)
            version = (b*4)(); result['version'](version)
            result['version_string'] = '.'.join(map(str, version))
            return result
        except (OSError, AttributeError, StopIteration):
            continue
    raise UnicodeEngineError('Complex text requires ICU C APIs (Windows ICU, libicu on Linux/macOS)')


def _utf16(text):
    raw = text.encode('utf-16-le', errors='strict')
    units = (C.c_uint16*(len(raw)//2))(*[int.from_bytes(raw[i:i+2],'little') for i in range(0,len(raw),2)])
    offsets = {0:0}; position = 0
    for index, char in enumerate(text):
        position += 2 if ord(char)>0xffff else 1; offsets[position] = index+1
    return units, offsets


def _check(status):
    if status.value>0: raise UnicodeEngineError('ICU failed with UErrorCode '+str(status.value))


def visual_runs(text, direction='auto'):
    """Azimlib's UAX #9 resolver; ICU supplies character properties only."""
    from ._bidi import visual_runs as resolve
    return resolve(text,direction)


def graphemes(text):
    """Extended grapheme spans according to the installed ICU Unicode data."""
    if not text:return ()
    api = _api(); units, offsets = _utf16(text); status = C.c_int32(0)
    handle = api['break_open'](0,b'root',units,len(units),C.byref(status))
    try:
        _check(status)
        if not handle:raise MemoryError('ICU grapheme allocation failed')
        start = api['first'](handle); result=[]
        while True:
            end = api['next'](handle)
            if end==-1:break
            result.append((offsets[start],offsets[end])); start=end
        return tuple(result)
    finally:
        if handle:api['break_close'](handle)


@lru_cache(maxsize=4096)
def script(char):
    api = _api(); status=C.c_int32(0)
    value=api['script'](ord(char),C.byref(status)); _check(status)
    return api['script_name'](value).decode('ascii')


def unicode_version():return _api()['version_string']


def unicode_data_version():
    api=_api();version=(C.c_uint8*4)();api['unicode_version'](version)
    return '.'.join(map(str,version))
