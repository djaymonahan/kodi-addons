# -*- coding: utf-8 -*-
# Module: apivideoaz
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import requests
import re
import xml.etree.ElementTree as ET

class videoaz:
 
    def __init__( self, params = {}, debug = False ):

        self.__debug = debug

        self.__movie = []
        self.__video = []
        self.__tvseries = []
        self.__episodes = []
        
        #Settings
        self.__settings = {'cfduid':        params.get('cfduid'),
                           'episode_title': params.get('episode_title', 'Episode'),
                           'season_title':  params.get('season_title','Season'),
                           'video_stream':  params.get('video_stream', 'mp4'),
                           'video_quality': params.get('video_quality', 'HD'),
                           'rating_source': params.get('rating_source', 'imdb')}
    
        #Инициализация 
        base_url = 'http://api.baku.video'

        #Links example 
        #http://api.baku.video:80/movie/browse?page=1&category=0&lang=0&genre=0&keyword=
        #http://api.baku.video:80/movie/by_id?id=12077
        #http://api.baku.video:80/tvseries/browse?page=1&keyword=
        #http://api.baku.video:80/tvseries/browse_episodes?tvserie_id=344&season=2
        #http://api.baku.video:80/category/movie
        #http://api.baku.video:80/category/genre
        #http://api.baku.video:80/main
        #http://api.baku.video:80/video/browse?page=1&category=0&keyword=
        #http://api.baku.video:80/category/video
        #http://api.baku.video:80/video/by_id?id=159153
        
        self.__actions = {'main':            {'type': 'get', 'url': base_url + '/main'},
                          #movie
                          'category_movie':  {'type': 'get', 'url': base_url + '/category/movie'},
                          'category_genre':  {'type': 'get', 'url': base_url + '/category/genre'},
                          'browse_movie':    {'type': 'get', 'url': base_url + '/movie/browse'},
                          'get_info_movie':  {'type': 'get', 'url': base_url + '/movie/by_id'},
                          #tvseries
                          'browse_tvseries': {'type': 'get', 'url': base_url + '/tvseries/browse'},
                          'browse_episodes': {'type': 'get', 'url': base_url + '/tvseries/browse_episodes'},
                          #video
                          'category_video':  {'type': 'get', 'url': base_url + '/category/video'},
                          'browse_video':    {'type': 'get', 'url': base_url + '/video/browse'},
                          'get_info_video':  {'type': 'get', 'url': base_url + '/video/by_id'}}

    def __debuglog( self, string ):
        if self.__debug: print(string)
        
    def __get_setting( self, id, default='' ):
        return self.__settings.get(id, default)

    def __set_setting( self, id, value ):
        self.__settings[id] = value

    def __http_request( self, action, params = {}, data={} ):
        action_settings = self.__actions.get(action)

        user_agent = 'Mozilla/5.0 (Linux; Android 5.1; KODI) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/40.0.2214.124 Mobile Safari/537.36'

        url = action_settings['url']
        cookies = {}
        cfduid = self.__get_setting('cfduid')
        if cfduid:
            cookies['__cfduid'] = cfduid

        headers = {'User-Agent': user_agent}

        request_type = action_settings.get('type', 'post')
        if request_type == 'post':
            return requests.post(url, data=data, params=params, headers=headers, cookies=cookies)
        elif request_type == 'get':
            return requests.get(url, data=data, params=params, headers=headers, cookies=cookies)
        else:
            return None

        r.raise_for_status()

        return r

    def __make_list( self, source, params = {} ):
        video_list = []
        
        if source == 'movie':
            for movie in self.__movie:
                video_info = {'type': source,
                              'id':   movie['id']}

                title = movie['title']
                title_orig = movie['title_original'] if movie['title_original'] != '' else movie['title']
                item_info = {'label':  title,
                             'info': { 'video': {'year':          int(movie['year']),
                                                 'title':         title,
                                                 'originaltitle': title_orig,
                                                 'genre':         movie['genres'],
                                                 'mediatype ':    'movie'} },
                             'art': { 'poster': movie['cover'] },
                             'fanart': movie['cover'].replace('cover','thumb'),
                             'thumb':  movie['cover'].replace('cover','thumb')}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'tvseries':
            for tvseries in self.__tvseries:
                
                video_info = {'type':   source,
                              'id':     tvseries['id'],
                              'season': tvseries['season']}

                title = tvseries['title']
                title_orig = tvseries['title_original'] if tvseries['title_original'] != '' else tvseries['title']
                item_info = {'label':  title,
                             'info': { 'video': {'title':         title,
                                                 'originaltitle': title_orig,
                                                 'tvshowtitle':   title_orig,
                                                 'mediatype ':    'tvshow'} },
                             'art': { 'poster': tvseries['cover'] },
                             'fanart': tvseries['cover'].replace('cover','thumb'),
                             'thumb':  tvseries['cover'].replace('cover','thumb')}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'episodes':
            season_title = self.__get_setting('season_title')
            episode_title = self.__get_setting('episode_title')
                          
            title = self.__tvseries['title']
            title_orig = self.__tvseries['title_original'] if self.__tvseries['title_original'] != '' else self.__tvseries['title']
            
            for episode in self.__episodes:
                video_info = {'type':       source,
                              'id':         episode['id'],
                              'tvserie_id': self.__tvseries['id'],
                              'season':     params['season']}

                title_part = '%s %s %s %s' % (season_title, params['season'], episode_title, episode['episode'])
                title_full = '%s. %s' % (title, title_part)
                title_orig_full = '%s. %s' % (title_orig, title_part)

                item_info = {'label': title_full,
                             'info':  { 'video': {'title':         title_full,
                                                  'originaltitle': title_orig_full,
                                                  'tvshowtitle':   title_orig,
                                                  'season':        int(params['season']),
                                                  'episode':       int(episode['episode']),
                                                  'mediatype ':    'episode'} },
                             'art': { 'poster': self.__tvseries['thumb'].replace('thumb','cover') }, 
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'seasons':
            season_title = self.__get_setting('season_title')
                          
            title = self.__tvseries['title']
            title_orig = self.__tvseries['title_original'] if self.__tvseries['title_original'] != '' else self.__tvseries['title']

            for season in self.__tvseries['season_list']:
                video_info = {'type':       source,
                              'tvserie_id': self.__tvseries['id'],
                              'season':     season}
                              
                title_part = '%s %s' % (season_title, season)              
                title_full = '%s. %s' % (title_part, title)              
                title_orig_full = '%s. %s' % (title_part, title_orig)              
                item_info = {'label':  title_full,
                             'info':  { 'video': {'title':         title_full,
                                                  'originaltitle': title_orig_full,
                                                  'tvshowtitle':   title_orig,
                                                  'season':        int(season),
                                                  'mediatype ':    'season'} },
                             'art': { 'poster': self.__tvseries['thumb'].replace('thumb','cover') }, 
                             'fanart': self.__tvseries['thumb'],
                             'thumb':  self.__tvseries['thumb']}
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})
        elif source == 'video':
            for video in self.__video:
                video_info = {'type': source,
                              'id':   video['id']}

                item_info = {'label':  video['title'],
                             'fanart': video['large'],
                             'thumb':  video['medium'],
                             'info':   { 'video': {'genre':      video['categories'],
                                                   'mediatype ': 'video'} },
                             'art':    { 'poster': video['medium'] } }
                
                video_list.append({'item_info':  item_info,
                                   'video_info': video_info})

        return video_list

    def get_cfduid( self ):

        r = self.__http_request('main')
        cfduid = r.cookies.get('__cfduid', '')
        self.__set_setting('cfduid', cfduid)
        return cfduid
        
    def browse_video( self, params ):

        u_params = {'page':     params.get('page', 1),
                    'category': params.get('category', 0),
                    'keyword':  params.get('keyword', '')}

        r = self.__http_request('browse_video', u_params)
        j = r.json()
        
        if type(j) == list:
            return []
        
        self.__video = j.get('video', [])
        return self.__make_list('video')

    def browse_movie( self, params ):

        u_params = {'page':     params.get('page', 1),
                    'category': params.get('category', 0),
                    'lang':     params.get('lang', 0),
                    'genre':    params.get('genre', 0),
                    'keyword':  params.get('keyword', '')}

        r = self.__http_request('browse_movie', u_params)
        j = r.json()
        
        if type(j) == list:
            return []
        
        self.__movie = j.get('movie', [])
        return self.__make_list('movie')

    def browse_tvseries( self, params ):

        u_params = {'page':    params.get('page', 1),
                    'keyword': params.get('keyword', '')}

        r = self.__http_request('browse_tvseries', u_params)
        j = r.json()
        
        if type(j) == list:
            return []
        
        self.__tvseries = j.get('tvseries', [])
        return self.__make_list('tvseries')

    def browse_episodes( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()
        
        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')
        return self.__make_list('episodes', params )

    def browse_seasons( self, params ):

        u_params = {'tvserie_id': params.get('tvserie_id', 0),
                    'season':     params.get('season', 0)}

        r = self.__http_request('browse_episodes', u_params)
        j = r.json()
        
        self.__episodes = j.get('episodes', [])
        self.__tvseries = j.get('tvseries')
        if len(self.__tvseries['season_list']) > 1:
            return self.__make_list('seasons')
        else:
            return self.__make_list('episodes', params )

    def get_movie_details( self, id):
        u_params = {'id': id}
        
        r = self.__http_request('get_info_movie', u_params)
        j = r.json()
        movie = j['player']

        rating_field = self.__get_setting('rating_source') + '_rating'
        
        duration_str = movie['duration']
        duration_sec = 0
        for part in duration_str.split(':'):
            duration_sec = duration_sec * 60 + int(part)

        details = {'rating': float(movie[rating_field]),
                   'cast': movie['actors'].split(','),
                   'director': movie['director'],
                   'video_quality': movie['video_quality'],
                   'duration': duration_sec,
                   'plot': re.sub(r'\<[^>]*\>', '', movie['description'])}
                   
        return details

    def get_video_url( self, params ):
        video_stream  = self.__get_setting('video_stream')
        video_quality = self.__get_setting('video_quality')
        
        type = params['type']
        if type == 'movie':
            u_params = {'id': params['id']}
            
            r = self.__http_request('get_info_movie', u_params)
            j = r.json()
            self.__movie = j['player']

            mp4_path = self.__movie['video']
            
            item_info = {'label':  self.__movie['title'],
                         'art':    { 'poster': self.__movie['thumb'].replace('thumb','cover') },
                         'info':   { 'video': {'mediatype ': 'movie'} },
                         'fanart': self.__movie['thumb'],
                         'thumb':  self.__movie['thumb']}

        elif type == 'episodes':
            u_params = {'tvserie_id': params['tvserie_id'],
                        'season':     params['season']}
                        
            r = self.__http_request('browse_episodes', u_params)
            j = r.json()
            self.__episodes = j.get('episodes', [])
            self.__tvseries = j.get('tvseries')
            for episode in self.__episodes:
                if episode['id'] == params['id']:
                    u_params['episode'] = episode['episode']
                    mp4_path = episode['video']

                    label = '%s. %s %s %s %s' % (self.__tvseries['title'], self.__get_setting('season_title'), params['season'], self.__get_setting('episode_title'), episode['episode'])              
                    item_info = {'label':  label,
                                 'art':    { 'poster': self.__tvseries['thumb'].replace('thumb','cover') },
                                 'info':   { 'video': {'mediatype ': 'movie'} },
                                 'fanart': self.__tvseries['thumb'],
                                 'thumb':  self.__tvseries['thumb']}
        elif type == 'video':
            u_params = {'id': params['id']}
            
            r = self.__http_request('get_info_video', u_params)
            j = r.json()
            self.__video = j['player']

            mp4_path = self.__video['video_sd']
            
            item_info = {'label':  self.__video['title'],
                         'info': { 'video': {'genre': self.__video['categories'],
                                                   'mediatype ': 'video'} },
                         'fanart': self.__video['large'],
                         'thumb':  self.__video['medium']}

        if video_stream == 'm3u8':
            m3u8_path = self.__get_playlist_url(type, u_params)
            path = m3u8_path if m3u8_path != '' else mp4_path
        else:
            path = mp4_path
        
        if type == 'video' and video_quality == 'HD' and self.__video['is_hd'] == '1':
            path = path.replace('sd.mp4', 'hd.mp4')

        item_info['path'] = path
        return item_info
        
    def __get_playlist_url( self, type, params ):
        
        if type == 'movie':
            xml_url = 'http://video.az/jw/movie/xml/%s' % (params['id'])
        elif type == 'episodes':
            xml_url = 'http://video.az/jw/tvseries/xml/%s/%s/%s' % (params['tvserie_id'], params['season'], params['episode'])
        elif type == 'video':
            xml_url = 'http://video.az/jw/video/xml/%s' % (params['id'])
        else: 
            xml_url = ''

        file = ''

        if xml_url != '':
            r = requests.get(xml_url)
            r.raise_for_status()

            root = ET.fromstring(r.text.encode('utf-8'))
            for sources in root.iter('{http://rss.jwpcdn.com/}source'):
                file = sources.attrib.get('file')
                if file[-4:] == 'm3u8': break

        return file