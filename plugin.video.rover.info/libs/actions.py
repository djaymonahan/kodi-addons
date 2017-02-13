# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

# This plugin uses my SimplePlugin library:
# https://github.com/romanvm/script.module.simpleplugin

import os
import urllib
import re
from collections import namedtuple
import xbmc
import xbmcgui
from simpleplugin import Plugin
import exua
import webclient
import login_window

plugin = Plugin()
icons = os.path.join(plugin.path, 'resources', 'icons')
commands = os.path.join(plugin.path, 'libs', 'commands.py')
_ = plugin.initialize_gettext()

SearchQuery = namedtuple('SearchQuery', ['query', 'path'])
dialog = xbmcgui.Dialog()


def _media_categories(categories, content):
    """
    Create media categories listing
    """
    for category in categories:
        yield {
            'label': u'{0} [COLOR=gray][{1}][/COLOR]'.format(category.name, category.items),
            'url': plugin.get_url(action='media_list', path=category.path, page='0'),
            'thumb': os.path.join(icons, content + '.png')
        }


@plugin.cached(180)
def _get_categories(path):
    return exua.get_categories(path)


@plugin.action('categories')
def media_categories(params):
    """
    Show media categories
    """
    if plugin.cache_pages:
        categories = _get_categories('/{0}/{1}?per=32'.format(plugin.site_lang, params['content']))
    else:
        categories = exua.get_categories('/{0}/{1}?per=32'.format(plugin.site_lang, params['content']))
    plugin.log_debug('Media categories: {0}'.format(categories))
    return _media_categories(categories, params['content'])


@plugin.action()
def root(params):
    """
    Plugin root action
    """
    # The 'content_type' parameter may be passed by Kodi if a plugin is called
    # from "Music add-ons" or "Video add-ons" section.
    if plugin.content_type == 1 or params.get('content_type') == 'video':
        listing = media_categories({'content': 'video'})
    elif plugin.content_type == 2 or params.get('content_type') == 'audio':
        listing = media_categories({'content': 'audio'})
    else:
        listing = [
            {'label': '[{0}]'.format(_('Video')),
             'url': plugin.get_url(action='categories', content='video'),
             'thumb': os.path.join(icons, 'video.png')
             },
            {'label': '[{0}]'.format(_('Audio')),
             'url': plugin.get_url(action='categories', content='audio'),
             'thumb': os.path.join(icons, 'audio.png')
             }
        ]
    for item in listing:
        yield item
    yield {
        'label': '[{0}]'.format(_('Search...')),
        'url': plugin.get_url(action='search'),
        'thumb': os.path.join(icons, 'search.png')
    }
    if plugin.savesearch:
        yield {
            'label': '[{0}]'.format(_('Search history')),
            'url': plugin.get_url(action='search_history'),
            'thumb': os.path.join(icons, 'search_history.png')
        }
    if plugin.authorization:
        bookmarks_item = {'url': plugin.get_url(action='bookmarks')}
        if webclient.is_logged_in():
            bookmarks_item['label'] = '[{0}]'.format(_('My bookmarks'))
            bookmarks_item['thumb'] = os.path.join(icons, 'bookmarks.png')
        else:
            bookmarks_item['label'] = '[{0}]'.format(_('Rover.Info login'))
            bookmarks_item['thumb'] = os.path.join(icons, 'key.png')
        yield bookmarks_item


