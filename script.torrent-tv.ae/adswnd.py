import xbmcgui
import xbmc

class AdsForm(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.playing = False
