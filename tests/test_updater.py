"""Offline integration tests of updater against a simulated Vu+ Zero 4K file system."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO=Path(__file__).resolve().parents[1]
UPDATER=REPO/'metrix_neo_updater.py'
def fixture():
    """Prepare a minimal OpenATV 8.0.1 + MyMetrixLite/V2 state."""
    work=tempfile.TemporaryDirectory()
    root=Path(work.name)
    settings=root/'etc/enigma2/settings'; settings.parent.mkdir(parents=True)
    settings.write_text('config.skin.primary_skin=MetrixHD/skin.MySkin.xml\n'
                        'config.plugins.MyMetrixLiteOther.EHDenabled=1\n'
                        'config.plugins.MyMetrixLiteColors.layeraselectionbackground=27408B\n'
                        'config.plugins.MyMetrixLiteColors.layerbbackground=0A173A\n'
                        'config.plugins.MyMetrixLiteColors.infobarprogress=1BA1E2\n'
                        'config.plugins.MyMetrixLiteColors.menusymbolbackground=0F0F0F\n')
    (root/'etc/image-version').write_text('box_type=vuzero4k\nversion=8.0.1\n')
    skindir=root/'usr/share/enigma2/MetrixHD';skindir.mkdir(parents=True)
    (skindir/'skin.MySkin.xml').write_text('<skin><include filename="/usr/share/enigma2/MetrixHD/skinfiles/skin_base.MySkin.xml" /></skin>')
    (skindir/'fonts').mkdir()
    (skindir/'fonts/Raleway-Regular.ttf').write_bytes(b'fake-font-fixture')
    xml=skindir/'skinfiles/skin_base.MySkin.xml';xml.parent.mkdir()
    colors={'layer-a-background':'1A0F0F0F','layer-a-selection-background':'1A27408B',
            'layer-b-background':'1A0A173A','menusymbolbackground':'1A0F0F0F',
            'infobarprogress':'1A1BA1E2','layer-a-progress':'1A27408B',
            'layer-a-underline':'00BDBDBD','epg-event-selected-background':'1A27408B'}
    xml.write_text('<skin><output id="0"><resolution xres="1920" yres="1080" bpp="32" /></output><colors>\n' +
                   '\n'.join('<color name="%s" value="#%s" />'%(k,v) for k,v in colors.items()) +
                   '</colors><fonts>' +
                   '<font filename="/usr/share/fonts/ae_AlMateen.ttf" name="Replacement" replacement="1" />' +
                   '</fonts></skin>')
    return work,root,settings,xml


def run(cmd, root, source, home):
    env=dict(os.environ, METRIX_NEO_TEST_ROOT=str(root), METRIX_NEO_SOURCE=source.as_uri()+'/', METRIX_NEO_HOME=str(home), METRIX_NEO_V3_MANIFEST=str(root/'home/root/MetrixNeoBlack_v3_backup/manifest.json'))
    return subprocess.run([sys.executable,str(UPDATER),cmd],env=env,capture_output=True,text=True)


def setup():
    t,root,settings,xml=fixture()
    source=Path(tempfile.mkdtemp(prefix='metrix-neo-source-'))
    rel=source/'releases/0.3.0'
    rel.mkdir(parents=True)
    script=rel/'apply.py'
    script.write_bytes((REPO/'releases/0.3.0/Metrix_AI_Neo_Black_Apply_v3.py').read_bytes())
    manifest=json.loads((REPO/'latest.json').read_text())
    manifest['script']='releases/0.3.0/apply.py'
    (source/'latest.json').write_text(json.dumps(manifest))
    home=root/'online-update-state'
    return t,root,settings,xml,source,home


def check_result(result, code=0):
    assert result.returncode==code, (result.stdout, result.stderr)


def test_apply_rollback():
    t,root,settings,xml,source,home=setup()
    old_settings,old_xml=settings.read_text(),xml.read_text()
    check_result(run('check',root,source,home))
    check_result(run('update',root,source,home))
    assert 'layeraselectionbackground=00008B' in settings.read_text()
    assert json.loads((home/'state.json').read_text())['installed_version']=='0.3.0'
    check_result(run('update',root,source,home))  # idempotent
    check_result(run('rollback',root,source,home))
    assert settings.read_text()==old_settings
    assert xml.read_text()==old_xml
    t.cleanup()
    print('PASS: updater install -> idempotent check -> rollback restores all settings/XML')


def test_checksum_refusal():
    t,root,settings,xml,source,home=setup()
    old_settings,old_xml=settings.read_text(),xml.read_text()
    m=json.loads((source/'latest.json').read_text());m['sha256']='0'*64;(source/'latest.json').write_text(json.dumps(m))
    result=run('update',root,source,home)
    assert result.returncode!=0 and 'SHA-256 mismatch' in result.stdout
    assert (settings.read_text(),xml.read_text())==(old_settings,old_xml)
    t.cleanup()
    print('PASS: bad checksum rejected without modifying skin/settings')


def test_existing_v3():
    t,root,settings,xml,source,home=setup()
    env=dict(os.environ,METRIX_NEO_TEST_ROOT=str(root))
    runscript=subprocess.run([sys.executable,str(source/'releases/0.3.0/apply.py'),'apply'],env=env,capture_output=True,text=True)
    check_result(runscript)
    already=settings.read_text()
    result=run('update',root,source,home)
    check_result(result)
    assert 'Detected already-applied V3' in result.stdout
    assert settings.read_text()==already
    check_result(run('rollback',root,source,home))
    t.cleanup()
    print('PASS: recognize existing V3 without repeated apply/reboot')


def test_auto_no_standby():
    t,root,settings,xml,source,home=setup()
    original=settings.read_text()
    result=run('auto',root,source,home)
    check_result(result)
    assert 'waiting for verified standby' in result.stdout
    assert settings.read_text()==original
    assert (home/'releases/0.3.0/apply.py').is_file()
    t.cleanup()
    print('PASS: auto mode downloads but refuses GUI restart without standby')


def test_upgrade_rollback():
    t,root,settings,xml,source,home=setup()
    check_result(run('update',root,source,home))
    v3settings=settings.read_text()
    rel=source/'releases/0.4.0'; rel.mkdir()
    newer=(source/'releases/0.3.0/apply.py').read_text()
    newer=newer.replace('MetrixNeoBlack_v3_backup','MetrixNeoBlack_v4_backup').replace("'infobarprogress': ('infobarprogress', '27408B')", "'infobarprogress': ('infobarprogress', '1BA1E2')")
    (rel/'apply.py').write_text(newer)
    m=json.loads((source/'latest.json').read_text()); m.update(version='0.4.0',script='releases/0.4.0/apply.py',sha256=hashlib.sha256(newer.encode()).hexdigest())
    (source/'latest.json').write_text(json.dumps(m))
    check_result(run('update',root,source,home))
    assert 'infobarprogress=1BA1E2' in settings.read_text()
    check_result(run('rollback',root,source,home))
    assert settings.read_text()==v3settings
    t.cleanup()
    print('PASS: upgrade V3->V4 and rollback V4->V3')


test_apply_rollback()
test_checksum_refusal()
test_existing_v3()
test_auto_no_standby()
test_upgrade_rollback()
print('ALL UPDATER TESTS PASSED')
