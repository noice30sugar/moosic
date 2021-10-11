import discord
import os
from discord.ext import commands
import youtube_dl as ydl
import asyncio
import random
import pickle

token = os.environ["token"]
prefix = os.environ["prefix"]
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
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')

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
        self.looping = False
        
        ctx.bot.loop.create_task(self.queue_loop())
        
    async def queue_loop(self):
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.play_next.clear()
            song_obj = await self.queue.get()
            song_obj = await Song.search(song_obj.title)
            self.guild.voice_client.play(song_obj, after=lambda _: self.bot.loop.call_soon_threadsafe(self.play_next.set))
            if self.looping:
                await self.queue.put(song_obj) 
            #await ctx.send(song_obj.url)
            await self.play_next.wait()
            
            # Make sure the FFmpeg process is cleaned up.
            song_obj.cleanup()
            
def format_for_queue_embed(song, author, index=0):
    if not(index):
        return '[%s](%s) | `%d:%d Requested By: %s`\n' %(song.title, song.url, song.duration//60, song.duration%60, author)
    else:
        return '`%d.` [%s](%s) | `%d:%d Requested By: %s`\n\n' %(index, song.title, song.url, song.duration//60, song.duration%60, author)
    
class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
    
    @commands.command(name='cp', help='check if song is currently playing')
    async def cp(self, ctx):
        try:
            current_song = ctx.voice_client.source.title
            return True
        except:
            return False
        
    @commands.command(name='join')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("Get in a channel".format(ctx.message.author.name))
        else:
            channel = ctx.message.author.voice.channel
            try:
                await channel.connect()
                await ctx.send(f':thumbsup: **Joined** `{ctx.voice_client.channel}` :thumbsup:')
            except:
                pass
            
    @commands.command(name='die', help='leaves channel')
    async def leave(self, ctx):
        vc = ctx.voice_client
        if not vc:
            await ctx.send("**im already dead**")
        elif vc.is_connected():
            await vc.disconnect()
            self.player = None
            
    @commands.command(name='p', help = 'plays stuff')        
    async def play(self, ctx, *search_param):
        vc = ctx.voice_client
        search_param = " ".join(search_param[:])
        if not vc:
            await ctx.invoke(self.join)
            vc = ctx.voice_client
        if not self.player:
            music_player = Queue(ctx)
            self.player = music_player
        await ctx.send(f":mag_right: **Searching** :mag_right: {search_param}")
        currently_playing = await ctx.invoke(self.cp)
        try:    
            song_obj = await Song.search(search_param, loop= self.bot.loop)
            await self.player.queue.put(song_obj)
        except:
            await ctx.send(':x: **Unable to load from Youtube** :x:')
            return
        if currently_playing:
            embed = discord.Embed(title="Added to queue", description=f"[{song_obj.title}]({song_obj.url})", color=discord.Color.blue())
            embed.add_field(name="Channel", value=song_obj.uploader, inline=True)
            embed.add_field(name="Duration", value="%d:%d" %(song_obj.duration//60, song_obj.duration%60), inline=True)
            embed.add_field(name="Requested By", value=str(ctx.author), inline=True)
            embed.add_field(name="Position in queue", value=len(self.player.queue._queue), inline=False)
            embed.set_thumbnail(url=song_obj.thumbnail)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'**Playing** :notes: `{song_obj.title}` - Now!')
            

    
    @commands.command(name='yw', help='youre welcome')
    async def yw(self, ctx):
        await ctx.invoke(self.join)
        await ctx.invoke(self.play, 'youre welcome')

    @commands.command(name='ty', help='test')
    async def ty(self, ctx):
        embed = discord.Embed(title="", description="you're welcome!!", color=discord.Color.blue())
        await ctx.send(embed=embed)
        await ctx.send(":luistretched:")
        
    @commands.command(name='pause', help='pauses')
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.send(':pause_button: **Pausing...** :pause_button:')

    @commands.command(name='resume', help='resumes')
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc.is_paused():
            vc.resume()
            await ctx.send(':arrow_forward: **Resuming...** :arrow_forward: ')
            
    @commands.command(name='np', help='now playing')
    async def np(self, ctx):
        vc = ctx.voice_client
        currently_playing = await ctx.invoke(self.cp)
        if currently_playing:
            line = "**-------------------------------**"
            embed = discord.Embed(title="♪ Now Playing ♪", description=f"[{vc.source.title}]({vc.source.url})\n{line}\n", color=discord.Color.blue())
            embed.add_field(name="Channel", value=vc.source.uploader, inline=True)
            embed.add_field(name="Duration", value="%d:%d" %(vc.source.duration//60, vc.source.duration%60), inline=True)
            embed.add_field(name="Requested By", value=str(ctx.author), inline=True)
            embed.set_thumbnail(url=vc.source.thumbnail)
            await ctx.send(embed=embed)
        else:
             await ctx.send('**Nothing currently playing**')
        
    @commands.command(name='q', help='queue')
    async def q(self, ctx):
        vc = ctx.voice_client
        currently_playing = await ctx.invoke(self.cp)
        if not(self.player) or not(currently_playing):
            embed = discord.Embed(title="Queue for " + ctx.message.guild.name, description="__Now Playing:__\n\nNothing\n", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            songs_in_queue = ""
            index = 0
            for song in self.player.queue._queue:
                index +=1
                songs_in_queue += format_for_queue_embed(song, ctx.author, index)
            
            embed = discord.Embed(title=f"Queue for {ctx.message.guild.name}", 
                                  description=f"__Now Playing:__\n{format_for_queue_embed(vc.source, ctx.author)}\n__Up Next:__\n{songs_in_queue}", color=discord.Color.blue())
            embed.set_thumbnail(url=vc.source.thumbnail)
            await ctx.send(embed = embed)
        
    @commands.command(name='clear', help='clears queue')
    async def clear(self, ctx):
        try:
            self.player.queue._queue.clear()
            await ctx.send('**Cleared**')
        except:
            await ctx.send('**Nothing to clear**')
        
    @commands.command(name='fs', help='skip')
    async def fs(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():           
            await ctx.send('**Not in a channel**')
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        vc.stop()
        await ctx.send(':track_next: **Skipping...** :track_next:')
        
    @commands.command(name='loop', help='loops the queue')
    async def loop(self, ctx):
        vc = ctx.voice_client
        if self.player.looping:
            self.player.looping = False
            await ctx.send(':no_entry_sign: **Queue loop OFF** :no_entry_sign:')
        else:
            self.player.looping = True
            await ctx.send(':white_check_mark:  **Queue loop ON** :white_check_mark: ')
        
    @commands.command(name='remove', help='removes an item from the queue, by index')
    async def remove(self, ctx, index):
        try:
            index = int(index)
        except:
            await ctx.send(":x: **Use a numerical index** :x:")
            return
        if self.player and index <= len(self.player.queue._queue): 
            song_to_remove = self.player.queue._queue[index-1]
            self.player.queue._queue.remove(song_to_remove)
            await ctx.send(f':white_check_mark: **Removed** `{song_to_remove.title}` :white_check_mark:')
        else:
            await ctx.send(":x: **Index out of range** :x:")
class Bet():
    def __init__(self, start_amt, player):
        self.bet_starter = player
        self.pot = start_amt
        self.min_bet = start_amt
        self.players = {player:start_amt}
        
    def add_to_pot(self, amount, player):
        self.pot += amount
        if player not in self.players:
            self.players[player] = amount
        else:
            self.players[player] += amount            

class Economy():
    def __init__(self, bank={}):
        self.bank = bank
        self.bet = False
        
    def new_user(self, user):
        if user not in self.bank:
            self.bank[user] = 3000
            return True
        else:
            return False
                
    def withdraw(self, amount, user):
        self.bank[user] -= amount
        
    def deposit(self, amount, user):
        self.bank[user] += amount
        
    def start_bet(self, amount, player):
        self.bet = Bet(amount, player)
        self.withdraw(amount, player)
    
    def join_bet(self, amount, player):
        self.bet.add_to_pot(amount, player)
        self.withdraw(amount, player)   
        
    def draw(self):
        winner = random.choice(list(self.bet.players.keys()))
        self.deposit(self.bet.pot, winner)
        self.bet = False
        return winner
    
    
class Konata(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data.pickle", "rb") as f:
            self.econ = pickle.load(f)    
    
    @commands.command()
    async def registered(self, ctx):
        if self.econ.new_user(ctx.author.name):
            return False
        else:
            return True
        
    @commands.command()
    @commands.cooldown(1, 60*60*5, commands.BucketType.user)
    async def daily(self, ctx):
        if await ctx.invoke(self.registered):
            coins = random.randint(150,350)
            self.econ.deposit(coins, ctx.author.name)
            await ctx.send(f':moneybag: Here you go: {coins} coins! You can claim another reward in 24 hours.')
            pickle.dump(self.econ, open('data.pickle', 'wb'))
        else:
            await ctx.send('Register for a bank account using `balance` first!')
        
    @commands.command()
    async def loot(self, ctx):
        if random.randint(1,20) == 1:
            coins = random.randint(20,60)
            await ctx.send(f':person_running: You walk a little and find {coins} coins!')
            if await ctx.invoke(self.registered):
                self.econ.deposit(coins, ctx.author.name)
                pickle.dump(self.econ, open('data.pickle', 'wb'))
            else:
                await ctx.send('Too bad you don\'t have a bank account!')
        else:
            await ctx.send('Nothing to loot here!')
            
    @commands.command()
    async def balance(self, ctx):
        if self.econ.new_user(ctx.author.name):
            pickle.dump(self.econ, open('data.pickle', 'wb'))
            await ctx.send(f'Created bank account for <@{ctx.author.name}>! 3000 coins have been added.')
        else:
            await ctx.send(f':information_source: You currently have {self.econ.bank[ctx.author.name]} coins in your account!')
    
    @commands.command()
    async def rate(self, ctx, *args):
        args = " ".join(args[:])
        await ctx.send(f':thinking: I give **{args}** a {random.randint(0,10)}/10')
        
    @commands.command()
    async def bet(self, ctx, cmd = None, coins = 10):
        if not(isinstance(coins, int)):
            await ctx.send('Enter a number of coins to bet.')
            return
        elif int(coins) <= 0:
            await ctx.send('Number of coins must be nonzero to bet')
            return
        coins = int(coins)
        if cmd == 'help':
            embed = discord.Embed(title=":information_source: Gambling Time", 
                                  description=":book: **Bet commands**\n" +
                                              "`bet start` - Starts a bet in the current channel with a minimum value.\n" + 
                                              "`bet join` - Joins a bet with a coin amount.\n" + 
                                              "`bet draw` - Collects the total bet amount and chooses a winner!\n" +
                                              "`bet info` - Shows you information on a bet running in the current channel;", color=discord.Color.blue())
            await ctx.send(embed=embed)
        elif cmd == 'start':
            if self.econ.bet:
                await ctx.send('Cannot start another bet while one is active.')
            elif await ctx.invoke(self.registered):
                    self.econ.start_bet(coins, ctx.author.name)
                    await ctx.send(f':white_check_mark: Started a bet with {coins} coins!')
                    pickle.dump(self.econ, open('data.pickle', 'wb'))
            else:
                await ctx.send('Register for a bank account to start bets')
                
        elif cmd == 'join':
            if not(self.econ.bet):
                await ctx.send('No current bet running')
            elif await ctx.invoke(self.registered):
                if coins < self.econ.bet.min_bet:
                    await ctx.send(f'The minimum amount to bet is {self.econ.bet.min_bet}')
                else:
                    self.econ.join_bet(coins, ctx.author.name)
                    await ctx.send(f'Added {coins} to the pot. Total pot: {self.econ.bet.pot}')
                    pickle.dump(self.econ, open('data.pickle', 'wb'))
            else:
                await ctx.send('Register for a bank account to join bets')
                
        elif cmd == 'draw':
            if not(self.econ.bet):
                await ctx.send('No current bet running')
            elif ctx.author.name == self.econ.bet.bet_starter:
                pot = self.econ.bet.pot
                await ctx.send(f'The bet has ended! And the lucky winner is... @{self.econ.draw()}! Congratulations, you won {pot} coins!')
                pickle.dump(self.econ, open('data.pickle', 'wb'))
            else:
                await ctx.send(f'Only the bet starter @{self.econ.bet.bet_starter} can draw the bet')
                
        elif cmd == 'info':
            if not(self.econ.bet):
                await ctx.send('No current bet running')
            else:
                players_info = ""
                index=1
                for player in self.econ.bet.players:
                    players_info += f"**#{index}** `{player}` - {self.econ.bet.players[player]} coins\n"
                    index += 1
                embed  = discord.Embed(title = f'{self.econ.bet.bet_starter}\'s bet', description = f"Total users participating: {len(self.econ.bet.players)}\n\n{players_info}",
                                       color=discord.Color.blue())
                embed.set_footer(text=f"Total coins: {self.econ.bet.pot}")
                await ctx.send(embed = embed)
                
                
bot = commands.Bot(command_prefix=prefix, intents=intents)
@bot.event    
async def on_ready():
    print('running')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f":sweat_smile: You have to wait {int(error.retry_after//(60*60))} hours, {int((error.retry_after%(60*60)//60))} minutes to claim another daily reward!")
    
bot.add_cog(MusicBot(bot))
bot.add_cog(Konata(bot))
bot.run(token)

        
        
    
            

        
        
        
        
        
    