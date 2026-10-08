#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verified online installer/updater for the Metrix Neo AI Enigma2 plugin.

Downloads all plugin code through HTTPS, checks SHA256 before touching the
installed package, keeps the old package for rollback, never restarts Enigma2
unattended, and never modifies the MetrixHD skin during plugin update.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
from datetime import datetime

VERSION = '0.4.0'
BASE='https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/neo-plugin/'
DEST=Path('/usr/lib/enigma2/python/Plugins/Extensions/MetrixNeoAI')
STATE_DIR=Path('/etc/enigma2/MetrixNeoAI')
PKG_STATE=STATE_DIR/'package.json'
BACKUPS=STATE_DIR/'package-backups'
MAX_MANIFEST=20000
MAX_FILE=250000
SCRIPT_PREFIX='plugin_files/'

class UpdateError(Exception): pass

def notify(msg): print('[Metrix Neo AI] '+str(msg),flush=True)

def fetch(url, limit):
    if not url.startswith('https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/neo-plugin/'):
        raise UpdateError('Unsafe source URL')
    req=Request(url,headers={'User-Agent':'MetrixNeoAI-Updater/0.4'})
    with urlopen(req,timeout=18) as r:
        data=r.read(limit+1)
    if len(data)>limit: raise UpdateError('Downloaded file too large')
    return data

def manifest():
    data=fetch(BASE+'manifest.json',MAX_MANIFEST)
    obj=json.loads(data.decode('utf-8'))
    if not isinstance(obj,dict) or obj.get('device')!='vuzero4k' or obj.get('image')!='openatv-8.0.1':
        raise UpdateError('Incorrect device/image manifest')
    if not re.fullmatch(r'\d+\.\d+\.\d+',obj.get('version','')):
        raise UpdateError('Invalid semantic version')
    files=obj.get('files')
    if not isinstance(files,dict) or set(files)!={'__init__.py','plugin.py','neo_engine.py','neo_update.py'}:
        raise UpdateError('Unexpected plugin file manifest')
    if any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in files.values()):
        raise UpdateError('Invalid SHA256')
    return obj

def current_version():
    try:
        return json.loads((DEST/'manifest.json').read_text(encoding='utf-8')).get('version')
    except (ValueError,OSError):
        return None

def standby_confirmed():
    p=Path('/proc/stb/power/standby')
    try: return p.read_text().strip()=='1'
    except OSError: return False

def _write_bytes(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd, name=tempfile.mkstemp(dir=str(path.parent),prefix='.'+path.name+'.')
    try:
        with os.fdopen(fd,'wb') as out:
            out.write(data);out.flush();os.fsync(out.fileno())
        os.chmod(name,0o644)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def _syscheck():
    iv=Path('/etc/image-version')
    if not iv.is_file():raise UpdateError('/etc/image-version not found')
    info=iv.read_text(errors='replace')
    if 'box_type=vuzero4k' not in info or 'version=8.0.1' not in info:
        raise UpdateError('Only OpenATV 8.0.1 Vu+ Zero 4K is supported')
    if not Path('/usr/share/enigma2/MetrixHD').is_dir():
        raise UpdateError('MetrixHD not installed')

def install(force=False, auto=False):
    _syscheck()
    if auto and not standby_confirmed():
        notify('Device not confirmed in standby: no unattended installation')
        return False
    remote=manifest()
    existing=current_version()
    if existing is not None and tuple(map(int,existing.split('.'))) >= tuple(map(int,remote['version'].split('.'))) and not force:
        notify('Already current: '+existing)
        return False
    DEST.parent.mkdir(parents=True,exist_ok=True)
    STATE_DIR.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='metrixneo-',dir=str(DEST.parent)) as td:
        stage=Path(td)/'MetrixNeoAI';stage.mkdir()
        for filename,expected in remote['files'].items():
            raw=fetch(BASE+SCRIPT_PREFIX+filename,MAX_FILE)
            if hashlib.sha256(raw).hexdigest()!=expected:
                raise UpdateError('SHA256 mismatch: '+filename)
            if filename.endswith('.py'):
                compile(raw.decode('utf-8'),filename,'exec')
            (stage/filename).write_bytes(raw)
        (stage/'manifest.json').write_text(json.dumps(remote,indent=2)+'\n',encoding='utf-8')
        backup=None
        if DEST.exists():
            BACKUPS.mkdir(parents=True,exist_ok=True)
            name=datetime.now().strftime('%Y%m%d-%H%M%S')
            backup=BACKUPS/('plugin-'+name)
            if backup.exists():raise UpdateError('Backup collision; retry later')
            os.replace(str(DEST),str(backup))
        try:
            os.replace(str(stage),str(DEST))
        except Exception:
            if backup and backup.exists() and not DEST.exists():
                os.replace(str(backup),str(DEST))
            raise
        pkg={'version':remote['version'],'previous_path':str(backup) if backup else None,
             'installed_at':datetime.now().isoformat(timespec='seconds')}
        _write_bytes(PKG_STATE,(json.dumps(pkg,indent=2)+'\n').encode('utf-8'))
    notify('Installed plugin version '+remote['version']+'. Restart Enigma2 GUI when convenient.')
    notify('Existing MetrixHD XML was not touched.')
    return True

