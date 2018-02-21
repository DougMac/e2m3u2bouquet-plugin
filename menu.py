import time
import os
import sys
import log
import plugin as E2m3u2b_Plugin

from about import E2m3u2b_About
from providers import E2m3u2b_Providers

from enigma import eTimer
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Sources.List import List
from Components.Label import Label
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.ScrollLabel import ScrollLabel

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
try:
    from Tools.Directoires import SCOPE_ACTIVE_SKIN
except:
    pass
from Tools.LoadPixmap import LoadPixmap


class E2m3u2b_Menu(Screen):
    skin = """
    <screen position="center,center" size="600,500">
        <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="5"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
        <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="5"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />

        <widget source="list" render="Listbox" position="0,50" size="600,420" scrollbarMode="showOnDemand">
            <convert type="TemplatedMultiContent">
                {"template": [
                    MultiContentEntryText(pos = (58, 5), size = (440, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
                    ],
                    "fonts": [gFont("Regular",22)],
                    "itemHeight": 40
                }
            </convert>
        </widget>        
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        Screen.setTitle(self, "IPTV Bouquet Maker")
        self.skinName = ['E2m3u2b_Menu', 'AutoBouquetsMaker_Menu']

        self.onChangedEntry = []
        l = []
        self['list'] = List(l)

        self["actions"] = ActionMap(["ColorActions", "SetupActions", "MenuActions"],
                                {
                                    'red': self.keyCancel,
                                    'green': self.manual_update,
                                    'cancel': self.keyCancel,
                                    'ok': self.openSelected,
                                    'menu': self.keyCancel
                                }, -2)
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Run')

        self.createSetup()

    def createSetup(self):
        l = []
        l.append(('0', 'Configure'))
        l.append(('1', 'Providers'))
        l.append(('2', 'Run'))
        l.append(('3', 'Status'))
        l.append(('4', 'Show Log'))
        l.append(('5', 'About'))
        self['list'].list = l

    def openSelected(self):
        index = self['list'].getIndex()

        if index == 0:
            self.session.openWithCallback(E2m3u2b_Plugin.done_configuring, E2m3u2b_Config)
            return
        if index == 1:
            self.session.open(E2m3u2b_Providers)
            return
        if index == 2:
            self.manual_update()
            return
        if index == 3:
            self.session.open(E2m3u2b_Status)
            return
        if index == 4:
            self.session.open(E2m3u2b_Log)
            return
        if index == 5:
            self.session.open(E2m3u2b_About)
            return

    def manual_update(self):
        """Manual update
        """
        self.session.openWithCallback(self.manual_update_callback, MessageBox, "Update of channels will start.\n"
                                                                               "This may take a few minutes.\n"
                                                                               "Proceed?", MessageBox.TYPE_YESNO,
                                      timeout=15, default=True)

    def manual_update_callback(self, confirmed):
        if not confirmed:
            return
        try:
            E2m3u2b_Plugin.do_update()
        except Exception, e:
            print>> log, "[e2m3u2b] manual_update_callback Error:", e
            if config.plugins.e2m3u2b.debug.value:
                raise e

    def keyCancel(self):
        self.close()


class E2m3u2b_Config(ConfigListScreen, Screen):
    skin = """
        <screen position="center,center" size="600,500">    
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />    
        <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
        <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />                
        <widget name="config" position="10,60" size="590,350" scrollbarMode="showOnDemand" />        
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setup_title = 'IPTV Bouquet Maker Configure'
        Screen.setTitle(self, self.setup_title)
        self.skinName = ["E2m3u2b_Config", "AutoBouquetsMaker_Setup"]

        self.onChangedEntry = [ ]
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

        self['actions'] = ActionMap(['SetupActions', 'ColorActions', 'VirtualKeyboardActions', 'MenuActions'],
                                    {
                                        'ok': self.keySave,
                                        'cancel': self.keyCancel,
                                        'red': self.keyCancel,
                                        'green': self.keySave,
                                        'menu': self.keyCancel,
                                    }, -2)

        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Ok')
        self['description'] = Label()

        self.createSetup()

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        indent = '- '

        self.list.append(getConfigListEntry('Automatic bouquet update (schedule):', config.plugins.e2m3u2b.autobouquetupdate, 'Enable to update bouquets on a schedule'))
        if config.plugins.e2m3u2b.autobouquetupdate.getValue():
            self.list.append(getConfigListEntry(indent + 'Update interval (hours):', config.plugins.e2m3u2b.updateinterval, 'Set the number of hours between automatic bouquet updates'))
        # leave update at boot disabled for now
        # self.list.append(getConfigListEntry('Automatic bouquet update (when box starts):', config.plugins.e2m3u2b.autobouquetupdateatboot, 'Update bouquets at startup'))
        self.list.append(getConfigListEntry('Picon save path:', config.plugins.e2m3u2b.iconpath, 'Select where to save picons (if download is enabled)'))
        self.list.append(getConfigListEntry('Debug mode:', config.plugins.e2m3u2b.debug, 'Enable debug mode'))

        self['config'].list = self.list
        self['config'].setList(self.list)

    def changedEntry(self):
        self.item = self['config'].getCurrent()
        for x in self.onChangedEntry:
            # for summary desc
            x()

        try:
            # If an option is changed that has additional config options show or hide these options
            if isinstance(self['config'].getCurrent()[1], ConfigYesNo) or isinstance(self['config'].getCurrent()[1], ConfigSelection):
                self.createSetup()
        except:
            pass

    def keySave(self):
        self.saveAll()
        self.close()

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()

    def keyCancel(self):
        if self['config'].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, 'Really close without saving settings?')
        else:
            self.close()

