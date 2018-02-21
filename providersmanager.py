import log
import os
import e2m3u2bouquet

from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, ConfigText, \
			 ConfigSelection, ConfigNumber, ConfigSubDict, NoSave, ConfigPassword, \
             ConfigSelectionNumber


class ProviderConfigEntry():
    name = ''
    enabled = False
    settings_level = 'simple'
    m3u_url = ''
    epg_url = ''
    username = ''
    password = ''
    iptv_types = False
    multi_vod = False
    all_bouquet = False
    picons = False
    sref_override = False
    bouquet_url = ''
    bouquet_download = False
    bouquet_top = False

class ProvidersConfig():
    providers = {}

    def read(self):
        """Read providers from config file"""

        # check if we need to migrate previous version setting
        if config.plugins.e2m3u2b.cfglevel.value != '1' and not os.path.isfile(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml')):
            self.migration()

        providers_list = get_providers_config()
        if providers_list:
            for provider_item in providers_list:
                provider = providers_list[provider_item]

                if provider['name']:
                    provider_entry = ProviderConfigEntry()
                    provider_entry.name = provider['name']

                    if 'enabled' in provider and provider['enabled'] == '1':
                        provider_entry.enabled = True;
                    if 'settingslevel' in provider and provider['settingslevel'] == 'expert':
                        provider_entry.settings_level = 'expert'
                    if 'm3uurl' in provider:
                        provider_entry.m3u_url = provider['m3uurl']
                    if 'epgurl' in provider:
                        provider_entry.epg_url = provider['epgurl']
                    if 'username' in provider:
                        provider_entry.username = provider['username']
                    if 'password' in provider:
                        provider_entry.password = provider['password']
                    if 'iptvtypes' in provider and provider['iptvtypes'] == '1':
                        provider_entry.iptv_types = True
                    if 'multivod' in provider and provider['multivod'] == '1':
                        provider_entry.multi_vod = True
                    if 'allbouquet' in provider and provider['allbouquet'] == '1':
                        provider_entry.all_bouquet = True
                    if 'picons' in provider and provider['picons'] == '1':
                        provider_entry.picons = True
                    if 'xcludesref' in provider and provider['xcludesref'] == '0':
                        provider_entry.sref_override = True
                    if 'bouqueturl' in provider:
                        provider_entry.bouquet_url = provider['bouqueturl']
                    if 'bouquetdownload' in provider and provider['bouquetdownload'] == '1':
                        provider_entry.bouquet_download = True
                    if 'bouquettop' in provider and provider['bouquettop'] == '1':
                        provider_entry.bouquet_top = True

                    self.providers[provider_entry.name] = provider_entry

    def migration(self):
        """Attempt to migrate settings from old version"""
        print>> log, '[e2m3u2b] Migrating previous plugin settings...'.format(self.provider_name.value)

        if config.plugins.e2m3u2b.providername.value:
            config_provider = config.plugins.e2m3u2b.providername.value

            # get m3u and epg url from git providers
            providers = get_github_providers()

            if config_provider in providers:
                git_provider = providers[config_provider]
                print("git provider", git_provider)
                if 'm3u' in git_provider:
                    provider_config = ProvidersConfig()
                    provider_entry = ProviderConfigEntry()
                    provider_entry.enabled = True
                    provider_entry.name = config_provider
                    provider_entry.m3u_url = git_provider['m3u']
                    provider_entry.epg_url = git_provider.get('epg', None)
                    provider_entry.username = config.plugins.e2m3u2b.username.value
                    provider_entry.password = config.plugins.e2m3u2b.password.value
                    provider_entry.iptv_types = config.plugins.e2m3u2b.iptvtypes.value
                    provider_entry.multi_vod = config.plugins.e2m3u2b.multivod.value
                    provider_entry.bouquet_top = config.plugins.e2m3u2b.bouquetpos.value == 'top'
                    provider_entry.all_bouquet = config.plugins.e2m3u2b.allbouquet.value
                    provider_entry.picons = config.plugins.e2m3u2b.picons.value
                    provider_entry.sref_override = config.plugins.e2m3u2b.srefoverride.value
                    provider_entry.bouquet_download = config.plugins.e2m3u2b.bouquetdownload.value

                    provider_config.providers[config_provider] = provider_entry
                    provider_config.write()

                    # reset legacy config value to default values so they are removed from settings file
                    config.plugins.e2m3u2b.providername.value = ''
                    config.plugins.e2m3u2b.providername.save()
                    config.plugins.e2m3u2b.username.value = ''
                    config.plugins.e2m3u2b.username.save()
                    config.plugins.e2m3u2b.password.value = ''
                    config.plugins.e2m3u2b.password.save()
                    config.plugins.e2m3u2b.iptvtypes.value = False
                    config.plugins.e2m3u2b.iptvtypes.save()
                    config.plugins.e2m3u2b.multivod.value = False
                    config.plugins.e2m3u2b.multivod.save()
                    config.plugins.e2m3u2b.bouquetpos.value = 'bottom'
                    config.plugins.e2m3u2b.bouquetpos.save()
                    config.plugins.e2m3u2b.allbouquet.value = False
                    config.plugins.e2m3u2b.allbouquet.save()
                    config.plugins.e2m3u2b.picons.value = False
                    config.plugins.e2m3u2b.picons.save()
                    config.plugins.e2m3u2b.srefoverride.value = False
                    config.plugins.e2m3u2b.srefoverride.save()
                    config.plugins.e2m3u2b.bouquetdownload.value = False
                    config.plugins.e2m3u2b.bouquetdownload.save()

                    #save cfglevel version
                    config.plugins.e2m3u2b.cfglevel.value = '1'
                    config.plugins.e2m3u2b.cfglevel.save()

    def write(self):
        """Write providers to config file
        Manually write instead of using ElementTree so that we can format the file for easy human editing
        (inc. Windows line endings)
        """
        config_file = os.path.join(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml'))
        indent = "  "

        if self.providers:
            with open(config_file, 'wb') as f:
                f.write('<!--\r\n')
                f.write('{}E2m3u2bouquet supplier config file\r\n'.format(indent))
                f.write('{}Add as many suppliers as required\r\n'.format(indent))
                f.write('{}this config file will be used and the relevant bouquets set up for all suppliers entered\r\n'.format(indent))
                f.write('{}0 = No/False\r\n'.format(indent))
                f.write('{}1 = Yes/True\r\n'.format(indent))
                f.write('{}For elements with <![CDATA[]] enter value between empty brackets e.g. <![CDATA[mypassword]]>\r\n'.format(indent))
                f.write('-->\r\n')
                f.write('<config>\r\n')
                for provider_name in self.providers:
                    provider_entry = self.providers[provider_name]
                    f.write('{}<supplier>\r\n'.format(indent))
                    f.write('{}<name>{}</name><!-- Supplier Name -->\r\n'.format(2 * indent, xml_escape(provider_entry.name)))
                    f.write('{}<enabled>{}</enabled><!-- Enable or disable the supplier (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.enabled else '0'))
                    f.write('{}<settingslevel>{}</settingslevel>\r\n'.format(2 * indent, provider_entry.settings_level))
                    f.write('{}<m3uurl><![CDATA[{}]]></m3uurl><!-- Extended M3U url --> \r\n'.format(2 * indent, provider_entry.m3u_url))
                    f.write('{}<epgurl><![CDATA[{}]]></epgurl><!-- XMLTV EPG url -->\r\n'.format(2 * indent, provider_entry.epg_url))
                    f.write('{}<username><![CDATA[{}]]></username><!-- (Optional) will replace USERNAME placeholder in urls -->\r\n'.format(2 * indent, provider_entry.username))
                    f.write('{}<password><![CDATA[{}]]></password><!-- (Optional) will replace PASSWORD placeholder in urls -->\r\n'.format(2 * indent, provider_entry.password))
                    f.write('{}<iptvtypes>{}</iptvtypes><!-- Change all TV streams to IPTV type (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.iptv_types else '0'))
                    f.write('{}<multivod>{}</multivod><!-- Split VOD into seperate categories (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.multi_vod else '0'))
                    f.write('{}<allbouquet>{}</allbouquet><!-- Create all channels bouquet (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.all_bouquet else '0'))
                    f.write('{}<picons>{}</picons><!-- Automatically download Picons (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.picons else '0'))
                    f.write('{}<xcludesref>{}</xcludesref><!-- Disable service ref overriding from override.xml file (0 or 1) -->\r\n'.format(2 * indent, '0' if provider_entry.sref_override else '1'))
                    f.write('{}<bouqueturl><![CDATA[{}]]></bouqueturl><!-- (Optional) url to download providers bouquet - to map custom service references -->\r\n'.format(2 * indent, provider_entry.bouquet_url))
                    f.write('{}<bouquetdownload>{}</bouquetdownload><!-- Download providers bouquet (uses default url) must have username and password set above - to map custom service references -->\r\n'.format(2 * indent, '1' if provider_entry.bouquet_download else '0'))
                    f.write('{}<bouquettop>{}</bouquettop><!-- Place IPTV bouquets at top (0 or 1) -->\r\n'.format(2 * indent, '1' if provider_entry.bouquet_top else '0'))
                    f.write('{}</supplier>\r\n'.format(indent))
                f.write('</config>\r\n')
        else:
            # no providers delete config file
            if os.path.isfile(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml')):
                print('no providers remove config')
                os.remove(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml'))

        # save cfglevel
        config.plugins.e2m3u2b.cfglevel.value = '1'
        config.plugins.e2m3u2b.cfglevel.save()

def get_github_providers():
    iptv = e2m3u2bouquet.IPTVSetup()
    providers = {}
    try:
        providers = iptv.read_providers((iptv.download_providers(e2m3u2bouquet.PROVIDERSURL)))
    except Exception, e:
        print>> log, '[e2m3u2b] Unable to download Github providers list'
        if config.plugins.e2m3u2b.debug.value:
            raise e
    return providers

def get_providers_config():
    suppliers = {}
    if os.path.isfile(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml')):
        try:
            # configs = e2m3u2bouquet.config()
            suppliers = e2m3u2bouquet.config().readconfig(os.path.join(e2m3u2bouquet.CFGPATH, 'config.xml'))
        except Exception, e:
            print>> log, '[e2m3u2b] Unable to read config file'
            if config.plugins.e2m3u2b.debug.value:
                raise e
    return suppliers


def xml_escape(string):
    return string.replace("&", "&amp;") \
        .replace("\"", "&quot;") \
        .replace("'", "&apos;") \
        .replace("<", "&lt;") \
        .replace(">", "&gt;")
