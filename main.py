import configparser
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

canvas = Canvas(API_URL, API_KEY)

initial_extensions = []

user = canvas.get_user(63424)


@bot.command()
async def list(ctx):
    courses = user.get_courses()

    embed = discord.Embed(
        title="Course List"
    )
    embed_string = "```\n"

    for course in courses:
        try:
            course_name = course.name
            course_name = re.sub(r'\([^)]*\)', '', course_name)

            course_string = f"{course_name.lstrip()} ({course.id})"
            embed_string += f"{course_string}\n"
        except AttributeError as error:
            print(error)
        except TypeError as error:
            print(error)

    embed_string += "```"

    embed.description = embed_string

    await ctx.send(embed=embed)


@bot.command(name="assignments")
async def _assignments(ctx, id):
    course = canvas.get_course(id)
    assignments = course.get_assignments()

    embed = discord.Embed(
        title="Assignment List"
    )
    embed_string = "```\n"

    for assignment in assignments:
        if not assignment.has_submitted_submissions:
            embed_string += f"{assignment}\n"

    embed_string += "```"

    embed.description = embed_string

    await ctx.send(embed=embed)

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

    bot.run(token)
