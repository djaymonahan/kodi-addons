# -*- coding: utf-8 -*-
# Module: default
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.apivideoaz as apivideoaz
import xbmcgui
from simpleplugin import Plugin
from urllib import urlencode

# Create plugin instance
plugin = Plugin()
_ = plugin.initialize_gettext()

def init_api():
    settings_list = ['cfduid', 'video_stream', 'video_quality']

    settings = {}
    for id in settings_list:
        settings[id] = plugin.get_setting(id)

    settings['episode_title'] = _('Episode').decode('utf-8')
    settings['season_title']  = _('Season').decode('utf-8')

    return apivideoaz.videoaz(settings)

def get_categories():
    categories = [{'action': 'list_videos',    'label': _('Videos'),    'params': {'cat': 'videos'}},
                  {'action': 'list_videos',    'label': _('Movies'),    'params': {'cat': 'movies'}},
                  {'action': 'list_videos',    'label': _('TV Series'), 'params': {'cat': 'tvseries'}},
                  {'action': 'search_history', 'label': _('Search')}]

    return categories

def get_setting(id):
    value = plugin.get_setting(id)

    if id == 'movie_lang':
        if   value == 1: return 'az'
        elif value == 2: return 'ru'
        elif value == 3: return 'en'
        elif value == 4: return 'tr'
        else: return '0'
    else:
        return value

def check_cookies():
    cfduid = plugin.get_setting('cfduid')
    if len(cfduid) == 0:
        cfduid = _api.get_cfduid()
        plugin.set_setting('cfduid', cfduid)
        
def get_request_params( params ):
    result = {}
    for param in params:
        if param[0] == '_':
            result[param[1:]] = params[param]
    return result

def make_items(video_list):
    listing = []

    use_atl_names = get_setting('use_atl_names')
    
    for video in video_list:
        item_info = video['item_info']

        video_info = video['video_info']
        video_type = video_info['type']

        if video_type == 'movie':
            is_playable = True
            url = plugin.get_url(action='play', _type = 'movie', _id = video_info['id'])

            details = get_movie_details(video_info['id'])
            
            label_list = []
            if use_atl_names:
                label_list.append(item_info['info']['video']['originaltitle'])
            else:
                label_list.append(item_info['info']['video']['title'])

            if item_info['info']['video']['year'] > 0:
                label_list.append(' (%d)' % item_info['info']['video']['year'])

            if not use_atl_names and details['video_quality'] != '':
                label_list.append(' [%s]' % details['video_quality'])
            del details['video_quality']
            
            item_info['label'] = ''.join(label_list)

            del item_info['info']['video']['title']
            item_info['info']['video'].update(details)

        elif video_type == 'tvseries':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'seasons', _tvserie_id = video_info['id'], _season = video_info['season'])

        elif video_type == 'seasons':
            is_playable = False
            url = plugin.get_url(action='list_videos', cat = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'])

        elif video_type == 'episodes':
            is_playable = True
            url = plugin.get_url(action='play', _type = 'episodes', _tvserie_id = video_info['tvserie_id'], _season = video_info['season'], _id = video_info['id'])

            if use_atl_names:
                label_list = []
                label_list.append(item_info['info']['video']['tvshowtitle'])
                label_list.append('.s%02de%02d' % (item_info['info']['video']['season'], item_info['info']['video']['episode']))
                item_info['label'] = ''.join(label_list)

                del item_info['info']['video']['title']

        elif video_type == 'video':
            is_playable = True
            item_info['fanart'] = plugin.fanart
            url = plugin.get_url(action='play', _type = 'video', _id = video_info['id'])

        item_info['url'] = url
        item_info['is_playable'] = is_playable
            
        listing.append(item_info)

    return listing

@plugin.cached()
def get_movie_details( id ):
    return _api.get_movie_details(id)

    
@plugin.action()
def root( params ):

    listing = []

    categories = get_categories()
    for category in categories:
        url = plugin.get_url(action=category['action'])
 
        params = category.get('params')
        if params != None:
            url = url + '&' + urlencode(params)

        listing.append({
            'label': category['label'],
            'url': url,
            'icon': plugin.icon,
            'fanart': plugin.fanart
        })

    return plugin.create_listing(listing, content='files')

@plugin.action()
def list_videos( params ):
    content='files'

    check_cookies()
    
    u_params = get_request_params(params)

    use_pages = False
    
    if params['cat'] == 'movies':
        u_params['lang'] = get_setting('movie_lang')
        video_list = _api.browse_movie(u_params)
        use_pages = True
        content='movies'
    elif params['cat'] == 'tvseries':
        video_list = _api.browse_tvseries(u_params)
        use_pages = True
        content='tvshows'
    elif params['cat'] == 'seasons':
        video_list = _api.browse_seasons(u_params)
        content='tvshows'
    elif params['cat'] == 'episodes':
        video_list = _api.browse_episodes(u_params)
        content='episodes'
    elif params['cat'] == 'videos':
        video_list = _api.browse_video(u_params)
        use_pages = True
        content='episodes'

    listing = make_items(video_list)
    
    if use_pages and len(video_list) >= 20:
        params['_page'] = int(params.get('_page', 1)) + 1
        url = plugin.get_url(action='list_videos')
        del params['action']
        url = url + '&' + urlencode(params)
        listing.append({
            'label': _('Next page...'),
            'url': url})
         
    return plugin.create_listing(listing, content=content)

@plugin.action()
def search( params ):
    history_length = 10
    new_search = False
    
    check_cookies()

    category = params.get('cat', 'all')
    
    keyword = params.get('keyword','')
    succeeded = False
 
    if keyword == '':
        new_search = True
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(_('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()

    listing = []
    if keyword != '':
        succeeded = True
        
        u_params = {'keyword': keyword}
        if category in ['all', 'movie']: 
            movie_list = _api.browse_movie(u_params)
            listing.extend(make_items(movie_list))
        if category in ['all', 'tvseries']:
            tvseries_list = _api.browse_tvseries(u_params)
            listing.extend(make_items(tvseries_list))

        if new_search:
            with plugin.get_storage('__history__.pcl') as storage:
                history = storage.get('history', [])
                history.insert(0, {'cat': category, 'keyword': keyword})
                if len(history) > plugin.history_length:
                    history.pop(-1)
                storage['history'] = history
        
    return plugin.create_listing(listing, succeeded = succeeded, content='movies')

@plugin.action()
def search_history( params ):
    history_length = 10
    
    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])

        if len(history) > history_length:
            history[history_length - len(history):] = []
            storage['history'] = history

    listing = []
    listing.append({'label': _('New Search...'),
                    'url': plugin.get_url(action='search', cat='all')})

    for item in history:
        listing.append({'label': item['keyword'],
                        'url': plugin.get_url(action='search', cat=item['cat'], keyword=item['keyword'])})

    return plugin.create_listing(listing, content='movies')
    
@plugin.action()
def play( params ):

    check_cookies()

    u_params = get_request_params( params )
    item = _api.get_video_url( u_params )

    return plugin.resolve_url(play_item=item)
        
if __name__ == '__main__':
    debug = plugin.get_setting('debug')
    if debug: plugin.log_error('%s' % (sys.argv[2]))

    _api = init_api()
    plugin.run()