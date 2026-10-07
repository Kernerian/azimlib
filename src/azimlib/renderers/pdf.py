"""Own dependency-free PDF 1.4 vector writer for backend-neutral scenes.

Text uses exact quadratic outlines of bundled licensed DejaVu (converted to
cubic Beziers), not font substitution. Text is not searchable in this cut.
PDF is one static page; no UI, external resources, TeX or cartographic backend.
"""
import math
from pathlib import Path as FilePath
from ..scene import Path,Text,Circle,Rect,Raster3D
from ..colors import to_rgba
from ..font_outline import text_commands
from ._common import validate

def n(value):
    # PDF real-number syntax has no exponent notation (unlike SVG).
    if not math.isfinite(float(value)):raise ValueError('PDF coordinates must be finite')
    result=format(float(value),'.8f').rstrip('0').rstrip('.')
    return '0' if result in ('','-0') else result

def render_pdf(scene,path_or_stream=None,*,dpi=100,_objects=False):
    """Return PDF bytes and optionally write them; dpi defines physical page units."""
    validate(scene)
    if not math.isfinite(dpi) or dpi<=0:raise ValueError('PDF dpi must be positive')
    objects=[None,None,None];states={};commands=[]
    def object(data):objects.append(data);return len(objects)
    def stream(data):return b'<< /Length '+str(len(data)).encode()+b' >>\nstream\n'+data+b'\nendstream'
    def rgba(value):return to_rgba(value or 'none')
    def paint(style,geometry,text=False):
        fill=rgba(style.get('fill','#172b38' if text else 'none'));stroke=rgba(style.get('stroke','none'))
        af=fill[3]*style.get('opacity',1)*style.get('fill_opacity',1)
        ast=stroke[3]*style.get('opacity',1)*style.get('stroke_opacity',1)
        key=(af,ast)
        if key not in states:
            name=f'GS{len(states)}';ref=object(f'<< /Type /ExtGState /ca {n(af)} /CA {n(ast)} >>'.encode());states[key]=(name,ref)
        name,_=states[key]
        prefix=[f'/{name} gs',f'{n(style.get("stroke_width",1))} w',f'{dict(butt=0,round=1,square=2)[style.get("linecap","butt")]} J',
                f'{dict(miter=0,round=1,bevel=2)[style.get("linejoin","round")]} j','10 M',
                '['+' '.join(n(x) for x in style.get('dash',()))+'] 0 d',
                ' '.join(n(x) for x in fill[:3])+' rg',' '.join(n(x) for x in stroke[:3])+' RG']
        op='B*' if af and ast and style.get('stroke_width',1)>0 else 'f*' if af else 'S' if ast and style.get('stroke_width',1)>0 else 'n'
        # Text halos must paint before fill, not PDF's standard fill-then-stroke.
        if text and op=='B*':return prefix+geometry+['S']+geometry+['f']
        if text and op=='f*':op='f'
        return prefix+geometry+[op]
    def path_commands(paths,closed):
        out=[]
        for part in paths:
            if len(part)<2:continue
            out.append(f'{n(part[0][0])} {n(part[0][1])} m')
            out.extend(f'{n(x)} {n(y)} l' for x,y in part[1:])
            if closed:out.append('h')
        return out
    def outlined(item):
        out=[];current=None
        for cmd in text_commands(item):
            if cmd[0]=='Z':out.append('h');continue
            if cmd[0] in ('M','L'):
                current=cmd[1];out.append(f'{n(current[0])} {n(current[1])} '+('m' if cmd[0]=='M' else 'l'))
            else:
                control,end=cmd[1:];a=tuple(current[i]+2*(control[i]-current[i])/3 for i in range(2));b=tuple(end[i]+2*(control[i]-end[i])/3 for i in range(2))
                out.append(' '.join(n(v) for p in (a,b,end) for v in p)+' c');current=end
        return out
    images=[]
    ratio=72/dpi
    commands.append(f'{n(ratio)} 0 0 {n(-ratio)} 0 {n(scene.height*ratio)} cm')
    items=list(scene.items)
    if scene.background is not None:items.insert(0,Rect(0,0,scene.width,scene.height,dict(fill=scene.background)))
    for item in items:
        commands.append('q')
        if item.clip is not None:commands.append(' '.join(n(v) for v in item.clip)+' re W n')
        if isinstance(item,Raster3D):
            import zlib
            from ..terrain3d import rasterize
            rw,rh=max(1,round(item.width)),max(1,round(item.height))
            image=rasterize(item.triangles,rw,rh)
            rgb=bytes(c for i,c in enumerate(image.rgba) if i%4!=3);alpha=image.rgba[3::4]
            def image_object(data,space,mask=''):
                compressed=zlib.compress(data)
                header=f'<< /Type /XObject /Subtype /Image /Width {rw} /Height {rh} /ColorSpace /{space} /BitsPerComponent 8 /Filter /FlateDecode {mask} /Length {len(compressed)} >>\nstream\n'.encode()
                return object(header+compressed+b'\nendstream')
            mask=image_object(alpha,'DeviceGray')
            ref=image_object(rgb,'DeviceRGB',f'/SMask {mask} 0 R')
            name=f'Im{len(images)}';images.append((name,ref))
            commands.append(f'{n(item.width)} 0 0 {n(-item.height)} {n(item.x)} {n(item.y+item.height)} cm /{name} Do')
            commands.append('Q');continue
        if isinstance(item,Text):
            if item.style.get('background'):
                from ..typography import text_bounds
                x,y,w,h=text_bounds(item.text,item.style);a=math.radians(item.style.get('rotation',0));c,s=math.cos(a),math.sin(a)
                points=[(item.x+u*c-v*s,item.y+u*s+v*c) for u,v in ((x-3,y-3),(x+w+3,y-3),(x+w+3,y+h+3),(x-3,y+h+3))]
                commands+=paint(dict(fill=item.style['background'],opacity=item.style.get('opacity',1)),path_commands([points],True))
            geometry=outlined(item)
        elif isinstance(item,Rect):geometry=[' '.join(n(v) for v in (item.x,item.y,item.width,item.height))+' re']
        elif isinstance(item,Circle):
            k=.5522847498307936;r=item.r;x=item.x;y=item.y
            geometry=[f'{n(x+r)} {n(y)} m']
            for angle in (0,math.pi/2,math.pi,3*math.pi/2):
                a=(x+r*math.cos(angle),y+r*math.sin(angle));b=(x+r*math.cos(angle+math.pi/2),y+r*math.sin(angle+math.pi/2))
                p=(a[0]-k*r*math.sin(angle),a[1]+k*r*math.cos(angle));q=(b[0]+k*r*math.sin(angle+math.pi/2),b[1]-k*r*math.cos(angle+math.pi/2))
                geometry.append(' '.join(n(v) for pt in (p,q,b) for v in pt)+' c')
            geometry.append('h')
        else:geometry=path_commands(item.paths,item.closed)
        commands+=paint(item.style,geometry,isinstance(item,Text));commands.append('Q')
    content=object(stream(('\n'.join(commands)+'\n').encode('ascii')))
    from ..typography import FONTS
    notice=(FONTS/'LICENSE_DEJAVU').read_bytes() if (FONTS/'LICENSE_DEJAVU').exists() else (FONTS/'LICENSE').read_bytes()
    notice_ref=object(stream(notice).replace(b'<< /Length',b'<< /Type /EmbeddedFile /Subtype /text#2Fplain /Length',1));file_ref=object(f'<< /Type /Filespec /F (DejaVu-license.txt) /EF << /F {notice_ref} 0 R >> >>'.encode())
    names=f'(DejaVu-license.txt) {file_ref} 0 R'
    if scene._material_notices:
        import json
        content_notice=json.dumps(scene._material_notices,ensure_ascii=True,sort_keys=True).encode('utf8')
        material_ref=object(stream(content_notice).replace(b'<< /Length',b'<< /Type /EmbeddedFile /Subtype /application#2Fjson /Length',1))
        material_file=object(f'<< /Type /Filespec /F (Material-provenance.json) /EF << /F {material_ref} 0 R >> >>'.encode())
        names+=f' (Material-provenance.json) {material_file} 0 R'
    objects[0]=f'<< /Type /Catalog /Pages 2 0 R /Names << /EmbeddedFiles << /Names [{names}] >> >> >>'.encode()
    objects[1]=b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>'
    resources=' '.join(f'/{name} {ref} 0 R' for name,ref in states.values())
    image_resources=(' /XObject << '+' '.join(f'/{name} {ref} 0 R' for name,ref in images)+' >>') if images else ''
    objects[2]=f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {n(scene.width*ratio)} {n(scene.height*ratio)}] /Resources << /ExtGState << {resources} >>{image_resources} >> /Contents {content} 0 R >>'.encode()
    info=object(b'<< /Producer (Azimlib independent PDF writer) /Subject (Vector text outlines; DejaVu notice attached) >>')
    if _objects:return tuple(objects)
    out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
    for index,data in enumerate(objects,1):
        offsets.append(len(out));out+=f'{index} 0 obj\n'.encode()+data+b'\nendobj\n'
    start=len(out);out+=f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    for offset in offsets[1:]:out+=f'{offset:010d} 00000 n \n'.encode()
    out+=f'trailer\n<< /Size {len(offsets)} /Root 1 0 R /Info {info} 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    value=bytes(out)
    if path_or_stream is not None:
        if hasattr(path_or_stream,'write'):path_or_stream.write(value)
        else:FilePath(path_or_stream).write_bytes(value)
    return value


