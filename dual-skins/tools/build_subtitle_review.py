"""Four illustrative native subtitle states, paired for both skins."""
import json
from build_menu_validation import ROOT,VISUAL,encode_image,fragment
from render_audio import render

STATES=[('active','Piste française active','streams','active','La marque X indique la piste active ; OK sur cette piste la désactive.'),
        ('inactive','Aucune piste active','streams','inactive','Les pistes restent disponibles ; aucune ne porte la marque X.'),
        ('empty','Aucun sous-titre disponible','streams','empty','Liste native vide : aucun sous-titre fourni dans cet exemple.'),
        ('config','Menu rapide sélectionné','config','active','Option native disponible lorsqu’une piste est active, selon le contexte.')]


def main():
    output=ROOT/'previews/review';output.mkdir(exist_ok=True)
    items={};hashes={}
    for key,label,focus,state,caption in STATES:
        item=dict(label=label,detail=[60,38,1802,976],caption='Simulation XML · vidéo et pistes d’exemple · '+caption)
        for side,profile in [('neo','MetrixNEO'),('advanced','MetrixNEOAdvanced')]:
            path=output/(profile+'-SubtitleSelection-'+key+'.png')
            render(profile,focus=focus,page='subtitles',subtitle_state=state).save(path,optimize=True)
            if key=='active':(output/(profile+'-SubtitleSelection.png')).write_bytes(path.read_bytes())
            item[side],hashes[path.name]=encode_image(path)
        items[key]=item
    path=VISUAL/'metrix-subtitle-selection.html'
    content=fragment((ROOT/'tools/menu-pairs.template.html').read_text(encoding='utf-8'),'subtitle-selection','Sous-titres · couleurs Metrix NEO',items)
    path.write_text(content,encoding='utf-8')
    assert path.stat().st_size<1000000
    assert path.read_text(encoding='utf-8')==content
    report=[dict(category='subtitle-selection',file=str(path),bytes=path.stat().st_size,screens=4,source_sha256=hashes,lossless_encoded_pixels=True)]
    (ROOT/'build/review/subtitle-review-widgets.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[0][k] for k in ('category','bytes','screens')},ensure_ascii=False))


if __name__=='__main__':main()
