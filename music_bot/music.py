import discord
from discord.ext import commands
from music_bot.music_utils import (
    seconds_format,
    format_for_queue_embed_np,
    format_for_queue_embed_q,
    BotAudioHandler,
)
import yt_dlp as ydl


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cp", help="check if song is currently playing")
    async def cp(self, ctx):
        try:
            return not self.player.song_queue.is_empty()
        except AttributeError:
            return False

    @commands.command(name="join")
    async def join(self, ctx):
        if not ctx.author.voice:
            await ctx.send("Get in a channel")
        else:
            self.player = BotAudioHandler(self.bot, ctx.guild)
            discord.opus.load_opus(
                "/usr/local/homebrew/Cellar/opus/1.3.1/lib/libopus.0.dylib"
            )
            channel = ctx.author.voice.channel
            await channel.connect(reconnect=True, timeout=None)
            await ctx.send(
                f":thumbsup: **Joined** `{ctx.voice_client.channel}` :thumbsup:"
            )

    @commands.command(name="die", help="leaves channel")
    async def leave(self, ctx):
        vc = ctx.voice_client
        if not vc:
            await ctx.send("**im already dead**")
        elif vc.is_connected():
            await vc.disconnect()
            self.player = None

    @commands.command(name="p", help="plays stuff")
    async def play(self, ctx, *search_param):
        vc = ctx.voice_client
        search_param = " ".join(search_param[:])
        if not vc:
            await ctx.invoke(self.join)
            vc = ctx.voice_client

        await ctx.send(f":mag_right: **Searching** :mag_right: {search_param}")
        currently_playing = await ctx.invoke(self.cp)
        try:
            await self.player.queue_song(search_param, ctx.author)
        except ydl.utils.ExtractorError:
            await ctx.send(":x: **Unable to load from Youtube** :x:")
            return
        song_obj = self.player.get_recently_added()
        if currently_playing:
            embed = discord.Embed(
                title="Added to queue",
                description=f"[{song_obj.title}]({song_obj.url})",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Channel", value=song_obj.uploader, inline=True)
            embed.add_field(
                name="Duration",
                value=f"{song_obj.duration // 60}:{seconds_format(song_obj.duration % 60)}",
                inline=True,
            )
            embed.add_field(
                name="Requested By", value=str(song_obj.requester), inline=True
            )
            embed.add_field(
                name="Position in queue",
                value=len(self.player.song_queue.queue) - 1,
                inline=False,
            )
            embed.add_field(
                name="Searched for:",
                value=song_obj.searched_title,
                inline=True,
            )
            embed.set_thumbnail(url=song_obj.thumbnail)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"**Playing** :notes: `{song_obj.title}` - Now!")
            await ctx.invoke(self.np)

    @commands.command(name="pause", help="pauses")
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.send(":pause_button: **Pausing...** :pause_button:")

    @commands.command(name="resume", help="resumes")
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc.is_paused():
            vc.resume()
            await ctx.send(":arrow_forward: **Resuming...** :arrow_forward: ")

    @commands.command(name="np", help="now playing")
    async def np(self, ctx):
        currently_playing = await ctx.invoke(self.cp)
        if currently_playing:
            song_obj = self.player.get_currently_playing()
            line = "**-------------------------------**"
            embed = discord.Embed(
                title="♪ Now Playing ♪",
                description=f"[{song_obj.title}]({song_obj.url})\n{line}\n",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Channel", value=song_obj.uploader, inline=True)
            embed.add_field(
                name="Duration",
                value=f"{song_obj.duration // 60}:{seconds_format(song_obj.duration % 60)}",
                inline=True,
            )
            embed.add_field(name="Requested By", value=song_obj.requester, inline=True)
            embed.set_thumbnail(url=song_obj.thumbnail)
            await ctx.send(embed=embed)
        else:
            await ctx.send("**Nothing currently playing**")

    @commands.command(name="q", help="queue")
    async def q(self, ctx):
        currently_playing = await ctx.invoke(self.cp)
        if not (currently_playing):
            embed = discord.Embed(
                title="Queue for " + ctx.guild.name,
                description="__Now Playing:__\n\nNothing\n",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        else:
            songs_in_queue = ""
            currently_playing_song = self.player.get_currently_playing()
            num_songs_in_queue = len(self.player.song_queue.queue) - 1
            for i in range(num_songs_in_queue):
                song = self.player.get_song_at_index(i + 1)
                songs_in_queue += format_for_queue_embed_q(song, i + 1)

            embed = discord.Embed(
                title=f"Queue for {ctx.guild.name}",
                description=f"__Now Playing:__\n{format_for_queue_embed_np(currently_playing_song)}\n__Up Next:__\n{songs_in_queue}",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=currently_playing_song.thumbnail)
            await ctx.send(embed=embed)

    @commands.command(name="clear", help="clears queue")
    async def clear(self, ctx):
        try:
            self.player.clear_queue()
            await ctx.send("**Cleared**")
        except AttributeError:
            await ctx.send("**Nothing to clear**")

    @commands.command(name="skip", help="skip")
    async def fs(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            await ctx.send("**Not in a channel**")
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        vc.stop()
        await ctx.send(":track_next: **Skipping...** :track_next:")

    @commands.command(name="loop", help="loops the queue")
    async def loop(self, ctx):
        if self.player.looping:
            self.player.looping = False
            await ctx.send(":no_entry_sign: **Queue loop OFF** :no_entry_sign:")
        else:
            self.player.looping = True
            await ctx.send(":white_check_mark:  **Queue loop ON** :white_check_mark: ")

    @commands.command(name="remove", help="removes an item from the queue, by index")
    async def remove(self, ctx, index):
        try:
            index = int(index)
        except ValueError:
            await ctx.send(":x: **Use a numerical index** :x:")
            return
        if index <= len(self.player.song_queue.queue) and index > 0:
            song_title = self.player.song_queue.queue[index].title
            self.player.remove_song(index)
            await ctx.send(
                f":white_check_mark: **Removed** `{song_title}` :white_check_mark:"
            )
        else:
            await ctx.send(":x: **Index out of range** :x:")

    @commands.command(name="shuffle", help="shuffles the queue")
    async def shuffle(self, ctx):
        self.player.shuffle_queue()
        await ctx.send(
            ":twisted_rightwards_arrows: **Shuffled the queue** :twisted_rightwards_arrows:"
        )


async def setup(bot):
    await bot.add_cog(MusicBot(bot))
