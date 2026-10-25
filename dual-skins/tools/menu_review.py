"""Offline secondary-screen review. XML chrome, illustrative native rows only.

Never imports Enigma2, executes callbacks, connects to a receiver or changes a
skin. Installed plugins, schedules, files and hardware values are not read.
"""
import ast
import html
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from render_previews import ROOT, COLORS, color, font, text_box, sample_text

PROFILES=("MetrixNEO","MetrixNEOAdvanced")
OUT=ROOT/"previews/review"
# key, label, native identity, aliases, approved PNG (or None)
GROUPS=[
 ("navigation","Menus et plugins",[
  ("menu_mainmenu","Menu principal","menu_mainmenu",["Menumainmenu"],"menu_mainmenu"),
  ("Menu","Menu natif complet / sous-menu","Menu",[],None),
  ("PluginBrowser-list","Plugins · liste","PluginBrowser",[],None),
  ("PluginBrowser-grid","Plugins · grille","PluginBrowser",[],None)]),
 ("contextes","Contextes et confirmations",[
  ("ChannelContextMenu","Menu contextuel · 15 lignes","ChannelContextMenu",["EventViewContextMenu","EventViewContextMenuChoiceBox"],"ChannelContextMenu"),
  ("ChoiceBox","Choix d’une action","ChoiceBox",[],None),
  ("MessageBox","Confirmation / message","MessageBox",[],None)]),
 ("preferences","Paramètres et préférences",[
  ("Setup","Paramètres système · extrait audio","Setup",[],"Setup"),
  *[("MetrixNEOSettings"+("-"+c if c else ""),label,"MetrixNEOSettings",[],"MetrixNEOSettings"+("-"+c if c else "")) for c,label in (("","Présentation"),("weather","Météo"),("images","Images EPG et logos d’équipes"),("smart","Smart EPG · Advanced"),("diagnostics","Diagnostics · Advanced"),("cache","Cache"))]]),
 ("programmations","Programmations et enregistrements",[
  *[(key,label,key,[],None) for key,label in (("TimerOverview","Programmations · vue générale"),("RecordTimerOverview","Programmations d’enregistrement"),("SchedulerOverview","Planifications système"),("ConflictTimerOverview","Conflit de programmations"),("MovieSelection","Enregistrements / films"))]]),
 ("utilitaires","Audio, sous-titres et saisie",[
  ('SubtitleSelection','Sous-titres · sélection native','AudioSelection',[],None),
  *[(key,label,key,["VirtualKeyBoard"] if key=="VirtualKeyboard" else [],None) for key,label in (("AudioSelection","Pistes audio"),("Subtitles","Sous-titres · repli configuration"),("InputBox","Saisie d’un texte"),("VirtualKeyboard","Clavier virtuel"),("Console","Console · texte illustratif"),("Volume","Volume"),("Mute","Son coupé"))]]),
 ("television","Chaînes, infobars et guides EPG",[
  ("ChannelSelection","Chaînes · image EPG","ChannelSelection",["ChannelSelectionDefault","ChannelSelectionPIG","ChannelSelectionFull","ChannelSelection_PIG"],"ChannelSelection"),
  ("ChannelSelectionText","Chaînes · sans image EPG","ChannelSelection",[],"ChannelSelectionText"),
  ("InfoBar","Infobar principale","InfoBar",[],"InfoBar"),
  ("SecondInfoBar","Seconde infobar","SecondInfoBar",[],"SecondInfoBar"),
  ("GraphicalEPG","Guide EPG graphique","GraphicalEPG",["GraphicalEPGPIG","GraphicalInfoBarEPG"],"GraphicalEPG"),
  ("EPGSelection","Guide EPG liste / multi / rapide","EPGSelection",["EPGSelectionMulti","QuickEPG"],None),
  ("EventView","Détails du programme","EventView",["EventViewSimple","InfoBarEventView"],"EventView")]),
]


def translations():
    result={};ident="";value="";mode=None
    path=ROOT/".upstream/enigma2/po/fr.po"
    for line in path.read_text(encoding="utf-8").splitlines()+[""]:
        if not line.strip():
            if ident and value:result[ident]=value
            ident=value="";mode=None
        elif line.startswith("msgid "):
            ident=ast.literal_eval(line[6:]);mode="id"
        elif line.startswith("msgstr "):
            value=ast.literal_eval(line[7:]);mode="value"
        elif line.startswith('"'):
            part=ast.literal_eval(line)
            if mode=="id":ident+=part
            elif mode=="value":value+=part
    return result


TR=translations()
def tr(value):return TR.get(value,value)


