"""XML-based audio preview. The pitch is an illustrative video, never packaged."""
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from generate_skins import ROOT,TOKENS
from render_previews import text_box,font


def rgba(token):
    raw=TOKENS.get(token,token.lstrip('#'))
    return tuple(bytes.fromhex(raw[-6:]))+(255-int(raw[:2],16) if len(raw)==8 else 255,)


def render(profile,focus='config',page='audio',subtitle_state='active'):
    root=ET.parse(ROOT/'skins'/profile/'skin.xml').getroot()
    screen=root.find("screen[@name='AudioSelection']")
    ox,oy=map(int,screen.get('position').split(','))
    image=Image.new('RGBA',(1920,1080),'#476746')
    draw=ImageDraw.Draw(image)
    for i in range(8):draw.rectangle((i*240,0,i*240+239,1079),fill='#506F46' if i%2 else '#4B6941')
    draw.line((0,190,1920,55),fill='#8A9A72',width=5)
    draw.line((0,820,1920,1010),fill='#8A9A72',width=5)
    draw.ellipse((650,330,1180,760),outline='#8A9A72',width=5)
    def ink(box,value,points=28,family='Regular',align='left',fill='audio_ink',valign='center'):
        text_box(draw,box,value,points,rgba(fill),align,family=family,valign=valign,no_wrap=True)
    for node in screen:
        if node.tag not in ('widget','eLabel','ePixmap'):continue
        x,y=map(int,node.get('position','0,0').split(','));w,h=map(int,node.get('size','0,0').split(','));x+=ox;y+=oy
        source,name=node.get('source',''),node.get('name','')
        if page=='subtitles' and source.startswith('key_'):
            if source!='key_red' or subtitle_state!='active':continue
        if name in ('switchdescription','key_left','key_right') and focus=='config':continue
        if node.get('backgroundColor') and node.get('transparent')!='1':
            overlay=Image.new('RGBA',image.size)
            ImageDraw.Draw(overlay).rectangle((x,y,x+w-1,y+h-1),fill=rgba(node.get('backgroundColor')))
            image=Image.alpha_composite(image,overlay);draw=ImageDraw.Draw(image)
        if node.tag=='ePixmap' or node.get('pixmap'):
            with Image.open(ROOT/'skins'/node.get('pixmap')) as asset:image.alpha_composite(asset.convert('RGBA'),(x,y))
            draw=ImageDraw.Draw(image);continue
        if node.get('render')=='MetrixNEOTrackIcon':
            name='subtitle-icon' if page=='subtitles' else 'audio-speaker'
            with Image.open(ROOT/'skins'/profile/'assets'/(name+'.png')) as asset:image.alpha_composite(asset.convert('RGBA'),(x,y))
            draw=ImageDraw.Draw(image);continue
        if name=='config':
            values=[('AC3 downmix','On'),('AAC downmix','On'),('Bluetooth Audio','Off'),('Audio Channel','stereo'),('3D Surround','Off'),('Auto Volume Level','Off'),('IPAudio Pro','')]
            if page=='subtitles':values=[('Menu rapide des sous-titres','')] if subtitle_state=='active' else []
            row=int(node.get('itemHeight'))
            for i,(label,value) in enumerate(values):
                yy=y+i*row
                if focus=='config' and i==(0 if page=='subtitles' else 6):
                    with Image.open(ROOT/'skins'/node.get('selectionPixmap')) as selected:image.alpha_composite(selected.convert('RGBA'),(x,yy))
                    draw=ImageDraw.Draw(image)
                ink((x+15,yy,w-30,row),label)
                ink((x+570,yy,w-585,row),value,align='right')
        elif source=='streams':
            values=[('1','AAC','English','X')]
            if page=='subtitles':values=[] if subtitle_state=='empty' else [('100','DVB','Français','X' if subtitle_state=='active' else ''),('888','teletext','English','')]
            for i,parts in enumerate(values):
                yy=y+48*i
                if focus=='streams' and i==0:
                    with Image.open(ROOT/'skins'/node.get('selectionPixmap')) as selected:image.alpha_composite(selected.convert('RGBA'),(x,yy))
                    draw=ImageDraw.Draw(image)
                for value,(dx,cw) in zip(parts,((10,90),(114,170),(300,570),(918,60))):ink((x+dx,yy,cw,48),value)
        elif name=='switchdescription':ink((x,y,w,h),'Basculer entre choix audio ou sélection des sous-titres' if page=='subtitles' else '◀  Audio / Subtitles  ▶',20)
        elif node.tag=='eLabel' or source in ('Title','global.CurrentTime'):
            converter=node.find('convert')
            value=node.get('text','')
            if source=='Title':value='Sélection des sous-titres' if page=='subtitles' else 'Select audio track'
            elif source=='global.CurrentTime':value={'Format:%A':'Sunday','Format:%d. %b.':'25. Oct.','Format:%H:%M':'20:05'}[converter.text]
            family,points=node.get('font','Regular;28').split(';')
            ink((x,y,w,h),value,int(points),family,node.get('halign','left'),node.get('foregroundColor','audio_ink'),node.get('valign','center'))
    caption='SIMULATION XML · vidéo et pistes illustratives · aucun accès au Vu+' if page=='subtitles' else 'SIMULATION XML · vidéo illustrative · valeurs et IPAudio Pro d’exemple · aucun accès au Vu+'
    ink((35,1030,1850,32),caption,20,align='center')
    return image.convert('RGB')


if __name__=='__main__':
    output=ROOT/'previews/review';output.mkdir(exist_ok=True)
    for profile in ('MetrixNEO','MetrixNEOAdvanced'):
        for focus in ('config','streams'):render(profile,focus).save(output/(profile+'-AudioSelection'+('-tracks' if focus=='streams' else '')+'.png'),optimize=True)
