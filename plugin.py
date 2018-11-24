import time
import os
import errno
import sys
import log
import urllib
import providersmanager as PM

from menu import E2m3u2b_Menu

from enigma import eTimer
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.PluginComponent import plugins


import e2m3u2bouquet

# Global variable
autoStartTimer = None
_session = None
providers_list = {}

# Set default configuration
config.plugins.e2m3u2b = ConfigSubsection()
config.plugins.e2m3u2b.cfglevel = ConfigText(default='')
config.plugins.e2m3u2b.debug = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.autobouquetupdate = ConfigYesNo(default=False)
config.plugins.e2m3u2b.scheduletype = ConfigSelection(default='interval', choices=['interval', 'fixed time'])
config.plugins.e2m3u2b.updateinterval = ConfigSelectionNumber(default=6, min=2, max=48, stepwidth=1)
config.plugins.e2m3u2b.schedulefixedtime = ConfigClock(default=0)
config.plugins.e2m3u2b.autobouquetupdateatboot = ConfigYesNo(default=False)
config.plugins.e2m3u2b.iconpath = ConfigSelection(default='/usr/share/enigma2/picon/',
                                                  choices=['/usr/share/enigma2/picon/',
                                                           '/media/usb/picon/',
                                                           '/media/hdd/picon/',
                                                           '/media/cf/picon/',
                                                           '/media/mmc/picon/'
                                                           '/picon/'
                                                           ])
config.plugins.e2m3u2b.last_update = ConfigText()
config.plugins.e2m3u2b.last_provider_update = ConfigText(default='0')
config.plugins.e2m3u2b.extensions = ConfigYesNo(default=False)
config.plugins.e2m3u2b.mainmenu = ConfigYesNo(default=False)


# legacy config
config.plugins.e2m3u2b.providername = ConfigText(default='')
config.plugins.e2m3u2b.username = ConfigText(default='')
config.plugins.e2m3u2b.password = ConfigPassword(default='')
config.plugins.e2m3u2b.iptvtypes = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.multivod = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.bouquetpos = ConfigSelection(default='bottom',
                                                    choices=['bottom', 'top']
                                                    )
config.plugins.e2m3u2b.allbouquet = ConfigYesNo(default=False)
config.plugins.e2m3u2b.picons = ConfigYesNo(default=False)
config.plugins.e2m3u2b.srefoverride = ConfigEnableDisable(default=False)
config.plugins.e2m3u2b.bouquetdownload = ConfigEnableDisable(default=False)


class AutoStartTimer:
    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        self.timer.callback.append(self.on_timer)
        self.update()

    def get_wake_time(self):
        print>> log, '[e2m3u2b] AutoStartTimer -> get_wake_time'
        if config.plugins.e2m3u2b.autobouquetupdate.value:
            if config.plugins.e2m3u2b.scheduletype.value == 'interval':
                interval = int(config.plugins.e2m3u2b.updateinterval.value)
                nowt = time.time()
                # set next wakeup value to now + interval
                return int(nowt) + (interval * 60 * 60)
            elif config.plugins.e2m3u2b.scheduletype.value == 'fixed time':
                # convert the config clock to a time
                fixed_time_clock = config.plugins.e2m3u2b.schedulefixedtime.value
                now = time.localtime(time.time())

                fixed_wake_time = int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, fixed_time_clock[0], \
                                                   fixed_time_clock[1], now.tm_sec, now.tm_wday, now.tm_yday, now.tm_isdst)))
                print('fixed schedule time: ', time.asctime(time.localtime(fixed_wake_time)))
                return fixed_wake_time
        else:
            return -1

    def update(self, atLeast=0):
        print>>log, '[e2m3u2b] AutoStartTimer -> update'
        self.timer.stop()
        wake = self.get_wake_time()
        nowt = time.time()
        now = int(nowt)

        if wake > 0:
            if wake < now + atLeast:
                if config.plugins.e2m3u2b.scheduletype.value == 'interval':
                    interval = int(config.plugins.e2m3u2b.updateinterval.value)
                    wake += interval * 60 * 60 # add interval in hours if wake up time is in past
                elif config.plugins.e2m3u2b.scheduletype.value == 'fixed time':
                    wake += 60 * 60 * 24 # add 1 day to fixed time if wake up time is in past
            next = wake - now
            self.timer.startLongTimer(next)
        else:
            wake = -1

        # print>> log, '[e2m3u2b] next wake up time {} (now={})'.format(wake, now)
        print>> log, '[e2m3u2b] next wake up time {} (now={})'.format(time.asctime(time.localtime(wake)), time.asctime(time.localtime(now)))
        return wake

    def on_timer(self):
        self.timer.stop()
        now = int(time.time())
        wake = now
        atLeast = 0
        print>> log, '[e2m3u2b] on_timer occured at {}'.format(now)
        print>> log, '[e2m3u2b] Stating bouquet update because auto update bouquet schedule is enabled'

        if config.plugins.e2m3u2b.scheduletype.value == 'fixed time':
            wake = self.get_wake_time()

        #if close enough to wake time do bouquet update
        if wake - now < 60:
            try:
                do_update()
            except Exception, e:
                print>> log, "[e2m3u2b] on_timer Error:", e
                if config.plugins.e2m3u2b.debug.value:
                    raise
        self.update(atLeast)

    def get_status(self):
        print>> log, '[e2m3u2b] AutoStartTimer -> getStatus'

