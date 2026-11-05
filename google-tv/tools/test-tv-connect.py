#!/usr/bin/env python3
"""Test Neo Connect on an authorized TV. Optional pairing input must come from
the trusted receiver screen/SSH, never from the unauthenticated discovery itself.
No private key, pairing code, receiver password or provider URL is reported.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb', required=True)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--pair-info', type=Path)
    a = p.parse_args()
    report = {'checks': [], 'scope': 'Actual Android UI, embedded native load and optional receiver tunnel handshake/API; no mobile network or video fluidity claim.'}

    def sh(c, allow_failure=False):
        r = subprocess.run([a.adb, '-s', a.serial, 'shell', c], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        if r.returncode and not allow_failure:
            raise RuntimeError('ADB operation unavailable')
        return r.stdout

    def key(*codes):
        for c in codes:
            sh('input keyevent ' + str(c))
            time.sleep(.3)

    def ui():
        sh('uiautomator dump /sdcard/neo-connect-test.xml')
        return ET.fromstring(sh('cat /sdcard/neo-connect-test.xml'))

    def node(root, tag):
        return next((n for n in root.iter('node') if n.get('resource-id', '').rsplit('/', 1)[-1] == tag), None)

    def find(tag, scroll=False):
        for i in range(7 if scroll else 4):
            r = ui()
            n = node(r, tag)
            if n is not None:
                bounds = tuple(map(int, re.findall(r'\d+', n.get('bounds', ''))))
                if len(bounds) == 4 and bounds[3] > bounds[1] and bounds[2] > bounds[0]:
                    return n
            if scroll:
                b = tuple(map(int, re.findall(r'\d+', next(r.iter('node')).get('bounds', ''))))
                width, height = b[2], b[3]
                start, end = (.8, .3) if i < 3 else (.3, .8)
                sh('input swipe %d %d %d %d 250' % (width*.85, height*start, width*.85, height*end))
            time.sleep(.3)
        raise AssertionError('Missing UI control: ' + tag)

    def tap(tag, scroll=False):
        n = find(tag, scroll)
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', n.get('bounds')))
        sh('input tap %d %d' % ((x1+x2)//2, (y1+y2)//2))
        time.sleep(.4)

    def check(name, condition):
        report['checks'].append({'name': name, 'passed': bool(condition)})
        print(('PASS ' if condition else 'FAIL ') + name, flush=True)
        if not condition:
            raise AssertionError(name)

    def wait_text(tag, needle, seconds=15):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            n = node(ui(), tag)
            if n is not None and needle in n.get('text', ''):
                return n.get('text', '')
            time.sleep(.4)
        return ''

    def foreground():
        m = re.search(r'topResumedActivity=.*?\s([^\s{}]+/[^\s{}]+)', sh('dumpsys activity activities'))
        return m[1] if m else ''

    def open_connect(cold=False):
        if cold:
            sh('am force-stop com.metrixneo.tv')
        sh('am start -W -n com.metrixneo.tv/.MainActivity')
        time.sleep(2)
        r = ui()
        if node(r, 'neo.menu') is None:
            key(82)
        key(9, 23)
        tap('neo.connect.open')
        check('Neo Connect screen opens', bool(wait_text('neo.connect.engine', 'Moteur intégré chargé')))

    try:
        key(224)
        open_connect(cold=True)
        report['version'] = re.search(r'versionName=(\S+)', sh('dumpsys package com.metrixneo.tv'))[1]
        check('Native WireGuard version call succeeds on the TV', 'chargé' in find('neo.connect.engine').get('text', ''))
        check('Opening settings does not automatically start VPN', 'NeoConnectService' not in sh('dumpsys activity services com.metrixneo.tv'))
        key(20)
        check('D-pad can focus an enabled action', any(n.get('focused') == 'true' and n.get('clickable') == 'true' for n in ui().iter('node')))

        if a.pair_info:
            info = json.loads(a.pair_info.read_text(encoding='utf-8'))
            if node(ui(), 'neo.connect.start') is None:
                tap('neo.connect.discover')
                displayed = find('neo.connect.fingerprint').get('text', '')
                fingerprint = ''.join(re.findall(r'[A-F0-9]{8}', displayed))
                check('Receiver TLS fingerprint matches the trusted reference', fingerprint == info['fingerprint'])
                tap('neo.connect.confirm')
                tap('neo.connect.code', scroll=True)
                time.sleep(.5)
                # The one-use code stays in memory; do not add it to logs or output.
                sh('input text ' + info['code'])
                time.sleep(.5)
                if 'mInputShown=true' in sh('dumpsys input_method'):
                    key(4)
                tap('neo.connect.pair', scroll=True)
                check('Pairing creates a local encrypted profile', bool(wait_text('neo.connect.message', 'Appareil associé', 15)))
            else:
                report['existing_profile_reused'] = True
            tap('neo.connect.start', scroll=True)
            time.sleep(1)
            r = ui()
            consent = next((n for n in r.iter('node') if n.get('resource-id') == 'android:id/button1'), None)
            if consent is not None:
                labels = ' '.join(n.get('text', '') for n in r.iter('node'))
                check('Android consent dialog belongs to the VPN request', any(v in labels.lower() for v in ('vpn', 'connexion', 'connection')))
                x1,y1,x2,y2 = map(int,re.findall(r'\d+',consent.get('bounds')))
                sh('input tap %d %d'%((x1+x2)//2,(y1+y2)//2))
            check('Real WireGuard authenticated exchange is reported', bool(wait_text('neo.connect.status', 'Échange WireGuard authentifié', 30)))
            tap('neo.connect.test', scroll=True)
            check('OpenWebif actually responds inside the tunnel', bool(wait_text('neo.connect.message', 'OpenWebif a répondu dans le tunnel', 20)))
            report['tunnel_api_verified_on_lan'] = True
            tap('neo.connect.stop', scroll=True)
            check('Disconnect returns to the stopped state', bool(wait_text('neo.connect.status', 'Tunnel arrêté', 15)))
            time.sleep(1)
            check('Disconnect stops the owned foreground service', 'NeoConnectService' not in sh('dumpsys activity services com.metrixneo.tv'))
            open_connect(cold=True)
            check('Encrypted profile survives process recreation', node(ui(), 'neo.connect.start') is not None)
        else:
            tap('neo.connect.discover')
            check('Missing receiver plugin is reported without a false connection', bool(wait_text('neo.connect.message', 'Association locale indisponible', 15)))
            check('Failed discovery creates no profile or fingerprint', node(ui(), 'neo.connect.fingerprint') is None and node(ui(), 'neo.connect.start') is None)

        key(4)
        check('Single Back restores Neo Setup', node(ui(), 'neo.settings') is not None)
        tap('neo.connect.open')
        time.sleep(.5)
        key(4, 4)
        until = time.monotonic() + 10
        current = ''
        while time.monotonic() < until:
            current = foreground()
            if current and not current.startswith('com.metrixneo.tv/'):
                break
            time.sleep(.3)
        check('Two separate Back presses return to TV Home', bool(current) and not current.startswith('com.metrixneo.tv/'))
        report['final_component'] = current
        report['passed'] = True
    except Exception as e:
        report['passed'] = False
        report['error_type'] = type(e).__name__
        print('Test stopped: ' + type(e).__name__, flush=True)
    finally:
        if not report.get('passed'):
            # A failed UI assertion must not leave our test VPN active.
            sh('am stopservice -n com.metrixneo.tv/.connect.NeoConnectService', allow_failure=True)
        sh('rm -f /sdcard/neo-connect-test.xml', allow_failure=True)
        a.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
