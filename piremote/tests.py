# piremote/tests.py -- Unit tests for all views.

from django.test import TestCase
from django.test import Client
from piremote.models import Rating, History

import time
import os.path

PLAYLIST_NAME = '__temp_unit_tests_playlist'
PLAYLIST_NAME2 = '__temp_unit_tests_playlist_2'


class IndexTests(TestCase):
    """Unit tests for main view"""

    def test_can_load_index(self):
        client = Client()
        response = client.get('/piremote/')
        self.assertIs(response.status_code, 200)

    def test_cmd_settime(self):
        client = Client()
        local = time.mktime(time.localtime()) * 1000
        response = client.post('/piremote/ajax/command/', dict(cmd='settime', payload=[local]))
        self.assertIs(response.json()['ok'], 1)

    def test_status(self):
        client = Client()
        response = client.get('/piremote/ajax/status/').json()
        self.assertTrue('state' in response)

    def test_mixer(self):
        client = Client()
        response = client.get('/piremote/ajax/mixer/', {'class': 'volume'}).json()
        self.assertIs(response['ok'], 1)

    def test_equalizer(self):
        client = Client()
        response = client.get('/piremote/ajax/mixer/', {'class': 'equalizer'}).json()
        self.assertIs(response['ok'], 1)


class PlaylistTests(TestCase):
    """Unit tests for playlist view"""

    def test_plinfo(self):
        client = Client()
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue('pl' in response)
        self.assertTrue('status' in response)

    def test_plactions(self):
        seed_n = 20
        client = Client()

        # get initial version
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue('status' in response and 'pl' in response)
        version = int(response['status']['playlist'])

        # clear
        response = client.post('/piremote/ajax/plaction/', dict(cmd='clear', plname='')).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # seed and test if result ok
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'seed', 'plname': '', 'list[]': [seed_n, '']}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        # result by plinfo
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue('pl' in response)
        self.assertTrue('status' in response)
        self.assertTrue('data' in response['pl'])
        self.assertTrue(response['pl']['length'] == seed_n)
        self.assertTrue(len(response['pl']['data']) == seed_n)
        self.assertTrue(len(response['pl']['data'][0]) == 8)
        # result by plchanges
        response = client.get('/piremote/ajax/plchanges/', dict(version=version)).json()
        self.assertTrue('pl' in response)
        self.assertTrue('status' in response)
        self.assertTrue('changes' in response['pl'])
        self.assertTrue(response['pl']['length'] == seed_n)
        self.assertTrue(len(response['pl']['changes']) == seed_n)
        self.assertTrue(len(response['pl']['changes'][0]) == 8)

        # randomize
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'randomize', 'plname': ''}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        response = client.post('/piremote/ajax/plaction/', {'cmd': 'randomize-rest', 'plname': ''}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # get current ids
        response = client.get('/piremote/ajax/plinfo/').json()
        ids = [int(x[5]) for x in response['pl']['data']]
        version = int(response['status']['playlist'])

        # start playing
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'playid', 'plname': '', 'list[]': [ids[0]]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # move last song to position 2
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'playidnext', 'plname': '', 'list[]': [ids[-1]]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # check that playlist has changed
        response = client.get('/piremote/ajax/plchanges/', dict(version=version)).json()
        self.assertTrue(response['pl']['length'] == 20)
        # this might fail if first song was not playable or is way too short
        self.assertTrue(len(response['pl']['changes']) == seed_n-1)
        self.assertTrue(len(response['pl']['changes'][0]) == 8)

        # move song again to end
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'moveidend', 'plname': '', 'list[]': [ids[-1]]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # get ids again
        response = client.get('/piremote/ajax/plinfo/').json()
        ids2 = [int(x[5]) for x in response['pl']['data']]
        # should match original ids
        self.assertTrue(ids == ids2)

        # remove last song
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'deleteid', 'plname': '', 'list[]': [ids[-1]]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue(len(response['pl']['data']) == seed_n - 1)

        # remove first 5 songs
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'deleteid', 'plname': '', 'list[]': ids[:5]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue(len(response['pl']['data']) == seed_n - 1 - 5)
        ids3 = [int(x[5]) for x in response['pl']['data']]

        # move songs 2..4 to end
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'moveidsend', 'plname': '', 'list[]': ids3[1:4]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # play first song
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'playid', 'plname': '', 'list[]': [ids3[0]]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # move last 3 songs after current
        response = client.get('/piremote/ajax/plinfo/').json()
        ids4 = [int(x[5]) for x in response['pl']['data']]
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'playidsnext', 'plname': '', 'list[]': list(reversed(ids4[-3:]))}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # should now match again ids3 -- might fail if first song already finished!
        response = client.get('/piremote/ajax/plinfo/').json()
        ids5 = [int(x[5]) for x in response['pl']['data']]
        self.assertTrue(ids3 == ids5)

        # download playlist
        response = client.get('/piremote/ajax/download/playlist/', dict(source='current', name='', filename='test.m3u')).json()
        self.assertTrue('data' in response)
        self.assertTrue('prefix' in response)
        self.assertTrue(len(response['data']) == len(ids5))
        # check that files are ok
        self.assertTrue(os.path.isfile(response['data'][0]))


