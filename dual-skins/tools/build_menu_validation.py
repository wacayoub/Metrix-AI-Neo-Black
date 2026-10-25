"""Offline review gallery and paired conversation images; no runtime changes."""
import base64
import argparse
import hashlib
import html
import io
import json
import re
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
VISUAL=ROOT/'build/conversation-previews'


def encode_image(path,reduced=False):
    raw=path.read_bytes()
    with Image.open(path) as source:
        rgba=source.convert('RGBA')
        assert rgba.size==(1920,1080)
        if reduced:rgba=rgba.resize((960,540),Image.Resampling.LANCZOS)
        stream=io.BytesIO()
        rgba.save(stream,format='WEBP',lossless=True,quality=80,method=4,exact=True)
        compressed=stream.getvalue()
        with Image.open(io.BytesIO(compressed)) as decoded:
            assert decoded.convert('RGBA').tobytes()==rgba.tobytes()
    payload,mime=(compressed,'webp') if reduced or len(compressed)<len(raw) else (raw,'png')
    return 'data:image/'+mime+';base64,'+base64.b64encode(payload).decode('ascii'),hashlib.sha256(raw).hexdigest()


def detail(key):
    return {'ChannelContextMenu':[220,115,1480,850], 'ChoiceBox':[290,145,1340,790],
            'MessageBox':[400,260,1120,560], 'InputBox':[310,395,1300,290],
            'Volume':[660,70,600,80], 'Mute':[835,70,250,66],
            'InfoBar':[0,680,1920,400], 'SecondInfoBar':[0,430,1920,650]}.get(key,[24,180,1872,890])


def fragment(template,category,title,items):
    config=dict(category=category,defaultScreen=next(iter(items)),defaultView='full',screens=items)
    values={'__ROOT__':'metrix-review-'+category,'__TITLE__':html.escape(title),
            '__OPTIONS__':''.join('<option value="'+html.escape(key,quote=True)+'">'+html.escape(item['label'])+'</option>' for key,item in items.items()),
            '__CONFIG__':json.dumps(config,ensure_ascii=False,separators=(',',':'))}
    for key,value in values.items():template=template.replace(key,value)
    if len(items)==1:
        template=re.sub(r'<label class="form-label">Écran\s*<select[^>]*data-screen[^>]*>.*?</select>\s*</label>','<input type="hidden" data-screen value="'+next(iter(items))+'">',template,flags=re.S)
    return template


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-inline',action='store_true',help='Refresh the local gallery without rewriting conversation comparisons')
    parser.add_argument('--remaining',action='store_true',help='Exclude the separately reviewed audio, subtitles and timers from comparisons')
    parser.add_argument('--visual-dir',type=Path,default=VISUAL,help='Output directory for conversation comparisons')
    args=parser.parse_args()
    if not args.no_inline:args.visual_dir.mkdir(parents=True,exist_ok=True)
    report=json.loads((ROOT/'reports/menu-validation.json').read_text(encoding='utf-8'))
    template=(ROOT/'tools/menu-pairs.template.html').read_text(encoding='utf-8')
    groups={}
    for screen in report['screens']:groups.setdefault(screen['group'],[]).append(screen)
    output=[];nav=[];panels=[];all_hashes={}
    approved={'AudioSelection','SubtitleSelection','TimerOverview','RecordTimerOverview','SchedulerOverview','ConflictTimerOverview'}
    for group,screens in groups.items():
        title=screens[0]['group_title'];chunks=[];chunk={};hashes={}
        nav.append('<a href="#'+group+'">'+html.escape(title)+'</a>')
        options=[];views=[]
        for i,screen in enumerate(screens):
            key=screen['key'];caption=screen['caption']
            if key=='MovieSelection':caption+=' · touches par défaut, modifiables'
            reduced=key=='ChannelContextMenu'
            if reduced:caption+=' · comparaison réduite à 960 × 540 ; original Full HD dans la galerie'
            item=dict(label=screen['label'],detail=detail(key),caption=caption)
            figures=[]
            for side,profile,label in [('neo','MetrixNEO','Metrix NEO'),('advanced','MetrixNEOAdvanced','Metrix NEO Advanced')]:
                relative=screen['images'][profile]
                item[side]=None
                if relative:
                    path=ROOT/relative;item[side],digest=encode_image(path,reduced)
                    hashes[relative]=digest;all_hashes[relative]=digest
                    local=path.relative_to(ROOT/'previews').as_posix()
                    content='<a href="'+html.escape(local,quote=True)+'"><img loading="lazy" src="'+html.escape(local,quote=True)+'" alt="'+html.escape(label+' · '+screen['label'],quote=True)+'"></a>'
                else:content='<p>Catégorie réservée à Advanced.</p>'
                figures.append('<figure><figcaption>'+label+'</figcaption>'+content+'</figure>')
            if not args.remaining or key not in approved:
                candidate={**chunk,key:item}
                if len(fragment(template,'validation-'+group,title,candidate).encode('utf-8'))>=950000 and chunk:
                    chunks.append(chunk);chunk={key:item}
                else:chunk=candidate
            options.append('<option value="'+html.escape(key,quote=True)+'">'+html.escape(screen['label'])+'</option>')
            views.append('<div data-key="'+html.escape(key,quote=True)+'"'+(' hidden' if i else '')+'><p>'+html.escape(caption)+'</p><div class="pair">'+''.join(figures)+'</div></div>')
        if chunk:chunks.append(chunk)
        panels.append('<section id="'+group+'"><h2>'+html.escape(title)+'</h2><label>Écran <select data-group="'+group+'">'+''.join(options)+'</select></label>'+''.join(views)+'</section>')
        if args.no_inline:continue
        for i,items in enumerate(chunks):
            suffix=('-'+str(i+1)) if len(chunks)>1 else ''
            category=('remaining-' if args.remaining else 'validation-')+group+suffix
            label=('Enregistrements' if args.remaining and group=='programmations' else title)+(' · '+str(i+1)+'/'+str(len(chunks)) if len(chunks)>1 else '')
            content=fragment(template,category,label,items)
            path=args.visual_dir/('metrix-'+category+'.html')
            assert len(content.encode('utf-8'))<1000000,(category,'budget exceeded')
            path.write_text(content,encoding='utf-8')
            assert path.read_text(encoding='utf-8')==content
            output.append(dict(category=category,file=str(path),bytes=path.stat().st_size,screens=len(items),lossless_encoded_pixels=True,reduced_screens=[key for key in items if key=='ChannelContextMenu'],source_sha256=hashes))
    page=(ROOT/'tools/menu-validation.template.html').read_text(encoding='utf-8').replace('__NAV__',''.join(nav)).replace('__PANELS__',''.join(panels))
    (ROOT/'previews/validation-menus.html').write_text(page,encoding='utf-8')
    if not args.no_inline:(ROOT/('build/review/remaining-menu-widgets.json' if args.remaining else 'build/review/menu-validation-widgets.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'reports/menu-validation-images.json').write_text(json.dumps(dict(views=len(report['screens']),native_identities=report['native_identities'],original_gallery_size=[1920,1080],inline_reduced_screens=['ChannelContextMenu'],lossless_encoded_pixels=True,source_sha256=all_hashes,receiver_access=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:item[k] for k in ('category','bytes','screens')} for item in output],indent=2))


if __name__=='__main__':main()
