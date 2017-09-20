import time
import os
import sys
import log

from enigma import eTimer
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.ScrollLabel import ScrollLabel
import Components.PluginComponent
from Plugins.Plugin import PluginDescriptor
import e2m3u2bouquet

# Global variable
autoStartTimer = None
_session = None

def get_providers_list():
    iptv = e2m3u2bouquet.IPTVSetup()
    providers = iptv.read_providers((iptv.download_providers(e2m3u2bouquet.PROVIDERSURL)))
    return sorted(providers.keys())

# Set default configuration
config.plugins.e2m3u2b = ConfigSubsection()
config.plugins.e2m3u2b.autobouquetupdate = ConfigYesNo(default=False)
config.plugins.e2m3u2b.updateinterval = ConfigSelectionNumber(default=6, min=2, max=48, stepwidth=1)
config.plugins.e2m3u2b.autobouquetupdateatboot = ConfigYesNo(default=False)
config.plugins.e2m3u2b.providername = ConfigSelection(default='FAB', choices=get_providers_list())
config.plugins.e2m3u2b.username = ConfigText(default='', fixed_size=False)
config.plugins.e2m3u2b.password = ConfigPassword(default='', fixed_size=False)
config.plugins.e2m3u2b.iptvtypes = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.multivod = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.bouquetpos = ConfigSelection(default='bottom',
                                                    choices=['bottom', 'top']
                                                    )
config.plugins.e2m3u2b.allbouquet = ConfigYesNo(default=False)
config.plugins.e2m3u2b.picons = ConfigYesNo(default=False)
config.plugins.e2m3u2b.iconpath = ConfigSelection(default='/usr/share/enigma2/picon/',
                                                  choices=['/usr/share/enigma2/picon/',
                                                           '/media/usb/picon/',
                                                           '/media/hdd/picon/',
                                                           '/picon/'
                                                           ])
config.plugins.e2m3u2b.srefoverride = ConfigEnableDisable(default=False)

config.plugins.e2m3u2b.bouquetdownload = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.last_update = ConfigText()



