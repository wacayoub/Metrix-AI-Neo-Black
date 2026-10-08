#!/usr/bin/env python3
"""Online release manager for wacayoub/Metrix-AI-Neo-Black on OpenATV.

Uses a versioned manifest, SHA-256 verification, local rollback scripts, and
standby-only unattended installation. No modification of Enigma2 core or HDMI.
"""
import datetime
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

VERSION = '0.1.0'
BASE = os.environ.get('METRIX_NEO_SOURCE', 'https://raw.githubusercontent.com/wacayoub/Metrix-AI-Neo-Black/main/').rstrip('/') + '/'
HOME = Path(os.environ.get('METRIX_NEO_HOME', '/home/root/.metrix-neo'))
RELEASES = HOME / 'releases'
STATE = HOME / 'state.json'
SCRIPT_PATH = Path(os.environ.get('METRIX_NEO_SCRIPT', '/home/root/metrix_neo_updater.py'))
MAX_MANIFEST = 16000
MAX_SCRIPT = 1000000
CRON_MARKER = '# metrix-neo-auto-update'
CRON_EXPR = '15 12 * * *'


class UpdateError(Exception):
    pass


def say(msg):
    print('[Metrix Neo] ' + str(msg), flush=True)


def read_state():
    if not STATE.exists():
        return {'installed_version': None, 'previous_version': None}
    s = json.loads(STATE.read_text(encoding='utf-8'))
    if not isinstance(s, dict):
        raise UpdateError('State file invalid')
    return s


def safe_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.' + path.name + '.')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_state(s):
    safe_write(STATE, (json.dumps(s, sort_keys=True, indent=2) + '\n').encode('utf-8'))


def fetch(relative, limit):
    # Reject paths that could jump to another host, repo, or directory.
    if not isinstance(relative, str) or not re.fullmatch(r'[a-zA-Z0-9_./-]+', relative):
        raise UpdateError('Invalid release path')
    if relative.startswith('/') or '..' in relative.split('/') or '//' in relative:
        raise UpdateError('Unsafe release path')
    req = Request(BASE + relative, headers={'User-Agent': 'MetrixNeoOpenATV/' + VERSION})
    with urlopen(req, timeout=18) as r:
        result = r.read(limit + 1)
    if len(result) > limit:
        raise UpdateError('Download exceeds size limit')
    return result


def release_info():
    m = json.loads(fetch('latest.json', MAX_MANIFEST).decode('utf-8'))
    if not isinstance(m, dict):
        raise UpdateError('Invalid latest.json')
    version = m.get('version')
    file = m.get('script')
    sha = m.get('sha256')
    if not isinstance(version, str) or not re.fullmatch(r'0\.[0-9]+\.[0-9]+', version):
        raise UpdateError('Unsupported release version')
    if not isinstance(file, str) or not file.startswith('releases/' + version + '/') or not file.endswith('.py'):
        raise UpdateError('Invalid release script location')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
        raise UpdateError('Missing SHA-256 checksum')
    if m.get('image') != 'openatv-8.0.1' or m.get('device') != 'vuzero4k':
        raise UpdateError('Release is not declared compatible with this device')
    return m


def parse_version(v):
    return tuple(map(int, v.split('.')))


def local_script(version):
    return RELEASES / version / 'apply.py'


def stage(info):
    data = fetch(info['script'], MAX_SCRIPT)
    sha = hashlib.sha256(data).hexdigest()
    if sha != info['sha256']:
        raise UpdateError('SHA-256 mismatch: update refused')
    import ast
    ast.parse(data.decode('utf-8'), filename=info['script'])
    target = local_script(info['version'])
    safe_write(target, data)
    return target


def check():
    m = release_info()
    installed = read_state().get('installed_version')
    newer = installed is None or parse_version(m['version']) > parse_version(installed)
    say('Installed: ' + (installed or 'not enrolled') + ', Online: ' + m['version'])
    say('Update: ' + ('available' if newer else 'already current'))
    return m, newer


def run_release(script, action):
    if not script.is_file():
        raise UpdateError('Local script missing: ' + str(script))
    say('Running ' + action + ': ' + str(script))
    res = subprocess.run([sys.executable, str(script), action], check=False)
    if res.returncode:
        raise UpdateError(action + ' failed with exit code ' + str(res.returncode))


