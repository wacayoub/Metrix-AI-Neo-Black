import importlib.util, tempfile, unittest, os, sys, types, hashlib, json
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]/'neo-plugin'/'plugin_files'
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,BASE/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
engine=module('neo_engine_test','neo_engine.py')
updater=module('neo_update_test','neo_update.py')
class Field:
    def __init__(self,value): self.value=value
    def setValue(self,value):self.value=value
    def save(self):pass
class Node:pass

def mockconfig():
    cfg=Node();cfg.plugins=Node();cfg.skin=Node();cfg.skin.primary_skin=Field('MetrixHD/skin.MySkin.xml')
    cfg.plugins.MyMetrixLiteColors=Node();cfg.plugins.MyMetrixLiteFonts=Node()
    cfg.plugins.MyMetrixLiteOther=Node();cfg.plugins.MyMetrixLiteOther.EHDenabled=Field(1)
    for role,_,_,_ in engine.FIELDS:
        setattr(cfg.plugins.MyMetrixLiteColors,role,Field('0F0F0F'))
        if role not in ('layeraunderline','infobarprogress','layeraprogress'):
            setattr(cfg.plugins.MyMetrixLiteColors,role+'transparency',Field('1A'))
    for role,_,font in engine.FONT_FIELDS:setattr(cfg.plugins.MyMetrixLiteFonts,role,Field(font))
    return cfg

def samplexml():
    names={name for _,name,_,_ in engine.FIELDS}
    lines=['<skin><colors>','<color name="Background" value="#00222222" />', '<color name="Background" value="#00444444" />']
    lines += ['<color name="'+x+'" value="#1A0F0F0F" />' for x in names]
    lines += ['<color name="'+x+'" value="#1A0F0F0F" />' for x in engine.GRADIENTS]
    lines += ['<!-- <color name="layer-a-selection-background" value="#00ff00ff" /> -->','</colors><fonts>']
    lines += ['<font name="'+name+'" filename="/stock/font.ttf" />' for _,name,_ in engine.FONT_FIELDS]
    return '\n'.join(lines+['</fonts></skin>'])

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.engine=engine
        self.old={k:getattr(engine,k) for k in ('STATE_DIR','STATE','ORIGINAL','SKIN','IMAGE_VERSION','MAIN')}
        engine.STATE_DIR=self.root/'state';engine.STATE=engine.STATE_DIR/'state.json'
        engine.ORIGINAL=engine.STATE_DIR/'original.xml';engine.SKIN=self.root/'skin.xml'
        engine.IMAGE_VERSION=self.root/'image-version';engine.MAIN=self.root/'skin.MySkin.xml'
        engine.IMAGE_VERSION.write_text('box_type=vuzero4k\nversion=8.0.1\n')
        engine.MAIN.write_text('<skin />');engine.SKIN.write_text(samplexml())
        self.cfg=mockconfig()
        fake=types.ModuleType('Components.config');fake.configfile=types.SimpleNamespace(save=lambda:None)
        pack=types.ModuleType('Components');pack.config=fake
        self.mods={name:sys.modules.get(name) for name in ('Components','Components.config')}
        sys.modules['Components']=pack;sys.modules['Components.config']=fake
        self.addCleanup(self.cleanup)
    def cleanup(self):
        for k,v in self.old.items():setattr(engine,k,v)
        for name,old in self.mods.items():
            if old is None:sys.modules.pop(name,None)
            else:sys.modules[name]=old
    def test_all_profiles_preserve_xml_and_duplicates(self):
        old=samplexml()
        for p in engine.PALETTES:
            cols,fonts=engine.palette_changes(p)
            rendered=engine.transform_xml(old,cols,fonts)
            self.assertIn('name="Background" value="#00222222"',rendered)
            self.assertIn('name="Background" value="#00444444"',rendered)
            self.assertIn('<!-- <color name="layer-a-selection-background" value="#00ff00ff" /> -->',rendered)
            self.assertIn('vertical,true',rendered)
            self.assertTrue(rendered.endswith('</skin>'))
    def test_apply_switch_restore(self):
        original=engine.SKIN.read_bytes()
        engine.apply('black',self.cfg)
        self.assertIn('Neo Black',engine.status())
        engine.apply('violet',self.cfg)
        self.assertIn('Neo Violet',engine.status())
        engine.restore(self.cfg)
        self.assertEqual(original,engine.SKIN.read_bytes())
        self.assertEqual(self.cfg.plugins.MyMetrixLiteColors.layeraselectionbackground.value,'0F0F0F')
    def test_external_edits_are_protected(self):
        engine.apply('blue',self.cfg)
        engine.SKIN.write_text(engine.SKIN.read_text().replace('#0000008B','#00FFFFFF'))
        with self.assertRaises(engine.SkinError):engine.apply('violet',self.cfg)
        with self.assertRaises(engine.SkinError):engine.restore(self.cfg)
    def test_bad_xml_is_rejected_before_settings_change(self):
        engine.SKIN.write_text('<skin><colors>')
        before=self.cfg.plugins.MyMetrixLiteColors.infobarprogress.value
        with self.assertRaises(engine.SkinError):engine.apply('black',self.cfg)
        self.assertEqual(self.cfg.plugins.MyMetrixLiteColors.infobarprogress.value,before)
        self.assertFalse(engine.STATE.exists())

class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.old={k:getattr(updater,k) for k in ('DEST','STATE_DIR','PKG_STATE','BACKUPS')}
        updater.DEST=self.root/'Plugins'/'MetrixNeoAI';updater.STATE_DIR=self.root/'state'
        updater.PKG_STATE=updater.STATE_DIR/'package.json';updater.BACKUPS=updater.STATE_DIR/'backups'
        self.addCleanup(lambda:[setattr(updater,k,v) for k,v in self.old.items()])
        self.raw={name:(BASE/name).read_bytes() for name in ['plugin.py','neo_engine.py','neo_update.py','__init__.py']}
        self.remote={'version':'0.4.0','device':'vuzero4k','image':'openatv-8.0.1',
                     'files':{k:hashlib.sha256(v).hexdigest() for k,v in self.raw.items()}}
    def _fakefetch(self,url,limit):return self.raw[url.split('/')[-1]]
    def test_install_verified_then_rollback(self):
        updater.DEST.mkdir(parents=True);(updater.DEST/'old.py').write_text('legacy')
        (updater.DEST/'manifest.json').write_text('{"version":"0.3.0"}')
        with patch.object(updater,'_syscheck'),patch.object(updater,'manifest',return_value=self.remote),patch.object(updater,'fetch',side_effect=self._fakefetch):
            self.assertTrue(updater.install())
            self.assertTrue((updater.DEST/'plugin.py').is_file())
            self.assertEqual(updater.current_version(),'0.4.0')
            updater.rollback()
        self.assertTrue((updater.DEST/'old.py').is_file())
    def test_wrong_sha_leaves_installed_unchanged(self):
        remote=dict(self.remote);remote['files']=dict(self.remote['files'])
        remote['files']['plugin.py']='0'*64
        with patch.object(updater,'_syscheck'),patch.object(updater,'manifest',return_value=remote),patch.object(updater,'fetch',side_effect=self._fakefetch):
            with self.assertRaises(updater.UpdateError):updater.install()
        self.assertFalse(updater.DEST.exists())
    def test_auto_will_not_install_without_confirmed_standby(self):
        with patch.object(updater,'_syscheck'),patch.object(updater,'standby_confirmed',return_value=False),patch.object(updater,'manifest') as manifest:
            self.assertFalse(updater.install(auto=True))
            manifest.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)