# Copyright (c) 2010-2011 Torrent-TV.RPI
# Writer (c) 2016, Welicobratov K.A., E-mail: 07pov23@gmail.com
import xbmcgui
import xbmc

class AdsForm(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.playing = False
