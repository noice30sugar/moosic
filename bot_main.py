import discord
from discord.ext import commands, tasks
import aiohttp

token = ""


class DiscordBot(commands.Bot):
    def __init__(self, command_prefix="-", intents=discord.Intents().all()):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.extensions_to_load = ["music_bot.music"]

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        for ext in self.extensions_to_load:
            await self.load_extension(ext)

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_ready(self):
        print("Ready!")


bot = DiscordBot()
bot.run(token)