class PlaylistsTests(TestCase):
    """Tests on other playlists"""

    def test_playlists_actions(self):
        seed_n = 20
        client = Client()
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='list', plname='')).json()
        self.assertTrue('pls' in response)
        pls = response['pls'][:]

        if PLAYLIST_NAME in pls:
            response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME)).json()
            self.assertTrue('status_str' in response and 'error_str' not in response)

        if PLAYLIST_NAME2 in pls:
            response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME2)).json()
            self.assertTrue('status_str' in response and 'error_str' not in response)

        # new
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='new', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='new', plname=PLAYLIST_NAME2)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # check existence
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='list', plname='')).json()
        self.assertTrue(PLAYLIST_NAME in response['pls'])

        # seed
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'seed', 'plname': PLAYLIST_NAME, 'list[]': [seed_n, '']}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # list
        response = client.get('/piremote/ajax/plshortinfo/', {'plname': PLAYLIST_NAME}).json()
        self.assertTrue(len(response['pl']) == 20)
        self.assertTrue(len(response['pl'][0]) == 3)
        ids = [int(x[2]) for x in response['pl']]

        # delete first 2 entries
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'delete', 'plname': PLAYLIST_NAME, 'payload[]': ids[:2]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # move next 2 items to end
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'moveend', 'plname': PLAYLIST_NAME, 'payload[]': ids[3:4]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # insert first 3 songs into current playlist
        response = client.get('/piremote/ajax/plshortinfo/', {'plname': PLAYLIST_NAME}).json()
        files = [x[0] for x in response['pl']]
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'insert', 'plname': '', 'payload[]': files[:3]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # append last 3 songs to current playlist
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'payload[]': files[-3:]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # append last 3 songs to  playlist2
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': PLAYLIST_NAME2, 'list[]': files[-3:]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plshortinfo/', {'plname': PLAYLIST_NAME2}).json()
        files2 = [x[0] for x in response['pl']]
        self.assertTrue(files[-3:] == files2)

        # clear
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'clear', 'plname': PLAYLIST_NAME}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plshortinfo/', {'plname': PLAYLIST_NAME}).json()
        self.assertTrue(len(response['pl']) == 0)

        # append current playlist
        response = client.get('/piremote/ajax/plinfo/').json()
        files = [x[6] for x in response['pl']['data']]
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': PLAYLIST_NAME, 'list[]': files}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # rename to playlist2
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME2)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'rename', 'plname': PLAYLIST_NAME2, 'payload[]': PLAYLIST_NAME}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # download playlist2
        response = client.get('/piremote/ajax/download/playlist/', dict(source='saved', name=PLAYLIST_NAME2, filename='test.m3u')).json()
        self.assertTrue('data' in response)
        self.assertTrue('prefix' in response)
        self.assertTrue(len(response['data']) == len(files))
        # check that files are ok
        self.assertTrue(os.path.isfile(response['data'][0]))

        # append to current
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'load', 'plname': PLAYLIST_NAME2}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # save current
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'saveas', 'plname': PLAYLIST_NAME}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # save again --> should fail
        response = client.post('/piremote/ajax/plsaction/', {'cmd': 'saveas', 'plname': PLAYLIST_NAME}).json()
        self.assertFalse('status_str' in response and 'error_str' not in response)

        # remove both
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME2)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)


