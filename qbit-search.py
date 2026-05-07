# VERSION: 1.1
# AUTHORS: LightDestory (https://github.com/LightDestory)
"""
This script is a qBittorrent search engine plugin that queries the API and
returns torrent results formatted for qBittorrent's search interface. Place
this file in qBittorrent's search engine plugin directory.

Usage:
  Installed automatically by qBittorrent when placed in the search engines folder.
  Typically: ~/.local/share/qBittorrent/nova3/engines/

Requirements:
  Requires qBittorrent's bundled nova3 search framework (helpers, novaprinter).
"""
import json, urllib.parse
from base64 import b64decode
from helpers import retrieve_url  # type: ignore
from novaprinter import prettyPrinter  # type: ignore


class searchplugin(object):
    url = b64decode('aHR0cHM6Ly90aGVwaXJhdGViYXkub3JnLw==')
    api_url = b64decode('aHR0cHM6Ly9hcGliYXkub3JnLw==')
    name = b64decode('VGhlIFBpcmF0ZSBCYXk=')
    supported_categories = {'all': '0'}

    def parseJSON(self, collection):
        if collection[0]['name'] == "No results returned":
            return
        for torrent in collection:
            data = {
                'link': 'magnet:?xt=urn:btih:{0}&dn={1}&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A6969%2Fannounce&tr=udp%3A%2F%2F9.rarbg.to%3A2710%2Fannounce&tr=udp%3A%2F%2F9.rarbg.me%3A2780%2Fannounce&tr=udp%3A%2F%2F9.rarbg.to%3A2730%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=http%3A%2F%2Fp4p.arenabg.com%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce'
                .format(torrent['info_hash'], urllib.parse.quote(torrent['name'])),
                'name': torrent['name'],
                'size': torrent['size'],
                'seeds': torrent['seeders'],
                'leech': torrent['leechers'],
                'engine_url': self.url,
                'desc_link': f'{self.url}description.php?id={format(torrent["id"])}'
            }
            prettyPrinter(data)

    def search(self, what, cat='all'):
        url = f'{self.api_url}q.php?q={what}&cat=0'
        collection = json.loads(retrieve_url(url))
        self.parseJSON(collection)
