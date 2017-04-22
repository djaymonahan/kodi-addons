import xbmcaddon
import xbmc
import sys
import urllib2
import urllib
import threading
import os
import json
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

ADDON = xbmcaddon.Addon( id = 'script.torrent-tv.ae' )
ADDON_ICON	 = ADDON.getAddonInfo('icon')
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_ICON	 = ADDON.getAddonInfo('icon')
DATA_PATH = xbmc.translatePath(os.path.join( "special://profile/addon_data", 'script.torrent-tv.ae') )
ENGINE_NOXBIT = 0
ENGINE_AS = 1
ENGINE_PROXY = 2
skin = ADDON.getSetting('skin')
SKIN_PATH = ADDON_PATH
print skin

class MyThread(threading.Thread):
    def __init__(self, func, params, back = True):
        threading.Thread.__init__(self)
        self.func = func
        self.params = params

    def run(self):
        self.func(self.params)
    def stop(self):
        pass

def showMessage(message = '', heading='Torrent-TV.AE', times = 1234):
    try: 
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, %s)' % (heading.encode('utf-8'), message.encode('utf-8'), times, ADDON_ICON))
    except Exception, e:
        try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, %s)' % (heading, message, times, ADDON_ICON))
        except Exception, e:
            xbmc.log( 'showMessage: exec failed [%s]' % 3)

def GET(target, post=None, cookie = None, tryies = 0):
    try:
        print target
        req = urllib2.Request(url = target, data = post)
        req.add_header('User-Agent', 'Mozilla/5.0')
        if cookie:
            req.add_header('Cookie', 'PHPSESSID=%s' % cookie)
        resp = urllib2.urlopen(req, timeout=10)
        http = resp.read()
        resp.close()
        return http
    except Exception, e:
        if tryies == 0:
            tryies = tryies + 1
            return GET(target, post, cookie, tryies)
        xbmc.log( 'GET EXCEPT [%s]' % (e), 4 )

def GET_JSON(target, post = None, cookie = None):
    return json.loads(GET(target, post, cookie))

def checkPort(params):
        data = GET("https://2ip.ru/check-port/?port=%s" % params)
        beautifulSoup = BeautifulSoup(data)
        port = beautifulSoup.find('div', attrs={'class': 'ip-entry'}).text
        if port.encode('utf-8').find("Порт закрыт") > -1:
            return False
        else:
            return True

def getUserInfo(session):
    data = GET("http://1ttvxbmc.top/v3/userinfo.php?session=%s&typeresult=json" % session)
    return json.loads(data)
    

def tryStringToInt(str_val):
    try:
        return int(str_val)
    except:
        return 0


def getSetting(name, default="", save=True):
    res = ADDON.getSetting(name)
    if res == "":
        res = default
        if res != "" and save:
            ADDON.setSetting(name, res)

    return res


def getSettingDef(name, name_cat):
    import xml.etree.ElementTree as ET
    import os
    path = os.path.join(ADDON_PATH, "resources/settings.xml")
    tree = ET.parse(path)
    xcat = [c for c in tree.getroot().findall("category") if c.attrib["label"] == name_cat][0]
    return [s for s in xcat.findall("setting") if s.attrib["id"] == name][0].attrib


def setSettingDef(name, name_cat, attrib, value):
    import xml.etree.ElementTree as ET
    import os
    path = os.path.join(ADDON_PATH, "resources/settings.xml")
    tree = ET.parse(path)
    xcat = [c for c in tree.getroot().findall("category") if c.attrib["label"] == name_cat][0]

    xel = [s for s in xcat.findall("setting") if s.attrib["id"] == name][0]
    xel.set(attrib, value)
    tree.write(path)


def setSetting(name, value):
    ADDON.setSetting(name, value)
