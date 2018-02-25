import time
import os
import sys
import log
import providersmanager as PM

from menu import E2m3u2b_Menu

from enigma import eTimer
from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber
from Plugins.Plugin import PluginDescriptor


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
config.plugins.e2m3u2b.updateinterval = ConfigSelectionNumber(default=6, min=2, max=48, stepwidth=1)
config.plugins.e2m3u2b.autobouquetupdateatboot = ConfigYesNo(default=False)
config.plugins.e2m3u2b.iconpath = ConfigSelection(default='/usr/share/enigma2/picon/',
                                                  choices=['/usr/share/enigma2/picon/',
                                                           '/media/usb/picon/',
                                                           '/media/hdd/picon/',
                                                           '/picon/'
                                                           ])
config.plugins.e2m3u2b.last_update = ConfigText()
config.plugins.e2m3u2b.last_provider_update = ConfigText(default='0')
config.plugins.e2m3u2b.extensions = ConfigYesNo(default=False)

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

        print>> log, '[e2m3u2b] AutoStartTimer -> update wake {} now {}'.format(wake, now)

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
        try:
            do_update()
        except Exception, e:
            print>> log, "[e2m3u2b] on_timer Error:", e
            if config.plugins.e2m3u2b.debug.value:
                raise e
        self.update()

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
            sys.argv.append('-m={}'.format(provider.m3u_url.replace('USERNAME', provider.username).replace('PASSWORD', provider.password)))
            sys.argv.append('-e={}'.format(provider.epg_url.replace('USERNAME', provider.username).replace('PASSWORD', provider.password)))

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
                sys.argv.append('-b={}'.format(provider.bouquet_url.replace('USERNAME', provider.username).replace('PASSWORD', provider.password)))

            # Call backend module with args
            print>> log, '[e2m3u2b] Starting backend script'
            e2m3u2bouquet.main(sys.argv)
            print>> log, '[e2m3u2b] Finished backend script'

            localtime = time.asctime(time.localtime(time.time()))
            config.plugins.e2m3u2b.last_update.value = localtime
            config.plugins.e2m3u2b.last_update.save()

def main(session, **kwargs):
    session.openWithCallback(done_configuring, E2m3u2b_Menu)

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
            raise e

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

    if config.plugins.e2m3u2b.extensions.value:
        result.append(
            PluginDescriptor(
                name=name,
                description=description,
                where=PluginDescriptor.WHERE_EXTENSIONSMENU,
                fnc=main
            )
        )

    return result
