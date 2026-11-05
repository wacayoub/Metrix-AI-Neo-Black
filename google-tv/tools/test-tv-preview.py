#!/usr/bin/env python3
"""Verify one live player resized between Mini TV, translucent list and full screen.

Uses authorized ADB UI nodes and sanitized decoder counters; never probes video pixels.
"""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb', required=True)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    checks = []
    report = {'checks': checks, 'scope': 'Actual UI bounds, single Media3 tune, rendered counters and persisted view choice; no video-pixel or audio certification.'}

    def sh(command):
        r = subprocess.run([args.adb, '-s', args.serial, 'shell', command], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=30)
        if r.returncode:
            raise RuntimeError('ADB command failed')
        return r.stdout

    def key(*codes):
        sh('input keyevent ' + ' '.join(map(str, codes)))
        time.sleep(.35)

    def ui():
        sh('uiautomator dump /sdcard/neo-preview-test.xml')
        return ET.fromstring(sh('cat /sdcard/neo-preview-test.xml'))

    def tag(n):
        return n.get('resource-id', '').rsplit('/', 1)[-1]

    def node(root, name):
        return next((n for n in root.iter('node') if tag(n) == name), None)

    def has(root, name):
        return node(root, name) is not None

    def bounds(n):
        return tuple(map(int, re.findall(r'\d+', n.get('bounds', '')))) if n is not None else ()

    def video_bounds():
        # Compose accessibility omits the video node occluded by the transparent frame.
        # Read only our actual compositor layer geometry, never video pixels.
        data = sh('dumpsys SurfaceFlinger')
        for block in data.split('\n+ Layer ('):
            first = block.split('\n', 1)[0]
            if not first.startswith('SurfaceView[com.metrixneo.tv/') or '(BLAST)' not in first:
                continue
            m = re.search(r'Region VisibleRegion[^\n]*\n\s*\[\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\]', block)
            if m:
                return tuple(map(int, m.groups()))
        return ()

    def check(label, predicate):
        for _ in range(4):
            root = ui()
            if predicate(root):
                checks.append({'name': label, 'passed': True})
                print('PASS ' + label, flush=True)
                return root
            time.sleep(.4)
        checks.append({'name': label, 'passed': False})
        raise AssertionError(label)

    def logs():
        return sh("logcat -d -t 8000 -s NeoZap:I NeoPlayback:I '*:S'").splitlines()

    def requests():
        return {line for line in logs() if 'NeoZap' in line and 'request id=' in line}

    def sample():
        pattern = r'id=(\d+) state=(\d+) playing=(\w+) position_ms=(\d+) buffered_ms=(\d+) rendered=(-?\d+) dropped=(-?\d+)'
        values = [re.search(pattern, line) for line in logs() if 'NeoPlayback' in line]
        values = [m for m in values if m]
        if not values:
            return None
        m = values[-1]
        return dict(zip(('id', 'state', 'playing', 'position_ms', 'buffered_ms', 'rendered', 'dropped'),
                        (int(m[1]), int(m[2]), m[3] == 'true', *(int(m[i]) for i in range(4, 8)))))

    def progressing(label):
        before = sample()
        for _ in range(28):
            time.sleep(.5)
            after = sample()
            if before is None:
                before = after
            elif after and after['id'] == before['id'] and after['state'] == 3 and after['playing'] and after['rendered'] > before['rendered'] and after['position_ms'] > before['position_ms']:
                checks.append({'name': label, 'passed': True})
                report.setdefault('decoder_samples', []).append({'before': before, 'after': after})
                print('PASS ' + label, flush=True)
                return
        checks.append({'name': label, 'passed': False})
        raise AssertionError(label)

    def screenshot(name):
        remote = '/sdcard/neo-preview.png'
        sh('screencap -p ' + remote)
        local = args.output.parent / name
        r = subprocess.run([args.adb, '-s', args.serial, 'pull', remote, str(local)], capture_output=True, timeout=20)
        if r.returncode:
            raise RuntimeError('UI screenshot transfer failed')

    try:
        report['version'] = re.search(r'versionName=(\S+)', sh('dumpsys package com.metrixneo.tv'))[1]
        sh('input keyevent 224')
        sh('am start -W -n com.metrixneo.tv/.MainActivity')
        time.sleep(3)
        key(183, 8, 23, 126)  # Real Rai 1, explicitly resume a previously paused fixture.
        time.sleep(8)
        key(183)
        root = check('Real channel list opens with twenty rows', lambda r: has(r, 'neo.channels') and sum(bool(re.fullmatch(r'neo\.channel\.\d+', tag(n))) for n in r.iter('node')) == 20)
        if not has(root, 'neo.miniTv'):
            key(185)
        root = check('Mini TV is available with the playing channel label', lambda r: has(r, 'neo.miniTv') and 'Rai 1' in (node(r, 'neo.playingPreviewName').get('text', '') if node(r, 'neo.playingPreviewName') is not None else ''))
        mini = bounds(node(root, 'neo.miniTv'))
        surface = video_bounds()
        report['mini_bounds'] = mini
        report['mini_surface_bounds'] = surface
        check('Single video surface fits the Mini TV frame', lambda r: len(surface) == 4 and all(abs(x-y) <= 2 for x, y in zip(mini, surface)) and 1.70 < (surface[2]-surface[0]) / max(1, surface[3]-surface[1]) < 1.85)
        baseline = requests()
        key(20)
        check('Browsing another channel keeps Rai 1 in Mini TV', lambda r: node(r, 'neo.selectedChannelName') is not None and node(r, 'neo.selectedChannelName').get('text') == 'Rai 2' and 'Rai 1' in node(r, 'neo.playingPreviewName').get('text', ''))
        progressing('Video decode and position continue in Mini TV')
        screenshot('sony-mini-tv-2026-11-02.png')
        key(185)
        root = check('Yellow opens transparent list without the Mini TV frame', lambda r: has(r, 'neo.channels') and not has(r, 'neo.miniTv'))
        full = video_bounds()
        report['transparent_surface_bounds'] = full
        check('Transparent list uses the full-screen video surface', lambda r: len(full) == 4 and full[0:2] == (0, 0) and full[2] > 2*(surface[2]-surface[0]) and full[3] > 2*(surface[3]-surface[1]))
        progressing('Video decode and position continue behind transparent list')
        screenshot('sony-transparent-list-2026-11-02.png')
        key(185)
        sh('input keyevent --longpress 185')
        check('Held Yellow toggles view only once', lambda r: has(r, 'neo.channels') and not has(r, 'neo.miniTv'))
        if requests() - baseline:
            raise AssertionError('Changing list view must not tune a new stream')
        checks.append({'name': 'View changes and browsing do not retune the stream', 'passed': True})
        print('PASS View changes and browsing do not retune the stream', flush=True)
        key(23)
        check('OK returns to full-screen playback', lambda r: has(r, 'neo.player') and not has(r, 'neo.miniTv'))
        key(183)
        time.sleep(1)
        sh('am force-stop com.metrixneo.tv')
        sh('am start -W -n com.metrixneo.tv/.MainActivity')
        time.sleep(4)
        key(183)
        check('Transparent view choice survives process restart', lambda r: has(r, 'neo.channels') and not has(r, 'neo.miniTv'))
        key(185)
        time.sleep(1)
        sh('am force-stop com.metrixneo.tv')
        sh('am start -W -n com.metrixneo.tv/.MainActivity')
        time.sleep(4)
        key(183)
        check('Mini TV choice survives process restart', lambda r: has(r, 'neo.miniTv'))
        report['passed'] = True
    except Exception as error:
        report['passed'] = False
        report['failure'] = type(error).__name__ + ': ' + str(error)
        print('FAIL ' + report['failure'], flush=True)
    finally:
        try:
            sh('rm -f /sdcard/neo-preview-test.xml /sdcard/neo-preview.png')
        except Exception:
            pass
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
