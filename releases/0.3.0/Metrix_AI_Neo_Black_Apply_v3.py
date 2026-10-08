#!/usr/bin/env python3
"""Metrix AI Neo Black v3: reversible refinement over V2 for OpenATV 8.0.1.

No change to HDMI mode, service lists, picons, Enigma2 core, or skin resolution.
Runs on the set-top box as root. Uses the installed MyMetrixLite-generated XML.
"""
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

TEST_ROOT = os.environ.get('METRIX_NEO_TEST_ROOT')
ROOT = Path(TEST_ROOT).resolve() if TEST_ROOT else Path('/')

def at(path):
    return ROOT / path.lstrip('/')

SETTINGS = at('/etc/enigma2/settings')
SKIN_XML = at('/usr/share/enigma2/MetrixHD/skinfiles/skin_base.MySkin.xml')
SKIN_MAIN = at('/usr/share/enigma2/MetrixHD/skin.MySkin.xml')
IMAGE_VERSION = at('/etc/image-version')
FONTS = at('/usr/share/enigma2/MetrixHD/fonts/Raleway-Regular.ttf')
BACKUP = at('/home/root/MetrixNeoBlack_v3_backup')
MANIFEST = BACKUP / 'manifest.json'

# All entries are in the standard MyMetrixLite palette (no custom unsupported RGBs).
# These deliberately preserve the original layout and Midnight secondary area.
COLORS = {
    # Black/navy palette from built-in MyMetrixLite choices. No green/neon.
    'layerabackground': ('layer-a-background', '0F0F0F'),
    'layeraselectionbackground': ('layer-a-selection-background', '00008B'),
    'layerbbackground': ('layer-b-background', '0F0F0F'),
    'menusymbolbackground': ('menusymbolbackground', '0F0F0F'),
    'infobarprogress': ('infobarprogress', '27408B'),
    'layeraprogress': ('layer-a-progress', '27408B'),
    'layeraunderline': ('layer-a-underline', '647687'),
    'epgeventselectedbackground': ('epg-event-selected-background', '00008B'),
}
# Metrix/Enigma2 uses leading 00-FF as transparency; preserve everything
# except these intentionally changed backgrounds. 0A: nearly opaque,
# 00: opaque. Keep the channel-preview and screen layout untouched.
TRANSPARENCY = {
    'layerabackground': ('layer-a-background', '0A'),
    'layeraselectionbackground': ('layer-a-selection-background', '00'),
    'epgeventselectedbackground': ('epg-event-selected-background', '00'),
}

FONTS_TO_SET = {}  # Preserve the currently selected fonts, including Arabic fallback.

# Match XML comments/CDATA as opaque tokens: never rewrite markup inside them.
XML_TOKEN = re.compile(
    r'<!--.*?-->|<!\[CDATA\[.*?\]\]>|<color\b[^>]*>|<font\b[^>]*>',
    re.IGNORECASE | re.DOTALL,
)
ATTR = re.compile(r'\b([a-zA-Z_-]+)=("[^"]*"|\'[^\']*\')')

class ConfigError(Exception):
    pass

def report(msg):
    print('[Metrix AI Neo] ' + msg, flush=True)

def get_attr(tag, name):
    for key, quoted in ATTR.findall(tag):
        if key == name:
            return quoted[1:-1]
    return None

def replace_attr(tag, name, value):
    regexp = re.compile(r'(\b' + re.escape(name) + r'\s*=\s*)(["\'])(.*?)(\2)')
    out, count = regexp.subn(lambda m: m.group(1) + m.group(2) + value + m.group(4), tag, count=1)
    if count != 1:
        raise ConfigError('Missing XML attribute ' + name)
    return out

def parse_settings(text):
    values = {}
    for line in text.splitlines():
        if line.startswith('config.') and '=' in line:
            k,v = line.split('=',1)
            values[k]=v
    return values

def patch_settings(text, updates):
    lines = text.splitlines(keepends=True)
    found = set()
    out = []
    for line in lines:
        if line.startswith('config.') and '=' in line:
            k = line.split('=', 1)[0]
            if k in updates:
                if k not in found:
                    out.append(k + '=' + updates[k] + '\n')
                    found.add(k)
                continue
        out.append(line)
    for k,v in updates.items():
        if k not in found:
            if out and not out[-1].endswith('\n'):
                out.append('\n')
            out.append(k + '=' + v + '\n')
    return ''.join(out)

def remove_setting(text, key):
    return ''.join(line for line in text.splitlines(keepends=True)
                   if not line.startswith(key + '='))

