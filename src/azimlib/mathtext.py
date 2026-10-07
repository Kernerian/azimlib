"""Small independent expression layout. No TeX, eval, external parser or shaping.

Supports inline $...$, groups, superscripts/subscripts, Greek letters,
fractions and square roots. Unknown commands and malformed expressions fail.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class MathLayout:
    width: float
    top: float
    bottom: float
    runs: tuple  # text, x, baseline, size
    rules: tuple # x1,y1,x2,y2,width

COMMANDS=dict(zip(('alpha beta gamma delta epsilon theta lambda mu pi rho sigma phi omega Gamma Delta Theta Lambda Pi Sigma Phi Omega').split(),
                 'αβγδεθλμπρσφωΓΔΘΛΠΣΦΩ'))
COMMANDS.update(times='×',cdot='·',pm='±',leq='≤',geq='≥',neq='≠',infty='∞',degree='°')

def has_math(text):
    count=len(re.findall(r'(?<!\\)\$',str(text)))
    return count>=2 and count%2==0

def layout(text,style):
    from .typography import _plain_text_width as text_width,_plain_text_line_metrics as text_line_metrics
    text=str(text)
    if len(text)>4096:raise ValueError('Math expression exceeds 4096 characters')
    def plain(value,size):
        opts=dict(style,font_size=size);a,d=text_line_metrics(value,opts)
        return MathLayout(text_width(value,opts),-a,d,((value,0.,0.,size),),())
    def shifted(box,x=0,y=0):
        return [(t,px+x,py+y,s) for t,px,py,s in box.runs],[(a+x,b+y,c+x,d+y,w) for a,b,c,d,w in box.rules]
    def join(boxes):
        x=0.;top=bottom=0.;runs=[];rules=[]
        for box in boxes:
            r,l=shifted(box,x);runs+=r;rules+=l;top=min(top,box.top);bottom=max(bottom,box.bottom);x+=box.width
        return MathLayout(x,top,bottom,tuple(runs),tuple(rules))
    size=style.get('font_size',12)
    def parse(expression):
        pos=0
        def group(s,depth):
            nonlocal pos
            if depth>16:raise ValueError('Math nesting exceeds 16')
            if pos>=len(expression):raise ValueError('Missing math operand')
            if expression[pos]=='{':
                pos+=1;box=sequence(s,depth+1,True)
                if pos>=len(expression) or expression[pos]!='}':raise ValueError('Unclosed math group')
                pos+=1;return box
            char=expression[pos];pos+=1
            if char in '}^_':raise ValueError('Unexpected math token')
            if char=='\\':
                m=re.match('[a-zA-Z]+',expression[pos:])
                if not m:raise ValueError('Require a named math command')
                command=m[0];pos+=len(command)
                if command=='frac':
                    a=group(s*.8,depth+1);b=group(s*.8,depth+1);w=max(a.width,b.width)+s*.3
                    ay=-s*.2-a.bottom;by=s*.2-b.top
                    ar,al=shifted(a,(w-a.width)/2,ay);br,bl=shifted(b,(w-b.width)/2,by)
                    return MathLayout(w,ay+a.top,by+b.bottom,tuple(ar+br),tuple(al+bl+[(0,0,w,0,s*.06)]))
                if command=='sqrt':
                    b=group(s,depth+1);a=plain('√',s);r,l=shifted(b,a.width)
                    return MathLayout(a.width+b.width,min(a.top,b.top)-s*.08,max(a.bottom,b.bottom),a.runs+tuple(r),a.rules+tuple(l)+((a.width,b.top-s*.04,a.width+b.width,b.top-s*.04,s*.05),))
                if command not in COMMANDS:raise ValueError(f'Unsupported math command: {command}')
                char=COMMANDS[command]
            return plain(char,s)
        def sequence(s,depth,stop=False):
            nonlocal pos
            boxes=[]
            while pos<len(expression) and expression[pos]!='}':
                base=group(s,depth);scripts={}
                while pos<len(expression) and expression[pos] in '^_':
                    token=expression[pos];pos+=1
                    if token in scripts:raise ValueError('Duplicate math script')
                    scripts[token]=group(s*.7,depth+1)
                if scripts:
                    runs=list(base.runs);rules=list(base.rules);top=base.top;bottom=base.bottom;extra=0
                    for token,b in scripts.items():
                        y=-s*.6 if token=='^' else s*.35
                        r,l=shifted(b,base.width,y);runs+=r;rules+=l
                        top=min(top,b.top+y);bottom=max(bottom,b.bottom+y);extra=max(extra,b.width)
                    base=MathLayout(base.width+extra,top,bottom,tuple(runs),tuple(rules))
                boxes.append(base)
            if not stop and pos<len(expression):raise ValueError('Unexpected closing math group')
            return join(boxes)
        return sequence(size,0)
    boxes=[];parts=re.split(r'(?<!\\)\$',text)
    if len(parts)%2==0:raise ValueError('Unclosed inline math delimiter')
    for i,part in enumerate(parts):boxes.append(parse(part) if i%2 else plain(part.replace(r'\$','$'),size))
    return join(boxes)

def primitives(item):
    """Expand a single expression before backend rendering and layout measurement."""
    import math
    from .scene import Text,Path
    b=layout(item.text,item.style);style=dict(item.style)
    dx=-{'start':0,'middle':.5,'end':1}[style.get('anchor','start')]*b.width
    dy={'top':-b.top,'middle':-(b.top+b.bottom)/2,'bottom':-b.bottom,'alphabetic':0}[style.get('baseline','alphabetic')]
    a=math.radians(style.get('rotation',0));c,s=math.cos(a),math.sin(a)
    def point(x,y):return item.x+(x+dx)*c-(y+dy)*s,item.y+(x+dx)*s+(y+dy)*c
    for text,x,y,size in b.runs:
        if text:yield Text(*point(x,y),text,dict(style,font_size=size,anchor='start',baseline='alphabetic',rotation_mode='anchor'),item.clip)
    for x,y,u,v,w in b.rules:
        yield Path([[point(x,y),point(u,v)]],False,dict(stroke=style.get('fill','#172b38'),stroke_width=w,opacity=style.get('opacity',1)),item.clip)
