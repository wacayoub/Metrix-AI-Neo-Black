"""NEO presentation for the native OpenATV timer lists; no timer operations."""
from PIL import Image,ImageDraw
from generate_skins import TOKENS,screen,header,sub,widget

SCREENS=('TimerOverview','RecordTimerOverview','SchedulerOverview','ConflictTimerOverview')
ICON_NAMES=('wait','rec','prep','done','rep','once','zap','off','failed','autotimer','icetv')


def build_assets(folder):
    from reference_assets import gradient
    prefix='' if folder.parent.name.endswith('Advanced') else 'classic_'
    gradient((1810,80),TOKENS[prefix+'menu_selected_top'],TOKENS[prefix+'menu_selected_bottom'],mid=TOKENS[prefix+'menu_selected_mid'],radius=6,border=TOKENS['selection_rim']).save(folder/'timer-selection.png')
    gradient((1834,664),TOKENS['panel'],TOKENS['background'],radius=10,border=TOKENS['line']).save(folder/'timer-frame.png')
    gradient((1834,122),TOKENS['secondary'],TOKENS['panel'],radius=8,border=TOKENS['line']).save(folder/'timer-detail.png')
    for key in ('red','green','yellow','blue'):Image.new('RGBA',(6,32),'#'+TOKENS[key]).save(folder/('timer-key-'+key+'.png'))
    icons=folder.parent/'icons';icons.mkdir(exist_ok=True)
    scale=4
    for name in ICON_NAMES:
        image=Image.new('RGBA',(32*scale,32*scale));draw=ImageDraw.Draw(image)
        ink='#'+TOKENS['foreground'];cyan='#'+TOKENS['accent']
        tone='#'+TOKENS['red'] if name in ('rec','failed') else '#'+TOKENS['muted'] if name=='off' else cyan
        def line(points,color=tone,width=2):draw.line([(x*scale,y*scale) for x,y in points],fill=color,width=width*scale,joint='curve')
        if name=='rec':draw.ellipse((6*scale,6*scale,26*scale,26*scale),fill=tone)
        elif name=='done':line([(5,16),(13,24),(27,7)],width=3)
        elif name in ('off','failed'):
            draw.ellipse((3*scale,3*scale,29*scale,29*scale),outline=tone,width=2*scale)
            if name=='off':line([(7,25),(25,7)])
            else:line([(16,7),(16,19)],width=3);draw.ellipse((15*scale,23*scale,17*scale,25*scale),fill=tone)
        elif name=='rep':
            line([(5,11),(25,11),(21,6)]);line([(27,21),(7,21),(11,26)])
            line([(25,11),(21,16)]);line([(7,21),(11,16)])
        elif name=='zap':draw.polygon([(18*scale,2*scale),(6*scale,18*scale),(15*scale,18*scale),(13*scale,30*scale),(27*scale,12*scale),(18*scale,12*scale)],fill=tone)
        else:
            draw.ellipse((3*scale,3*scale,29*scale,29*scale),outline=tone,width=2*scale)
            line([(16,7),(16,16),(23,19)],ink)
            if name=='prep':draw.ellipse((23*scale,2*scale,30*scale,9*scale),fill='#'+TOKENS['yellow'])
            elif name=='autotimer':line([(4,27),(8,17),(12,27)],ink);line([(6,24),(10,24)],ink)
            elif name=='icetv':line([(4,20),(11,20)],ink);line([(8,20),(8,28)],ink);line([(4,28),(11,28)],ink)
        image.resize((32,32),Image.Resampling.LANCZOS).save(icons/('timer_'+name+'.png'))


def build(root,profile):
    def picture(parent,name,pos,size):sub(parent,'ePixmap',position=pos,size=size,pixmap=profile+'/assets/'+name+'.png',alphatest='blend')
    for name in SCREENS:
        main=screen(root,name)
        header(main,profile)
        for node in main:
            if node.get('source')=='Title':node.set('font','Regular;32');node.set('size','820,70');node.set('noWrap','1')
            if node.get('pixmap','').endswith('/menu-television.png'):node.set('pixmap',profile+'/assets/menu-timers.png')
        picture(main,'timer-frame','36,178','1834,664')
        widget(main,'48,190','1810,640',name='timerlist',render='Listbox',timerNameFont='Regular;28',statusFont='Regular;24',detailFont='Regular;24',itemHeight='80',topHeight='42',bottomHeight='38',showSeparator='0',indent='16',iconMargin='12',statusOffset='0',satPosLeft='420',scrollbarMode='showOnDemand',backgroundColor='panel',backgroundColorSelected='selection',foregroundColor='foreground',foregroundColorSelected='foreground',selectionPixmap=profile+'/assets/timer-selection.png')
        picture(main,'timer-detail','36,854','1834,122')
        widget(main,'58,868','1790,94',name='description',font=26,foregroundColor='muted')
        for index,key in enumerate(('red','green','yellow','blue')):
            x=48+index*405
            widget(main,f'{x},1015','6,32',source='key_'+key,render='Pixmap',pixmap=profile+'/assets/timer-key-'+key+'.png',alphatest='blend',conditional='key_'+key,converters=[('ConditionalShowHide','')])
            widget(main,f'{x+18},1008','365,44',source='key_'+key,font=24,conditional='key_'+key,converters=[('ConditionalShowHide','')])
        widget(main,'1720,1008','130,44',source='key_info',font=23,halign='right',foregroundColor='muted',conditional='key_info',converters=[('ConditionalShowHide','')])
