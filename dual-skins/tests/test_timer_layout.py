"""Run the audited native RecordTimerList entry builder against our geometry."""
import ast
from pathlib import Path
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from render_previews import font

PINNED=ROOT/'.upstream/enigma2/lib/python/Screens/Timers.py'


class NativeTimerLayout(unittest.TestCase):
    @unittest.skipUnless(PINNED.is_file(),'Audited upstream source unavailable')
    def test_real_native_record_entry_cells_fit_all_states_and_our_fonts(self):
        tree=ast.parse(PINNED.read_text(encoding='utf-8'))
        klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RecordTimerList')
        method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='buildTimerEntry')
        states=types.SimpleNamespace(StateWaiting=0,StatePrepared=1,StateRunning=2,StateEnded=3,StateFailed=4,StateDisabled=5)
        env=dict(eListboxPythonMultiContent=types.SimpleNamespace(TYPE_TEXT=0,TYPE_PIXMAP_ALPHABLEND=1),
                 eLabel=types.SimpleNamespace(calculateTextSize=lambda face,value,size,wrap:types.SimpleNamespace(width=lambda:round(font(face).getlength(value)))),eSize=lambda *args:args,
                 TimerEntry=states,TIMER_STATES={n:str(n) for n in range(6)},UNKNOWN='?',
                 fuzzyDate=lambda stamp:('Demain','20:45'),ngettext=lambda one,many,n:one if n==1 else many,_=lambda value:value,
                 RT_HALIGN_LEFT=1,RT_HALIGN_RIGHT=2,RT_VALIGN_CENTER=4,BT_SCALE=1,DAY_LIST=['Monday']*7,WEEKDAYS=[],WEEKENDS=[])
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(PINNED),'exec'),env)
        for profile in ('MetrixNEO','MetrixNEOAdvanced'):
            screen=ET.parse(ROOT/'skins'/profile/'skin.xml').getroot().find("screen[@name='RecordTimerOverview']")
            node=screen.find("widget[@name='timerlist']")
            width,height=map(int,node.get('size').split(','));row=int(node.get('itemHeight'))
            self.assertEqual(height//row,8)
            size=types.SimpleNamespace(width=lambda:width,height=lambda:row)
            owner=types.SimpleNamespace(timerListWidget=types.SimpleNamespace(getItemSize=lambda:size),detailFont=24,getOrbitalPos=lambda *args:'7.0°W')
            for name in ('itemHeight','topHeight','bottomHeight','indent','iconMargin','statusOffset','satPosLeft'):setattr(owner,name,int(node.get(name)))
            owner.showSeparator=node.get('showSeparator')=='1'
            for icon_name in ('Wait','Recording','Prepared','Done','Repeat','Once','Zapped','Disabled','Failed','AutoTimer','IceTVTimer'):setattr(owner,'icon'+icon_name,object())
            for png in (ROOT/'skins'/profile/'icons').glob('timer_*.png'):
                with Image.open(png) as image:self.assertEqual(image.size,(32,32))
            owner.iconWidth=owner.iconHeight=32
            for state,disabled,processed in [(0,False,False),(1,False,False),(2,False,False),(3,False,True),(0,True,False)]:
                timer=types.SimpleNamespace(repeated=0,isAutoTimer=False,service_ref=types.SimpleNamespace(getServiceName=lambda:'Chaîne documentaire'),state=state,begin=0,end=3600,marginBefore=0,marginAfter=0,eventBegin=0,eventEnd=3600,justplay=False,disabled=disabled,failed=False,name='Nom de programme de démonstration',isRunning=lambda:state==2)
                cells=env['buildTimerEntry'](owner,timer,processed)
                self.assertEqual(owner.topHeight+owner.bottomHeight+(2 if owner.showSeparator else 0),row)
                for cell in cells[1:]:
                    _,x,y,w,h,*_=cell
                    self.assertGreaterEqual(min(x,y,w,h),0)
                    self.assertLessEqual(x+w,width)
                    self.assertLessEqual(y+h,row)

    def test_footer_empty_labels_hide_both_marker_and_text_without_actions(self):
        for profile in ('MetrixNEO','MetrixNEOAdvanced'):
            for name in ('TimerOverview','RecordTimerOverview','SchedulerOverview','ConflictTimerOverview'):
                screen=ET.parse(ROOT/'skins'/profile/'skin.xml').getroot().find("screen[@name='%s']"%name)
                self.assertIsNone(screen.find('applet'))
                self.assertIsNotNone(screen.find("widget[@name='timerlist']"))
                for key in ('red','green','yellow','blue'):
                    targets=screen.findall("widget[@source='key_%s']"%key)
                    self.assertEqual(len(targets),2)
                    self.assertTrue(all(n.get('conditional')=='key_'+key and n.find("convert[@type='ConditionalShowHide']") is not None for n in targets))


if __name__=='__main__':unittest.main()
