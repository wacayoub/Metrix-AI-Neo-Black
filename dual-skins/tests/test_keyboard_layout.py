"""Native French keyboard geometry from the audited drawing-only builder."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


class NativeKeyboardLayout(unittest.TestCase):
    @unittest.skipUnless((ROOT/'.upstream/enigma2/lib/python/Screens/VirtualKeyBoard.py').is_file(),'Audited upstream source unavailable')
    def test_french_map_and_merged_keys_fit_native_grid(self):
        from keyboard_preview import native_keys
        rows=native_keys()
        self.assertEqual(len(rows),5)
        texts=[item['text'] for row in rows for item in row if item['kind']=='text']
        self.assertIn('é',texts);self.assertIn('a',texts);self.assertIn('z',texts)
        self.assertEqual(texts.count('SPACE'),1)
        self.assertEqual(texts.count('ENTER'),1)
        for row in rows:
            for item in row:
                x,y=item['pos'];w,h=item['size']
                self.assertGreaterEqual(min(x,y,w,h),0)
                self.assertLessEqual(x+w,14*112)
                self.assertLessEqual(y+h,60)


if __name__=='__main__':unittest.main()
