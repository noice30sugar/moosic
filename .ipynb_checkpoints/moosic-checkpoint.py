import discord
import os
from discord.ext import commands
import nest_asyncio 
import youtube_dl as ydl
import asyncio
from dotenv import load_dotenv

with ('token.txt', 'r') as f:
    token = f.readlines()
    token = token[0].strip()
    

nest_asyncio.apply()
 
intents = discord.Intents().all()
client = discord.Client(intents=intents)


ydl_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}


yt = ydl.YoutubeDL(ydl_options)

class Song(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')

    @classmethod
    async def search(cls, search, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        playlist = await loop.run_in_executor(None, lambda: yt.extract_info(search, download=False))
        if 'entries' in playlist:
            playlist = playlist['entries'][0]
        return cls(discord.FFmpegPCMAudio(playlist['url']), data=playlist)
    
class Queue:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.queue = asyncio.Queue()
        self.play_next = asyncio.Event()
        
        ctx.bot.loop.create_task(self.queue_loop())
        
    async def queue_loop(self):
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.play_next.clear()
            song_obj = await self.queue.get()
            song_obj = await Song.search(song_obj.title)
            self.guild.voice_client.play(song_obj, after=lambda _: self.bot.loop.call_soon_threadsafe(self.play_next  .set))
            await self.queue.put(song_obj)
            await self.ctx.send('Playing '+ song_obj.title)
            #await ctx.send(song_obj.url)
            await self.play_next.wait()
            
            # Make sure the FFmpeg process is cleaned up.
            song_obj.cleanup()
            
class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        
    @commands.command(name='join')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("Get in a channel".format(ctx.message.author.name))
        else:
            channel = ctx.message.author.voice.channel
            try:
                await channel.connect()
            except:
                pass
            
    @commands.command(name='die', help='leaves channel')
    async def leave(self, ctx):
        vc = ctx.message.guild.voice_client
        if not vc:
            await ctx.send("im already dead")
        elif vc.is_connected():
            await vc.disconnect()
            self.player = None
            
    @commands.command(name='p', help = 'plays stuff')        
    async def play(self, ctx, search_param):
        vc = ctx.message.guild.voice_client
        if not vc:
            await ctx.invoke(self.join)
            vc = ctx.message.guild.voice_client
        if not self.player:
            music_player = Queue(ctx)
            self.player = music_player
        try:
            song_obj = await Song.search(search_param, loop= self.bot.loop)
            await self.player.queue.put(song_obj)
            await ctx.send('Queued '+ song_obj.title)
        except:
            await ctx.send('Unable to load from youtube')

    
    @commands.command(name='yw', help='youre welcome')
    async def yw(self, ctx):
        await ctx.invoke(self.join)
        await ctx.invoke(self.play, 'youre welcome')

    @commands.command(name='ty', help='test')
    async def ty(self, ctx):
        embed = discord.Embed(title="", description="you're welcome!!", color=discord.Color.blue())
        await ctx.send(embed=embed)
        
    @commands.command(name='pause', help='pauses')
    async def pause(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.send('Pausing...')

    @commands.command(name='resume', help='resumes')
    async def resume(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_paused():
            vc.resume()
            await ctx.send('Resuming...')
            
    @commands.command(name='np', help='now playing')
    async def np(self, ctx):
        vc = ctx.voice_client
        await ctx.send("Currently playing " + vc.source.title)
        #await ctx.send(vc.source.url)
        
    @commands.command(name='q', help='queue')
    async def np(self, ctx):
        if not self.player:
            ctx.send('Queue is empty')
        else:
            songs_in_queue = []
            for song in self.player.queue._queue:
                songs_in_queue.append(song.title)
            await ctx.send(songs_in_queue)
        #await ctx.send(vc.source.url)
        
    @commands.command(name='clear', help='clears queue')
    async def clear(self, ctx):
        self.player.queue._queue.clear()
        await ctx.send('Cleared')
        
    @commands.command(name='fs', help='skip')
    async def fs(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():           
            ctx.send('Not in a channel')
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        vc.stop()
        await ctx.send('Skipping...')
        
        
bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event    
async def on_ready():
    print('running')
    
bot.add_cog(MusicBot(bot))
bot.run(token)
            
    