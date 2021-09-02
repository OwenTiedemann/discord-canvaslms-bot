import configparser
import datetime
import re

import discord
from discord.ext import commands, tasks
from canvasapi import Canvas

config = configparser.ConfigParser()
config.read('config.ini')
API_URL = config['CANVAS']['api_url']
API_KEY = config['CANVAS']['access_token']
token = config['DISCORD']['token']

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=['canvas '], intents=intents)

bot.canvas = Canvas(API_URL, API_KEY)

initial_extensions = ['cogs.tracking', 'cogs.lists', 'jishaku']


if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

    bot.run(token)
