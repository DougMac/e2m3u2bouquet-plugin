import time
import os
import sys

#from enigma import getDesktop
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave
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
from e2m3u2bouquet import main as E2m3u2bMain


#Set default configuration
config.plugins.e2m3u2b = ConfigSubsection()
config.plugins.e2m3u2b.providername = ConfigSelection(default='FAB', choices=['FAB', 'EPIC', 'PRO'])
config.plugins.e2m3u2b.username = ConfigText(default='', fixed_size=False)
config.plugins.e2m3u2b.password = ConfigText(default='', fixed_size=False)
config.plugins.e2m3u2b.iptvtypes = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.multivod = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.picons = ConfigYesNo(default=False)
config.plugins.e2m3u2b.iconpath = ConfigSelection(default='/usr/share/enigma2/picon/',
                                                  choices=['/usr/share/enigma2/picon/',
                                                           '/media/usb/picon/',
                                                           '/media/hdd/picon/',
                                                           ])
config.plugins.e2m3u2b.allbouquet = ConfigYesNo(default=False)

class E2m3u2bConfig(ConfigListScreen, Screen):
    #skin = """
    #<screen position="center,center" size="500,400" title="IPTV-Bouquet Maker v">
    #<widget name="lblProvider" position="30,20" size="200,40" font="Regular;20"/>
	#<widget name="lblUsername" position="30,60" size="200,40" font="Regular;20"/>
	#<widget name="lblPassword" position="30,100" size="200,40" font="Regular;20"/>
	#<widget name="chkmultivod" position="220,140" size="32,32" alphatest="on" zPosition="1" pixmaps="skin_default/icons/lock_off.png,skin_default/icons/lock_on.png"/>
	#<widget name="lblmultivod" position="30,140" size="200,40" font="Regular; 22" halign="left" zPosition="2" transparent="0" />
    #</screen>"""

    skin = """
    <screen position="center,center" size="600,430" title="E2m3ubouquet Config">    
    <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
    <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="config" position="10,60" size="590,250" scrollbarMode="showOnDemand" />
    </screen>"""

    def __init__(self, session, args=None):
        self.session = session
        Screen.__init__(self, session)
        self['key_red'] = Button(_('Cancel'))
        self['key_green'] = Button(_('Save'))
        self['key_yellow'] = Button(_('Run'))
        self['key_blue'] = Button()
        self.cfglist = []
        self.cfglist.append(getConfigListEntry(_('Provider:'), config.plugins.e2m3u2b.providername))
        self.cfglist.append(getConfigListEntry(_('Username:'), config.plugins.e2m3u2b.username))
        self.cfglist.append(getConfigListEntry(_('Password:'), config.plugins.e2m3u2b.password))
        self.cfglist.append(getConfigListEntry(_('All IPTV type:'), config.plugins.e2m3u2b.iptvtypes))
        self.cfglist.append(getConfigListEntry(_('Multi VOD:'), config.plugins.e2m3u2b.multivod))
        self.cfglist.append(getConfigListEntry(_('Download picons:'), config.plugins.e2m3u2b.picons))
        self.cfglist.append(getConfigListEntry(_('Picon save path:'), config.plugins.e2m3u2b.iconpath))
        self.cfglist.append(getConfigListEntry(_('Create all channels bouquet:'), config.plugins.e2m3u2b.allbouquet))
        ConfigListScreen.__init__(self, self.cfglist, session=self.session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
                                    {
                                    'red': self.exit,
                                    'green': self.key_green,
                                    'yellow': self.do_update,
                                    # 'blue': self.key_blue,
                                    'cancel': self.exit},
                                    -1
                                    )

    def key_green(self):
        """Save
        """
        for x in self['config'].list:
            x[1].save()
        self.close()

    def do_update(self):
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
            if config.plugins.e2m3u2b.multivod.value:
                sys.argv.append('-M')
            if config.plugins.e2m3u2b.picons.value:
                sys.argv.append('-P')
                sys.argv.append('-q={}'.format(config.plugins.e2m3u2b.iconpath.value))

            # Call backend module with args
            E2m3u2bMain(sys.argv)

    def exit(self):
        print('************************************Exiting {}'.format(self))
        print(self['config'].list)
        for x in self['config'].list:
            # cancel unsaved changes
            x[1].cancel()
        self.close()


def main(session, **kwargs):
    session.open(E2m3u2bConfig)


def Plugins(**kwargs):
    result = PluginDescriptor(
        name="E2m3u2bouquet",
        description="Usable IPTV for Enigma2",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        fnc=main)
    return result
