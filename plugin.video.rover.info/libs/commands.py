# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import sys
import xbmc
import xbmcgui
from webclient import plugin, load_page, SITE

_ = plugin.initialize_gettext()
dialog = xbmcgui.Dialog()


def clear_history():
    history = os.path.join(plugin.config_dir, '__history__.pcl')
    if os.path.exists(history) and dialog.yesno(_('Warning!'), _('Do you really want to clear search history?')):
        os.remove(history)
        if not os.path.exists(history):
            dialog.notification(plugin.id, _('Search history cleaned successfully'), icon=plugin.icon, sound=False)


def clear_cache():
    cache = os.path.join(plugin.config_dir, '__cache__.pcl')
    if os.path.exists(cache) and dialog.yesno(_('Warning!'), _('Do you really want to clear plugin cache?')):
        os.remove(cache)
        if not os.path.exists(cache):
            dialog.notification(plugin.id, _('Plugin cache cleaned successfully'), icon=plugin.icon, sound=False)


def clear_cookies():
    cookies = os.path.join(plugin.config_dir, '__cookies__.pcl')
    if os.path.exists(cookies) and dialog.yesno(_('Warning!'), _('Do you really want to clear cookies?')):
        os.remove(cookies)
        if not os.path.exists(cookies):
            dialog.notification(plugin.id, _('Cookies cleaned successfully'), icon=plugin.icon, sound=False)


def add_remove_bookmark(action, link):
    load_page(SITE + link)
    if action == 'add_bookmark':
        message = _('Item added to Rover.Info bookmarks')
    else:
        message = _('Item removed from Rover.Info bookmarks')
        xbmc.executebuiltin('Container.Refresh')
    dialog.notification(plugin.id, message, icon=plugin.icon, sound=False)


if __name__ == '__main__':
    if sys.argv[1] == 'history':
        clear_history()
    elif sys.argv[1] == 'cache':
        clear_cache()
    elif sys.argv[1] == 'cookies':
        clear_cookies()
    elif sys.argv[1] in ('add_bookmark', 'remove_bookmark'):
        add_remove_bookmark(sys.argv[1], sys.argv[2])
