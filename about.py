import os
import sys
import e2m3u2bouquet

from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Button import Button

class E2m3u2b_About(Screen):
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
        Screen.setTitle(self, "IPTV Bouquet Maker - About")
        self.skinName = ['E2m3u2b_About', 'AutoBouquetsMaker_About']

        self["about"] = Label("")
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
                                    {
                                        "red": self.keyCancel,
                                        "cancel": self.keyCancel,
                                        "menu": self.keyCancel
                                    }, -2)
        self["key_red"] = Button("Close")

        credit = "IPTV Bouquet Maker Plugin v{}\n".format(e2m3u2bouquet.__version__)
        credit += "Doug Mackay, Dave Sully\n"
        credit += "Multi provider IPTV bouquet maker for enigma2\n"
        credit += "This plugin is free and should not be resold\n"
        credit += "https://www.suls.co.uk\n"
        credit += "https://github.com/su1s/e2m3u2bouquet\n\n"
        credit += "Application credits:\n"
        credit += "- Doug Mackay (main developer) \n"
        credit += "- Dave Sully aka suls (main developer) \n\n"
        credit += "Resources: \n"
        credit += "Tommy Burke's (@tommycahir) enigma2 guides \n"
        credit += "Epg Importer plugin \n"
        credit += "Auto Bouquet Maker plugin"

        self["about"].setText(credit)

    def keyCancel(self):
        self.close()