def rollback():
    state=json.loads(PKG_STATE.read_text(encoding='utf-8'))
    backup=Path(state.get('previous_path') or '')
    if not backup.is_dir() or backup.parent!=BACKUPS:
        raise UpdateError('No validated previous plugin package to restore')
    if DEST.exists():
        with tempfile.TemporaryDirectory(dir=str(DEST.parent)) as tmp:
            hold=Path(tmp)/'new';os.replace(DEST,hold)
            try:os.replace(backup,DEST)
            except Exception:os.replace(hold,DEST);raise
    else:os.replace(backup,DEST)
    _write_bytes(PKG_STATE,json.dumps({'version':current_version(),'previous_path':None}).encode('utf-8'))
    notify('Previous plugin package restored; restart Enigma2 GUI.')

def enable_daily():
    """Add one guarded daily updater cron, preserving unrelated jobs."""
    try:
        proc=subprocess.run(['crontab','-l'],capture_output=True,text=True,timeout=8)
        cron=proc.stdout if proc.returncode==0 else ''
        if proc.returncode not in (0,1): raise UpdateError('Cannot read user crontab')
        STATE_DIR.mkdir(parents=True,exist_ok=True)
        _write_bytes(STATE_DIR/'crontab-before.txt',cron.encode('utf-8'))
        jobs=[line for line in cron.splitlines() if '# metrix-neo-ai-daily' not in line and '# metrix-neo-auto-update' not in line]
        jobs.append('37 12 * * * /usr/bin/python3 '+str(DEST/'neo_update.py')+' auto >> /home/root/metrix-neo-ai-update.log 2>&1 # metrix-neo-ai-daily')
        changed='\n'.join(jobs)+'\n'
        subprocess.run(['crontab','-'],input=changed,text=True,timeout=10,check=True)
        notify('Daily standby-only update registered: 12:37 local receiver time')
        if '# metrix-neo-auto-update' in cron: notify('Legacy V3 daily schedule disabled (files and backups preserved)')
    except Exception as e:
        notify('Daily scheduler not available: '+str(e))

def main(argv):
    if len(argv)!=2 or argv[1] not in ('check','update','install','auto','rollback','status','enable-daily'):
        raise UpdateError('Usage: neo_update.py check|update|auto|rollback|status|enable-daily')
    cmd=argv[1]
    if cmd=='check':
        remote=manifest();notify('Installed: '+str(current_version())+' / GitHub: '+remote['version'])
    elif cmd=='update':install()
    elif cmd=='install':
        installed=install()
        enable_daily() if installed else None
    elif cmd=='auto':install(auto=True)
    elif cmd=='rollback':rollback()
    elif cmd=='status':notify('Installed: '+str(current_version()))
    elif cmd=='enable-daily':enable_daily()

if __name__=='__main__':
    try:main(sys.argv)
    except Exception as exc:
        notify('FAILED: '+str(exc));sys.exit(1)