def xml_snapshot(text):
    """Inspect active root color/font definitions only, ignoring unrelated duplicates.

    Some real MyMetrixLite builds legitimately repeat unrelated names like
    `Background`, which is not one of our patch targets. Reject ambiguity only
    when one of our specific target names has contradictory source definitions.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ConfigError('XML malformed: ' + str(exc))
    colors, fonts = {}, {}
    for group in root.findall('./colors'):
        for elem in group.findall('color'):
            name, value = elem.get('name'), elem.get('value')
            if not name:
                continue
            if name in colors and colors[name] != value and name in (set(v[0] for v in COLORS.values())):
                raise ConfigError('Conflicting XML target color values: ' + name)
            colors[name] = value
    for group in root.findall('./fonts'):
        for elem in group.findall('font'):
            name, filename = elem.get('name'), elem.get('filename')
            if not name:
                continue
            if name in fonts and fonts[name] != filename and name in FONTS_TO_SET.values():
                raise ConfigError('Conflicting XML target font values: ' + name)
            fonts[name] = filename
    return colors, fonts


def patch_xml(text, updates_color, updates_font, updates_alpha=None):
    updates_alpha = updates_alpha or {}
    colors, fonts = xml_snapshot(text)
    for name in updates_color:
        if name not in colors or not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', colors[name] or ''):
            raise ConfigError('Missing or invalid color: ' + name)
    for name in updates_font:
        if name not in fonts or not fonts[name]:
            raise ConfigError('Missing font role: ' + name)

    def transform(match):
        tag = match.group(0)
        if tag.startswith('<!--') or tag.startswith('<![CDATA['):
            return tag
        name = get_attr(tag, 'name')
        if tag.lower().startswith('<color') and name in updates_color:
            old = get_attr(tag, 'value')
            rgb = updates_color[name]
            if not re.fullmatch('[0-9a-fA-F]{6}', rgb):
                raise ConfigError('Bad RGB: ' + rgb)
            if not old or not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', old):
                raise ConfigError('Invalid color value in XML tag: ' + name)
            # Preserve opacity/transparency byte when the value uses AARRGGBB.
            alpha = updates_alpha.get(name, old[1:3] if len(old) == 9 else '')
            return replace_attr(tag, 'value', '#' + alpha + rgb)
        if tag.lower().startswith('<font') and name in updates_font:
            return replace_attr(tag, 'filename', updates_font[name])
        return tag

    result = XML_TOKEN.sub(transform, text)
    xml_snapshot(result)
    return result

def atomic_write(path, text):
    old = path.stat()
    fd,tmp = tempfile.mkstemp(dir=str(path.parent),prefix='.' + path.name + '.')
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp,stat.S_IMODE(old.st_mode))
        try:
            os.chown(tmp,old.st_uid,old.st_gid)
        except PermissionError:
            pass
        os.replace(tmp,str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def validate_system():
    if not SETTINGS.is_file() or not SKIN_XML.is_file():
        raise ConfigError('MyMetrixLite active settings or generated XML missing. No changes applied.')
    version = IMAGE_VERSION.read_text(errors='replace') if IMAGE_VERSION.is_file() else ''
    if 'box_type=vuzero4k' not in version or 'version=8.0.1' not in version:
        raise ConfigError('This installer targets Vu+ Zero 4K running OpenATV 8.0.1 only.')
    cfg = parse_settings(SETTINGS.read_text(errors='replace'))
    if cfg.get('config.skin.primary_skin') != 'MetrixHD/skin.MySkin.xml':
        raise ConfigError('MetrixHD/skin.MySkin.xml is not the active skin.')
    if cfg.get('config.plugins.MyMetrixLiteOther.EHDenabled') != '1':
        raise ConfigError('FHD MyMetrixLite mode is not confirmed. Refusing to change resolution.')
    if not SKIN_MAIN.is_file() or 'skin_base.MySkin.xml' not in SKIN_MAIN.read_text(errors='replace'):
        raise ConfigError('The active MySkin.xml does not reference the generated skin_base.MySkin.xml.')
    return cfg

def gui_restart(action):
    if TEST_ROOT:
        action()
        return
    report('Stopping Enigma2 GUI to protect live settings...')
    subprocess.run(['init','4'],check=True)
    time.sleep(3)
    try:
        action()
    finally:
        report('Restarting Enigma2 GUI...')
        subprocess.run(['init','3'],check=True)

def build_updates():
    cupdates={'config.plugins.MyMetrixLiteColors.'+k:v for k,(_,v) in COLORS.items()}
    xml_cupdates={tag:rgb for tag,rgb in COLORS.values()}
    fupdates={}
    xml_fupdates={}
    if FONTS.is_file():
        for config_role, xml_role in FONTS_TO_SET.items():
            fupdates['config.plugins.MyMetrixLiteFonts.'+config_role]=str(FONTS)
            xml_fupdates[xml_role]=str(FONTS)
    else:
        report('Raleway font not installed; leaving all original fonts intact.')
    for config_role, (_, transp) in TRANSPARENCY.items():
        cupdates['config.plugins.MyMetrixLiteColors.' + config_role + 'transparency'] = transp
    alpha_updates = {tag: alpha for tag, alpha in TRANSPARENCY.values()}
    return cupdates|fupdates,xml_cupdates,xml_fupdates,alpha_updates

def apply():
    cfg=validate_system()
    if MANIFEST.exists():
        raise ConfigError('V3 already applied. Use status or restore first.')
    updates,xml_colors,xml_fonts,xml_alpha=build_updates()
    old_cfg_text=SETTINGS.read_text(encoding='utf-8')
    old_xml_text=SKIN_XML.read_text(encoding='utf-8')
    old_colors,old_fonts=xml_snapshot(old_xml_text)
    # Preflight every XML replacement *before* stopping Enigma2.
    new_cfg=patch_settings(old_cfg_text,updates)
    new_xml=patch_xml(old_xml_text,xml_colors,xml_fonts,xml_alpha)
    original_settings=parse_settings(old_cfg_text)
    manifest={
        'created':datetime.now().isoformat(timespec='seconds'),
        'changed_settings':{k:{'before':original_settings.get(k),'after':v} for k,v in updates.items()},
        'changed_colors':{k:{'before':old_colors[k], 'after_rgb':v, 'after_alpha':xml_alpha.get(k,old_colors[k][1:3] if len(old_colors[k])==9 else '')} for k,v in xml_colors.items()},
        'changed_fonts':{k:{'before':old_fonts[k],'after':v} for k,v in xml_fonts.items()},
    }
    def commit():
        BACKUP.mkdir(parents=True,exist_ok=True)
        shutil.copy2(SETTINGS,BACKUP/'settings.original')
        shutil.copy2(SKIN_XML,BACKUP/'skin_base.MySkin.xml.original')
        # manifest written last so incomplete transactions aren't considered installed
        try:
            atomic_write(SETTINGS,new_cfg)
            atomic_write(SKIN_XML,new_xml)
            xml_snapshot(SKIN_XML.read_text(encoding='utf-8'))
            (BACKUP/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        except Exception:
            report('ERROR: restoration from backups')
            shutil.copy2(BACKUP/'settings.original',SETTINGS)
            shutil.copy2(BACKUP/'skin_base.MySkin.xml.original',SKIN_XML)
            raise
    gui_restart(commit)
    report('SUCCESS: V3 black/navy palette and contrast refinements applied.')
    report('Original backup: '+str(BACKUP))
    report('HDMI mode, skin resolution, layout and existing fonts unchanged.')

def restore():
    validate_system()
    if not MANIFEST.is_file():
        raise ConfigError('No previous V3 backup found.')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    text=SETTINGS.read_text(encoding='utf-8')
    colors_xml=SKIN_XML.read_text(encoding='utf-8')
    values=parse_settings(text)
    changes={}
    for k,details in manifest['changed_settings'].items():
        if values.get(k)==details['after']:
            changes[k]=details['before']
    restored_settings=text
    for k,v in changes.items():
        if v is None:
            restored_settings=remove_setting(restored_settings,k)
        else:
            restored_settings=patch_settings(restored_settings,{k:v})
    current_colors,current_fonts=xml_snapshot(colors_xml)
    color_changes={}
    for name,details in manifest['changed_colors'].items():
        actual=current_colors.get(name,'')
        if actual and actual[-6:].upper()==details['after_rgb'].upper() and (not details.get('after_alpha') or actual[1:3].upper()==details['after_alpha'].upper()):
            color_changes[name]=details['before'][-6:]
    font_changes={}
    for name,details in manifest['changed_fonts'].items():
        if current_fonts.get(name)==details['after']:
            font_changes[name]=details['before']
    restore_alphas={k: d['before'][1:3] for k,d in manifest['changed_colors'].items() if k in color_changes and len(d['before'])==9}
    restored_xml=patch_xml(colors_xml,color_changes,font_changes,restore_alphas)
    def commit():
        atomic_write(SETTINGS,restored_settings)
        atomic_write(SKIN_XML,restored_xml)
        MANIFEST.rename(BACKUP/'manifest.restored.json')
    gui_restart(commit)
    report('SUCCESS: V3 changes reverted. Your V2 state was preserved.')

def status():
    cfg=validate_system()
    report('Skin: '+cfg['config.skin.primary_skin'])
    report('FHD setting remains: '+cfg['config.plugins.MyMetrixLiteOther.EHDenabled'])
    report('Backup: '+('present' if MANIFEST.exists() else 'not present'))
    for k in COLORS:
        report(k+' = '+cfg.get('config.plugins.MyMetrixLiteColors.'+k,'(default)'))

if __name__=='__main__':
    try:
        if len(sys.argv)!=2 or sys.argv[1] not in ('apply','restore','status'):
            raise ConfigError('Usage: python3 Metrix_AI_Neo_Black_Apply_v3.py apply|restore|status')
        {'apply':apply,'restore':restore,'status':status}[sys.argv[1]]()
    except (ConfigError,OSError,ValueError,subprocess.CalledProcessError) as exc:
        report('FAILED: '+str(exc))
        sys.exit(1)
