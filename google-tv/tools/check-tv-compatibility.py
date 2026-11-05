#!/usr/bin/env python3
"""Actual Android TV UI and decoder checks; no receiver writes or video pixel probes."""
import argparse
import json
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb', required=True)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=90)
    a = p.parse_args()
    report = {'native_channels': [], 'checks': [], 'limits': [
        'Decoder counters do not certify final panel motion or audible sound.',
        'Short HD IPTV test does not certify all channels, 4K or HDR.',
        'Only normal app streaming and read-only receiver API access.']}
    collector = None
    captured = []

    def sh(cmd):
        r = subprocess.run([a.adb, '-s', a.serial, 'shell', cmd], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=30)
        if r.returncode:
            raise RuntimeError('ADB operation failed')
        return r.stdout

    def key(*codes):
        for c in codes:
            sh('input keyevent ' + str(c))
            time.sleep(.3)

    def number(n):
        key(*(7 + int(d) for d in str(n)), 23)

    def ui():
        sh('uiautomator dump /sdcard/neo-compatibility.xml')
        return ET.fromstring(sh('cat /sdcard/neo-compatibility.xml'))

    def tag(n):
        return n.get('resource-id', '').rsplit('/', 1)[-1]

    def text(r):
        return ' '.join(n.get('text', '') for n in r.iter('node'))

    def has(r, name):
        return any(tag(n) == name for n in r.iter('node'))

    def check(name, ok):
        report['checks'].append({'name': name, 'passed': bool(ok)})
        print(('PASS ' if ok else 'FAIL ') + name, flush=True)

    def find(prefix, needle):
        for _ in range(12):
            for n in ui().iter('node'):
                if re.fullmatch(re.escape(prefix) + r'\d+', tag(n)) and needle.casefold() in text(n).casefold():
                    return int(tag(n).removeprefix(prefix))
            key(22)
        raise RuntimeError('Expected catalogue entry not found')

    def logs():
        return list(captured)

    def observations(lines):
        result = []
        for line in lines:
            m = re.search(r'(NeoZap|NeoPlayback)\s*:\s*(.*)', line)
            if not m:
                continue
            fields = dict(re.findall(r'(\w+)=([\w.-]+)', m[2]))
            result.append({'tag': m[1], 'event': m[2].split(' ', 1)[0], **{k: v for k, v in fields.items() if k in {
                'id', 'state', 'value', 'elapsed_ms', 'cached', 'code', 'playing', 'position_ms', 'buffered_ms', 'rendered', 'dropped'}}})
        return result

    try:
        report['manufacturer'] = sh('getprop ro.product.manufacturer').strip()
        report['model'] = sh('getprop ro.product.model').strip()
        report['version'] = re.search(r'versionName=(\S+)', sh('dumpsys package com.metrixneo.tv'))[1]
        key(224)
        sh('am start -W -n com.metrixneo.tv/.MainActivity')
        time.sleep(2)
        pid = sh('pidof com.metrixneo.tv').strip()
        collector = subprocess.Popen([a.adb, '-s', a.serial, 'shell',
            "logcat -T 1 --pid=" + pid + " -s NeoZap:I NeoPlayback:I '*:S'"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            encoding='utf-8', errors='replace')
        def collect():
            for line in collector.stdout:
                captured.append(line.rstrip())
        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        for n in (1, 2, 3):
            before = set(logs())
            key(183)
            number(n)
            time.sleep(5)
            r = ui()
            obs = observations([l for l in logs() if l not in before])
            error = next((x.get('text') for x in r.iter('node') if 'HTTP 400' in x.get('text', '') or 'Lecture impossible' in x.get('text', '')), None)
            report['native_channels'].append({'name': 'Rai ' + str(n), 'observations': obs, 'displayed_error': error})
            print('Native Rai ' + str(n) + ': ' + ('receiver HTTP 400' if error and 'HTTP 400' in error else 'see decoder evidence'), flush=True)
        key(186)
        number(find('neo.folder.', 'PURE IPTV') + 1)
        check('Provider folder opens', has(ui(), 'neo.folders'))
        number(find('neo.folder.', 'FRANCE FHD') + 1)
        check('Nested provider leaf opens channels', has(ui(), 'neo.channels'))
        tf1 = find('neo.channel.', 'TF1')
        before = set(logs())
        number(tf1 + 1)
        time.sleep(5)
        check('IPTV selection opens player', has(ui(), 'neo.player'))
        key(183)
        r = ui()
        if not has(r, 'neo.miniTv'):
            key(185)
            r = ui()
        check('Mini TV frame opens', has(r, 'neo.miniTv'))
        check('Preview identifies the playing IPTV channel', any(tag(n) == 'neo.playingPreviewName' and 'TF1' in n.get('text', '') for n in r.iter('node')))
        time.sleep(12)
        key(185)
        r = ui()
        check('Yellow opens transparent channel list', has(r, 'neo.channels') and not has(r, 'neo.miniTv'))
        time.sleep(12)
        key(185)
        check('Yellow restores Mini TV', has(ui(), 'neo.miniTv'))
        start = time.monotonic()
        while time.monotonic() - start < a.seconds:
            time.sleep(max(.01, min(5, a.seconds - (time.monotonic() - start))))
        obs = observations([l for l in logs() if l not in before])
        report['iptv'] = {'service': 'TF1 / PURE IPTV / FRANCE FHD', 'additional_observation_seconds': a.seconds, 'observations': obs}
        frames = [o for o in obs if o['event'] == 'first_frame']
        check('Media3 reports a first video frame', bool(frames))
        tune = frames[-1].get('id') if frames else None
        samples = [o for o in obs if o['tag'] == 'NeoPlayback' and o.get('id') == tune]
        progress = len(samples) >= 2 and int(samples[-1].get('rendered', -1)) > int(samples[0].get('rendered', -1)) and int(samples[-1].get('position_ms', 0)) > int(samples[0].get('position_ms', 0))
        check('Video counter and playback clock advance', progress)
        errors = [o for o in obs if o['event'] == 'error']
        check('No Media3 error during IPTV observation', not errors)
        check('IPTV still playing at last sample', bool(samples) and samples[-1].get('playing') == 'true' and samples[-1].get('state') == '3')
        report['app_process_survived'] = sh('pidof com.metrixneo.tv').strip() == pid
    except Exception as e:
        report['test_error_type'] = type(e).__name__
        print('Test interrupted: ' + type(e).__name__, flush=True)
    finally:
        if collector is not None:
            collector.terminate()
            collector.wait(timeout=5)
        for cmd in ('input keyevent 127', 'rm -f /sdcard/neo-compatibility.xml'):
            try:
                sh(cmd)  # Release the provider session before testing the other TV.
            except Exception:
                report.setdefault('cleanup_errors', []).append('ADB cleanup unavailable')
        a.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if not report.get('test_error_type') and all(c['passed'] for c in report['checks']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