def do_update():
    """Run m3u channel update
    """
    print('do_update called')

    providers_config = PM.ProvidersConfig()
    providers_config.read()

    for provider_name in providers_config.providers:
        provider = providers_config.providers[provider_name]

        if provider.enabled and not provider.name.startswith('Supplier Name'):
            sys.argv = []
            sys.argv.append('-n={}'.format(provider.name))
            if provider.username:
                sys.argv.append('-u={}'.format(provider.username))
            if provider.password:
                sys.argv.append('-p={}'.format(provider.password))
            sys.argv.append('-m={}'.format(provider.m3u_url.replace('USERNAME', urllib.quote_plus(provider.username)).replace('PASSWORD', urllib.quote_plus(provider.password))))
            sys.argv.append('-e={}'.format(provider.epg_url.replace('USERNAME', urllib.quote_plus(provider.username)).replace('PASSWORD', urllib.quote_plus(provider.password))))

            if provider.iptv_types:
                sys.argv.append('-i')
            if provider.streamtype_tv:
                sys.argv.append('-sttv={}'.format(provider.streamtype_tv))
            if provider.streamtype_vod:
                sys.argv.append('-stvod={}'.format(provider.streamtype_vod))
            if provider.multi_vod:
                sys.argv.append('-M')
            if provider.all_bouquet:
                sys.argv.append('-a')
            if provider.picons:
                sys.argv.append('-P')
                sys.argv.append('-q={}'.format(config.plugins.e2m3u2b.iconpath.value))
            if not provider.sref_override:
                sys.argv.append('-xs')
            if provider.bouquet_top:
                sys.argv.append('-bt')
            if provider.bouquet_download:
                sys.argv.append('-bd')
            if provider.bouquet_url:
                sys.argv.append('-b={}'.format(provider.bouquet_url.replace('USERNAME', urllib.quote_plus(provider.username)).replace('PASSWORD', urllib.quote_plus(provider.password))))

            # Call backend module with args
            print>> log, '[e2m3u2b] Starting backend script'
            e2m3u2bouquet.main(sys.argv)
            print>> log, '[e2m3u2b] Finished backend script'

            localtime = time.asctime(time.localtime(time.time()))
            config.plugins.e2m3u2b.last_update.value = localtime
            config.plugins.e2m3u2b.last_update.save()

def do_reset():
    """Reset bouquets and
    epg importer config by running the script uninstall method
    """
    print('do_reset called')

    iptv = e2m3u2bouquet.IPTVSetup()
    iptv.uninstaller()
    iptv.reload_bouquets()


def main(session, **kwargs):
    check_cfg_folder()
    session.open(E2m3u2b_Menu)

