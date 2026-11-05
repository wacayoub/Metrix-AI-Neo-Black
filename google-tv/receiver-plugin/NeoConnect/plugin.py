"""Enigma2 UI. Activation is explicit; no autostart of a tunnel at installation."""
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import re

from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import ConfigText, ConfigInteger, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from .core import Controller, ConnectError, private_ipv4

_controller = None


def controller():
    global _controller
    if _controller is None:
        _controller = Controller()
    return _controller


def lan_ip():
    try:
        result = Controller._run(['ip', '-4', '-o', 'address', 'show'], None)
        for address in re.findall(r'\binet ([0-9.]+)/', result.stdout):
            if private_ipv4(address) and ipaddress.IPv4Address(address) not in ipaddress.IPv4Network('10.78.0.0/24'):
                return address
    except Exception:
        pass
    return ''


class NeoConnectScreen(ConfigListScreen, Screen):
    skin = '''<screen name="NeoConnect" position="center,center" size="1160,670" title="Neo Connect">
      <widget name="config" position="30,30" size="1100,135" font="Regular;26" itemHeight="40" />
      <widget name="status" position="30,185" size="1100,395" font="Regular;25" />
      <widget name="keys" position="30,610" size="1100,40" font="Regular;23" />
    </screen>'''

    def __init__(self, session):
        Screen.__init__(self, session)
        self.control = controller()
        self.host = ConfigText(default=self.control.settings.get('receiver_host', lan_ip()), fixed_size=False)
        try:
            from Components.config import config
            owif_port = config.OpenWebif.port.value
        except Exception:
            owif_port = 80
        self.port = ConfigInteger(default=self.control.settings.get('receiver_port', owif_port), limits=(1, 65535))
        self.endpoint = ConfigText(default=self.control.settings.get('endpoint', ''), fixed_size=False)
        ConfigListScreen.__init__(self, [
            getConfigListEntry('Adresse LAN du Vu+', self.host),
            getConfigListEntry('Port OpenWebif local', self.port),
            getConfigListEntry('Adresse Internet (hote:port)', self.endpoint)], session=session)
        self['status'] = Label('Neo Android : Setup > Neo Connect.\n'
            'Moteur prive integre : aucun module ni regle reseau du noyau ajoute.\n'
            'Le routeur doit acheminer UDP 51820 vers ce Vu+.\n'
            'Ne pas ouvrir OpenWebif ou le port d association 9843 sur Internet.\n'
            'Pas de service cloud ; aucun transcodage video ajoute.')
        self['keys'] = Label('ROUGE : arreter   VERT : activer / nouveau code   JAUNE : appareils   EXIT : fermer')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
            'cancel': self.close, 'red': self.stop, 'green': self.activate, 'yellow': self.devices}, -2)
        self.worker = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.closed = False
        self.timer = eTimer()
        self.timer.callback.append(self.poll)
        self.onClose.append(self.cleanup)
        if self.control.active:
            self.show_active()

    def cleanup(self):
        self.closed = True
        self.timer.stop()
        self.worker.shutdown(wait=False)

    def work(self, function):
        if self.future is not None:
            return
        self['status'].setText('Operation en cours...')
        self.future = self.worker.submit(function)
        self.timer.start(200)

    def poll(self):
        if self.closed or self.future is None or not self.future.done():
            return
        self.timer.stop()
        future, self.future = self.future, None
        try:
            message = future.result()
            if self.control.active:
                self.show_active(message or '')
            else:
                self['status'].setText(message or 'Neo Connect arrete. Aucun tunnel actif.')
        except ConnectError as error:
            self['status'].setText(str(error))
        except Exception:
            self['status'].setText('Operation impossible. Aucune connexion distante validee.')

    def show_active(self, message=''):
        fingerprint = self.control.fingerprint()
        grouped = ' '.join(fingerprint[i:i+8] for i in range(0, len(fingerprint), 8))
        code = self.control.code if self.control.code and self.control.clock() < self.control.code_until else 'aucun'
        self['status'].setText('%s\nTunnel configure ; acces Internet non teste.\n'
            'Association LAN HTTPS : %s:9843\n'
            'Empreinte SHA-256 (a comparer dans Neo) :\n%s\n'
            'Code a usage unique, valable 2 minutes : %s\n'
            '%d appareil(s). VERT : renouveler le code.' %
            (message, self.control.settings['receiver_host'], grouped, code, len(self.control.peers)))

    def activate(self):
        if self.future is not None:
            return
        if self.control.active:
            self.control.new_code()
            self.show_active()
            return
        missing = self.control.requirements()
        if missing:
            self['status'].setText('Activation refusee. Composants absents : ' + ', '.join(missing) +
                                  '\nAucune installation automatique effectuee.')
            return
        self.session.openWithCallback(self.confirm, MessageBox,
            'Demarrer le moteur prive Neo Connect sur UDP 51820 ?\n'
            'Seuls les ports OpenWebif et video locaux seront accessibles dans le tunnel.\n'
            'Aucun reglage du routeur ne sera change automatiquement.', MessageBox.TYPE_YESNO, default=False)

    def confirm(self, answer):
        if answer:
            host, port, endpoint = self.host.value, self.port.value, self.endpoint.value
            def start():
                self.control.up(host, port, endpoint)
                self.control.new_code()
            self.work(start)

    def stop(self):
        self.work(self.control.down)

    def devices(self):
        if self.future is not None:
            return
        choices = [(p['name'] + ' — ' + p['address'], p['public_key']) for p in self.control.peers]
        if not choices:
            self['status'].setText('Aucun appareil associe.')
            return
        self.session.openWithCallback(self.selected_device, ChoiceBox, title='Choisir un appareil a revoquer', list=choices)

    def selected_device(self, value):
        if value:
            self.session.openWithCallback(lambda yes: self.work(lambda: self.control.revoke(value[1])) if yes else None,
                MessageBox, 'Revoquer cet appareil ? Sa connexion sera supprimee.', MessageBox.TYPE_YESNO, default=False)


def main(session, **kwargs):
    try:
        session.open(NeoConnectScreen)
    except Exception:
        session.open(MessageBox, 'Neo Connect : configuration locale invalide ou composant absent.', MessageBox.TYPE_ERROR)


def shutdown(reason, **kwargs):
    if reason == 1 and _controller is not None:
        try:
            _controller.down()
        except Exception:
            pass


def Plugins(**kwargs):
    return [PluginDescriptor(name='Neo Connect', description='Association privee avec Neo Android',
                             where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
            PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=shutdown)]
