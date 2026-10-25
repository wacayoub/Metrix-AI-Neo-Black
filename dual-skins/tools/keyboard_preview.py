"""Render the audited native French key map/rectangle builder without actions."""
import ast
import types
from PIL import ImageDraw
from generate_skins import ROOT,TOKENS
from render_previews import COLORS,text_box


def native_keys():
    path=ROOT/'.upstream/enigma2/lib/python/Screens/VirtualKeyBoard.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='VirtualKeyboard')
    init=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    owner=types.SimpleNamespace(SPACE='SPACEICON',green='ENTERICON')
    for wanted in ('footer','french'):
        node=next(n for n in init.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr==wanted for t in n.targets))
        setattr(owner,wanted,eval(compile(ast.Expression(node.value),str(path),'eval'),{'__builtins__':{}},{'self':owner}))
    method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='nativeKeyboardEntryComponent')
    colors=tuple(int(TOKENS[k],16) for k in ('secondary','selection','accent','foreground','red','green','yellow','blue'))
    env=dict(parameters={'VirtualKeyboardNativeColors':colors,'VirtualKeyboardNativeGeometry':(4,6,2)},
             MultiContentEntryRectangle=lambda **kw:dict(kind='rect',**kw),MultiContentEntryText=lambda **kw:dict(kind='text',**kw),
             RT_HALIGN_CENTER=1,RT_VALIGN_CENTER=2)
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),env)
    owner.keyboardWidth=14;owner.width=112;owner.height=60;owner.selectedKey=56;owner.index=0
    return [env['nativeKeyboardEntryComponent'](owner,row)[1:] for row in owner.french[0]]


def render(image,box):
    draw=ImageDraw.Draw(image);x,y,w,h=box
    for row,cells in enumerate(native_keys()):
        for cell in cells:
            dx,dy=cell['pos'];cw,ch=cell['size'];xx=x+dx;yy=y+row*60+dy
            assert dx+cw<=w and row*60+dy+ch<=h
            if cell['kind']=='rect':
                fill='#%06x'%(cell['backgroundColor']&0xffffff)
                border=cell.get('borderWidth',0)
                draw.rounded_rectangle((xx,yy,xx+cw-1,yy+ch-1),cell.get('cornerRadius',0),fill=fill,outline='#%06x'%(cell.get('borderColor',0)&0xffffff) if border else None,width=border or 1)
            else:text_box(draw,(xx,yy,cw,ch),cell['text'],15 if cell['font']==1 else 28,COLORS['foreground'],'center',valign='center',no_wrap=True)
