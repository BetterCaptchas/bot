import asyncpg
import asyncio
from discord.ext import commands
import discord
import sys, traceback
import json
from termcolor import colored

async def get_prefix(bot_par, message):
    if not message.guild:
        return commands.when_mentioned_or(".")(bot_par, message)

    data = await bot.pool.fetch('SELECT prefix FROM guilds WHERE guildid=$1;', message.guild.id)
    return data[0]["prefix"]

def read_json():
    with open(fr"config.json", "r") as f:
        data = json.load(f)
    return data

config = read_json()
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print(colored('[BOOT] BetterCaptcha has successfully booted up! | v.1 |', 'white'))

initial_extensions = [
    'events_jole',
    'config'
]

loop = asyncio.get_event_loop()
bot.pool = loop.run_until_complete(asyncpg.create_pool(
    **config["database_info"], ssl='require'
))

if __name__ == "__main__":
    for cog in initial_extensions:
        try:
            bot.load_extension(f"cogs.{cog}")
            print(colored(f"[IMPORT] Successfully loaded {cog}!", 'white'))
        except Exception as e:
            print(
                f"[IMPORT FAIL] Failed to load {cog}, error:\n",
                file=sys.stderr
            )
            traceback.print_exc()

bot.token = config["token"]
bot.run(
    bot.token,
    reconnect=True
)