def update(force=False):
    m, newer = check()
    if not newer and not force:
        return
    previous = read_state().get('installed_version')
    script = stage(m)
    if previous == m['version']:
        say('Same release verified; no reapplication needed.')
        return
    if not previous and m['version'] == '0.3.0':
        # User may have manually applied the V3 script before installing manager.
        v3_manifest = Path(os.environ.get('METRIX_NEO_V3_MANIFEST', '/home/root/MetrixNeoBlack_v3_backup/manifest.json'))
        if v3_manifest.is_file():
            save_state({'installed_version': m['version'], 'previous_version': None, 'source': 'existing-v3'})
            say('Detected already-applied V3; enrolled without restarting Enigma2.')
            return
    if previous:
        old = local_script(previous)
        if not old.is_file():
            raise UpdateError('Previous release missing: cannot safely upgrade')
        run_release(old, 'restore')
    try:
        run_release(script, 'apply')
    except Exception:
        if previous:
            say('New version failed; trying to return to previous version.')
            try:
                run_release(local_script(previous), 'apply')
            except Exception as e:
                say('WARNING: automated recovery failed: ' + str(e))
        raise
    save_state({'installed_version': m['version'], 'previous_version': previous})
    say('Installed ' + m['version'] + '. Previous: ' + str(previous))


def rollback():
    state = read_state()
    current = state.get('installed_version')
    if not current:
        raise UpdateError('No managed version to restore')
    run_release(local_script(current), 'restore')
    prev = state.get('previous_version')
    if prev:
        try:
            run_release(local_script(prev), 'apply')
        except Exception as e:
            say('Could not reapply previous version: ' + str(e))
            raise
    save_state({'installed_version': prev, 'previous_version': None})
    say('Rollback completed. Current version: ' + str(prev))


def is_standby():
    # Some Enigma2 images expose this; when absent/ambiguous do NOT reboot GUI.
    test_path = Path(os.environ.get('METRIX_NEO_STANDBY_PATH', '/proc/stb/power/standby'))
    try:
        return test_path.read_text().strip().lower() in ('1', 'on', 'true', 'standby')
    except OSError:
        return False


def auto():
    try:
        m, newer = check()
        if not newer:
            return
        stage(m)
        if not is_standby():
            say('Downloaded and verified; waiting for verified standby. Manual command: metrix-neo update')
            return
        say('Standby confirmed; applying update.')
        update()
    except Exception as exc:
        say('Auto-check failed, keeping current skin: ' + str(exc))
        raise


def read_crontab():
    p = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if p.returncode and (not any(t in (p.stderr + p.stdout).lower() for t in ('no crontab', "can't open 'root'", 'no such file or directory'))):
        raise UpdateError('Cannot read crontab: ' + p.stderr.strip())
    return p.stdout if p.returncode == 0 else ''


def set_auto(enable):
    before = read_crontab()
    lines = [line for line in before.splitlines() if CRON_MARKER not in line]
    if enable:
        if not SCRIPT_PATH.is_file():
            raise UpdateError('Install updater at ' + str(SCRIPT_PATH) + ' before enabling cron')
        cmd = '%s %s auto >> /home/root/.metrix-neo/auto.log 2>&1' % (sys.executable, SCRIPT_PATH)
        lines.append(CRON_EXPR + ' ' + cmd.strip() + ' ' + CRON_MARKER)
    new = '\n'.join(lines).rstrip('\n') + ('\n' if lines else '')
    p = subprocess.run(['crontab', '-'], input=new, capture_output=True, text=True)
    if p.returncode:
        raise UpdateError('Failed to set crontab: ' + p.stderr.strip())
    say('Daily standby-only auto-update ' + ('enabled' if enable else 'disabled') + '; local time 12:15.')


def status():
    s = read_state()
    say('Updater ' + VERSION + '; installed release ' + str(s.get('installed_version')))
    say('Downloaded release scripts: ' + ', '.join(sorted(p.parent.name for p in RELEASES.glob('*/apply.py'))))
    if s.get('installed_version'):
        say('Rollback possible with: metrix-neo rollback')
    say('Automatic installation requires confirmed standby. Otherwise updates stay staged.')


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('check', 'update', 'rollback', 'status', 'auto', 'auto-on', 'auto-off'):
        raise UpdateError('Usage: metrix-neo check|update|rollback|status|auto|auto-on|auto-off')
    cmd = sys.argv[1]
    HOME.mkdir(parents=True, exist_ok=True)
    {
        'check': check, 'update': update, 'rollback': rollback,
        'status': status, 'auto': auto,
        'auto-on': lambda: set_auto(True),
        'auto-off': lambda: set_auto(False),
    }[cmd]()


if __name__ == '__main__':
    try:
        main()
    except (UpdateError, OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        say('ERROR: ' + str(e))
        sys.exit(1)
