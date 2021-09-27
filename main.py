import configparser

import discord
from discord.ext import commands, tasks
from canvasapi import Canvas
import motor.motor_asyncio
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

config = configparser.ConfigParser()
config.read('config.ini')
API_URL = config['CANVAS']['api_url']
API_KEY = config['CANVAS']['access_token']
token = config['DISCORD']['token']
mongo_token = config['MONGODB']['mongo_token']

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=['canvas '], intents=intents)

bot.canvas = Canvas(API_URL, API_KEY)
database_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_token)

bot.database = database_client['CanvasTracking']

initial_extensions = ['cogs.tracking', 'cogs.lists', 'jishaku']


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)


if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

    bot.run(token)
