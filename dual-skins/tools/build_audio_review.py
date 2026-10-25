"""Paired audio review with both native focus states, without receiver access."""
import json
from build_menu_validation import ROOT,VISUAL,encode_image,fragment


def main():
    items={};hashes={}
    for key,label,suffix in [('config','Réglages audio sélectionnés',''),('streams','Piste audio sélectionnée','-tracks')]:
        item=dict(label=label,detail=[60,38,1802,976],caption='Simulation XML · vidéo et valeurs illustratives · IPAudio Pro seulement si fourni par une extension · langue réelle selon OpenATV')
        for side,profile in [('neo','MetrixNEO'),('advanced','MetrixNEOAdvanced')]:
            path=ROOT/'previews/review'/(profile+'-AudioSelection'+suffix+'.png')
            item[side],hashes[path.name]=encode_image(path)
        items[key]=item
    path=VISUAL/'metrix-audio-selection.html'
    content=fragment((ROOT/'tools/menu-pairs.template.html').read_text(encoding='utf-8'),'audio-selection','Sélection audio · les deux thèmes',items)
    path.write_text(content,encoding='utf-8')
    assert path.stat().st_size<1000000
    report=[dict(category='audio-selection',file=str(path),bytes=path.stat().st_size,screens=2,source_sha256=hashes,lossless_encoded_pixels=True)]
    (ROOT/'build/review/audio-review-widgets.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report[0],ensure_ascii=False,indent=2))


if __name__=='__main__':main()
