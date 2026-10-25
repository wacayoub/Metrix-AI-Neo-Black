"""Illustrative data and native two-line timer geometry; never schedules jobs."""
from PIL import Image
from render_previews import ROOT,COLORS,text_box,font


def fixture(state):
    rows=[dict(name='Horizons · Les routes du monde',service='Chaîne documentaire',state='Waiting',icon='wait',date='Demain 20:45 … 21:40 (55 minutes)',repeat=False),
          dict(name='Le journal du soir',service='Chaîne information',state='Waiting',icon='wait',date='Lun, Mar, Mer, Jeu, Ven 20:00 … 20:30 (30 minutes)',repeat=True),
          dict(name='Cinéma · séance du soir',service='Chaîne cinéma',state='Disabled',icon='off',date='Dimanche 22:00 … 23:45 (105 minutes)',repeat=False),
          dict(name='Documentaire · épisode précédent',service='Chaîne documentaire',state='Done',icon='done',date='Hier 18:00 … 19:00 (60 minutes)',repeat=False)]
    if state=='empty':rows=[]
    elif state=='running':rows[0].update(state='Running',icon='rec')
    elif state=='disabled':rows[0],rows[2]=rows[2],rows[0]
    elif state=='completed':rows[0],rows[3]=rows[3],rows[0]
    elif state=='conflict':rows=[dict(name='Film · créneau en conflit',service='Chaîne cinéma',state='Waiting',icon='wait',date='Demain 20:45 … 22:30 (105 minutes)',repeat=False),dict(name='Match · créneau en conflit',service='Chaîne sportive',state='Waiting',icon='wait',date='Demain 21:00 … 23:00 (120 minutes)',repeat=False)]
    elif state=='system':
        rows=[dict(name='Standby',service='At end: %s',state='Waiting',icon='wait',date='Tous les jours 23:30 … 23:31 (1 minute)',repeat=True),dict(name='Wake up',service='At end: %s',state='Waiting',icon='wait',date='Demain 07:00 … 07:01 (1 minute)',repeat=False)]
    keys={'red':'','green':'Add','yellow':'','blue':'','info':''}
    if rows:
        keys.update(red='Stop' if state=='running' else 'Delete',info='INFO')
        if state not in ('running','completed'):keys['yellow']='Enable' if state=='disabled' else 'Disable'
        if state not in ('conflict','system'):keys['blue']='Cleanup'
    if state=='conflict':keys.update(green='',blue='Ignore')
    return rows,keys


def draw_rows(draw,image,node,box,profile,state,tr):
    rows,_=fixture(state)
    x,y,w,h=box
    row=int(node.get('itemHeight'));top=int(node.get('topHeight'));bottom=int(node.get('bottomHeight'))
    indent=int(node.get('indent'));left=indent+32+int(node.get('iconMargin'));sat=int(node.get('satPosLeft'))
    def text(rect,value,size=24,align='left'):
        text_box(draw,rect,value,size,COLORS['foreground'],align,valign='center',no_wrap=True)
    for i,item in enumerate(rows[:h//row]):
        yy=y+i*row
        if i==0:
            with Image.open(ROOT/'skins'/node.get('selectionPixmap')) as asset:image.paste(asset,(x,yy),asset)
        for name,iy in [('rep' if item['repeat'] else 'once',yy+(top-32)//2),(item['icon'],yy+top+(bottom-32)//2)]:
            with Image.open(ROOT/'skins'/profile/'icons'/('timer_'+name+'.png')) as icon:image.paste(icon,(x+indent,iy),icon)
        service=tr(item['service']) if state=='system' else item['service']
        if state=='system':
            service=tr('At end: %s')%tr('Do nothing')
            width=(w-left-indent)//2-5
            text((x+left,yy,width,top),tr(item['name']),28)
            text((x+left+width+10,yy,width,top),service,align='right')
            minor=(w-left-indent)//4-5
            text((x+left,yy+top,minor,bottom),tr(item['state']))
            text((x+left+minor+10,yy+top,w-left-indent-minor-10,bottom),item['date'],align='right')
        else:
            service_width=round(font(24).getlength(service))+2
            text((x+left,yy,w-left-service_width-indent-10,top),item['name'],28)
            text((x+w-service_width-indent,yy,service_width,top),service,align='right')
            text((x+left,yy+top,sat-left,bottom),tr(item['state']))
            text((x+sat,yy+top,100,bottom),'7.0°W')
            text((x+sat+110,yy+top,w-sat-indent-110,bottom),item['date'],align='right')
