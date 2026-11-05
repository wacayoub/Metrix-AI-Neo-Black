#!/usr/bin/env python3
"""Exercise Neo's implemented remote flows on an already authorized Android TV.

Uses input events, accessibility nodes and gfxinfo; never reads video pixels or writes to Vu+.
Start on Neo's channel list. A paused player may remain underneath the list for benchmarking.
"""
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
    parser.add_argument('--gfx-output', type=Path, required=True)
    parser.add_argument('--providers-only', action='store_true')
    parser.add_argument('--wrap-only', action='store_true', help='Only check circular row navigation and existing page keys.')
    args = parser.parse_args()
    results = []
    report = {'checks': results, 'scope': 'Implemented remote/UI flows; no visual/audio certification of the video plane.'}

    def shell(command, timeout=25):
        result = subprocess.run([args.adb, '-s', args.serial, 'shell', command], capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode:
            raise RuntimeError('ADB action failed')
        return result.stdout

    def key(*codes):
        if any(a == b == 4 for a, b in zip(codes, codes[1:])):
            # These calls traverse two parent screens; a quick double Back now exits.
            for index, code in enumerate(codes):
                if index and code == codes[index-1] == 4:
                    time.sleep(2.2)
                shell('input keyevent ' + str(int(code)))
        else:
            shell('input keyevent ' + ' '.join(str(int(code)) for code in codes))
        time.sleep(.18)

    def number(value):
        key(*(7 + int(digit) for digit in str(value)), 23)

    def ui():
        shell('uiautomator dump /sdcard/neo-functional-test.xml')
        return ET.fromstring(shell('cat /sdcard/neo-functional-test.xml'))

    def tag(node):
        return node.get('resource-id', '').rsplit('/', 1)[-1]

    def has(root, value):
        return any(tag(node) == value for node in root.iter('node'))

    def text(root):
        return ' '.join(node.get('text', '') for node in root.iter('node'))

    def selected(root, prefix):
        return [int(tag(node).removeprefix(prefix)) for node in root.iter('node')
                if tag(node).startswith(prefix) and (node.get('selected') == 'true' or node.get('checked') == 'true')]

    def check(name, predicate):
        start = time.monotonic()
        for _ in range(3):
            root = ui()
            if predicate(root):
                results.append({'name': name, 'passed': True, 'check_seconds': round(time.monotonic()-start, 2)})
                print('PASS ' + name, flush=True)
                return root
            time.sleep(.4)
        results.append({'name': name, 'passed': False})
        raise AssertionError(name)

    def page(name, value):
        return check(name, lambda root: has(root, value))

    def back_to(value, maximum=3):
        for _ in range(maximum):
            key(4)
            if has(ui(), value):
                return
        raise AssertionError('Back did not reach ' + value)

    def find_entry(prefix, needle, maximum=10):
        for _ in range(maximum):
            root = ui()
            for node in root.iter('node'):
                if tag(node).startswith(prefix) and re.sub(r'\W', '', needle.casefold()) in re.sub(r'\W', '', text(node).casefold()):
                    return int(tag(node).removeprefix(prefix))
            key(22)
        raise AssertionError('Expected receiver entry not found: ' + needle)

    def player_logs():
        process = shell('pidof com.metrixneo.tv').strip()
        if not process.isdigit():
            raise AssertionError('Neo process missing')
        return shell("logcat -d --pid=" + process + " -s NeoZap:I NeoGst:I NeoGstNative:I '*:S'").splitlines()

    def event(name, action, pattern, timeout=20):
        before = set(player_logs())
        started = time.monotonic()
        action()
        while time.monotonic() - started < timeout:
            if any(re.search(pattern, line) for line in player_logs() if line not in before):
                results.append({'name': name, 'passed': True, 'check_seconds': round(time.monotonic()-started, 2), 'verification': 'player_state_or_decoder_callback'})
                print('PASS ' + name, flush=True)
                return
            time.sleep(.5)
        results.append({'name': name, 'passed': False})
        raise AssertionError(name)

    try:
        installed_version = re.search(r'versionName=(\S+)', shell('dumpsys package com.metrixneo.tv'))
        if not installed_version:
            raise AssertionError('Installed Neo version unavailable')
        report['app_version'] = installed_version[1]
        if args.wrap_only:
            # A startup refresh can restore the saved bouquet after an early Red key.
            for _ in range(3):
                key(183)
                current = ui()
                if any(n.get('text') == 'TV - Tous les services' for n in current.iter('node')):
                    break
                time.sleep(.5)
            root = check('All services starts on row one', lambda r: has(r, 'neo.channels') and selected(r, 'neo.channel.') == [0] and any(n.get('text') == 'TV - Tous les services' for n in r.iter('node')))
            total = re.search(r'\b1 / (\d+)\s+•', text(root))
            if not total or int(total[1]) < 21:
                raise AssertionError('Expected a real channel catalogue larger than one page')
            count = int(total[1])
            report['channel_count'] = count
            key(19)
            check('Up from channel one selects the last channel', lambda r: selected(r, 'neo.channel.') == [count-1])
            check('Last channel page is displayed', lambda r: [int(tag(n).removeprefix('neo.channel.')) for n in r.iter('node') if tag(n).startswith('neo.channel.')] == list(range((count-1)//20*20, count)))
            key(20)
            check('Down from last channel returns to row one', lambda r: selected(r, 'neo.channel.') == [0])
            key(20)
            check('Normal Down still selects row two', lambda r: selected(r, 'neo.channel.') == [1])
            key(19)
            check('Normal Up still selects row one', lambda r: selected(r, 'neo.channel.') == [0])
            key(21)
            check('Previous page remains bounded at row one', lambda r: selected(r, 'neo.channel.') == [0])
            key(167)
            check('CH down retains twenty-row pagination', lambda r: selected(r, 'neo.channel.') == [20])
            key(166)
            check('CH up retains twenty-row pagination', lambda r: selected(r, 'neo.channel.') == [0])
            key(19, 19)
            check('Up continues backwards on the last page', lambda r: selected(r, 'neo.channel.') == [count-2])
            key(20, 20)
            check('Down crosses the end back to row one', lambda r: selected(r, 'neo.channel.') == [0])

            for color, page_tag, prefix in ((184, 'neo.satellites', 'neo.group.'), (186, 'neo.folders', 'neo.folder.')):
                key(color)
                check(page_tag + ' starts on row one', lambda r: has(r, page_tag) and selected(r, prefix) == [0])
                key(19)
                root = check(page_tag + ' Up selects last visible entry', lambda r: len(selected(r, prefix)) == 1 and selected(r, prefix)[0] > 0 and selected(r, prefix)[0] == max(int(tag(n).removeprefix(prefix)) for n in r.iter('node') if tag(n).startswith(prefix)))
                report[page_tag + '_last_index'] = selected(root, prefix)[0]
                key(20)
                check(page_tag + ' Down returns to row one', lambda r: selected(r, prefix) == [0])
            key(183)
            check('Final list is on row one', lambda r: has(r, 'neo.channels') and selected(r, 'neo.channel.') == [0])

            def details_match(root):
                indices = selected(root, 'neo.channel.')
                if len(indices) != 1:
                    return False
                labels = {tag(n): n.get('text', '') for n in root.iter('node')}
                name = labels.get('neo.selectedChannelName', '')
                return bool(name) and labels.get('neo.channelText.' + str(indices[0]), '').split('   │   ', 1)[0] == name

            shell('input keyevent --longpress 20')
            time.sleep(.5)
            check('Held Down retains both initial and repeated navigation', lambda r: selected(r, 'neo.channel.') == [2])
            check('EPG pane matches selected channel after held key release', details_match)
            shell('input keyevent 19 19')
            time.sleep(.5)
            check('Rapid Up burst preserves every movement', lambda r: selected(r, 'neo.channel.') == [0])
            check('EPG pane settles on the selected channel after burst', details_match)
            key(20)
            check('Isolated Down updates the EPG pane consistently', lambda r: selected(r, 'neo.channel.') == [1] and details_match(r))
            key(19)
            check('Final settled list returns to row one', lambda r: selected(r, 'neo.channel.') == [0] and details_match(r))
            report['passed'] = True
            return 0
        if not args.providers_only:
            key(127, 183)
            root = page('All services opens', 'neo.channels')
            check('Twenty rows and selected first channel', lambda root: len([n for n in root.iter('node') if tag(n).startswith('neo.channel.')]) == 20 and selected(root, 'neo.channel.') == [0])
            shell('dumpsys gfxinfo com.metrixneo.tv reset')
            shell('for i in 1 2 3 4 5 6 7 8 9 10; do input keyevent 20; sleep 0.10; done; for i in 1 2 3 4 5 6 7 8 9 10; do input keyevent 19; sleep 0.10; done; input keyevent 22 22 21 21', timeout=40)
            time.sleep(.4)
            gfx = shell('dumpsys gfxinfo com.metrixneo.tv framestats')
            args.gfx_output.parent.mkdir(parents=True, exist_ok=True)
            args.gfx_output.write_text(gfx, encoding='utf-8')
            report['gfxinfo'] = {key: re.search(pattern, gfx)[1] for key, pattern in {
                'total_frames': r'Total frames rendered: (\d+)',
                'janky_frames': r'Janky frames: (\d+)',
                'median_ms': r'50th percentile: (\d+)ms',
                'p90_ms': r'90th percentile: (\d+)ms',
                'p95_ms': r'95th percentile: (\d+)ms',
            }.items() if re.search(pattern, gfx)}
            check('Navigation burst returns to first row', lambda r: selected(r, 'neo.channel.') == [0])
            key(22)
            check('Right advances twenty channels', lambda r: selected(r, 'neo.channel.') == [20])
            key(166)
            check('CH up pages channel list', lambda r: selected(r, 'neo.channel.') == [0])
            key(167)
            check('CH down pages channel list', lambda r: selected(r, 'neo.channel.') == [20])
            key(21)
            number(10001)
            check('Five digit channel number is preserved', lambda r: has(r, 'neo.player') and '10001' in text(r))
            key(183)
            number(1)
            page('Numeric channel selection opens player', 'neo.player')
            key(165)
            page('INFO opens programme details', 'neo.details')
            key(4)
            page('Back from details restores player', 'neo.player')
            key(20)
            page('Down opens channel list', 'neo.channels')
            key(165)
            page('INFO on list opens guide', 'neo.guide')
            key(22)
            page('Guide channel navigation stays in guide', 'neo.guide')
            key(23)
            page('Guide OK tunes selected service', 'neo.player')
            key(222)
            page('Audio key opens tracks', 'neo.tracks')
            key(23)
            page('Track confirmation returns to player', 'neo.player')

            shell('input keyevent --longpress 82')
            page('Held MENU opens once', 'neo.menu')
            number(1)
            check('Plugin dialog honestly states limitation', lambda r: 'pas port' in text(r) or 'ne sont pas port' in text(r))
            key(23)
            page('OK closes dialog once', 'neo.menu')
            number(2)
            page('Setup opens through menu number', 'neo.settings')
            key(4)
            page('Setup Back restores list', 'neo.channels')
            key(82)
            number(3)
            page('Timers read-only view opens', 'neo.details')
            check('Timers read-only request completes', lambda r: has(r, 'neo.details') and 'Chargement des programmations' not in text(r) and 'Programmations indisponibles' not in text(r))
            key(4)
            number(4)
            check('Standby dialog does not power off receiver', lambda r: 'POWER' in text(r) and 'Vu+' in text(r))
            key(23)
            number(5)
            check('Information shows installed version', lambda r: has(r, 'neo.details') and report['app_version'] in text(r))
            key(4, 4)

        key(186)
        root = page('Blue opens native bouquet root', 'neo.folders')
        report['weather_city_visible'] = 'Casablanca' in text(root)
        report['clock_visible'] = bool(re.search(r'\b\d{2}:\d{2}\b', text(root)))
        pure = find_entry('neo.folder.', 'PURE IPTV')
        before_page = selected(ui(), 'neo.folder.')[0]
        key(166)
        check('CH up pages native folders', lambda r: selected(r, 'neo.folder.') == [max(0, before_page-20)])
        key(167)
        number(pure+1)
        page('Nested provider folder opens', 'neo.folders')
        france = find_entry('neo.folder.', 'FRANCE FHD')
        # Move to the desired row without activating it, then hold OK.
        # Number selection activates; choose first category with number on this real receiver.
        number(france+1)
        page('Nested leaf displays channels', 'neo.channels')
        key(4)
        page('Leaf Back restores parent folder', 'neo.folders')
        check('Parent selection restored', lambda r: selected(r, 'neo.folder.') == [france])
        shell('input keyevent --longpress 23')
        page('Held OK opens leaf once without accidental tune', 'neo.channels')
        key(4, 4)
        check('Provider selection restored in root', lambda r: has(r, 'neo.folders') and selected(r, 'neo.folder.') == [pure])
        number(pure+1)
        number(france+1)
        page('Cached nested path reopens', 'neo.channels')

        key(184)
        page('Green opens satellite list', 'neo.satellites')
        key(167)
        check('CH down pages satellites', lambda r: selected(r, 'neo.group.') == [20])
        key(166)
        check('CH up pages satellites', lambda r: selected(r, 'neo.group.') == [0])
        hotbird = find_entry('neo.group.', 'Hotbird')
        number(hotbird+1)
        check('Satellite number opens its populated channel list', lambda r: has(r, 'neo.channels') and 'hotbird' in text(r).casefold().replace(' ', '') and any(tag(n).startswith('neo.channel.') for n in r.iter('node')))
        key(184)
        number(hotbird+1)
        check('Cached satellite reopens populated', lambda r: has(r, 'neo.channels') and 'hotbird' in text(r).casefold().replace(' ', '') and any(tag(n).startswith('neo.channel.') for n in r.iter('node')))
        was_mini = has(ui(), 'neo.miniTv')
        key(185)
        check('Yellow toggles Mini TV and transparent list', lambda r: has(r, 'neo.channels') and has(r, 'neo.miniTv') != was_mini)
        key(185, 183)
        number(1)
        page('Final return to normal TV playback', 'neo.player')
        event('Media3 pause changes actual player state', lambda: key(127), r'playing id=.*value=false')
        event('Media3 resume changes actual player state', lambda: key(126), r'playing id=.*value=true')
        event('CH up decodes next satellite channel', lambda: key(166), r'first_frame id=')
        key(20)
        check('CH up selects the next service', lambda r: selected(r, 'neo.channel.') == [1])
        key(23)
        event('CH down decodes previous satellite channel', lambda: key(167), r'first_frame id=')
        event('Zero recalls the previous service', lambda: key(7), r'first_frame id=')
        key(20)
        check('Recall restores the previous channel position', lambda r: selected(r, 'neo.channel.') == [1])

        key(186)
        pure = find_entry('neo.folder.', 'PURE IPTV')
        number(pure+1)
        france = find_entry('neo.folder.', 'FRANCE FHD')
        number(france+1)
        event('Media3 decodes the IPTV FHD service', lambda: number(2), r'first_frame id=')
        key(82)
        number(2)
        page('Setup retains player selector', 'neo.settings')
        def activate_gstreamer():
            key(22, 23)
            check('GStreamer selection is visible', lambda r: 'GStreamer  ✓' in text(r))
            key(4, 82, 4)
            page('GStreamer uses the same TV interface', 'neo.player')
        gst_error = None
        try:
            event('Optimized APK initializes GStreamer and opens stream', activate_gstreamer, r'NeoGst\s*: event id=.*kind=2', timeout=30)
            event('GStreamer pause reaches native pipeline', lambda: key(127), r'NeoGst\s*: event id=.*kind=8')
            event('GStreamer resume reaches native pipeline', lambda: key(126), r'NeoGst\s*: event id=.*kind=2')
            key(222)
            page('GStreamer exposes the discovered audio track', 'neo.tracks')
            event('GStreamer accepts audio stream selection', lambda: key(23), r'NeoGstNative\s*: track id=.*type=1 index=0 accepted=1')
            page('Audio selection returns to GStreamer playback', 'neo.player')
            event('GStreamer CH up decodes next IPTV service', lambda: key(166), r'NeoGst\s*: video_frame id=', timeout=30)
            event('GStreamer CH down decodes previous IPTV service', lambda: key(167), r'NeoGst\s*: video_frame id=', timeout=30)
        except AssertionError as error:
            # Restore the working default and test it even when the optional engine fails.
            gst_error = error
        key(82)
        number(2)
        page('Reopen selector with GStreamer selected', 'neo.settings')
        event('Return to Media3 decodes IPTV again', lambda: key(21, 23), r'first_frame id=')
        check('Media3 selection is restored', lambda r: 'Media3  ✓' in text(r))
        key(4, 82, 4)
        page('Final FHD playback with Media3 restored', 'neo.player')
        if gst_error:
            raise gst_error
        report['passed'] = True
    except Exception as error:
        report['passed'] = False
        report['failure'] = type(error).__name__ + ': ' + str(error)
        print('FAIL ' + report['failure'], flush=True)
    finally:
        try:
            shell('rm -f /sdcard/neo-functional-test.xml')
        except Exception:
            pass
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
