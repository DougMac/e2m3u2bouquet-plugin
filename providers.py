import os
import log
#import providersmanager as PM
import e2m3u2bouquet
from enigma import eTimer
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.config import config, \
			 getConfigListEntry
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Sources.List import List
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
try:
    from Tools.Directoires import SCOPE_ACTIVE_SKIN
except:
    pass

ENIGMAPATH = '/etc/enigma2/'
CFGPATH = os.path.join(ENIGMAPATH, 'e2m3u2bouquet/')

class E2m3u2b_Providers(Screen):
    skin = """
        <screen position="center,center" size="600,500">
            <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
            <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
            <widget source="list" render="Listbox" position="10,50" size="580,430" scrollbarMode="showOnDemand">
                <convert type="TemplatedMultiContent">
                    {"template": [
                        MultiContentEntryPixmapAlphaTest(pos = (10, 0), size = (32, 32), png = 0),
                        MultiContentEntryText(pos = (47, 0), size = (400, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
                        MultiContentEntryText(pos = (450, 0), size = (120, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
                        ],
                        "fonts": [gFont("Regular",22)],
                        "itemHeight": 30
                    }
                </convert>
            </widget>
            <widget name="pleasewait" position="10,60" size="580,140" font="Regular;18" halign="center" valign="center" transparent="0" zPosition="5"/>
            <widget name="no_providers" position="10,50" size="580,430" font="Regular;18" zPosition="4" />
        </screen>
        """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        Screen.setTitle(self, "IPTV Bouquet Maker - Providers")
        self.skinName = ['E2m3u2b_Providers', 'AutoBouquetsMaker_HideSections']

        self.drawList = []
        self["list"] = List(self.drawList)

        self.activityTimer = eTimer()
        self.activityTimer.timeout.get().append(self.prepare)

        self["actions"] = ActionMap(["ColorActions", "SetupActions", "MenuActions"],
                                    {
                                        'ok': self.openSelected,
                                        'cancel': self.keyCancel,
                                        'red': self.keyCancel,
                                        'green': self.key_add,
                                        'menu': self.keyCancel
                                    }, -2)
        self["key_red"] = Button("Cancel")
        self["key_green"] = Button("Add")

        self["pleasewait"] = Label()
        self['no_providers'] = Label()
        self['no_providers'].setText('No providers please add one (use green button) or create config.xml file')
        self['no_providers'].hide()

        self.onLayoutFinish.append(self.populate)

    def populate(self):
        self["actions"].setEnabled(False)

        self["pleasewait"].setText('Please wait...')
        self.activityTimer.start(1)

    def prepare(self):
        self.activityTimer.stop()

        self.e2m3u2b_config = e2m3u2bouquet.Config()
        if os.path.isfile(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml')):
            self.e2m3u2b_config.providers = self.e2m3u2b_config.read_config(os.path.join(CFGPATH, 'config.xml'))

        self.refresh()
        self["pleasewait"].hide()
        self["actions"].setEnabled(True)

    def keyCancel(self):
        self.close()

    def key_add(self):
        provider = e2m3u2bouquet.Provider()
        provider.name = 'New'
        provider.enabled = True
        self.e2m3u2b_config.providers.append(provider)
        self.session.openWithCallback(self.provider_add_callback, E2m3u2b_Providers_Config, self.e2m3u2b_config, provider)

    def openSelected(self):
        provider_name = self['list'].getCurrent()[1]
        # find provider in providers list
        provider = next((x for x in self.e2m3u2b_config.providers if x.name == provider_name), None)

        self.session.openWithCallback(self.provider_config_callback, E2m3u2b_Providers_Config, self.e2m3u2b_config, provider)

    def buildListEntry(self, provider):
        if provider.enabled:
            try:
                pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/lock_on.png'))
            except:
                pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/lock_on.png'))
        else:
            try:
                pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/lock_off.png'))
            except:
                pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/lock_off.png'))

        return (pixmap, str(provider.name), '')

    def refresh(self):
        self.drawList = []

        for provider in self.e2m3u2b_config.providers:
            self.drawList.append(self.buildListEntry(provider))
        self['list'].setList(self.drawList)

        if not self.e2m3u2b_config.providers:
            self['no_providers'].show()
        else:
            self['no_providers'].hide()

    def provider_config_callback(self):
        self.refresh()

    def provider_add_callback(self):
        for x in self.e2m3u2b_config.providers:
            if x.name == 'New':
                try:
                    self.e2m3u2b_config.providers.remove(x)
                except ValueError:
                    pass
        self.refresh()

class E2m3u2b_Providers_Config(ConfigListScreen, Screen):
    skin = """
    <screen position="center,center" size="600,500">
    <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
    <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
    <widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
    <widget name="config" position="10,60" size="590,330" scrollbarMode="showOnDemand" />
    <widget name="description" position="10,410" size="590,80" font="Regular;18" halign="center" valign="top" transparent="0" zPosition="1"/>
    <widget name="pleasewait" position="10,60" size="590,350" font="Regular;18" halign="center" valign="center" transparent="0" zPosition="2"/>
    </screen>"""

    def __init__(self, session, providers_config, provider):
        Screen.__init__(self, session)
        self.session = session
        self.e2m3u2b_config = providers_config
        self.provider = provider

        self.setup_title = 'Provider Configure - {}'.format(provider.name)
        Screen.setTitle(self, self.setup_title)
        self.skinName = ["E2m3u2b_Providers_Config", "AutoBouquetsMaker_ProvidersSetup"]

        self.onChangedEntry = [ ]
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

        self.activityTimer = eTimer()
        self.activityTimer.timeout.get().append(self.prepare)

        self['actions'] = ActionMap(['SetupActions', 'ColorActions', 'VirtualKeyboardActions', 'MenuActions'],
                                    {
                                        'ok': self.keySave,
                                        'cancel': self.keyCancel,
                                        'red': self.keyCancel,
                                        'green': self.keySave,
                                        'yellow': self.key_delete,
                                        'menu': self.keyCancel,
                                    }, -2)

        self['key_red'] = Button('Cancel')
        self['key_green'] = Button('Save')
        self['key_yellow'] = Button('Delete')
        self['description'] = Label()
        self['pleasewait'] = Label()

        self.onLayoutFinish.append(self.populate)

    def populate(self):
        self['actions'].setEnabled(False)
        self['pleasewait'].setText("Please wait...")
        self.activityTimer.start(1)

    def prepare(self):
        self.activityTimer.stop()

        self.provider_delete = ConfigYesNo(default=False)
        self.provider_enabled = ConfigYesNo(default=False)
        self.provider_enabled.value = self.provider.enabled
        self.provider_name = ConfigText(default='', fixed_size=False, visible_width=20)
        self.provider_name.value = self.provider.name if self.provider.name != 'New' else ''
        self.provider_settings_level = ConfigSelection(default='simple', choices=['simple', 'expert'])
        self.provider_settings_level.value = self.provider.settings_level
        self.provider_m3u_url = ConfigText(default='', fixed_size=False, visible_width=20)
        self.provider_m3u_url.value = self.provider.m3u_url
        self.provider_epg_url = ConfigText(default='', fixed_size=False, visible_width=20)
        self.provider_epg_url.value = self.provider.epg_url
        self.provider_username = ConfigText(default='', fixed_size=False)
        self.provider_username.value = self.provider.username
        self.provider_password = ConfigPassword(default='', fixed_size=False)
        self.provider_password.value = self.provider.password
        self.provider_multi_vod = ConfigEnableDisable(default=False)
        self.provider_multi_vod.value = self.provider.multi_vod
        self.provider_picons = ConfigYesNo(default=False)
        self.provider_picons.value = self.provider.picons
        self.provider_bouquet_pos = ConfigSelection(default='bottom', choices=['bottom', 'top'])
        if self.provider.bouquet_top:
            self.provider_bouquet_pos.value = 'top'
        self.provider_all_bouquet = ConfigYesNo(default=False)
        self.provider_all_bouquet.value = self.provider.all_bouquet
        self.provider_iptv_types = ConfigEnableDisable(default=False)
        self.provider_iptv_types.value = self.provider.iptv_types
        self.provider_streamtype_tv = ConfigSelection(default='', choices=[' ', '1', '4097', '5001', '5002'])
        self.provider_streamtype_tv.value = self.provider.streamtype_tv
        self.provider_streamtype_vod = ConfigSelection(default='', choices=[' ', '4097', '5001', '5002'])
        self.provider_streamtype_vod.value = self.provider.streamtype_vod
        # n.b. first option in stream type choice lists is an intentional single space
        self.provider_sref_override = ConfigEnableDisable(default=False)
        self.provider_sref_override.value = self.provider.sref_override
        self.provider_bouquet_download = ConfigEnableDisable(default=False)
        self.provider_bouquet_download.value = self.provider.bouquet_download

        self.create_setup()
        self['pleasewait'].hide()
        self['actions'].setEnabled(True)

    def create_setup(self):
        self.editListEntry = None
        self.list = []
        indent = '- '

        self.list.append(getConfigListEntry('Name:', self.provider_name, 'Provider name'))
        self.list.append(getConfigListEntry('Delete:', self.provider_delete, 'Delete provider {}'.format(self.provider.name)))
        if not self.provider_delete.value:
            self.list.append(getConfigListEntry('Enabled:', self.provider_enabled, 'Enable provider {}'.format(self.provider.name)))
            if self.provider_enabled.value:
                self.list.append(getConfigListEntry('Setup mode:', self.provider_settings_level, 'Choose level of settings. Expert shows all options'))
                self.list.append(getConfigListEntry('M3U url:', self.provider_m3u_url, 'Providers M3U url. USERNAME & PASSWORD will be replaced by values below'))
                self.list.append(getConfigListEntry('EPG url:', self.provider_epg_url,'Providers EPG url. USERNAME & PASSWORD will be replaced by values below'))
                self.list.append(getConfigListEntry('Username:', self.provider_username, 'If set will replace USERNAME placeholder in urls'))
                self.list.append(getConfigListEntry('Password:', self.provider_password, 'If set will replace PASSWORD placeholder in urls'))
                self.list.append(getConfigListEntry('Multi VOD:', self.provider_multi_vod, 'Enable to create multiple VOD bouquets rather than single VOD bouquet'))
                self.list.append(getConfigListEntry('Picons:', self.provider_picons, 'Automatically download Picons'))
                self.list.append(getConfigListEntry("IPTV bouquet position", self.provider_bouquet_pos, 'Select where to place IPTV bouquets '))
                self.list.append(getConfigListEntry('Create all channels bouquet:', self.provider_all_bouquet, 'Create a bouquet containing all channels'))
                if self.provider_settings_level.value == 'expert':
                    self.list.append(getConfigListEntry('All IPTV type:', self.provider_iptv_types, 'Normally should be left disabled. Setting to enabled may allow recording on some boxes. If you playback issues (e.g. stuttering on channels) set back to disabled'))
                    self.list.append(getConfigListEntry('TV Stream Type:', self.provider_streamtype_tv, 'Stream type for TV services'))
                    self.list.append(getConfigListEntry('VOD Stream Type:', self.provider_streamtype_vod, 'Stream type for VOD services'))
                    self.list.append(getConfigListEntry("Override service refs", self.provider_sref_override, 'Should be left disabled unless you need to use the override.xml to override service refs (e.g. for DVB to IPTV EPG mapping)'))
                    self.list.append(getConfigListEntry("Check providers bouquet", self.provider_bouquet_download, 'Enable this option to check and use providers custom service refs'))

        self['config'].list = self.list
        self['config'].setList(self.list)

    def changedEntry(self):
        self.item = self['config'].getCurrent()
        for x in self.onChangedEntry:
            # for summary desc
            x()
        try:
            # if an option is changed that has additional config options show or hide these options
            if isinstance(self['config'].getCurrent()[1], ConfigYesNo) or isinstance(self['config'].getCurrent()[1], ConfigSelection):
                self.create_setup()
        except:
            pass

    def keySave(self):
        previous_name = self.provider.name

        # if delete is set to true or empty name show message box to confirm deletion
        if self.provider_name.value == '' or self.provider_delete.value:
            self.session.openWithCallback(self.delete_confirm, MessageBox, 'Confirm deletion of provider {}'.format(previous_name))
        self.provider.enabled = self.provider_enabled.value
        self.provider.name = self.provider_name.value
        self.provider.settings_level = self.provider_settings_level.value
        self.provider.m3u_url = self.provider_m3u_url.value
        self.provider.epg_url = self.provider_epg_url.value
        self.provider.username = self.provider_username.value
        self.provider.password = self.provider_password.value
        self.provider.multi_vod = self.provider_multi_vod.value
        self.provider.picons = self.provider_picons.value
        if self.provider_bouquet_pos.value == 'top':
            self.provider.bouquet_top = True
        else:
            self.provider.bouquet_top = False
        self.provider.all_bouquet = self.provider_all_bouquet.value
        self.provider.iptv_types = self.provider_iptv_types.value
        self.provider.streamtype_tv = self.provider_streamtype_tv.value.strip()
        self.provider.streamtype_vod = self.provider_streamtype_vod.value.strip()
        self.provider.sref_override = self.provider_sref_override.value
        self.provider.bouquet_download = self.provider_bouquet_download.value

        # disable provider if no m3u url
        if not self.provider_m3u_url.value:
            self.provider.enabled = False

        if self.provider_name.value != '' and self.provider_name.value != previous_name:
            print>> log, '[e2m3u2b] Provider {} updated'.format(self.provider_name.value)

        # save xml config
        self.e2m3u2b_config.write_config()
        self.close()

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()

    def keyCancel(self):
        self.close()

        # TODO detect if provider config screen is closed without saving
        #if self['config'].isChanged():
        #    self.session.openWithCallback(self.cancelConfirm, MessageBox, 'Really close without saving settings?')
        #else:
        #    self.close()

    def key_delete(self):
        self.session.openWithCallback(self.delete_confirm, MessageBox, 'Confirm deletion of provider {}'.format(self.provider.name))

    def delete_confirm(self, result):
        if not result:
            return
        print>> log, '[e2m3u2b] Provider {} delete'.format(self.provider.name)
        try:
            self.e2m3u2b_config.providers.remove(self.provider)
        except ValueError:
            pass
        self.e2m3u2b_config.write_config()
        self.close()
