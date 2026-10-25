"""Shared NEO selection colors for screens still awaiting visual validation."""
from generate_skins import TOKENS

TARGETS={
    'Menu':('menu',), 'PluginBrowser':('pluginList','pluginGrid'),
    'MovieSelection':('list',), 'Setup':('config',),
    'MetrixNEOSettings':('config',), 'ChoiceBox':('list',),
    'MessageBox':('list',), 'Subtitles':('config',),
    'VirtualKeyboard':('list',),
}


def apply(root,profile):
    import xml.etree.ElementTree as ET
    prefix='' if profile.endswith('Advanced') else 'classic_'
    parameters=root.find('parameters')
    # Opt-in supported by the pinned native keyboard. Older builds ignore these
    # keys and keep their native bitmap keyboard; no Enigma2 code is replaced.
    ET.SubElement(parameters,'parameter',name='VirtualKeyboardNative',value='1')
    ET.SubElement(parameters,'parameter',name='VirtualKeyboardNativeGeometry',value='4,6,2')
    ET.SubElement(parameters,'parameter',name='VirtualKeyboardNativeColors',value=','.join(('secondary','selection','accent','foreground','red','green','yellow','blue')))
    value=','.join(prefix+'menu_selected_'+stop for stop in ('top','mid','bottom'))+',vertical'
    for screen in root.findall('screen'):
        targets=TARGETS.get(screen.get('name'),())
        for node in screen.findall('widget'):
            if (node.get('source') or node.get('name')) in targets:
                # Native gradient fills follow the component's actual row height,
                # including user-configurable MovieList items per page.
                node.set('backgroundColorSelected',value)
                node.set('foregroundColorSelected','foreground')


def paint_selection(image,node,box):
    from PIL import ImageDraw
    from reference_assets import gradient
    x,y,w,h=box
    value=node.get('backgroundColorSelected','selection')
    if ',' in value:
        parts=value.split(',')
        asset=gradient((w,h),TOKENS[parts[0]],TOKENS[parts[2]],mid=TOKENS[parts[1]])
        image.paste(asset,(x,y),asset)
    else:ImageDraw.Draw(image).rectangle((x,y,x+w-1,y+h-1),fill='#'+TOKENS.get(value,TOKENS['selection'])[-6:])
