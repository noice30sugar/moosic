from collections import deque
import discord
import yt_dlp as ydl
import random

ydl_options = {
    "format": "bestaudio/best",
    "title": True,
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
}


class Song:
    """Holds important song information

    data: YoutubeDL.extract_info output
    author: discord user requester
    """

    def __init__(self, data, author):
        self.searched_title = data["id"]
        data = data["entries"][0]
        self.title = data["title"]
        self.duration = data["duration"]
        self.url = data["webpage_url"]
        self.thumbnail = data["thumbnail"]
        self.uploader = data["uploader"]
        self.requester = author

    def get_mp3_link(self):
        yt = ydl.YoutubeDL(ydl_options)
        song_obj = yt.extract_info(self.searched_title, download=False)
        return song_obj["entries"][0]["url"]


class SongQueue:
    """Performs simple queue operations

    queue: holds Song objects
    looping: toggle for whether a song should be readded to queue after it is played
    """

    def __init__(self):
        self.queue = deque()
        self.looping = False

    def add_song(self, song):
        self.queue.append(song)

    def next_song(self):
        song_played = self.queue.popleft()
        if self.looping:
            self.queue.append(song_played)

        if self.is_empty():
            return None
        return self.queue[0]

    def shuffle(self):
        current_song = self.queue.popleft()
        random.shuffle(self.queue)
        self.queue.appendleft(current_song)

    def clear(self):
        current_song = self.queue.popleft()
        self.queue.clear()
        self.queue.appendleft(current_song)

    def remove(self, index):
        self.queue.remove(self.queue[index])

    def is_empty(self):
        if len(self.queue):
            return False
        return True


class BotAudioHandler:
    def __init__(self, bot, guild):
        self.bot = bot
        self.song_queue = SongQueue()
        self.guild = guild

    def get_song_at_index(self, index):
        return self.song_queue.queue[index]

    def get_currently_playing(self):
        return self.get_song_at_index(0)

    def get_recently_added(self):
        return self.get_song_at_index(-1)

    def shuffle_queue(self):
        self.song_queue.shuffle()

    def remove_song(self, index):
        self.song_queue.remove(index)

    def clear_queue(self):
        self.song_queue.clear()

    async def queue_song(self, search_param, author):
        """Adds the searched song to the queue and plays it if nothing is playing

        Args:
            search_param (_type_): _description_
        """
        queue_empty = self.song_queue.is_empty()

        yt = ydl.YoutubeDL(ydl_options)
        song_data = yt.extract_info(search_param, download=False)
        self.song_queue.add_song(Song(song_data, author))
        if queue_empty:
            await self.play_from_queue()

    def next_song(self):
        next_song = self.song_queue.next_song()
        if next_song is None:
            return

        coro = self.play_from_queue()
        self.bot.loop.create_task(coro)

    async def play_from_queue(self):
        song = self.get_currently_playing()

        self.guild.voice_client.play(
            discord.FFmpegPCMAudio(
                song.get_mp3_link(),
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            ),
            after=lambda _: self.next_song(),
        )


def format_for_queue_embed_np(song):
    return f"[{song.title}]({song.url}) | `Duration: {song.duration//60}:{seconds_format(song.duration%60)} Requested By: {song.requester}`\n"


def format_for_queue_embed_q(song, index):
    return f"`{index}.` [{song.title}]({song.url}) | `Duration: {song.duration//60}:{seconds_format(song.duration%60)} Requested By: {song.requester}`\n\n"


def seconds_format(num):
    if num < 10:
        return "0" + str(num)
    else:
        return str(num)
