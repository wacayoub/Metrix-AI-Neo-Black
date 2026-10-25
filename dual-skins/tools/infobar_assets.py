"""Deterministic antialiased pictograms matching the two approved infobar styles."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[1]
INK="#DDE5EC"
MUTED="#72818C"
GOLD="#EFC643"
CYAN="#12BCE2"
RED="#ED3246"


def face(size,bold=False):
    name="LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"
    paths=[ROOT/".upstream/enigma2/data/fonts"/name,Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),Path('/usr/share/fonts/truetype/liberation2')/name,Path('/usr/share/fonts/truetype/dejavu')/("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")]
    for path in paths:
        if path.is_file():return ImageFont.truetype(str(path),size)
    return ImageFont.load_default(size=size)


def draw_icon(name, advanced=False):
    # Four samples per native pixel; only code/font geometry, no reference crops.
    s=4
    width,height=(104,48) if name.startswith("audio-") else (64,48) if name.startswith(("resolution-","hdr-")) else (78,48) if name.startswith("codec-") else (106,48) if name.startswith("source-") else (48,48)
    if name.startswith("source-") and not advanced:width=64
    im=Image.new("RGBA",(width*s,height*s))
    d=ImageDraw.Draw(im)
    def line(points,fill=INK,w=2):d.line(tuple((int(x*s),int(y*s)) for x,y in points),fill=fill,width=w*s,joint="curve")
    def ellipse(box,fill=None,outline=None,w=2):d.ellipse(tuple(round(v*s) for v in box),fill=fill,outline=outline,width=w*s)
    def frame(color=MUTED):d.rounded_rectangle((s,5*s,(width-1)*s,43*s),2*s,outline=color,width=s)
    def label(value,x,y,size=21,bold=False,fill=INK,anchor="mm"):
        if anchor=="mm":
            available=max(1,2*min(x-4,width-4-x))*s
            while size>10 and face(size*s,bold).getlength(value)>available:
                size-=1
        d.text((x*s,y*s),value,font=face(size*s,bold),fill=fill,anchor=anchor,stroke_width=0)
    if name.startswith(("resolution-","hdr-","codec-")):
        text=name.split('-',1)[1].upper().replace("H264","H.264")
        color=GOLD if name.startswith("resolution-") or (name.startswith("hdr-") and not advanced) else INK
        frame(GOLD if color==GOLD else MUTED)
        label(text,width/2,24,20 if len(text)>4 else 23,name.startswith("resolution-"),color)
    elif name.startswith("audio-"):
        frame()
        if name in ("audio-aac","audio-dts"):
            label(name.split('-')[1].upper(),width/2,24,23,True)
            return im.resize((width,height),Image.Resampling.LANCZOS)
        # Two opposed D glyphs, each with its proper open counter.
        letter=Image.new("RGBA",(18*s,30*s))
        ImageDraw.Draw(letter).text((0,15*s),"D",font=face(25*s,True),fill=INK,anchor="lm")
        im.alpha_composite(letter,(6*s,9*s))
        im.alpha_composite(ImageOps.mirror(letter),(23*s,9*s))
        text={"audio-ac3":"AC3","audio-ddplus":"DD+","audio-aac":"AAC","audio-dts":"DTS","audio-atmos":"Dolby"}[name]
        label(text,68,21 if name.endswith("atmos") else 24,16 if name.endswith("atmos") else 20,True)
        if name.endswith("atmos"):label("Atmos",58,36,12)
    elif name=="lock":
        frame()
        d.arc((16*s,9*s,32*s,28*s),180,360,fill=INK,width=3*s)
        d.rounded_rectangle((13*s,21*s,35*s,37*s),2*s,fill=INK)
        ellipse((22,25,26,29),fill=(0,0,0,0))
        d.rectangle((23*s,28*s,25*s,33*s),fill=(0,0,0,0))
    elif name.startswith("source-"):
        if not advanced and not name.endswith("sat"):
            frame()
            label(name.split('-')[1].upper(),width/2,25,20)
        elif name.endswith("sat"):
            # Dish rim follows a NW-SE diagonal; its concave face opens NE.
            # A separate feed, arm, pedestal and waves stay readable at 720p.
            offset = 0 if advanced else -3
            def shift(points):return tuple((x+offset,y) for x,y in points)
            points=[]
            for i in range(25):
                t=i/24
                points.append((10+22*t-8*math.sin(math.pi*t)+offset,
                               11+22*t+8*math.sin(math.pi*t)))
            d.polygon(tuple((round(x*s),round(y*s)) for x,y in points),fill=INK)
            line(shift(((10,11),(32,33))),w=2)
            line(shift(((19,29),(16,40),(34,40))),w=2)
            line(shift(((28,28),(36,14))),w=2)
            ellipse((33+offset,10,38+offset,15),fill=INK,w=1)
            d.arc(((32+offset)*s,3*s,(46+offset)*s,19*s),270,348,fill=INK,width=s)
            d.arc(((31+offset)*s,0,(51+offset)*s,24*s),270,348,fill=INK,width=s)
            if not advanced:label("SAT",49,25,14)
        else:
            d.rounded_rectangle((9*s,12*s,37*s,33*s),2*s,outline=INK,width=2*s)
            line(((23,33),(23,39),(34,39),(13,39)))
        if advanced:label(name.split('-')[1].upper(),74,25,18)
    elif name=="record":
        if advanced:ellipse((11,11,37,37),fill=RED)
        else:
            ellipse((5,5,43,43),outline=RED,w=3)
            ellipse((12,12,36,36),outline=RED,w=2)
    elif name in ("timeshift","seekback","seekforward"):
        color=RED if name=="seekback" else CYAN
        d.arc((6*s,6*s,42*s,42*s),35,335,fill=color,width=3*s)
        d.polygon(tuple((x*s,y*s) for x,y in ((35,7),(43,15),(32,17))),fill=color)
        if name=="timeshift":
            line(((24,14),(24,25),(30,28)),color,w=2)
            line(((34,34),(43,34)),color,w=2)
            line(((39,30),(39,38)),color,w=2)
        else:
            label("−" if name=="seekback" else "+",24,24,21,True,color)
    return im.resize((width,height),Image.Resampling.LANCZOS)


def build_icons(folder,advanced=False):
    from Components.MetrixNEO.infobar_icons import ICONS
    names=sorted({name for group in ICONS.values() for name in group.values()}|{"record","timeshift","seekback","seekforward"})
    for name in names:
        draw_icon(name,advanced).save(folder/("infobar-icon-"+name+".png"),optimize=True)
    return names


def build_guide(path):
    from Components.MetrixNEO.infobar_icons import ICONS
    names=sorted({name for group in ICONS.values() for name in group.values()}|{"record","timeshift","seekback","seekforward"})
    sheet=Image.new("RGB",(960,1020),"#031323")
    d=ImageDraw.Draw(sheet)
    for section,advanced in enumerate((False,True)):
        top=section*480
        d.text((24,top+16),"Metrix NEO Advanced" if advanced else "Metrix NEO",font=face(26,True),fill=INK)
        for i,name in enumerate(names):
            x,y=24+(i%6)*155,top+68+(i//6)*94
            asset=draw_icon(name,advanced)
            sheet.paste(asset,(x+(130-asset.width)//2,y),asset)
            d.text((x+65,y+55),name,font=face(12),fill="#A7B6C8",anchor="mt")
    d.text((24,980),"Icônes pilotées par les données réelles. Seekback / seekforward : ressources, sans ajout de commande.",font=face(16),fill="#A7B6C8")
    sheet.save(path,optimize=True)
