"""Local bounded input and planar ring helpers for independently written readers."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def _chunks(stream,limit,*,text=False):
    """Bound reads themselves, including short-reading streams and tiny files."""
    chunks=[]; total=0; kind=None
    while True:
        chunk=stream.read(min(65536,limit-total+1))
        if not isinstance(chunk,(str,bytes)) or (not text and not isinstance(chunk,bytes)):
            raise TypeError('Input stream must return bytes' + (' or text' if text else ''))
        if kind is not None and type(chunk) is not kind: raise TypeError('Input stream changed text/binary type')
        kind=type(chunk)
        if not chunk: break
        raw=chunk.encode('utf8') if isinstance(chunk,str) else chunk
        total+=len(raw)
        if total>limit: raise ValueError('Input exceeds reader byte limit')
        chunks.append(raw)
    return b''.join(chunks)


def binary(source, limit=256 * 1024 * 1024):
    if isinstance(limit,bool) or not isinstance(limit,int) or limit<0: raise ValueError('Reader limit must be a nonnegative integer')
    if isinstance(source, bytes):
        result = source
    elif hasattr(source, 'read'):
        result = _chunks(source,limit)
    else:
        with Path(source).open('rb') as stream:
            result = _chunks(stream,limit)
    if not isinstance(result, bytes):
        raise TypeError('Binary input requires bytes, a local path or a binary stream')
    if len(result) > limit:
        raise ValueError('Input exceeds reader byte limit')
    return result


def xml_root(source):
    if isinstance(source, str) and source.lstrip('\ufeff \r\n\t').startswith('<'):
        raw = source.encode('utf-8')
    elif hasattr(source, 'read'):
        raw = _chunks(source,64 * 1024 * 1024,text=True)
    else:
        raw = binary(source, 64 * 1024 * 1024)
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError('XML input exceeds 64 MiB')
    # NUL removal also recognizes declarations in UTF-16/32 before parsing.
    if re.search(rb'<!\s*(?:DOCTYPE|ENTITY)\b', raw.replace(b'\0', b''), re.I):
        raise ValueError('XML DTDs and entity declarations are forbidden')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError('Malformed XML') from exc
    if any(e.tag.startswith('{http://www.w3.org/2001/XInclude}') for e in root.iter()):
        raise ValueError('XML includes are forbidden')
    return root


def inside(point, ring):
    """Even-odd containment; boundary counts as inside for hole assignment."""
    x, y = point[:2]
    result = False
    for a, b in zip(ring, ring[1:]):
        ax, ay = a[:2]; bx, by = b[:2]
        cross = (x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if cross == 0 and min(ax, bx) <= x <= max(ax, bx) and min(ay, by) <= y <= max(ay, by):
            return True
        if (ay > y) != (by > y) and x < ax+(y-ay)*(bx-ax)/(by-ay):
            result = not result
    return result


def area(ring):
    x, y = ring[0][:2]
    return sum((a[0]-x)*(b[1]-y)-(b[0]-x)*(a[1]-y) for a, b in zip(ring, ring[1:]))/2


def assign_holes(outers, holes):
    if not outers:
        raise ValueError('Polygon has no outer ring')
    groups = [[ring] for ring in outers]
    for hole in holes:
        candidates = [i for i, ring in enumerate(outers) if all(inside(p, ring) for p in hole[:-1])]
        if not candidates:
            raise ValueError('Polygon hole has no containing outer ring')
        owner = min(candidates, key=lambda i: abs(area(outers[i])))
        groups[owner].append(hole)
    return groups
