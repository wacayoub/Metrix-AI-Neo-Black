"""Essential native audio contracts: real tuple fields, focus and no actions."""
import hashlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PROFILES=('MetrixNEO','MetrixNEOAdvanced')


class AudioLayout(unittest.TestCase):
    def screen(self,profile):
        return ET.parse(ROOT/'skins'/profile/'skin.xml').getroot().find("screen[@name='AudioSelection']")

    def template(self,profile):
        source=self.screen(profile).find("widget[@source='streams']/convert").text
        return eval(source,{'__builtins__':{},'gFont':lambda *args:args,'MultiContentEntryText':lambda **kwargs:kwargs,'RT_VALIGN_CENTER':1,'RT_ELLIPSIS':2})

    def test_native_audio_and_subtitle_tuples_keep_meaning_in_both_focus_states(self):
        fixtures=[(object(),'','1','AAC','English','X'),(object(),'','100','DVB','Français','')]
        for profile in PROFILES:
            template=self.template(profile)
            for style in ('default','notselected'):
                fields=template['templates'][style][1]
                for row in fixtures:
                    self.assertEqual([row[field['text']] for field in fields],list(row[2:]))
                for field in fields:
                    self.assertLessEqual(field['pos'][0]+field['size'][0],1005)
                    self.assertLessEqual(field['pos'][1]+field['size'][1],48)

    def test_focus_does_not_leave_two_blue_selections(self):
        for profile in PROFILES:
            styles=self.template(profile)['templates']
            self.assertIs(styles['default'][2],True)
            self.assertIs(styles['notselected'][2],False)

    def test_transparent_window_preserves_live_video_and_seven_rows(self):
        for profile in PROFILES:
            screen=self.screen(profile)
            self.assertEqual(screen.get('backgroundColor'),'transparent')
            self.assertEqual(screen.get('size'),'1802,976')
            config=screen.find("widget[@name='config']")
            self.assertEqual(int(config.get('size').split(',')[1])//int(config.get('itemHeight')),7)
            self.assertEqual(config.get('transparent'),'1')
            self.assertFalse(any(n.get('render') in ('Pig','Video') or n.get('name')=='video' for n in screen))
            self.assertFalse(any('reference' in n.get('pixmap','') for n in screen))

    def test_boolean_shortcuts_are_conditional_markers_and_do_not_invent_actions(self):
        for profile in PROFILES:
            screen=self.screen(profile)
            for key in ('red','green','yellow','blue'):
                marker=screen.find("widget[@source='key_%s']"%key)
                self.assertEqual(marker.find('convert').get('type'),'ConditionalShowHide')
                self.assertEqual(marker.get('text'),'')
            self.assertIsNone(screen.find('applet'))
            self.assertNotIn('IPAudio',ET.tostring(screen,encoding='unicode'))
            self.assertIsNotNone(screen.find("widget[@name='switchdescription']"))
            self.assertIsNotNone(screen.find("widget[@name='key_left']"))
            self.assertIsNotNone(screen.find("widget[@name='key_right']"))

    def test_both_skins_have_their_own_licensed_light_font_and_original_speaker(self):
        digests=[];icons=[]
        for profile in PROFILES:
            root=ET.parse(ROOT/'skins'/profile/'skin.xml').getroot()
            face=root.find("fonts/font[@name='AudioLight']")
            self.assertEqual(face.get('filename'),'/usr/share/enigma2/'+profile+'/fonts/Raleway-Light.ttf')
            digests.append(hashlib.sha256((ROOT/'skins'/profile/'fonts/Raleway-Light.ttf').read_bytes()).hexdigest())
            path=ROOT/'skins'/profile/'assets/audio-speaker.png'
            with Image.open(path) as image:
                self.assertEqual(image.size,(304,236))
                self.assertEqual(image.mode,'RGBA')
                self.assertEqual(image.getpixel((0,0))[3],0)
            icons.append(path.read_bytes())
        self.assertEqual(digests,['3cf1d8bf160d93b4a2ec30dbfc177bfb9d14358fe4232b51df39a1c677695bf5']*2)
        self.assertEqual(*icons)


if __name__=='__main__':unittest.main()