class FilesTests(TestCase):
    """tests for browse by files view"""

    def test_browse(self):
        client = Client()
        response = client.post('/piremote/ajax/browse/', dict(dirname='')).json()
        self.assertTrue('browse' in response)
        self.assertTrue(len(response['browse'][0]) == 6)

        # dive into directories
        while response['browse'][0][0] == "1":
            response = client.post('/piremote/ajax/browse/', dict(dirname=response['browse'][0][5])).json()

        # latest response now should list only file items
        dirname = response['dirname']
        self.assertTrue(len(response['browse'][0]) == 9)
        file = response['browse'][0][5]

        # create temp playlist
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='new', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response or 'error_str' in response)

        # file: insert/append/append to other
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'insert', 'plname': '', 'list[]': [file]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'list[]': [file]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': PLAYLIST_NAME, 'list[]': [file]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # dir: append/append to other
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'list[]': [dirname]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': PLAYLIST_NAME, 'list[]': [dirname]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # dir: seed
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'seed', 'plname': '', 'list[]': [20, dirname]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'seed', 'plname': PLAYLIST_NAME, 'list[]': [20, dirname]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # remove temp playlist
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)


class BrowseTagsTests(TestCase):
    """tests for browse by tags view"""

    def test_browse_tags(self):
        client = Client()

        # create temp playlist
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='new', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response or 'error_str' in response)

        # Seed some stuff into playlist to fill ratings db from it
        response = client.post('/piremote/ajax/plaction/',
                               {'cmd': 'seed', 'plname': '', 'list[]': [100, '']}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plinfo/').json()
        files = [x[6] for x in response['pl']['data']]
        for file in files:
            response = client.get('/piremote/ajax/fileinfo/', {'file': file}).json()
            info = response['info'][0]
            path = info['file']
            title = info['title']
            artist = info['artist'] if 'artist' in info else ''
            album = info['album'] if 'artist' in info else ''
            genre = info['genre'] if 'genre' in info else ''
            date = info['date'] if 'date' in info else ''
            rating = info['rating'] if 'rating' in info else 0
            try:
                r = Rating(path=path, title=title, artist=artist, album=album, genre=genre, date=date, rating=rating)
                r.save()
            except TypeError:
                print('TYPE ERROR: {}'.format(info[0]))

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'rating',
                               'ratings[]': ['All'],
                               'dates[]': ['All'],
                               'genres[]': ['All'],
                               'artists[]': ['All'],
                               'albums[]': ['All']}).json()
        self.assertTrue(response['what'] == 'rating')
        self.assertTrue(len(response['browse']) == 11)

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'date',
                               'ratings[]': ['at least 1', 'unrated'],
                               'dates[]': 'All',
                               'genres[]': 'All',
                               'artists[]': 'All',
                               'albums[]': 'All'}).json()
        self.assertTrue(response['what'] == 'date')
        self.assertTrue(len(response['browse']) > 0)
        dates = response['browse'][:10][:]

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'genre',
                               'ratings[]': ['at least 1', 'unrated'],
                               'dates[]': dates,
                               'genres[]': 'All',
                               'artists[]': 'All',
                               'albums[]': 'All'}).json()
        self.assertTrue(response['what'] == 'genre')
        self.assertTrue(len(response['browse']) > 0)
        genres = response['browse'][:2][:]

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'artist',
                               'ratings[]': ['at least 1', 'unrated'],
                               'dates[]': dates,
                               'genres[]': genres,
                               'artists[]': 'All',
                               'albums[]': 'All'}).json()
        self.assertTrue(response['what'] == 'artist')
        self.assertTrue(len(response['browse']) > 0)
        artists = response['browse'][:2][:]

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'album',
                               'ratings[]': ['at least 1', 'unrated'],
                               'dates[]': dates,
                               'genres[]': genres,
                               'artists[]': artists,
                               'albums[]': 'All'}).json()
        self.assertTrue(response['what'] == 'album')
        self.assertTrue(len(response['browse']) > 0)
        albums = response['browse'][:]

        response = client.get('/piremote/ajax/listby/',
                              {'what': 'song',
                               'ratings[]': ['at least 1', 'unrated'],
                               'dates[]': dates,
                               'genres[]': genres,
                               'artists[]': artists,
                               'albums[]': albums}).json()
        self.assertTrue(response['what'] == 'song')
        self.assertTrue(len(response['browse']) > 0)
        files = [x[0] for x in response['browse']]

        # append/insert/...
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'list[]': files[:10]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'insert', 'plname': '', 'list[]': files[:10]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': PLAYLIST_NAME, 'list[]': files[:10]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # seed
        response = client.post('/piremote/ajax/seedbrowse/',
                               {'what': 'song',
                                'count': 20,
                                'plnane': PLAYLIST_NAME,
                                'ratings[]': ['at least 1', 'unrated'],
                                'dates[]': dates,
                                'genres[]': genres,
                                'artists[]': artists,
                                'albums[]': albums}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # remove temp playlist
        response = client.post('/piremote/ajax/plsaction/', dict(cmd='rm', plname=PLAYLIST_NAME)).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)