def native_preview(profile,key,identity,timer_state=None):
    if identity=='AudioSelection':
        from render_audio import render
        return render(profile,focus='streams',page='subtitles') if key=='SubtitleSelection' else render(profile)
    screens={s.get("name"):s for s in ET.parse(ROOT/"skins"/profile/"skin.xml").findall("screen")}
    screen=screens[identity]
    sw,sh=map(int,screen.get("size").split(','))
    pos=screen.get("position","0,0").split(',')
    ox=(1920-sw)//2 if pos[0]=="center" else int(pos[0]);oy=(1080-sh)//2 if pos[1]=="center" else int(pos[1])
    image=Image.new("RGB",(1920,1080),COLORS["background"] if sw==1920 else "#25323D")
    draw=ImageDraw.Draw(image)
    if sw<1920:
        draw.rectangle((ox,oy,ox+sw-1,oy+sh-1),fill=COLORS["background"])
    titles={"Menu":"Menu complet · exemple","PluginBrowser":tr("Plugin Browser"),"MovieSelection":tr("Movie Selection"),"VirtualKeyboard":tr("Virtual Keyboard"),"AudioSelection":tr("Select audio track"),"Subtitles":tr("Subtitle Selection"),"Console":"Console · aperçu sans exécution"}
    titles.update({key:tr(value) for key,value in (("RecordTimerOverview","RecordTimer Overview"),("SchedulerOverview","Scheduler Overview"),("ConflictTimerOverview","ConflictTimer Overview"))})
    keys={}
    if identity=="Menu":keys={"red":tr("Exit")}
    if identity=="PluginBrowser":keys=dict(zip(("red","green","yellow","blue"),map(tr,("Remove Plugins","Install Plugins","Update Plugins",""))))
    elif "TimerOverview" in identity or identity=="SchedulerOverview":keys=dict(zip(("red","green","yellow","blue"),map(tr,("Delete","Add","Disable","Cleanup"))))
    elif identity=="VirtualKeyboard":keys=dict(zip(("red","green","yellow","blue"),map(tr,("Exit","Enter","Shift","Upper case"))))
    elif identity=="MovieSelection":keys=dict(zip(("red","green","yellow","blue"),map(tr,("Delete","Move","Bookmarks","Sort"))))
    if identity=="ConflictTimerOverview":keys["blue"]=tr("Ignore")
    from timer_design import SCREENS as TIMER_SCREENS
    if identity in TIMER_SCREENS:
        from timer_preview import fixture
        timer_state=timer_state or {'SchedulerOverview':'system','ConflictTimerOverview':'conflict'}.get(identity,'planned')
        timer_rows,timer_keys=fixture(timer_state)
        keys={key:tr(value) for key,value in timer_keys.items()}
    # MovieSelection shows upstream default assignments, which are configurable.
    def text(node,box,value,size=28,fill="foreground",align="left"):
        text_box(draw,box,value,size,color(fill),align,family=node.get("font","Regular;28").split(';')[0],valign=node.get("valign","top"),no_wrap=node.get("noWrap")=="1")
    def rows(node,box,values,height=64,points=28):
        x,y,w,h=box
        for index,value in enumerate(values[:max(1,h//height)]):
            yy=y+height*index
            if index==0:
                from remaining_design import paint_selection
                paint_selection(image,node,(x,yy,w,height))
            primary,secondary=value if isinstance(value,tuple) else (value,"")
            text(node,(x+18,yy+8,w-36,height-12),primary,points)
            if secondary:text(node,(x+18,yy+43,w-36,height-48),secondary,22,"muted")
    def visit(parent,seen=()):
        for node in parent:
            if node.tag=="panel":
                target=node.get("name")
                if target in screens and target not in seen:visit(screens[target],seen+(target,))
                continue
            if node.tag not in ("widget","eLabel","ePixmap"):continue
            source,name,kind=node.get("source",""),node.get("name",""),node.get("render","")
            condition=node.get("conditional","")
            if condition in ("pluginList","pluginGrid") and condition!=("pluginGrid" if key.endswith("-grid") else "pluginList"):continue
            if condition.startswith("key_") and not keys.get(condition[4:]):continue
            x,y=map(int,node.get("position","0,0").split(','));w,h=map(int,node.get("size","0,0").split(','));x+=ox;y+=oy
            box=(x,y,w,h)
            if node.get("backgroundColor") and node.get("transparent")!="1":draw.rectangle((x,y,x+w-1,y+h-1),fill=color(node.get("backgroundColor")))
            if node.tag=="ePixmap" or kind=="Pixmap" or (name=="icon" and node.get("pixmaps")):
                resource=node.get("pixmap") or node.get("pixmaps","").split(',')[0]
                if resource:
                    with Image.open(ROOT/"skins"/resource) as asset:
                        asset=ImageOps.contain(asset.convert("RGBA"),(w,h))
                        image.paste(asset,(x,y),asset)
                continue
            if kind=="MetrixNEOWeather":
                day=node.get("neoDay","0");weather={"-1":"moon","0":"sun","1":"cloud","2":"rain"}.get(day,"sun")
                with Image.open(ROOT/"skins"/profile/"assets"/("weather-"+weather+".png")) as asset:
                    asset=ImageOps.contain(asset.convert("RGBA"),(w,h));image.paste(asset,(x+(w-asset.width)//2,y+(h-asset.height)//2),asset)
                continue
            if source=="menu":
                rows(node,box,list(map(tr,("Timers","Information","Plugins","Setup","Standby / Restart"))),height=72)
            elif source in ("pluginList","pluginGrid"):
                values=[("Metrix NEO · Préférences","Helper facultatif · exemple"),("Extension de démonstration A","Description de plugin illustrative"),("Extension de démonstration B","Aucun inventaire de plugins du Vu+ lu")]
                if source=="pluginList":
                    from remaining_design import paint_selection
                    for i,(label,detail) in enumerate(values):
                        yy=y+i*88
                        if i==0:paint_selection(image,node,(x,yy,w,88))
                        with Image.open(ROOT/'skins'/profile/'assets/menu-plugins.png') as icon:
                            icon=ImageOps.contain(icon.convert('RGBA'),(100,50));image.paste(icon,(x+12,yy+10),icon)
                        text(node,(x+150,yy+4,1600,40),label,30)
                        text(node,(x+150,yy+46,1600,32),detail,24,'muted')
                else:
                    for i,(label,detail) in enumerate(values):
                        xx=x+(i%4)*450;yy=y+(i//4)*175
                        if i==0:
                            from remaining_design import paint_selection
                            paint_selection(image,node,(xx,yy,450,175))
                        with Image.open(ROOT/"skins"/profile/"assets/menu-plugins.png") as icon:
                            icon=ImageOps.contain(icon.convert("RGBA"),(100,50));image.paste(icon,(xx+145,yy+20),icon)
                        text(node,(xx+16,yy+90,358,78),label,28,align="center")
            elif name=="quickselect":continue
            elif name=="timerlist":
                from timer_preview import draw_rows
                draw_rows(draw,image,node,box,profile,timer_state,tr)
            elif name=="list" and identity=="MovieSelection":
                rows(node,box,[("Les routes du monde.ts","Exemple de fichier · 52 min"),("Documentaire de démonstration.ts","Exemple de fichier · 90 min"),("Émission enregistrée.ts","Exemple de fichier · 45 min")],96)
            elif name=="list" and identity in ("ChoiceBox","MessageBox"):
                rows(node,box,list(map(tr,("Yes","No"))) if identity=="MessageBox" else list(map(tr,("All services","Bouquets","Providers","Satellites"))),48)
            elif name=="config" and identity in ("AudioSelection","Subtitles"):
                rows(node,box,[tr("AC3 downmix")+" : "+tr("Downmix"),tr("Audio Channel")+" : "+tr("Stereo")] if identity=="AudioSelection" else [tr("Subtitle Quickmenu")],46)
            elif source=="streams":
                values=[("1","AC3","Piste audio 1 · exemple","Français","X"),("2","AAC","Piste audio 2 · exemple","Anglais","")] if identity=="AudioSelection" else [("1","DVB","Sous-titres · exemple","Français","X"),("2","teletext","Sous-titres · exemple","Anglais","")]
                for i,parts in enumerate(values):
                    yy=y+i*52
                    if i==0:draw.rectangle((x,yy,x+w-1,yy+51),fill=COLORS["selection"])
                    for value,(dx,cw) in zip(parts,((16,80),(110,100),(230,700),(960,600),(1600,120))):text(node,(x+dx,yy,cw,52),value,26)
            elif name=="list" and identity=="VirtualKeyboard":
                from keyboard_preview import render as render_keyboard
                render_keyboard(image,box)
            elif name=="list" and identity=="EPGSelection":rows(node,box,[("20:45  Horizons · Les routes du monde","21:40  Programme suivant · exemples"),("21:00  Le journal","21:30  Reportage · exemples")],100)
            elif name=="Volume":
                draw.rectangle((x,y,x+w-1,y+h-1),fill=COLORS["track"])
                draw.rectangle((x,y,x+int(.45*w),y+h-1),fill=COLORS["accent"])
            elif source=="Title":text(node,box,titles.get(identity,dict((entry[2],entry[1]) for _,_,group in GROUPS for entry in group).get(identity,identity)),int(node.get("font","Regular;28").split(';')[-1]))
            elif source.startswith("key_"):text(node,box,keys.get(source[4:],node.get("text","")),int(node.get("font","Regular;24").split(';')[-1]),node.get("foregroundColor","foreground"))
            elif name=="text" and identity=="Console":text(node,box,"[APERÇU]\nZone de sortie texte illustrative.\nAucune commande exécutée ; aucun journal du récepteur lu.",24)
            elif name=="text" and identity=="MessageBox":text(node,box,"Message de démonstration.\nCet aperçu n’exécute aucune action sur le récepteur.",30)
            elif name=="text" and identity=="ChoiceBox":text(node,box,"Choisir une action · exemple",29)
            elif name=="text" and identity=="InputBox":text(node,box,"Saisir un nom · exemple",30)
            elif name in ("text","input") and identity in ("InputBox","VirtualKeyboard"):text(node,box,"Texte de démonstration",32)
            elif name=="prompt":text(node,box,"Saisir un nom",28)
            elif name=="locale":text(node,box,"Français · AZERTY",24)
            elif name=="freeDiskSpace":text(node,box,"Espace disque : non lu sur le Vu+",24)
            elif name=="waitingtext":continue
            elif name=="description" or source=="description":
                value="Description de l’extension sélectionnée · exemple" if identity=="PluginBrowser" else "Description de l’élément sélectionné · exemple"
                if identity in TIMER_SCREENS:value='' if timer_state in ('empty','system') else 'Description du programme sélectionné · exemple EPG'
                text(node,box,value,26,"muted")
            elif name=="switchdescription":text(node,box,tr("Switch between Audio-, Subtitlepage"),25)
            elif kind=="Label" or node.tag=="eLabel" or name in ("description","lab1"):
                value=node.get("text","") if node.tag=="eLabel" else sample_text(node,identity,profile)
                text(node,box,value,int(node.get("font","Regular;28").split(';')[-1]),node.get("foregroundColor","foreground"),node.get("halign","left"))
    visit(screen,(identity,))
    draw.rectangle((0,0,1919,19),fill=COLORS["secondary"])
    draw.text((960,9),"SIMULATION XML · RANGÉES NATIVES ILLUSTRATIVES · AUCUN ACCÈS VU+",font=font(13),fill=COLORS["muted"],anchor="mm")
    return image


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[];covered=set()
    for group,title,entries in GROUPS:
        for key,label,identity,aliases,reuse in entries:
            covered.update([identity,*aliases])
            record=dict(key=key,label=label,group=group,group_title=title,native_screen=identity,aliases=aliases,images={},caption="Simulation XML · données d’exemple" if reuse else "Géométrie XML · rangées/clavier illustratifs · touches natives selon l’état et la configuration")
            if identity=='AudioSelection':record['caption']='Simulation XML · vidéo et valeurs illustratives · IPAudio Pro seulement si fourni par une extension · langue réelle selon OpenATV'
            if key=='SubtitleSelection':record['caption']='Simulation XML · sélecteur natif AudioSelection en mode sous-titres · vidéo et pistes illustratives'
            for profile in PROFILES:
                if profile=="MetrixNEO" and key in ("MetrixNEOSettings-smart","MetrixNEOSettings-diagnostics"):
                    record["images"][profile]=None;continue
                path=ROOT/"previews"/(profile+"-"+reuse+".png") if reuse else OUT/(profile+"-"+key+".png")
                if not reuse:native_preview(profile,key,identity).save(path,optimize=True)
                assert path.is_file(),path
                record["images"][profile]=path.relative_to(ROOT).as_posix()
            records.append(record)
    for profile in PROFILES:
        names={s.get("name") for s in ET.parse(ROOT/"skins"/profile/"skin.xml").findall("screen")}
        assert covered==names,(names-covered,covered-names)
    report=dict(result="REVIEW_READY_NOT_USER_APPROVED",native_identities=len(covered),views=len(records),receiver_access=False,hardware_validation="NOT_PERFORMED",limitations=["Les rangées natives secondaires et le clavier sont illustratifs, pas un moteur Enigma2.","Les alias sont regroupés par présentation ; leurs callbacks ne sont pas validés par les images.","Les fenêtres spécifiques AutoTimer, NetworkOverview et plugins tiers conservent leur repli natif ; elles ne sont pas toutes redessinées."],screens=records)
    (ROOT/"reports/menu-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("result","native_identities","views","receiver_access")},ensure_ascii=False))


if __name__=="__main__":main()
