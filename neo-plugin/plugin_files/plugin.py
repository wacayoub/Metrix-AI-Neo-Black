# -*- coding: utf-8 -*-
"""Metrix Neo AI theme manager — standalone Enigma2 Extensions plugin."""
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.config import config
from . import neo_engine

class NeoThemeManager(Screen):
    skin = '''<screen name="NeoThemeManager" position="center,center" size="1080,630" title="Metrix Neo AI" flags="wfNoBorder" backgroundColor="#090D17">
        <eLabel position="0,0" size="1080,68" backgroundColor="#16213B" />
        <widget name="heading" position="36,15" size="940,47" font="Regular;32" foregroundColor="#FFFFFF" transparent="1" />
        <widget name="profiles" position="45,94" size="510,290" itemHeight="72" font="Regular;29" scrollbarMode="showOnDemand" backgroundColor="#0F0F0F" foregroundColor="#FFFFFF" transparent="0" />
        <eLabel position="590,97" size="425,275" backgroundColor="#16213B" />
        <widget name="details" position="607,116" size="375,250" font="Regular;25" foregroundColor="#FFFFFF" transparent="1" />
        <widget name="status" position="45,422" size="950,87" font="Regular;24" foregroundColor="#C5D4EF" transparent="1" />
        <eLabel position="0,552" size="1080,78" backgroundColor="#10182D" />
        <widget source="red" render="Label" position="40,572" size="180,43" font="Regular;22" foregroundColor="#FF8080" transparent="1" />
        <widget source="green" render="Label" position="248,572" size="245,43" font="Regular;22" foregroundColor="#8BE5C1" transparent="1" />
        <widget source="yellow" render="Label" position="515,572" size="227,43" font="Regular;22" foregroundColor="#F3D384" transparent="1" />
        <widget source="blue" render="Label" position="745,572" size="305,43" font="Regular;22" foregroundColor="#98C4FF" transparent="1" />
    </screen>'''

    DESCRIPTIONS = {
        'black': 'NEO BLACK\n\nBlack graphite + royal blue.\nCyan EPG progress.\nSubtle panel gradients.',
        'blue': 'NEO BLUE\n\nDark navy + deep blue.\nPremium glass contrast.\nSubtle panel gradients.',
        'violet': 'NEO VIOLET\n\nGraphite + soft violet.\nCyan-teal progress.\nSubtle panel gradients.'
    }

    def __init__(self, session):
        Screen.__init__(self, session)
        self['heading'] = Label('METRIX NEO AI   /   OPENATV')
        self.order=['black','blue','violet']
        self['profiles']=MenuList([(neo_engine.PALETTES[key]['title'],key) for key in self.order])
        self['details']=Label('')
        self['status']=Label(neo_engine.status())
        self['red']=StaticText('Red: Exit')
        self['green']=StaticText('Green: Apply')
        self['yellow']=StaticText('Yellow: Restore')
        self['blue']=StaticText('Blue: Online update')
        self['actions']=ActionMap(['OkCancelActions','ColorActions','DirectionActions'], {
            'ok':self.ask_apply,'cancel':self.close,'red':self.close,
            'green':self.ask_apply,'yellow':self.ask_restore,'blue':self.online_update,
            'up':self.up,'down':self.down
        },-1)
        self.onLayoutFinish.append(self.update_description)

    def selected(self):
        row=self['profiles'].getCurrent()
        return row[1] if row else 'black'
    def update_description(self):
        self['details'].setText(self.DESCRIPTIONS.get(self.selected(),''))
    def up(self): self['profiles'].up();self.update_description()
    def down(self): self['profiles'].down();self.update_description()
    def ask_apply(self):
        profile=self.selected()
        self.session.openWithCallback(lambda yes:self.do_apply(profile) if yes else None,MessageBox,
            'Apply '+neo_engine.PALETTES[profile]['title']+'? A GUI restart will be offered.',MessageBox.TYPE_YESNO)
    def do_apply(self, profile):
        try:
            message=neo_engine.apply(profile,config)
            self['status'].setText(message)
            self.ask_restart()
        except Exception as exc:
            self.session.open(MessageBox,'Theme not applied: '+str(exc),MessageBox.TYPE_ERROR)
    def ask_restore(self):
        self.session.openWithCallback(lambda yes:self.do_restore() if yes else None,MessageBox,
            'Restore the previous MetrixHD appearance?',MessageBox.TYPE_YESNO)
    def do_restore(self):
        try:
            self['status'].setText(neo_engine.restore(config))
            self.ask_restart()
        except Exception as exc:
            self.session.open(MessageBox,'Restore cancelled: '+str(exc),MessageBox.TYPE_ERROR)
    def ask_restart(self):
        self.session.openWithCallback(self.restart_if_yes,MessageBox,
            'Restart Enigma2 GUI now to load the theme?',MessageBox.TYPE_YESNO)
    def restart_if_yes(self,yes):
        if yes: self.session.open(TryQuitMainloop,3)
    def online_update(self):
        try:
            from Screens.Console import Console
            from os.path import dirname, join
            from sys import executable
            script=join(dirname(__file__),'neo_update.py')
            self.session.open(Console,title='Metrix Neo AI online update',cmdlist=[executable+' '+script+' update'],closeOnSuccess=False)
        except Exception as exc:
            self.session.open(MessageBox,'Update could not start: '+str(exc),MessageBox.TYPE_ERROR)

def main(session,**kwargs):
    session.open(NeoThemeManager)

def Plugins(**kwargs):
    return [PluginDescriptor(name='Metrix Neo AI',description='Modern MetrixHD colors, 3D shading, online updates and restore',where=PluginDescriptor.WHERE_PLUGINMENU,fnc=main)]