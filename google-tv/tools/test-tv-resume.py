#!/usr/bin/env python3
"""Restart only Neo on an authorized TV; verify real saved lists and playback callbacks."""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    checks = []
    report = {'checks': checks, 'scope': 'Actual saved channel/list position, cold/warm restart and real decoder callbacks. No panel-motion or audio certification.'}

    def sh(command, timeout=25):
        result = subprocess.run([args.adb, '-s', args.serial, 'shell', command], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=timeout)
        if result.returncode:
            raise RuntimeError('ADB action failed')
        return result.stdout

    def key(*codes):
        sh('input keyevent ' + ' '.join(str(c) for c in codes)); time.sleep(.2)

    def number(n):
        key(*(7 + int(d) for d in str(n)), 23)

    def ui():
        sh('uiautomator dump /sdcard/neo-resume-test.xml')
        return ET.fromstring(sh('cat /sdcard/neo-resume-test.xml'))

    def tag(n):
        return n.get('resource-id', '').rsplit('/', 1)[-1]

    def has(r, value):
        return any(tag(n) == value for n in r.iter('node'))

    def selected(r, prefix='neo.channel.'):
        return [int(tag(n).removeprefix(prefix)) for n in r.iter('node') if tag(n).startswith(prefix) and (n.get('checked') == 'true' or n.get('selected') == 'true')]

    def title(r):
        return next((n.get('text', '') for n in r.iter('node') if n.get('text', '').startswith('TV - ')), '')

    def name(r):
        return next((n.get('text', '') for n in r.iter('node') if tag(n) == 'neo.selectedChannelName'), '')

    def check(label, predicate):
        for _ in range(5):
            root = ui()
            if predicate(root):
                checks.append({'name': label, 'passed': True}); print('PASS ' + label, flush=True); return root
            time.sleep(.5)
        checks.append({'name': label, 'passed': False}); raise AssertionError(label)

    def logs():
        return sh("logcat -d -t 4000 -s NeoResume:I NeoZap:I '*:S'").splitlines()

    def event(label, before, pattern):
        for _ in range(35):
            if any(re.search(pattern, line) for line in logs() if line not in before):
                checks.append({'name': label, 'passed': True}); print('PASS ' + label, flush=True); return
            time.sleep(.4)
        checks.append({'name': label, 'passed': False}); raise AssertionError(label)

    def start(cold=True):
        if cold:
            sh('am force-stop com.metrixneo.tv')
        sh('am start -W -n com.metrixneo.tv/.MainActivity')

    def cold_restore(expected_title, at, selected_name):
        time.sleep(1.5)
        before = set(logs()); start()
        event('Cold restart reports an actual restored bookmark', before, r'NeoResume\s*: restored kind=')
        return check('Cold restart restores source and exact selection', lambda r: has(r, 'neo.channels') and title(r) == expected_title and selected(r) == [at] and name(r) == selected_name)

    def find_entry(prefix, needle):
        for _ in range(12):
            root = ui()
            for n in root.iter('node'):
                text = ' '.join(x.get('text', '') for x in n.iter('node'))
                if tag(n).startswith(prefix) and re.sub(r'\W', '', needle.casefold()) in re.sub(r'\W', '', text.casefold()):
                    return int(tag(n).removeprefix(prefix))
            key(22)
        raise AssertionError('Required real receiver entry unavailable: ' + needle)

    try:
        report['version'] = re.search(r'versionName=(\S+)', sh('dumpsys package com.metrixneo.tv'))[1]
        sh('input keyevent 224'); start(False); time.sleep(3)
        key(183)
        # Establish known playback independently of the bookmark left by a prior run.
        # Selecting an already-playing channel deliberately does not retune Neo.
        number(2); time.sleep(3)
        before = set(logs()); number(1)
        event('Baseline Rai 1 freshly decodes before restart checks', before, r'first_frame id=')
        key(183)
        check('All services is available', lambda r: title(r) == 'TV - Tous les services')
        key(22, 20, 20, 20, 20, 20, 20, 20)
        root = check('Browse to a later page without tuning', lambda r: selected(r) == [27])
        cold_restore(title(root), 27, name(root))

        key(183)
        before = set(logs()); number(2)
        event('A different real channel decodes before playback save test', before, r'first_frame id=')
        before = set(logs()); number(1)
        event('Rai 1 really decodes before saving playback', before, r'first_frame id=')
        key(20, 22, 20, 20, 20, 20, 20, 20, 20)
        root = check('Browse position can differ from playing channel', lambda r: selected(r) == [27])
        selected_name = name(root); time.sleep(1)
        key(4, 4)
        check('Double EXIT closes Neo', lambda r: not any(n.get('package') == 'com.metrixneo.tv' for n in r.iter('node')))
        before = set(logs()); start(False)
        event('Last channel automatically decodes after relaunch', before, r'first_frame id=')
        check('Playback screen is restored', lambda r: has(r, 'neo.player'))
        key(20)
        check('First list opening keeps the saved cursor', lambda r: selected(r) == [27] and name(r) == selected_name)

        key(3); time.sleep(.7); before = set(logs()); start(False)
        event('Warm return from HOME retunes the last channel', before, r'first_frame id=')
        check('Warm return keeps the exact list position', lambda r: selected(r) == [27] and name(r) == selected_name)

        key(186); pure = find_entry('neo.folder.', 'PURE IPTV'); number(pure+1)
        france = find_entry('neo.folder.', 'FRANCE FHD'); number(france+1)
        key(20, 20, 20, 20, 20)
        root = check('Native nested bouquet has a selected service', lambda r: has(r, 'neo.channels') and selected(r) == [5])
        cold_restore(title(root), 5, name(root))
        key(4)
        check('Restored nested bouquet Back returns to its real parent', lambda r: has(r, 'neo.folders') and selected(r, 'neo.folder.') == [france])
        time.sleep(2.2); key(4)
        check('Restored parent path returns to the provider in root', lambda r: has(r, 'neo.folders') and selected(r, 'neo.folder.') == [pure])

        key(184); hotbird = find_entry('neo.group.', 'Hotbird'); number(hotbird+1)
        check('Real satellite services are loaded', lambda r: has(r, 'neo.channels') and any(tag(n) == 'neo.channel.0' for n in r.iter('node')))
        key(22, 20, 20, 20)
        root = check('Satellite cursor is on a later page', lambda r: selected(r) == [23])
        cold_restore(title(root), 23, name(root))

        # Leave a known real channel ready to resume, with a separate saved list cursor.
        key(183); before = set(logs()); number(2)
        event('Final channel change really decodes', before, r'first_frame id=')
        before = set(logs()); number(1)
        event('Final Rai 1 playback decodes', before, r'first_frame id=')
        key(20, 22, 20, 20, 20, 20, 20, 20, 20)
        check('Final saved list position is row 28', lambda r: selected(r) == [27])
        time.sleep(1.5); key(4, 4)
        check('Final exit returns to the TV launcher', lambda r: not any(n.get('package') == 'com.metrixneo.tv' for n in r.iter('node')))
        report['passed'] = True
    except Exception as error:
        report['passed'] = False; report['failure'] = type(error).__name__ + ': ' + str(error)
        print('FAIL ' + report['failure'], flush=True)
    finally:
        try:
            sh('rm -f /sdcard/neo-resume-test.xml')
        except Exception:
            pass
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
