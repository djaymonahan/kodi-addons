import xbmc
import xbmcaddon
import cPickle
import defines
import os

import mainform

if __name__ == '__main__':
    if not defines.ADDON.getSetting('skin'):
       defines.ADDON.setSetting('skin', 'estuary')
    if not defines.ADDON.getSetting("login"):
       defines.ADDON.setSetting("login", "anonymous")
       defines.ADDON.setSetting("password", "anonymous")

    print defines.ADDON_PATH
    print defines.SKIN_PATH
    w = mainform.WMainForm("mainform.xml", defines.SKIN_PATH, defines.ADDON.getSetting('skin'))
    w.doModal()
    defines.showMessage('Close plugin', 'Torrent-TV.AML', 1000)
    del w
    