"""Local style sheets and stacked contexts; only supported rcParams apply."""
import ast
from pathlib import Path
from os import PathLike
from collections.abc import Mapping
from contextlib import contextmanager
from .config import DEFAULTS,rcParams,rc_context,RcParams
from .cycles import cycler,Cycler,AZIM10

def _lighten(color):
    return "#"+"".join(f"{round(int(color[i:i+2],16)*.65+255*.35):02x}" for i in (1,3,5))


library={'default':dict(DEFAULTS),
         'grayscale':{'axes.facecolor':'white','grid.color':'#b0b0b0','text.color':'black',
                      'axes.prop_cycle':cycler(color=['black','#666666','#999999','#bbbbbb'])},
         'dark_background':{'figure.facecolor':'black','axes.facecolor':'black','axes.edgecolor':'white',
                            'axes.labelcolor':'white','text.color':'white','grid.color':'#666666',
                            'axes.prop_cycle':cycler(color=[_lighten(color) for color in AZIM10])}}
available=tuple(library)


def _literal(node):
    # Small AST interpreter: no eval, imports, attributes or arbitrary calls.
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='cycler':
        if any(key.arg is None for key in node.keywords):raise ValueError('Cycle unpacking is unsupported')
        return cycler(*[_literal(a) for a in node.args],**{k.arg:_literal(k.value) for k in node.keywords})
    if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Mult)):
        left,right=_literal(node.left),_literal(node.right)
        if not isinstance(left,Cycler) or not isinstance(right,Cycler):raise ValueError('Only cycle addition/product are supported')
        return left+right if isinstance(node.op,ast.Add) else left*right
    try:return ast.literal_eval(node)
    except (ValueError,TypeError) as exc:raise ValueError('Unsupported style expression') from exc


def _strip_comment(line):
    quote=None;escaped=False
    for i,char in enumerate(line):
        if escaped:escaped=False;continue
        if char=='\\' and quote:escaped=True;continue
        if char in ('"',"'"):
            if quote==char:quote=None
            elif quote is None:quote=char
        elif char=='#' and quote is None:return line[:i]
    return line


def read(path):
    """Read local UTF-8 rcParam sheets, quoted hex colors and safe cycler."""
    result={}
    for number,line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(),1):
        line=_strip_comment(line).strip()
        if not line:continue
        if ':' not in line:raise ValueError(f'{path}:{number}: expected key: value')
        key,text=(part.strip() for part in line.split(':',1))
        if not text:raise ValueError(f'{path}:{number}: missing value (quote hex colors)')
        if key in result:raise ValueError(f'{path}:{number}: duplicate rcParam {key}')
        try:
            if key=='axes.prop_cycle':value=_literal(ast.parse(text,mode='eval').body)
            else:
                try:value=ast.literal_eval(text)
                except (ValueError,SyntaxError):value=text
            checked=RcParams({key:value});result[key]=checked[key]
        except (ValueError,TypeError,KeyError,SyntaxError) as exc:
            raise ValueError(f'{path}:{number}: {exc}') from exc
    return result


def _resolve(spec):
    if isinstance(spec,Mapping):return dict(spec)
    if isinstance(spec,(str,PathLike)):
        if isinstance(spec,str) and spec in library:return dict(library[spec])
        path=Path(spec)
        if path.is_file():return read(path)
        raise ValueError(f'Unknown style or local file {spec!s}; available: {available}')
    raise TypeError('Style must be a name, mapping, local path or list of these')


def _stack(spec):
    result={}
    for item in spec if isinstance(spec,(list,tuple)) else [spec]:
        values=_resolve(item);RcParams(values);result.update(values)
    return result


def use(spec):rcParams.update(_stack(spec))

@contextmanager
def context(spec,after_reset=False):
    values=_stack(spec)
    if after_reset:values={**DEFAULTS,**values}
    with rc_context(values):yield
