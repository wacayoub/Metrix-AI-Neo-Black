#!/usr/bin/env python3
"""Check GStreamer surface resizing and state ACKs; restore Media3 afterwards."""
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
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    checks = []
    report = {'checks': checks, 'scope': 'Actual GStreamer first-frame callback, compositor bounds and PLAYING/PAUSED ACKs. No video-pixel, motion or audio certification.'}

    def sh(c):
        r = subprocess.run([a.adb, '-s', a.serial, 'shell', c], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        if r.returncode:
            raise RuntimeError('ADB command failed')
        return r.stdout

    def key(*codes):
        sh('input keyevent ' + ' '.join(map(str, codes))); time.sleep(.4)

    def ui():
        sh('uiautomator dump /sdcard/neo-gst-preview.xml')
        return ET.fromstring(sh('cat /sdcard/neo-gst-preview.xml'))

    def has(r, tag):
        return any(n.get('resource-id', '').rsplit('/', 1)[-1] == tag for n in r.iter('node'))

    def check(label, value):
        checks.append({'name': label, 'passed': bool(value)})
        print(('PASS ' if value else 'FAIL ') + label, flush=True)
        if not value:
            raise AssertionError(label)

    def logs():
        return sh("logcat -d -t 8000 -s NeoGst:I NeoGstNative:I NeoZap:I '*:S'").splitlines()

    def event(label, before, pattern):
        for _ in range(40):
            if any(re.search(pattern, line) for line in logs() if line not in before):
                check(label, True); return
            time.sleep(.4)
        check(label, False)

    def engine(name):
        key(82, 9, 23)
        root = ui()
        n = next(n for n in root.iter('node') if n.get('text', '').startswith(name))
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', n.get('bounds', '')))
        before = set(logs())
        sh(f'input tap {(x1+x2)//2} {(y1+y2)//2}')
        return before

    def video_bounds():
        for block in sh('dumpsys SurfaceFlinger').split('\n+ Layer ('):
            first = block.split('\n', 1)[0]
            if first.startswith('SurfaceView[com.metrixneo.tv/') and '(BLAST)' in first:
                m = re.search(r'Region VisibleRegion[^\n]*\n\s*\[\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\]', block)
                if m:
                    return tuple(map(int, m.groups()))
        return ()

    try:
        sh('am start -W -n com.metrixneo.tv/.MainActivity'); time.sleep(3)
        key(183, 8, 23, 126); time.sleep(4)
        before = engine('GStreamer')
        event('GStreamer decodes a real first video frame', before, r'NeoGst\s*: video_frame id=')
        key(4, 183)
        if not has(ui(), 'neo.miniTv'):
            key(185)
        check('GStreamer list exposes the Mini TV frame', has(ui(), 'neo.miniTv'))
        mini = video_bounds(); report['mini_bounds'] = mini
        check('GStreamer surface is actually 640 by 360 in Mini TV', len(mini) == 4 and mini[2]-mini[0] == 640 and mini[3]-mini[1] == 360)
        baseline = set(logs())
        before = set(logs()); key(127)
        event('GStreamer Mini TV pause is acknowledged', before, r'NeoGst\s*: event id=\d+ kind=8')
        before = set(logs()); key(126)
        event('GStreamer Mini TV play is acknowledged', before, r'NeoGst\s*: event id=\d+ kind=2')
        key(185)
        full = video_bounds(); report['transparent_bounds'] = full
        check('GStreamer transparent mode has full-screen video', len(full) == 4 and full[0:2] == (0, 0) and full[2] >= 1920 and full[3] >= 1080)
        before = set(logs()); key(127)
        event('GStreamer transparent view pause is acknowledged', before, r'NeoGst\s*: event id=\d+ kind=8')
        before = set(logs()); key(126)
        event('GStreamer transparent view play is acknowledged', before, r'NeoGst\s*: event id=\d+ kind=2')
        delta = [line for line in logs() if line not in baseline]
        check('GStreamer view changes produce no retune or pipeline error', not any('request id=' in line or re.search(r'NeoGst\s*: event id=\d+ kind=[45]', line) or 'error id=' in line for line in delta))
        key(185)
        before = engine('Media3')
        event('Media3 is restored and really decodes', before, r'NeoZap\s*: first_frame id=')
        key(4, 183)
        check('Final restored player retains Mini TV', has(ui(), 'neo.miniTv'))
        report['passed'] = True
    except Exception as error:
        report['passed'] = False; report['failure'] = type(error).__name__ + ': ' + str(error)
        print('FAIL ' + report['failure'], flush=True)
        try:
            key(183); engine('Media3'); key(4, 183)
        except Exception:
            pass
    finally:
        try:
            sh('rm -f /sdcard/neo-gst-preview.xml')
        except Exception:
            pass
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