def _media_list(path, media_listing, page=0, is_search_result=False, from_bookmarks=False):
    """
    Create the list of videos
    """
    if media_listing.original_id is not None and not page and not is_search_result:
        yield {
            'label': '[{0}]'.format(_('Search in the category...')),
            'url': plugin.get_url(action='search', original_id=media_listing.original_id),
            'thumb': os.path.join(icons, 'search.png')
        }
    if media_listing.prev_page is not None:
        yield {
            'label': '{0} < {1}'.format(media_listing.prev_page, _('Previous')),
            'url': plugin.get_url(action='media_list', path=path, page=str(page - 1)),
            'thumb': os.path.join(icons, 'previous.png')
        }
    is_logged_in = webclient.is_logged_in()
    for item in media_listing.media:
        list_item = {
            'label': item.title,
            'url': plugin.get_url(action='display_path', path=item.path),
            'thumb': item.thumb
        }
        if is_logged_in:
            item_id_match = re.search(r'^/(\d+)', item.path)
            if item_id_match is not None:
                if from_bookmarks:
                    list_item['context_menu'] = [(_('Remove from Rover.Info bookmarks'),
                                                 'RunScript({commands},remove_bookmark,{link})'.format(
                                                     commands=commands,
                                                     link='/delete_link/{0}?link_id=4'.format(item_id_match.group(1))
                                                 ))]
                else:
                    list_item['context_menu'] = [(_('Add to Rover.Info bookmarks'),
                                                  'RunScript({commands},add_bookmark,{link})'.format(
                                                      commands=commands,
                                                      link='/add_link/{0}?link_id=4'.format(item_id_match.group(1))
                                                  ))]
        yield list_item
    if media_listing.next_page is not None:
        yield {
            'label': '{0} > {1}'.format(_('Next'), media_listing.next_page),
            'url': plugin.get_url(action='media_list', path=path, page=str(page + 1)),
            'thumb': os.path.join(icons, 'next.png')
        }


@plugin.cached(30)
def _get_media_list(path, page, items):
    return exua.get_media_list(path, page, items)


@plugin.action()
def media_list(params):
    """
    Display the list of videos

    params: path, page
    """
    page = int(params['page'])
    if plugin.cache_pages:
        media_listing = _get_media_list(params['path'], page, plugin.itemcount)
    else:
        media_listing = exua.get_media_list(params['path'], page, plugin.itemcount)
    plugin.log_debug('Media list: {0}'.format(media_listing))
    return plugin.create_listing(_media_list(params['path'],
                                             media_listing,
                                             page,
                                             params.get('is_search_result')),
                                 update_listing=page > 0)


def _media_info(media_details):
    """
    Show a page with media information
    """
    for index, mediafile in enumerate(media_details.files):
        video_info = {'title': mediafile.filename}
        music_info = {'album': media_details.title, 'tracknumber': index + 1}
        if media_details.info:
            if media_details.info.get('year'):
                try:
                    video_info['year'] = music_info['year'] = int(media_details.info['year'])
                except ValueError:
                    pass
            if media_details.info.get('genre'):
                video_info['genre'] = music_info['genre'] = media_details.info['genre']
            if media_details.info.get('director'):
                video_info['director'] = media_details.info['director']
            if media_details.info.get('plot'):
                video_info['plot'] = video_info['plotoutline'] = media_details.info['plot']
            if media_details.info.get('cast'):
                video_info['cast'] = media_details.info['cast'].split(', ')
            if media_details.info.get('rating'):
                try:
                    video_info['rating'] = float(media_details.info['rating'])
                except ValueError:
                    pass
        try:
            mp4 = media_details.mp4[index]
        except (IndexError, TypeError):
            mp4 = ''
        yield {
            'label': mediafile.filename,
            'thumb': media_details.thumb,
            'icon': media_details.thumb,
            'art': {'poster': media_details.thumb},
            'url': plugin.get_url(action='play',
                                  path=mediafile.path,
                                  mirrors=mediafile.mirrors,
                                  mp4=mp4),
            'is_playable': True,
            'context_menu': [
                (_('Show info'), 'Action(Info)'),
                (_('Mark as watched/unwatched'), 'Action(ToggleWatched)'),
                ],
            'info': {'video': video_info, 'music': music_info}
            }


@plugin.cached(180)
def _detect_page_type(path):
    return exua.detect_page_type(path)


@plugin.action()
def display_path(params):
    """
    Display a Rover.Info page depending on its type

    params: path
    """
    if plugin.cache_pages:
        result = _detect_page_type(params['path'])
    else:
        result = exua.detect_page_type(params['path'])
    plugin.log_debug('Page type detection result: {0}'.format(result))
    content = None
    if result.type == 'media_page':
        listing = _media_info(result.content)
        content = 'movies'  # The best tried and tested variant
    elif result.type == 'media_list':
        listing = _media_list(params['path'], result.content)
    elif result.type == 'media_categories':
        listing = _media_categories(result.content, 'video')
    else:
        listing = []
    return plugin.create_listing(listing, content=content)