class SearchTests(TestCase):
    """tests for browse by tags view"""

    def test_search(self):
        client = Client()

        # try search
        response = client.post('/piremote/ajax/search/', dict(pattern='.mp3')).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        self.assertTrue(len(response['search']) > 0)
        self.assertTrue(len(response['search'][0]) == 7)
        files = [x[5] for x in response['search']]

        # append
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'list[]': files[:10]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # all other append actions tested enough


class HistoryTests(TestCase):
    """tests for browse by tags view"""

    def test_historty(self):
        client = Client()

        # Seed some stuff into playlist to fill history db from it
        response = client.post('/piremote/ajax/plaction/',
                               {'cmd': 'seed', 'plname': '', 'list[]': [100, '']}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)
        response = client.get('/piremote/ajax/plinfo/').json()
        files = [x[6] for x in response['pl']['data']]
        for file in files:
            response = client.get('/piremote/ajax/fileinfo/', {'file': file}).json()
            info = response['info'][0]
            path = info['file']
            title = info['title']
            h = History(path=path, title=title)
            h.save()

        # full hist
        response = client.get('/piremote/ajax/history/', dict(mode='dates')).json()
        self.assertTrue(response['mode'] == 'dates')
        self.assertTrue(len(response['history']) > 0)
        self.assertTrue(len(response['history'][0]) == 2)
        dates = [x[0] for x in response['history']]

        # last date
        response = client.get('/piremote/ajax/history/', dict(mode=dates[0])).json()
        self.assertTrue(response['mode'] == dates[0])
        self.assertTrue(len(response['history']) > 0)
        self.assertTrue(len(response['history'][0]) == 6)
        files = [x[5] for x in response['history']]

        # append
        response = client.post('/piremote/ajax/plaction/', {'cmd': 'append', 'plname': '', 'list[]': files[:10]}).json()
        self.assertTrue('status_str' in response and 'error_str' not in response)

        # get playlist from history
        response = client.get('/piremote/ajax/download/playlist/', dict(source='history', name=dates[0], filename='test.m3u')).json()
        self.assertTrue('data' in response)
        self.assertTrue('prefix' in response)
        # check that files are ok
        self.assertTrue(os.path.isfile(response['data'][0]))

        # try search
        title = History.objects.all()[0].title
        response = client.get('/piremote/ajax/history/', dict(mode='search', pattern=title)).json()
        self.assertTrue(len(response['history']) > 0)
        self.assertTrue(len(response['history'][0]) == 6)
        self.assertTrue(response['history'][0][1] == title)




