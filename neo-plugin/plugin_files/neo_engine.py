# -*- coding: utf-8 -*-
"""Metrix Neo AI: safe, reversible appearance profiles for installed MetrixHD.

Only generated MyMetrixLite color/font definitions are changed. Enigma2 screens,
video mode, service settings and bundled MetrixHD assets remain untouched.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from xml.etree import ElementTree as ET

VERSION = '0.4.0'
SKIN = Path('/usr/share/enigma2/MetrixHD/skinfiles/skin_base.MySkin.xml')
STATE_DIR = Path('/etc/enigma2/MetrixNeoAI')
STATE = STATE_DIR / 'state.json'
ORIGINAL = STATE_DIR / 'original.skin_base.MySkin.xml'
IMAGE_VERSION = Path('/etc/image-version')
MAIN = Path('/usr/share/enigma2/MetrixHD/skin.MySkin.xml')
FONT_RALEWAY = '/usr/share/enigma2/MetrixHD/fonts/Raleway-Regular.ttf'
FONT_OPENSANS = '/usr/share/enigma2/MetrixHD/fonts/OpenSans-Regular.ttf'

# RGBs are all declared in MyMetrixLite's ColorList on OpenATV 8.0.1.
PALETTES = {
    'black': {'title': 'Neo Black', 'selection': '27408B', 'secondary': '0F0F0F', 'progress': '1BA1E2', 'accent': '647687'},
    'blue':  {'title': 'Neo Blue', 'selection': '00008B', 'secondary': '000080', 'progress': '1BA1E2', 'accent': '647687'},
    'violet':{'title': 'Neo Violet', 'selection': '76608A', 'secondary': '0F0F0F', 'progress': '149BAF', 'accent': '76608A'},
}

# (MyMetrixLite config role, generated skin name, alpha byte, palette key)
FIELDS = [
    ('layerabackground', 'layer-a-background', '23', 'base'),
    ('layerbbackground', 'layer-b-background', '23', 'secondary'),
    ('layeraselectionbackground', 'layer-a-selection-background', '00', 'selection'),
    ('menusymbolbackground', 'menusymbolbackground', '12', 'base'),
    ('menubackground', 'menubackground', '23', 'base'),
    ('infobarbackground', 'infobarbackground', '18', 'base'),
    ('infobarprogress', 'infobarprogress', '00', 'progress'),
    ('layeraprogress', 'layer-a-progress', '00', 'progress'),
    ('layeraunderline', 'layer-a-underline', '00', 'accent'),
    ('epgbackground', 'epg-background', '23', 'base'),
    ('epgeventselectedbackground', 'epg-event-selected-background', '00', 'selection'),
    ('epgservicenowbackground', 'epg-service-now-background', '18', 'secondary'),
    ('epgeventdescriptionbackground', 'epg-eventdescription-background', '18', 'secondary'),
]
FONT_FIELDS = [('globaltitle_type', 'global_title', FONT_RALEWAY), ('globalmenu_type', 'global_menu', FONT_RALEWAY)]
GRADIENTS = { 'layer-a-background_gradient': ('base','50','18'), 'infobarbackground_gradient': ('base','48','14'), 'epg-background_gradient': ('base','50','18') }
TAG = re.compile(r'<!--.*?-->|<!\[CDATA\[.*?\]\]>|<color\b[^>]*>|<font\b[^>]*>', re.DOTALL | re.I)
ATTR = re.compile(r'\b([\w-]+)\s*=\s*(["\'])(.*?)\2', re.DOTALL)

class SkinError(Exception):
    pass

def _sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _attr(tag, name):
    for key, quote, value in ATTR.findall(tag):
        if key == name:
            return value
    return None

def _set_attr(tag, name, value):
    pattern = re.compile(r'(\b'+re.escape(name)+r'\s*=\s*)(["\'])(.*?)\2')
    updated, count = pattern.subn(lambda m: m.group(1)+m.group(2)+value+m.group(2), tag, count=1)
    if count != 1:
        raise SkinError('XML attribute missing: '+name)
    return updated

def _read_names(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise SkinError('Generated skin XML invalid: '+str(e))
    colors, fonts = {}, {}
    for child in root.findall('./colors/color'):
        key, value = child.get('name'), child.get('value')
        if key:
            colors.setdefault(key, []).append(value)
    for child in root.findall('./fonts/font'):
        key, value = child.get('name'), child.get('filename')
        if key:
            fonts.setdefault(key, []).append(value)
    return colors, fonts

def palette_changes(profile):
    if profile not in PALETTES:
        raise SkinError('Unknown profile: '+str(profile))
    p = dict(PALETTES[profile]); p['base'] = '0F0F0F'
    colors = {xmlname: '#'+alpha+p[key] for _,xmlname,alpha,key in FIELDS}
    # subtle vertical pseudo-3D shading using stock Enigma2 gradient property
    for name,(key,top,bottom) in GRADIENTS.items():
        colors[name] = '#'+top+p[key]+',#'+bottom+p[key]+',vertical,true'
    fonts = {name:font for _,name,font in FONT_FIELDS if Path(font).is_file()}
    return colors, fonts

def transform_xml(xml, colors, fonts):
    existing_colors, existing_fonts = _read_names(xml)
    required = {field[1] for field in FIELDS}
    missing = required - set(existing_colors)
    if missing:
        raise SkinError('Missing expected skin color(s): '+', '.join(sorted(missing)))
    for name in required:
        vals=existing_colors[name]
        if len(set(vals)) > 1:
            raise SkinError('Conflicting target definitions: '+name)
    def update(m):
        tag=m.group(0)
        if tag.startswith('<!--') or tag.startswith('<![CDATA['):
            return tag
        name=_attr(tag,'name')
        if tag.lower().startswith('<color') and name in colors:
            return _set_attr(tag,'value',colors[name])
        if tag.lower().startswith('<font') and name in fonts:
            return _set_attr(tag,'filename',fonts[name])
        return tag
    result=TAG.sub(update,xml)
    _read_names(result)
    return result

def _atomic(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    mode=path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix='.'+path.name+'.')
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(content)
            stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,mode); os.replace(tmp,str(path))
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def validate_host(config):
    if not IMAGE_VERSION.is_file() or not SKIN.is_file() or not MAIN.is_file():
        raise SkinError('MetrixHD/OpenATV files missing')
    system=IMAGE_VERSION.read_text(encoding='utf-8',errors='replace')
    if 'box_type=vuzero4k' not in system or 'version=8.0.1' not in system:
        raise SkinError('Supported device: Vu+ Zero 4K / OpenATV 8.0.1')
    if config.skin.primary_skin.value != 'MetrixHD/skin.MySkin.xml':
        raise SkinError('Select the original MetrixHD/MySkin skin first')
    if not hasattr(config.plugins,'MyMetrixLiteColors') or not hasattr(config.plugins,'MyMetrixLiteFonts'):
        raise SkinError('MyMetrixLite configuration has not been initialized')
    if str(config.plugins.MyMetrixLiteOther.EHDenabled.value) not in ('1','True'):
        raise SkinError('FHD MyMetrixLite mode expected; no resolution changes')

def _cfg_field(config, kind, key):
    return getattr(getattr(config.plugins,kind),key)

def _profile_config(profile):
    p=dict(PALETTES[profile]);p['base']='0F0F0F'
    entries={}
    for role, name, alpha, key in FIELDS:
        entries[('MyMetrixLiteColors',role)]=p[key]
        alpha_role=role+'transparency'
        # Only fields with a transparency control are changed. Others use XML opacity.
        if role not in ('layeraunderline','infobarprogress','layeraprogress'):
            entries[('MyMetrixLiteColors',alpha_role)]=alpha
    for role, name, font in FONT_FIELDS:
        if Path(font).is_file(): entries[('MyMetrixLiteFonts',role)]=font
    return entries

def _read_state():
    if not STATE.exists(): return None
    try: return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception as e: raise SkinError('Invalid stored backup state: '+str(e))

def _config_get(config, wanted):
    result={}
    for kind,key in wanted:
        block=getattr(config.plugins,kind)
        if not hasattr(block,key):
            continue
        result[kind+'.'+key]=str(getattr(block,key).value)
    return result

def _config_apply(config, values):
    from Components.config import configfile
    for dotted,value in values.items():
        kind,key=dotted.split('.',1)
        field=_cfg_field(config,kind,key)
        if value is not None:
            field.setValue(value)
        field.save()
    configfile.save()

def apply(profile, config):
    validate_host(config)
    updates=_profile_config(profile)
    colors, fonts=palette_changes(profile)
    src=SKIN.read_bytes(); xml=src.decode('utf-8')
    target=transform_xml(xml,colors,fonts).encode('utf-8')
    state=_read_state()
    if state:
        # Do not overwrite manual MyMetrixLite or plugin changes behind the user's back.
        if state.get('applied_sha256') != _sha(src):
            raise SkinError('Skin changed outside Neo AI; restore/check MyMetrixLite before replacing')
        original_values=state['original_config']
        original_hash=state['original_sha256']
    else:
        original_values=_config_get(config,updates)
        original_hash=_sha(src)
    newvals={kind+'.'+key:value for (kind,key),value in updates.items() if hasattr(getattr(config.plugins,kind),key)}
    if not newvals:
        raise SkinError('No supported MyMetrixLite configuration fields found')
    if not state:
        _atomic(ORIGINAL,src)
    save_previous=_config_get(config,updates)
    try:
        _config_apply(config,newvals)
        _atomic(SKIN,target)
        _read_names(SKIN.read_text(encoding='utf-8'))
        newstate={'profile':profile,'version':VERSION,'original_config':original_values,'original_sha256':original_hash,'applied_sha256':_sha(target),'last_changes':newvals}
        _atomic(STATE,(json.dumps(newstate,indent=2,sort_keys=True)+'\n').encode('utf-8'))
    except Exception:
        _config_apply(config,save_previous)
        _atomic(SKIN,src)
        raise
    return PALETTES[profile]['title']+' applied. Restart the Enigma2 GUI to see it.'

def restore(config):
    validate_host(config)
    state=_read_state()
    if not state:
        raise SkinError('No Neo AI backup to restore')
    live=SKIN.read_bytes()
    if _sha(live) != state.get('applied_sha256'):
        raise SkinError('Skin changed since apply; refusing to overwrite manual changes')
    orig=ORIGINAL.read_bytes()
    if _sha(orig)!=state.get('original_sha256'):
        raise SkinError('Backup checksum mismatch')
    _read_names(orig.decode('utf-8'))
    current=_config_get(config,[(k.split('.',1)[0],k.split('.',1)[1]) for k in state['last_changes']])
    try:
        _config_apply(config,state['original_config'])
        _atomic(SKIN,orig)
        STATE.unlink()
    except Exception:
        _config_apply(config,current)
        _atomic(SKIN,live)
        raise
    return 'Previous MetrixHD appearance restored. Restart the Enigma2 GUI.'

def status():
    state=_read_state()
    if not state: return 'No Neo AI profile applied'
    if not SKIN.exists(): return 'Skin file missing'
    if state.get('applied_sha256')!=_sha(SKIN.read_bytes()):
        return 'Other skin changes detected — rollback disabled until reviewed'
    return 'Active: '+PALETTES.get(state.get('profile'),{}).get('title',state.get('profile','?'))