def check_cfg_folder():
    """Make config folder if it doesn't exist
    """
    try:
        os.makedirs(e2m3u2bouquet.CFGPATH)
    except OSError, e:      # race condition guard
        if e.errno != errno.EEXIST:
            print>> log, "[e2m3u2b] unable to create config dir:", e
            if config.plugins.e2m3u2b.debug.value:
                raise

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
    try:
        do_update()
    except Exception, e:
        print>> log, "[e2m3u2b] on_boot_start_check Error:", e
        if config.plugins.e2m3u2b.debug.value:
            raise


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
    else:
        print>>log, '[e2m3u2b] stop'


def get_next_wakeup():
    # don't enable waking from deep standby for now
    print>> log, '[e2m3u2b] get_next_wakeup'
    return -1

def menuHook(menuid):
    """ Called whenever a menu is created"""
    if menuid == "mainmenu":
        return [(plugin_name, quick_import_menu, plugin_name, 45)]
    return[]


def extensions_menu(session, **kwargs):
    """ Needed for the extension menu descriptor
    """
    main(session, **kwargs)

def quick_import_menu(session, **kwargs):
    session.openWithCallback(quick_import_callback, MessageBox, "Update of channels will start.\n"
                                                                            "This may take a few minutes.\n"
                                                                            "Proceed?", MessageBox.TYPE_YESNO,
                                   timeout=15, default=True)


def quick_import_callback(confirmed):
    if not confirmed:
        return
    try:
        do_update()
    except Exception, e:
        print>> log, "[e2m3u2b] manual_update_callback Error:", e
        if config.plugins.e2m3u2b.debug.value:
            raise


def update_extensions_menu(cfg_el):
    print>> log, '[e2m3u2b] update extensions menu'
    try:
        if cfg_el.value:
            plugins.addPlugin(extDescriptorQuick)
        else:
            plugins.removePlugin(extDescriptorQuick)
    except Exception, e:
        print>> log, '[e2m3u2b] Failed to update extensions menu: ', e


def update_main_menu(cfg_el):
    print>> log, '[e2m3u2b] update main menu'
    try:
        if cfg_el.value:
            plugins.addPlugin(extDescriptorQuickMain)
        else:
            plugins.removePlugin(extDescriptorQuickMain)
    except Exception, e:
        print>> log, '[e2m3u2b] Failed to update main menu: ', e

plugin_name = 'IPTV Bouquet Maker'
plugin_description = 'IPTV for Enigma2 - E2m3u2bouquet plugin'
print('[e2m3u2b]add notifier')
extDescriptor = PluginDescriptor(name=plugin_name, description=plugin_description, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensions_menu)
extDescriptorQuick = PluginDescriptor(name=plugin_name, description=plugin_description, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=quick_import_menu)
extDescriptorQuickMain = PluginDescriptor(name=plugin_name, description=plugin_description, where=PluginDescriptor.WHERE_MENU, fnc=menuHook)
config.plugins.e2m3u2b.extensions.addNotifier(update_extensions_menu, initial_call=False)
config.plugins.e2m3u2b.mainmenu.addNotifier(update_main_menu, initial_call=False)


def Plugins(**kwargs):
    result = [
        PluginDescriptor(
            name=plugin_name,
            description=plugin_description,
            where=[
                PluginDescriptor.WHERE_AUTOSTART,
                PluginDescriptor.WHERE_SESSIONSTART,
            ],
            fnc=autostart,
            wakeupfnc=get_next_wakeup
        ),
        PluginDescriptor(
            name=plugin_name,
            description=plugin_description,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon='images/e2m3ubouquetlogo.png',
            fnc=main
        )#,
        #PluginDescriptor(
        #    name=plugin_name,
        #    description=plugin_description,
        #    where=PluginDescriptor.WHERE_MENU,
        #    icon='images/e2m3ubouquetlogo.png',
        #    fnc=menuHook
        #)
    ]

    if config.plugins.e2m3u2b.extensions.value:
        result.append(extDescriptorQuick)
    if config.plugins.e2m3u2b.mainmenu.value:
        result.append(extDescriptorQuickMain)
    return result