class E2m3u2bConfig(ConfigListScreen, Screen):
    skin = """
    <screen position="center,center" size="600,430" title="IPTV Bouquet Maker Config">    
    <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
    <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <ePixmap position="562,30" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
    <widget name="config" position="10,60" size="590,300" scrollbarMode="showOnDemand" />
    <widget name="statusbar" position="10,410" size="500,20" font="Regular;18" />    
    </screen>"""

    def __init__(self, session, args=None):
        self.session = session
        Screen.__init__(self, session)
        self.skinName = ["E2m3u2bConfig", "EPGImportConfig", "EPGMainSetup"]
        self['key_red'] = Button('Cancel')
        self['key_green'] = Button('Save')
        self['key_yellow'] = Button('Run')
        self['key_blue'] = Button()
        self['setupActions'] = ActionMap(['SetupActions', 'OkCancelActions', 'ColorActions', 'TimerEditActions', 'MovieSelectionActions'],
                                    {
                                    'red': self.exit,
                                    'green': self.key_green,
                                    'yellow': self.manual_update,
                                    'cancel': self.exit,
                                    'contextMenu': self.openMenu
                                    },-1)
        self['statusbar'] = Label()
        ConfigListScreen.__init__(self, [], session=self.session)
        self.init_config()
        self.create_setup()
        self.update_status()

    def init_config(self):
        def get_prev_values(section):
            res = {}
            for (key, val) in section.content.items.items():
                if isinstance(val, ConfigSubsection):
                    res[key] = get_prev_values(val)
                else:
                    res[key] = val.value
            return res

        self.E2M3U2B = config.plugins.e2m3u2b
        self.prev_values = get_prev_values(self.E2M3U2B)
        self.cfg_autobouquetupdate = getConfigListEntry('Automatic bouquet update (schedule):',self.E2M3U2B.autobouquetupdate)
        self.cfg_updateinterval = getConfigListEntry('Update interval (hours):', self.E2M3U2B.updateinterval)
        self.cfg_autobouquetupdateatboot = getConfigListEntry('Automatic bouquet update (when box starts):',self.E2M3U2B.autobouquetupdateatboot)
        self.cfg_providername = getConfigListEntry('Provider:', self.E2M3U2B.providername)
        self.cfg_username = getConfigListEntry('Username:', self.E2M3U2B.username)
        self.cfg_password = getConfigListEntry('Password:', self.E2M3U2B.password)
        self.cfg_iptvtypes = getConfigListEntry('All IPTV type:', self.E2M3U2B.iptvtypes)
        self.cfg_multivod = getConfigListEntry('Multi VOD:', self.E2M3U2B.multivod)
        self.cfg_bouquetpos = getConfigListEntry("IPTV bouquet position", self.E2M3U2B.bouquetpos)
        self.cfg_allbouquet = getConfigListEntry('Create all channels bouquet:', self.E2M3U2B.allbouquet)
        self.cfg_picons = getConfigListEntry('Download picons:', self.E2M3U2B.picons)
        self.cfg_iconpath = getConfigListEntry('Picon save path:', self.E2M3U2B.iconpath)
        self.cfg_srefoverride = getConfigListEntry("Override service refs", self.E2M3U2B.srefoverride)
        self.cfg_bouquetdownload = getConfigListEntry("Check providers bouquet", self.E2M3U2B.bouquetdownload)

    def create_setup(self):
        list = [ self.cfg_autobouquetupdate ]
        if self.E2M3U2B.autobouquetupdate.value:
            list.append(self.cfg_updateinterval)
        # leave update at boot disabled for now
        # list.append(self.cfg_autobouquetupdateatboot)
        list.append(self.cfg_providername)
        list.append(self.cfg_username)
        list.append(self.cfg_password)
        list.append(self.cfg_iptvtypes)
        list.append(self.cfg_multivod)
        list.append(self.cfg_bouquetpos)
        list.append(self.cfg_allbouquet)
        list.append(self.cfg_picons)
        list.append(self.cfg_iconpath)
        list.append(self.cfg_srefoverride)
        list.append(self.cfg_bouquetdownload)
        self['config'].list = list
        self['config'].l.setList(list)

    def new_config(self):
        """If an option is picked that has
        additional config option show or hide these options
        """
        cur = self['config'].getCurrent()
        if cur in (self.cfg_autobouquetupdate, self.cfg_updateinterval):
            self.create_setup()

    def key_green(self):
        """Save
        """
        for x in self['config'].list:
            x[1].save()
        self.close()

    def manual_update(self):
        """Manual update
        """
        self.session.openWithCallback(self.manual_update_callback, MessageBox, "Update of channels will start.\n"
                                                                                   "This may take a few minutes.\n"
                                                                                   "Proceed?", MessageBox.TYPE_YESNO,
                                      timeout = 15, default = True)

    def manual_update_callback(self, confirmed):
        if not confirmed:
            return
        try:
            do_update()
        except Exception, e:
            print>>log, "[e2m3u2b] Error:", e
        self.update_status()


    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.new_config()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.new_config()

    def update_status(self):
        if config.plugins.e2m3u2b.last_update:
            self["statusbar"].setText('Last channel update: {}'.format(config.plugins.e2m3u2b.last_update.value))

    def openMenu(self):
        menu = [('Show log', self.showLog), ('About', self.showAbout)]
        text = 'Select action'
        def setAction(choice):
            if choice:
                choice[1]()
        self.session.openWithCallback(setAction, ChoiceBox, title=text, list=menu)

    def showAbout(self):
        about = """
        IPTV for Enigma2 - E2m3u2bouquet plugin\n
        Multi provider IPTV bouquet maker for enigma2\n
        This plugin is free and should not be resold\n
        E2m3u2bouquet v{}
        """.format(e2m3u2bouquet.__version__)
        self.session.open(MessageBox,about, type=MessageBox.TYPE_INFO)

    def showLog(self):
        self.session.open(E2m3u2bLog)

    def exit(self):
        print(self['config'].list)
        for x in self['config'].list:
            # cancel unsaved changes
            x[1].cancel()
        self.close()

