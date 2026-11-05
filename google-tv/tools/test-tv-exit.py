#!/usr/bin/env python3
"""Verify EXIT on an authorized TV; finishes on its resolved Home launcher.

Sends remote keys, launches Neo, reads activity state and sanitized app logs.
The playback case opens the first real service. Never modifies the receiver.
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--ui-only', action='store_true', help='Test exit controls without requiring an available satellite stream.')
    args = parser.parse_args()
    checks = []
    report = {'checks': checks, 'scope': 'Actual Android TV exit/navigation and playback-state callbacks; no video motion or audio certification.'}

    def shell(command, timeout=25):
        result = subprocess.run([args.adb, '-s', args.serial, 'shell', command], capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode:
            raise RuntimeError('ADB action failed')
        return result.stdout

    def key(*codes):
        shell('input keyevent ' + ' '.join(str(int(code)) for code in codes))
        time.sleep(.15)

    def foreground():
        match = re.search(r'topResumedActivity=.*?\s([^\s{}]+/[^\s{}]+)', shell('dumpsys activity activities'))
        return match[1] if match else ''

    def logs():
        return shell("logcat -d -t 3000 -s NeoExit:I NeoZap:I '*:S'").splitlines()

    def check(name, predicate):
        passed = bool(predicate())
        checks.append({'name': name, 'passed': passed})
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        if not passed:
            raise AssertionError(name)

    def wait_for(predicate, seconds=8):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            if predicate():
                return True
            time.sleep(.25)
        return False

    def neo():
        return foreground().startswith('com.metrixneo.tv/')

    def launch():
        shell('am start -W -n com.metrixneo.tv/.MainActivity')
        check('Neo opens with saved configuration', lambda: wait_for(neo))
        time.sleep(.5)

    def new_event(before, pattern):
        return any(re.search(pattern, line) for line in logs() if line not in before)

    try:
        home = shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME').strip().splitlines()[-1]
        if '/' not in home:
            raise AssertionError('No Home launcher resolved')
        report['home_component'] = home
        version = re.search(r'versionName=(\S+)', shell('dumpsys package com.metrixneo.tv'))
        report['app_version'] = version[1] if version else 'unknown'
        shell('input keyevent 224')
        # A user-installed Home accessibility service may redirect the resolved launcher.
        # Compare with the actual HOME key; never disable or reconfigure that service.
        key(3)
        time.sleep(2)
        effective_home = foreground()
        if not effective_home or effective_home.startswith('com.metrixneo.tv/'):
            raise AssertionError('Physical HOME did not reach an external launcher')
        report['physical_home_component'] = effective_home
        report['home_redirected'] = effective_home.split('/')[0] != home.split('/')[0]
        home_package = effective_home.split('/')[0]
        launch()

        before = set(logs())
        key(4)
        check('One Back stays inside Neo', neo)
        check('One physical Back produces exactly one app Back', lambda: sum('back_first' in line for line in logs() if line not in before) == 1)
        time.sleep(2.2)
        key(4)
        check('Two Back presses more than two seconds apart do not exit', neo)
        time.sleep(2.2)
        key(4, 20, 4)
        check('Navigation between Back presses cancels exit confirmation', neo)
        time.sleep(2.2)
        before = set(logs())
        shell('input keyevent --longpress 4')
        check('Held Back does not exit Neo', neo)
        check('Held Back repeat is ignored', lambda: sum('back_first' in line for line in logs() if line not in before) == 1)

        time.sleep(2.2)
        key(4, 4)
        check('Double Back reaches the same Home as the physical HOME key', lambda: wait_for(lambda: foreground().startswith(home_package + '/')))
        check('Closed Neo task is removed from Recents', lambda: 'realActivity=com.metrixneo.tv/' not in shell('dumpsys activity recents'))

        launch()
        key(4)
        check('First Back after relaunch does not exit', neo)
        key(82)
        key(111)
        check('One EXIT/Escape in menu stays inside Neo', neo)
        key(111)
        check('Double EXIT/Escape in menu opens Home', lambda: wait_for(lambda: foreground().startswith(home_package + '/')))

        launch()
        key(82, 9, 23)
        time.sleep(.5)
        shell('uiautomator dump /sdcard/neo-exit-test.xml')
        check('Setup is open for focused-control exit test', lambda: 'neo.settings' in shell('cat /sdcard/neo-exit-test.xml'))
        key(4, 4)
        check('Double Back from Setup opens Home', lambda: wait_for(lambda: foreground().startswith(home_package + '/')))

        if args.ui_only:
            report['playback_exit_test'] = 'Not run: UI-only selection; no decoder claim.'
            report['final_component'] = foreground()
            report['passed'] = True
            return 0

        launch()
        before = set(logs())
        key(183, 8, 23)
        check('Real first channel decodes before playback exit test', lambda: wait_for(lambda: new_event(before, r'first_frame id='), seconds=20))
        check('Real player is playing before exit', lambda: wait_for(lambda: new_event(before, r'playing id=.*value=true')))
        before = set(logs())
        key(4, 4)
        check('Double Back from playback opens Home', lambda: wait_for(lambda: foreground().startswith(home_package + '/')))
        check('Playback pauses when exiting', lambda: wait_for(lambda: new_event(before, r'playing id=.*value=false')))
        check('Playback task is removed from Recents', lambda: 'realActivity=com.metrixneo.tv/' not in shell('dumpsys activity recents'))
        report['final_component'] = foreground()
        report['passed'] = True
    except Exception as error:
        report['passed'] = False
        report['failure'] = type(error).__name__ + ': ' + str(error)
        print('FAIL ' + report['failure'], flush=True)
    finally:
        try:
            shell('rm -f /sdcard/neo-exit-test.xml')
        except Exception:
            pass
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
