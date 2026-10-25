"""Side-by-side review of native timer overview states; no receiver access."""
import json
from build_menu_validation import ROOT,VISUAL,encode_image,fragment
from menu_review import native_preview

STATES=[('planned','Enregistrements planifiés','RecordTimerOverview','Une programmation terminée dans l’exemple rend Nettoyage disponible.'),
        ('running','Enregistrement en cours','RecordTimerOverview','La touche rouge devient Arrêter ; le basculement jaune est masqué dans cet exemple.'),
        ('disabled','Programmation désactivée','RecordTimerOverview','La touche jaune propose Activer pour l’élément sélectionné.'),
        ('completed','Programmation terminée','RecordTimerOverview','Le nettoyage concerne les programmations terminées, selon l’état natif.'),
        ('empty','Liste vide','RecordTimerOverview','Seul Ajouter est disponible dans cet exemple ; aucune programmation n’est créée.'),
        ('system','Planifications système','SchedulerOverview','Exemples de veille et réveil ; aucune action système exécutée.'),
        ('conflict','Conflit de programmations','ConflictTimerOverview','La touche bleue native propose Ignorer ; Ajouter n’existe pas dans cette fenêtre.')]


def main():
    items={};hashes={};output=ROOT/'previews/review';output.mkdir(exist_ok=True)
    for key,label,identity,caption in STATES:
        item=dict(label=label,detail=[24,165,1872,900],caption='Simulation XML · programmations et états d’exemple · '+caption)
        for side,profile in [('neo','MetrixNEO'),('advanced','MetrixNEOAdvanced')]:
            path=output/(profile+'-TimerReview-'+key+'.png')
            native_preview(profile,identity,identity,timer_state=key).save(path,optimize=True)
            item[side],hashes[path.name]=encode_image(path)
        items[key]=item
    path=VISUAL/'metrix-timer-selection.html'
    content=fragment((ROOT/'tools/menu-pairs.template.html').read_text(encoding='utf-8'),'timer-selection','Programmations · couleurs Metrix NEO',items)
    assert len(content.encode('utf-8'))<1000000
    path.write_text(content,encoding='utf-8')
    assert path.read_text(encoding='utf-8')==content
    report=[dict(category='timer-selection',file=str(path),bytes=path.stat().st_size,screens=len(items),source_sha256=hashes,lossless_encoded_pixels=True)]
    (ROOT/'build/review/timer-review-widgets.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[0][k] for k in ('category','bytes','screens')},ensure_ascii=False))


if __name__=='__main__':main()