class E2m3u2b_Status(Screen):
    skin = """
        <screen position="center,center" size="600,500">
            <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="5"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />        
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <widget name="about" position="10,50" size="580,430" font="Regular;18"/>                    
        </screen>
        """

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        Screen.setTitle(self, "IPTV Bouquet Maker - Status")
        self.skinName = ['E2m3u2b_Status', 'AutoBouquetsMaker_About']

        self["about"] = Label("")
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
                                    {
                                        "red": self.keyCancel,
                                        "cancel": self.keyCancel,
                                        "menu": self.keyCancel
                                    }, -2)
        self["key_red"] = Button("Close")

        if config.plugins.e2m3u2b.last_update:
            self["about"].setText('Last channel update: {}'.format(config.plugins.e2m3u2b.last_update.value))

    def keyCancel(self):
        self.close()

class E2m3u2b_Log(Screen):
    skin = """
    <screen position="center,center" size="600,500">
    <ePixmap name="red" position="0,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />    
    <ePixmap name="blue" position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />    
    <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />    
    <widget name="key_blue" position="140,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />        
    <widget name="list" position="10,40" size="540,340" />
    </screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        Screen.setTitle(self, "IPTV Bouquet Maker - Log")
        self.skinName = ["E2m3u2b_Log", "EPGImportLog", "XMLTVImportLog"]

        self["key_red"] = Button("Close")
        self["key_blue"] = Button("Clear")
        self["list"] = ScrollLabel(log.getvalue())
        self["actions"] = ActionMap(["DirectionActions", "OkCancelActions", "ColorActions", "MenuActions"],
                                    {
                                        "red": self.keyCancel,
                                        "blue": self.keyClear,
                                        "cancel": self.keyCancel,
                                        "ok": self.keyCancel,
                                        "left": self["list"].pageUp,
                                        "right": self["list"].pageDown,
                                        "up": self["list"].pageUp,
                                        "down": self["list"].pageDown,
                                        "pageUp": self["list"].pageUp,
                                        "pageDown": self["list"].pageDown,
                                        "menu": self.keyCancel,
                                    }, -2)

    def keyCancel(self):
        self.close(False)

    def keyClear(self):
        log.logfile.reset()
        log.logfile.truncate()
        self.close(False)

#class SetupSummary(Screen):
#    def __init__(self, session, parent):
#        Screen.__init__(self, session, parent=parent)
#        self['SetupTitle'] = StaticText(parent.setup_title)
#        self['SetupEntry'] = StaticText('')
#        self['SetupValue'] = StaticText('')
#        self.onShow.append(self.addWatcher)
#        self.onHide.append(self.removeWatcher)#
#
#    def addWatcher(self):
#        self.parent.onChangedEntry.append(self.selectionChanged)
#        self.parent['config'].onSelectionChanged.append(self.selectionChanged)
#        self.selectionChanged()#
#
#    def removeWatcher(self):
#        self.parent.onChangedEntry.remove(self.selectionChanged)
#        self.parent['config'].onSelectionChanged.remove(self.selectionChanged)#
#
#    def selectionChanged(self):
#        print('SetupSummary -> selectionChanged')
#        self['SetupEntry'].text = self.parent.getCurrentEntry()
#        self['SetupValue'].text = self.parent.getCurrentValue()
#        if hasattr(self.parent, 'getCurrentDescription'):
#            self.parent['description'].text = self.parent.getCurrentDescription()