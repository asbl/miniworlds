"""Local miniworlds audio adapter; no SDL audio thread or backend access is needed."""
import itertools as _audio_ids
import json as _audio_json
import os as _audio_os
import wave as _audio_wave
from js import mwAudio as _audio_send, mwAudioState as _audio_state
from miniworlds.base.platform import PlatformAdapter as _AudioPlatform

_audio_counter = _audio_ids.count()


def _audio_command(action, channel, **values):
    _audio_send(_audio_json.dumps(dict(action=action, channel=str(channel), **values)))


def _audio_file(path):
    path = str(path)
    if not _audio_os.path.isfile(path):
        raise FileNotFoundError(path)
    return path


class _BrowserChannel:
    def __init__(self, channel=None):
        self.channel = str(next(_audio_counter)) if channel is None else str(channel)
        self.volume = 1.0

    def play(self, sound, loops=0, *args, **kwargs):
        self.volume = sound.get_volume()
        _audio_command("play", self.channel, name=_audio_os.path.basename(sound.path), volume=self.volume, loops=loops)

    def stop(self):
        _audio_command("stop", self.channel)

    def set_volume(self, volume, *args):
        self.volume = max(0, min(1, volume))
        _audio_command("volume", self.channel, volume=self.volume)

    def get_busy(self):
        return _audio_json.loads(_audio_state(self.channel)).get("busy", False)

    def pause(self):
        _audio_command("pause", self.channel)

    def unpause(self):
        _audio_command("resume", self.channel)


class _BrowserSound:
    def __init__(self, path):
        self.path = _audio_file(path)
        self.volume = 1.0

    def play(self, loops=0, *args, **kwargs):
        channel = _BrowserChannel()
        channel.play(self, loops)
        return channel

    def set_volume(self, value):
        self.volume = max(0, min(1, value))

    def get_volume(self):
        return self.volume

    def get_length(self):
        try:
            with _audio_wave.open(self.path) as file:
                return file.getnframes() / file.getframerate()
        except (_audio_wave.Error, EOFError):
            return 0.0

    def stop(self):
        _audio_command("stop_path", "", name=_audio_os.path.basename(self.path))


class _BrowserMusic(_BrowserChannel):
    def __init__(self):
        super().__init__("music")
        self.path = None

    def load(self, path):
        self.path = _audio_file(path)

    def play(self, loops=-1, *args):
        if self.path:
            _audio_command("play", self.channel, name=_audio_os.path.basename(self.path), volume=self.volume, loops=loops)

    def fadeout(self, time):
        _audio_command("fadeout", self.channel, duration=time)

    def get_volume(self):
        return self.volume


_browser_music = _BrowserMusic()
_AudioPlatform.ensure_audio = lambda self, **kwargs: None
_AudioPlatform.load_sound = lambda self, path: _BrowserSound(path)
_AudioPlatform.find_channel = lambda self: _BrowserChannel()
_AudioPlatform.music = property(lambda self: _browser_music)
