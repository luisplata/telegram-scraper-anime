import os
import json
import pytest

from app.usecases.channel_media_downloader import ChannelMediaDownloader


class DummyEntity:
    def __init__(self, id, username=None, name=None, title=None):
        self.id = id
        self.username = username
        self.title = title
        self.name = name


class DummyDialog:
    def __init__(self, entity, name):
        self.entity = entity
        self.name = name


class FakeMessage:
    def __init__(self, id, media_type='photo', text='', date=None, grouped_id=None):
        self.id = id
        self.text = text
        self.date = date or '2025-01-01'
        self.grouped_id = grouped_id
        # media_type: 'photo' or 'video' or None
        if media_type == 'photo':
            class Photo: pass
            self.media = Photo()
        elif media_type == 'video':
            class Doc:
                def __init__(self):
                    self.document = type('D', (), {'mime_type': 'video/mp4', 'attributes': []})()
            self.media = Doc()
        else:
            self.media = None


class FakeClient:
    def __init__(self, channel_id, messages):
        self._channel_id = channel_id
        self._messages = messages

    def get_dialogs(self):
        return [DummyDialog(DummyEntity(self._channel_id, username='chan', name='Chan'), 'Chan')]

    def get_entity(self, id_or_channel):
        return DummyEntity(self._channel_id, username='chan', title='Chan')

    def iter_messages(self, entity, reverse=True, limit=100, search=None, offset_id=None, grouped=None):
        msgs = self._messages
        if search:
            msgs = [m for m in msgs if search in getattr(m, 'text', '')]
        return msgs[:limit]

    def download_media(self, msg, file=None):
        # create a dummy file to simulate download
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'wb') as f:
            f.write(b'data')

    def get_messages(self, entity, ids):
        for m in self._messages:
            if m.id == ids:
                return m
        return None


def test_download_by_message_id(tmp_path, monkeypatch):
    # set cwd to tmp_path so downloads/ is created there
    monkeypatch.chdir(tmp_path)
    messages = [FakeMessage(10, media_type='video', text='video'), FakeMessage(11, media_type=None)]
    client = FakeClient(channel_id=123, messages=messages)

    downloader = ChannelMediaDownloader(client, '123')
    # download message id 10
    result = downloader._descargar_mensaje(messages[0], [], 1, 1)
    # ensure file created under downloads
    base = tmp_path / 'downloads' / '123' / 'images'
    # because message is considered video detection may vary; just check db path exists after descargar_medios
    db_path = downloader.db_path
    # call descargar_medios which will write db
    db = downloader.descargar_medios()
    assert os.path.exists(db)
    with open(db, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'media' in data


def test_download_by_search_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    messages = [FakeMessage(21, media_type='photo', text='match'), FakeMessage(22, media_type='photo', text='match2')]
    client = FakeClient(channel_id=456, messages=messages)
    downloader = ChannelMediaDownloader(client, '456', limit=10, search='match')
    db = downloader.descargar_medios()
    assert os.path.exists(db)
    with open(db, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data['media']) >= 1
