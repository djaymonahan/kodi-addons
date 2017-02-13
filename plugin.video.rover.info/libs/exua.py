# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import ast
import re
import xml.etree.ElementTree as et
from collections import namedtuple
from bs4 import BeautifulSoup
from simpleplugin import Plugin
import webclient

# Extensions for supported media files
MEDIA_EXTENSIONS = 'avi|mkv|ts|m2ts|mp4|m4v|flv|vob|mpg|mpeg|mov|wmv|mp3|aac|ogg|wav|dts|ac3|flac|m4a|wma'
VIDEO_DETAILS = {
    'year': ur'(?:[Гг]од|[Рр]ік).*?: *?(\d{4})',
    'genre': ur'[Жж]анр.*?:(.*)',
    'director': ur'[Рр]ежисс?[её]р.*?:(.*)',
    'plot': ur'(?:Описание|О фильме|Сюжет|О чем|О сериале).*?:\n?(.*)',
    'cast': ur'(?:[ВвУу] ролях|[Аа]кт[ео]р[ыи]).*?:(.*)',
    'rating': ur'IMD[Bb].*?: *?(\d\.\d)',
    }

MediaCategory = namedtuple('MediaCategory', ['name', 'path', 'items'])
MediaList = namedtuple('MediaList', ['media', 'prev_page', 'next_page', 'original_id'])
MediaItem = namedtuple('MediaItem', ['title', 'thumb', 'path'])
MediaDetails = namedtuple('MediaDetails', ['title', 'thumb', 'files', 'mp4', 'info'])
MediaFile = namedtuple('MediaFile', ['filename', 'path', 'mirrors'])
ExUaPage = namedtuple('ExUaPage', ['type', 'content'])

plugin = Plugin()
poster_quality = '400' if plugin.hq_posters else '200'


def get_categories(path):
    """
    Get video categories
    """
    return parse_categories(webclient.load_page(webclient.SITE + path))


def parse_categories(web_page):
    """
    Parse media categories list
    """
    parse = re.findall('<b>(.*?)</b></a><p><a href=\'(.*?)\' class=info>(.*?)</a>', web_page)
    listing = []
    for item in parse:
        listing.append(MediaCategory(item[0], item[1], item[2]))
    return listing


def get_media_list(path, page=0, items=25):
    """
    Get the list of media articles
    """
    if page:
        if '?r=' in path or '?s=' in path:
            p = '&p={0}'.format(page)
        else:
            p = '?p={0}'.format(page)
    else:
        p = ''
    if path != '/buffer':
        per = '&per={0}'.format(items)
    else:
        per = ''
    url = webclient.SITE + path + p + per
    web_page = webclient.load_page(url)
    return parse_media_list(web_page)


def parse_media_list(web_page):
    """
    Parse a media list page to get the list of videos and navigation links
    """
    soup = BeautifulSoup(web_page, 'html5lib')
    nav_table = soup.find('table', border='0', cellpadding='5', cellspacing='0')
    if nav_table is not None:
        prev_tag = nav_table.find('img', src='/t3/arr_l.gif')
        if prev_tag is not None:
            prev_page = prev_tag.find_previous('a', text=re.compile('\.\.')).text
        else:
            prev_page = None
        next_tag = nav_table.find('img', src='/t3/arr_r.gif')
        if next_tag is not None:
            next_page = next_tag.find_next('a', text=re.compile('\.\.')).text
        else:
            next_page = None
    else:
        prev_page = next_page = None
    content_table = soup.find('table', width='100%', border='0', cellpadding='0', cellspacing='8')
    if content_table is not None:
        media = _parse_media_items(content_table)
    else:
        media = []
    original_id_tag = soup.find('input', {'type': 'hidden', 'name': 'original_id'})
    if original_id_tag is not None:
        original_id = original_id_tag['value']
    else:
        original_id = None
    return MediaList(media, prev_page, next_page, original_id)


def _parse_media_items(content_table):
    """
    Parse the list of media
    """
    content_cells = content_table.find_all('td')
    listing = []
    for content_cell in content_cells:
        try:
            link_tag = content_cell.find('a')
            if link_tag is not None:
                image_tag = content_cell.find('img')
                if image_tag is not None:
                    thumb = image_tag['src'][:-3] + poster_quality
                    title = image_tag['alt']
                else:
                    thumb = ''
                    title = link_tag.text
                listing.append(MediaItem(title, thumb, link_tag['href']))
        except TypeError:
            pass
    return listing


def get_media_details(path):
    """
    Get video details.
    """
    web_page = webclient.load_page(webclient.SITE + path)
    return parse_media_details(web_page)


