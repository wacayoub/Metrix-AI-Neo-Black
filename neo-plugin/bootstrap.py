#!/usr/bin/env python3
"""Small one-time online installer: fetch + verify the new plugin updater."""
import hashlib, json, os, re, subprocess, sys, tempfile
from urllib.request import Request,urlopen
BASE='https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/neo-plugin/'

def fetch(url,n):
    with urlopen(Request(url,headers={'User-Agent':'MetrixNeoAI-Installer'}),timeout=20) as resp:
        b=resp.read(n+1)
    if len(b)>n:raise ValueError('Oversized network response')
    return b

def main():
    data=fetch(BASE+'manifest.json',20000)
    obj=json.loads(data.decode())
    expected=obj['files']['neo_update.py']
    if not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Invalid manifest checksum')
    raw=fetch(BASE+'plugin_files/neo_update.py',250000)
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Updater SHA mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        path=tmp+'/neo_update.py'
        with open(path,'wb') as f:f.write(raw)
        subprocess.run([sys.executable,path,'install'],check=True)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('[Metrix Neo AI] Installation FAILED:',e)
        sys.exit(1)