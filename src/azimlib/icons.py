"""Bounded local monochrome SVG symbols with explicit source/license/hash.

Subset: svg/path, absolute M/L/H/V/Q/C/Z. No transforms, scripts, styles,
entities, URLs, images or embedded fonts. Unsupported content is rejected.
"""
import hashlib
import re
from pathlib import Path as FilePath
from dataclasses import replace
from .path import Path
from .patches import Symbol
from .patterns import Provenance

def read_svg_symbol(path,*,provenance):
    """Read a local SVG geometry subset; caller supplies legal provenance."""
    if not isinstance(provenance,Provenance):raise TypeError('Require explicit Provenance')
    with FilePath(path).open('rb') as stream:raw=stream.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError('SVG symbol exceeds one megabyte')
    digest=hashlib.sha256(raw).hexdigest()
    if provenance.sha256 and provenance.sha256!=digest:raise ValueError('SVG symbol hash mismatch')
    from ._readers import xml_root
    import io
    root=xml_root(io.BytesIO(raw))
    if root.tag.rsplit('}',1)[-1]!='svg':raise ValueError('Require SVG root')
    if set(root.attrib)-{'viewBox','width','height','version'}:raise ValueError('Unsupported SVG root attribute')
    if len(root)!=1:raise ValueError('Require exactly one SVG path element')
    vertices=[];codes=[]
    for child in root:
        if child.tag.rsplit('}',1)[-1]!='path' or set(child.attrib)-{'d','fill','fill-rule'}:raise ValueError('Only monochrome SVG paths are supported')
        if child.get('fill-rule','evenodd') not in ('evenodd','nonzero'):raise ValueError('Invalid SVG fill rule')
        data=child.get('d','');tokens=re.findall(r'[MLHVQCZ]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',data)
        if re.sub(r'[\s,]','',data)!=re.sub(r'[\s,]','',''.join(tokens)):raise ValueError('Unsupported SVG path syntax')
        if not tokens or tokens[0]!='M':raise ValueError('SVG path must start with M')
        i=0;command=None;current=(0.,0.);start=None
        while i<len(tokens):
            if tokens[i] in ('M','L','H','V','Q','C','Z'):command=tokens[i];i+=1
            if command is None:raise ValueError('SVG path needs an initial command')
            if command=='Z':
                if start is None:raise ValueError('Close without subpath')
                vertices.append(start);codes.append(Path.CLOSEPOLY);current=start;command=None;continue
            count=dict(M=2,L=2,H=1,V=1,Q=4,C=6)[command]
            try:values=[float(v) for v in tokens[i:i+count]]
            except ValueError as exc:raise ValueError('Incomplete SVG command') from exc
            if len(values)!=count:raise ValueError('Incomplete SVG command')
            i+=count
            if command in ('H','V'):
                current=(values[0],current[1]) if command=='H' else (current[0],values[0]);vertices.append(current);codes.append(Path.LINETO)
            else:
                points=list(zip(values[::2],values[1::2]));vertices.extend(points)
                codes.extend([dict(M=Path.MOVETO,L=Path.LINETO,Q=Path.CURVE3,C=Path.CURVE4)[command]]*len(points));current=points[-1]
                if command=='M':start=current;command='L'
            if len(vertices)>10000:raise ValueError('SVG symbol exceeds 10000 vertices')
    import math
    if any(not math.isfinite(v) for p in vertices for v in p):raise ValueError('SVG coordinates must be finite')
    if not vertices:raise ValueError('SVG symbol has no path geometry')
    if codes.count(Path.MOVETO)>1 and root[0].get('fill-rule')!='evenodd':raise ValueError('Multipart SVG symbols require explicit evenodd fill-rule')
    symbol=Symbol(Path(vertices,codes));symbol.provenance=replace(provenance,sha256=digest)
    return symbol