def _parse_xspf(xspf):
    """
    Load the list of media files from a .xspf file
    """
    root = et.fromstring(xspf.encode('utf-8'))
    title = root.find('{http://xspf.org/ns/0/}title').text
    files = []
    for track in root.find('{http://xspf.org/ns/0/}trackList').findall('{http://xspf.org/ns/0/}track'):
        files.append(MediaFile(
            track.find('{http://xspf.org/ns/0/}title').text,
            track.find('{http://xspf.org/ns/0/}location').text,
            []
            ))
    return title, files


def _parse_media_details_simplified(web_page):
    """
    Simplified media details parsing if BeautifulSoup does not work

    This method is slower and does not parse information about the media but it is more reliable.
    """
    xspf_tag = re.search(r'<a href=\'(/playlist/\d+?\.xspf)\' rel=\'nofollow\'>\.xspf</a>', web_page)
    if xspf_tag is not None:
        xspf_path = xspf_tag.group(1)
        title, files = _parse_xspf(webclient.load_page(webclient.SITE + xspf_path))
    else:
        title = ''
        files = []
    image_tag = re.search(r'<link rel="image_src" href="(.+?)">', web_page)
    if image_tag is not None:
        thumb = image_tag.group(1)[:-3] + poster_quality
    else:
        thumb = ''
    return MediaDetails(title, thumb, files, None, {})


def _parse_media_info(soup):
    """
    Extract media description if possible
    """
    info = {}
    descr_table_tag = soup.find('table', width=True, cellpadding=True, cellspacing=True, border=True, height=False)
    if descr_table_tag is not None:
        try:
            # Clean the media item description
            br_tags = descr_table_tag.find_all('br')
            for br in br_tags:
                br.replace_with('\n')
            p_tags = descr_table_tag.find_all('p')
            text = u''
            for p in p_tags:
                text += p.text + '\n'
            # Extract info
            for detail, regex in VIDEO_DETAILS.iteritems():
                match = re.search(regex, text)
                if match is not None:
                    info[detail] = match.group(1).lstrip()
            if not info.get('plot'):
                info['plot'] = text
        except AttributeError:  # May throw on malformed html
            pass
    return info


def parse_media_details(web_page):
    """
    Parse a video item page to extract as much details as possible
    """
    soup = BeautifulSoup(web_page, 'html5lib')
    # Try to extract tags with links to media files
    media_tags = soup.find_all('a',
                               title=re.compile('^(.+\.(?:{0}))$'.format(MEDIA_EXTENSIONS), re.IGNORECASE),
                               rel='nofollow')
    # If BeautifulSoup parsing fails then fall bask to the simplified parsing method.
    if not media_tags:
        return _parse_media_details_simplified(web_page)
    # Extract mediafiles
    files = []
    for media_tag in media_tags:
        mirror_tags = media_tag.find_next('td', class_='small').find_all('a', rel='nofollow', title=True)
        mirrors = []
        if mirror_tags:
            for mirror_tag in mirror_tags:
                mirrors.append(mirror_tag['href'])
        files.append(MediaFile(media_tag.text, media_tag['href'], mirrors))
    # Extract lightweight mp4 videos
    mp4_regex = re.compile('player_list = \'(.*)\';')
    var_player_list = soup.find('script', text=mp4_regex)
    if var_player_list is not None:
        mp4 = []
        for mp4_item in ast.literal_eval('[' + re.search(mp4_regex, var_player_list.text).group(1) + ']'):
            mp4.append(mp4_item['url'])
    else:
        mp4 = None
    # Extract title and poster
    title = soup.find('h1').text
    thumb_tag = soup.find('link', rel='image_src')
    if thumb_tag is not None:
        thumb = thumb_tag['href'][:-3] + poster_quality
    else:
        thumb = ''
    return MediaDetails(title, thumb, files, mp4, _parse_media_info(soup))


def detect_page_type(path):
    """
    Detect the type of an Rover.Info page
    """
    page_type = None
    content = None
    web_page = webclient.load_page(webclient.SITE + path)
    if '<table width=100% class=list border=0 cellpadding=0 cellspacing=0 style=\'padding-top: 8px\'>' in web_page:
        page_type = 'media_page'
        content = parse_media_details(web_page)
    elif ('<table width=100% border=0 cellpadding=0 cellspacing=8' in web_page and
              ('<form name=search action=\'/search\'>' in web_page or '<span class=modify_time>' in web_page)):
        page_type = 'media_list'
        content = parse_media_list(web_page)
    elif '<table width=100% border=0 cellpadding=0 cellspacing=8 class=include_0>' in web_page:
        page_type = 'media_categories'
        content = parse_categories(web_page)
    return ExUaPage(page_type, content)
