"""Native AudioSelection presentation traced from the user's audio capture.

Only skin geometry and original pictograms; no audio settings or actions changed.
"""
from PIL import Image, ImageDraw
from generate_skins import screen, rect, sub, widget, label, TOKENS


def build_assets(folder):
    from reference_assets import gradient
    prefix='' if folder.parent.name.endswith('Advanced') else 'classic_'
    for name,size in [('config',(833,45)),('streams',(1005,48))]:
        gradient(size,TOKENS[prefix+'menu_selected_top'],TOKENS[prefix+'menu_selected_bottom'],mid=TOKENS[prefix+'menu_selected_mid'],radius=6,border=TOKENS['selection_rim']).save(folder/('audio-selection-'+name+'.png'))
    gradient((122,60),TOKENS['tile_top'],TOKENS['tile_bottom'],mid=TOKENS['tile_mid'],radius=6,border=TOKENS['line_bright']).save(folder/'audio-keycap.png')
    scale=4
    image=Image.new('RGBA',(304*scale,236*scale))
    draw=ImageDraw.Draw(image)
    ink='#'+TOKENS['foreground']
    draw.rounded_rectangle((0,62*scale,62*scale,174*scale),18*scale,fill=ink)
    draw.rectangle((33*scale,62*scale,62*scale,174*scale),fill=ink)
    draw.polygon([(64*scale,56*scale),(184*scale,0),(184*scale,236*scale),(64*scale,180*scale)],fill=ink)
    for box,width in [((153,30,261,206),23),((144,4,303,232),26)]:
        draw.arc(tuple(v*scale for v in box),-48,48,fill='#'+TOKENS['accent'],width=width*scale)
    image.resize((304,236),Image.Resampling.LANCZOS).save(folder/'audio-speaker.png')
    image=Image.new('RGBA',(304*scale,236*scale))
    draw=ImageDraw.Draw(image)
    cyan='#'+TOKENS['accent']
    draw.rounded_rectangle((12*scale,26*scale,292*scale,198*scale),22*scale,outline=cyan,width=8*scale)
    draw.polygon([(48*scale,194*scale),(48*scale,226*scale),(94*scale,194*scale)],fill=cyan)
    for left in (57,169):
        draw.arc((left*scale,66*scale,(left+78)*scale,158*scale),42,318,fill=ink,width=14*scale)
    image.resize((304,236),Image.Resampling.LANCZOS).save(folder/'subtitle-icon.png')
    for direction in ('left','right'):
        image=Image.new('RGBA',(24*scale,26*scale))
        draw=ImageDraw.Draw(image)
        points=[(16,3),(6,13),(16,23)] if direction=='left' else [(6,3),(16,13),(6,23)]
        draw.line([(x*scale,y*scale) for x,y in points],fill='#'+TOKENS['accent'],width=3*scale,joint='curve')
        image.resize((24,26),Image.Resampling.LANCZOS).save(folder/('audio-'+direction+'.png'))


def build(root,profile):
    main=screen(root,'AudioSelection',size='1802,976',position='60,38',bg='transparent')
    # Non-overlapping rectangles form the stepped silhouette in the reference.
    for pos,size in [('0,0','1133,52'),('0,52','1802,870'),('0,922','1133,54')]:
        rect(main,pos,size,'audio_panel')
    def text(pos,size,source=None,name=None,**attrs):
        attrs.setdefault('foregroundColor','audio_ink')
        return widget(main,pos,size,source=source,name=name,**attrs)
    text('26,22','710,70',source='Title',font='AudioLight;50',noWrap='1')
    text('738,15','180,34',source='global.CurrentTime',font='AudioLight;23',halign='right',converters=[('ClockToText','Format:%A')])
    text('738,50','180,34',source='global.CurrentTime',font='AudioLight;23',halign='right',converters=[('ClockToText','Format:%d. %b.')])
    text('918,3','192,84',source='global.CurrentTime',font='AudioLight;68',foregroundColor='accent',halign='right',converters=[('ClockToText','Format:%H:%M')])
    rect(main,'0,94','1133,2','audio_rule')
    widget(main,'210,262','833,315',name='config',render='Listbox',font='Regular;28',valueFont='Regular;28',itemHeight='45',scrollbarMode='showOnDemand',backgroundColor='transparent',backgroundColorSelected='audio_selection',foregroundColor='audio_ink',foregroundColorSelected='audio_ink',selectionPixmap=profile+'/assets/audio-selection-config.png',transparent='1')
    # Native Boolean sources target the first four available config entries.
    # No invented Audio/Subtitles/Options callbacks or fixed plugin entry.
    for index,key in enumerate(('red','green','yellow','blue')):
        widget(main,f'119,{262+45*index}','9,45',source='key_'+key,text='',font=1,backgroundColor='audio_'+key,transparent='0',converters=[('ConditionalShowHide','')])
    widget(main,'1316,291','304,236',source='Title',render='MetrixNEOTrackIcon',neoProfile=profile,alphatest='blend')
    rect(main,'45,607','1050,2','audio_rule')
    stream=widget(main,'104,630','1005,192',source='streams',render='Listbox',scrollbarMode='showOnDemand',backgroundColor='transparent',backgroundColorSelected='audio_selection',foregroundColor='audio_ink',foregroundColorSelected='audio_ink',selectionPixmap=profile+'/assets/audio-selection-streams.png',transparent='1')
    # Audited native tuple: (key, empty, number, description, language, selected).
    # Preserve every column while native focus switches to 'notselected'.
    fields='[MultiContentEntryText(pos=(10,0),size=(90,48),font=0,flags=RT_VALIGN_CENTER|RT_ELLIPSIS,text=2), MultiContentEntryText(pos=(114,0),size=(170,48),font=0,flags=RT_VALIGN_CENTER|RT_ELLIPSIS,text=3), MultiContentEntryText(pos=(300,0),size=(570,48),font=0,flags=RT_VALIGN_CENTER|RT_ELLIPSIS,text=4), MultiContentEntryText(pos=(918,0),size=(60,48),font=0,flags=RT_VALIGN_CENTER|RT_ELLIPSIS,text=5)]'
    sub(stream,'convert',type='TemplatedMultiContent').text='{"templates": {"default": (48, '+fields+', True), "notselected": (48, '+fields+', False)}, "fonts": [gFont("Regular",28)], "itemHeight": 48}'
    text('104,835','1005,30',name='switchdescription',font=20)
    for direction,x in [('left',72),('right',1116)]:
        widget(main,f'{x},837','24,26',name='key_'+direction,render='Pixmap',pixmap=profile+'/assets/audio-'+direction+'.png',alphatest='blend')
    for title,pos,size in [('MENU','1508,862','122,60'),('EXIT','1650,862','122,60')]:
        sub(main,'ePixmap',position=pos,size=size,pixmap=profile+'/assets/audio-keycap.png',alphatest='blend')
        label(main,title,pos,size,font=35,color='audio_button_ink',halign='center',valign='center')
    return main