def render_pdf_pages(pages):
    """Serialize/rebase only object dictionaries produced by our own writer.

    Binary image/notice/content streams are kept byte for byte. This is not a
    parser for arbitrary third-party PDFs. Each page retains its attached notices.
    """
    import re
    if not 1<=len(pages)<=256:raise ValueError('Require 1..256 own PDF pages')
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',None];kids=[]
    for page in pages:
        if len(page)<4 or b'/Type /Page ' not in page[2]:raise ValueError('Not an own page object bundle')
        start=len(objects);mapping={old:start+old for old in range(1,len(page)+1)}
        def remap(match):
            old=int(match.group(1))
            if old not in mapping:raise ValueError('PDF reference is outside page objects')
            return f'{mapping[old]} 0 R'.encode()
        for data in page:
            header,marker,stream=data.partition(b'\nstream\n')
            objects.append(re.sub(rb'(?<![0-9])([0-9]+) 0 R',remap,header)+marker+stream)
        # Replace the page parent; its original single-page catalog/tree remain
        # harmless private objects so all notice/image references stay intact.
        index=start+2
        objects[index]=objects[index].replace(f'/Parent {mapping[2]} 0 R'.encode(),b'/Parent 2 0 R')
        kids.append(mapping[3])
    objects[1]=('<< /Type /Pages /Kids ['+' '.join(f'{k} 0 R' for k in kids)+f'] /Count {len(kids)} >>').encode()
    # Surface every per-page catalog's EmbeddedFiles through the final catalog.
    names=[]
    for i,page in enumerate(pages):
        # Original catalogs list only controlled filenames and object references.
        start=2+sum(len(p) for p in pages[:i]);catalog=objects[start]
        match=re.search(rb'/Names \[([^]]*)\]',catalog)
        if match:
            entries=match.group(1)
            entries=re.sub(rb'\(([^)]*)\)',lambda m:b'(page-'+str(i+1).encode()+b'-'+m.group(1)+b')',entries)
            names.append(entries)
    if names:objects[0]=b'<< /Type /Catalog /Pages 2 0 R /Names << /EmbeddedFiles << /Names ['+b' '.join(names)+b'] >> >> >>'
    out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
    for index,data in enumerate(objects,1):
        offsets.append(len(out));out+=f'{index} 0 obj\n'.encode()+data+b'\nendobj\n'
    start=len(out);out+=f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    for offset in offsets[1:]:out+=f'{offset:010d} 00000 n \n'.encode()
    out+=f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    return bytes(out)