@plugin.action()
def search(params):
    """
    Search on Rover.Info

    params: original_id (optional)
    """
    listing = []
    keyboard = xbmc.Keyboard('', _('Search query'))
    keyboard.doModal()
    search_text = keyboard.getText()
    if keyboard.isConfirmed() and search_text:
        search_path = '/search?s={0}'.format(urllib.quote_plus(search_text))
        if params.get('original_id'):
            search_path += '&original_id={0}'.format(params['original_id'])
        if plugin.cache_pages:
            results = _get_media_list(search_path, 0, plugin.itemcount)
        else:
            results = exua.get_media_list(search_path, 0, plugin.itemcount)
        plugin.log_debug('Search results: {0}'.format(results))
        if results.media:
            listing = _media_list(search_path, results, is_search_result=True)
            if plugin.savesearch:
                with plugin.get_storage('__history__.pcl') as storage:
                    history = storage.get('history', [])
                    history.insert(0, SearchQuery(search_text, search_path))
                    if len(history) > plugin.historylength:
                        history.pop(-1)
                    storage['history'] = history
        else:
            dialog.ok(_('No results found'), _('Refine your search and try again'))
    return plugin.create_listing(listing, cache_to_disk=True)


@plugin.action()
def search_history(params):
    """
    Show search history
    """
    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])
        plugin.log_debug('Search history: {0}'.format(history))
        if len(history) > plugin.historylength:
            history[plugin.historylength - len(history):] = []
            storage['history'] = history
    for item in history:
        yield {
            'label': item.query,
            'url': plugin.get_url(action='media_list', path=item.path, page='0', is_search_result='true'),
            'thumb': os.path.join(icons, 'search_history.png')
        }


@plugin.action()
def play(params):
    """
    Play a media file

    params: path, mirrors, mp4
    """
    path = params['path']
    mirrors = params.get('mirrors', [])
    mp4 = params.get('mp4')
    if mirrors or mp4:
        if plugin.choose_mirrors == 1:
            menu_items = []
            paths = []
            for index, mirror in enumerate(mirrors):
                menu_items.append(_('Mirror {0}').format(index + 1))
                paths.append(mirror)
            menu_items.insert(0, _('Original media'))
            paths.insert(0, path)
            if mp4:
                menu_items.append(_('Lightweight version'))
                paths.append(mp4)
            selection = dialog.select(_('Select media to play'), menu_items)
            if selection >= 0:
                path = paths[selection]
            else:
                return plugin.resolve_url(succeeded=False)
        elif plugin.choose_mirrors == 2 and mp4:
            path = mp4
    if webclient.SITE not in path:
        path = webclient.SITE + path
    if plugin.authorization and webclient.is_logged_in():
        path += '|Cookie=' + urllib.quote(urllib.urlencode(webclient.get_cookies()).replace('&', '; '))
    plugin.log_debug('Playing path: {0}'.format(path))
    return path


@plugin.action()
def bookmarks(params):
    """
    Login to display Rover.Info bookmarks
    """
    if not webclient.is_logged_in():
        plugin.log_debug('Trying to login to Rover.Info')
        username = plugin.get_setting('username', False)
        password = webclient.decode(plugin.get_setting('password', False))
        captcha = webclient.check_captcha()
        login_dialog = login_window.LoginWindow(username, password, captcha.image)
        login_dialog.doModal()
        if not login_dialog.login_cancelled:
            try:
                webclient.login(login_dialog.username,
                                login_dialog.password,
                                captcha.captcha_id,
                                login_dialog.captcha_text)
            except webclient.LoginError:
                plugin.log_debug('Rover.Info login error')
                dialog.ok(_('Login error!'), _('Check your login and password, and try again.'))
            else:
                plugin.log_debug('Successful login to Rover.Info')
                plugin.set_setting('username', login_dialog.username)
                if plugin.save_pass:
                    plugin.set_setting('password', webclient.encode(login_dialog.password))
                else:
                    plugin.set_setting('password', '')
        del login_dialog
    if webclient.is_logged_in():
        plugin.log_debug('The user is logged in, getting bookmarks.')
        media = exua.get_media_list('/buffer')
        plugin.log_debug('My bookmarks: {0}'.format(media))
        listing = _media_list('/buffer', media, from_bookmarks=True)
    else:
        listing = []
    return listing