class E2m3u2bLog(Screen):
    skin = """
    <screen position="center,center" size="560,400" title="E2m3ubouquet Log" >
    <ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
    <ePixmap name="green" position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
    <ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
    <ePixmap name="blue" position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
    <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />    
    <widget name="list" position="10,40" size="540,340" />
    </screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.skinName = ["E2m3u2bLog", "EPGImportLog", "XMLTVImportLog"]
        self["key_red"] = Button("Clear")
        self["key_green"] = Button()
        self["key_yellow"] = Button()
        self["key_blue"] = Button()
        self["list"] = ScrollLabel(log.getvalue())
        self["actions"] = ActionMap(["DirectionActions", "OkCancelActions", "ColorActions", "MenuActions"],
                                    {
                                        "red": self.clear,
                                        "green": self.cancel,
                                        "yellow": self.cancel,
                                        "blue": self.cancel,
                                        "cancel": self.cancel,
                                        "ok": self.cancel,
                                        "left": self["list"].pageUp,
                                        "right": self["list"].pageDown,
                                        "up": self["list"].pageUp,
                                        "down": self["list"].pageDown,
                                        "pageUp": self["list"].pageUp,
                                        "pageDown": self["list"].pageDown,
                                        "menu": self.cancel,
                                    }, -2)

    def cancel(self):
        self.close(False)

    def clear(self):
        log.logfile.reset()
        log.logfile.truncate()
        self.close(False)

class AutoStartTimer:
    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        self.timer.callback.append(self.on_timer)
        self.update()

    def get_wake_time(self):
        print>> log, '[e2m3u2b] AutoStartTimer -> get_wake_time'
        if config.plugins.e2m3u2b.autobouquetupdate.value and config.plugins.e2m3u2b.updateinterval.value:
            interval = int(config.plugins.e2m3u2b.updateinterval.value)
            nowt = time.time()
            return int(nowt) + (interval * 60 * 60)
        else:
            return -1

    def update(self, atLeast = 0):
        print>>log, '[e2m3u2b] AutoStartTimer -> update'
        self.timer.stop()
        wake = self.get_wake_time()
        nowt = time.time()
        now = int(nowt)

        print>> log, '[e2m3u2b] wake {} now {}'.format(wake, now)

        if wake > 0:
            next = wake - now
            self.timer.startLongTimer(next)
        else:
            wake = -1
        return wake

    def on_timer(self):
        self.timer.stop()
        now = int(time.time())
        print>> log, '[e2m3u2b] on_timer occured at {}'.format(now)
        print>> log, '[e2m3u2b] Stating bouquet update because auto update bouquet schedule is enabled'
        do_update()
        self.update()

    def get_status(self):
        print>> log, '[e2m3u2b] AutoStartTimer -> getStatus'

def do_update():
    """Run
    """
    if config.plugins.e2m3u2b.providername.value:
        sys.argv = []
        sys.argv.append('-n={}'.format(config.plugins.e2m3u2b.providername.value))
        sys.argv.append('-u={}'.format(config.plugins.e2m3u2b.username.value))
        sys.argv.append('-p={}'.format(config.plugins.e2m3u2b.password.value))
        if config.plugins.e2m3u2b.iptvtypes.value:
            sys.argv.append('-i')
        if config.plugins.e2m3u2b.multivod.value:
            sys.argv.append('-M')
        if config.plugins.e2m3u2b.allbouquet.value:
            sys.argv.append('-a')
        if config.plugins.e2m3u2b.picons.value:
            sys.argv.append('-P')
            sys.argv.append('-q={}'.format(config.plugins.e2m3u2b.iconpath.value))
        if not config.plugins.e2m3u2b.srefoverride.value:
            sys.argv.append('-xs')
        if config.plugins.e2m3u2b.bouquetpos.value and config.plugins.e2m3u2b.bouquetpos.value == 'top' :
            sys.argv.append('-bt')
        if config.plugins.e2m3u2b.bouquetdownload.value:
            sys.argv.append('-bd')

        # Call backend module with args
        print>> log, '[e2m3u2b] Starting backend script'
        e2m3u2bouquet.main(sys.argv)
        print>> log, '[e2m3u2b] Finished backend script'

        localtime = time.asctime(time.localtime(time.time()))
        config.plugins.e2m3u2b.last_update.value = localtime
        config.plugins.e2m3u2b.last_update.save()

def main(session, **kwargs):
    session.openWithCallback(done_configuring, E2m3u2bConfig)

def done_configuring():
    """Check for new config values for auto start
    """
    print>>log, '[e2m3u2b] Done configuring'
    if autoStartTimer is not None:
        autoStartTimer.update()

def on_boot_start_check():
    """This will only execute if the
    config option autobouquetupdateatboot is true
    """
    now = int(time.time())
    # TODO Skip if there is an upcoming scheduled update
    print>>log, '[e2m3u2b] Stating bouquet update because auto update bouquet at start enabled'
    do_update()

def autostart(reason, session=None, **kwargs):
    # these globals need declared as they are reassigned here
    global autoStartTimer
    global _session
    # reason is 0 at start and 1 at shutdown
    print>>log, '[e2m3u2b] autostart {} occured at {}'.format(reason, time.time())
    if reason == 0 and _session is None:
        if session is not None:
            _session = session
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
            if config.plugins.e2m3u2b.autobouquetupdateatboot.value:
                on_boot_start_check()

def get_next_wakeup():
    # don't enable waking from deep standby for now
    print>> log, '[e2m3u2b] get_next_wakeup'
    return -1

def Plugins(**kwargs):
    name = 'IPTV Bouquet Maker'
    description = 'IPTV for Enigma2 - E2m3u2bouquet plugin'

    result = [
        PluginDescriptor(
            name=name,
            description=description,
            where=[
                PluginDescriptor.WHERE_AUTOSTART,
                PluginDescriptor.WHERE_SESSIONSTART,
            ],
            fnc=autostart,
            wakeupfnc=get_next_wakeup
        ),
        PluginDescriptor(
            name=name,
            description=description,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon='e2m3ubouquetlogo.png',
            fnc=main
        )
    ]
    return result
