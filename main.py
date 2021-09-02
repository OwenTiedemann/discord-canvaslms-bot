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


class_list = [56444, 56967, 56281, 56289, 56709]

class_dict = {
    "class_list": [
        56444, 56967, 56281, 56289, 56709
    ],
    56444: 0,
    56967: 0,
    56281: 0,
    56289: 0,
    56709: 0,
}


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


@tasks.loop(seconds=30)
async def post_announcements():
    announcements = canvas.get_announcements(context_codes=class_dict['class_list'], latest_only=True)
    for announcement in announcements:
        s = announcement.html_url
        start = s.find("/courses/") + len("/courses/")
        end = s.find("/discussion_topics/")
        course_id = int(s[start:end])
        if announcement.id != class_dict[course_id]:
            class_dict[course_id] = announcement.id
            announcement_course = canvas.get_course(course_id)
            embed = discord.Embed(
                title=f"{announcement_course.course_code} Announcement: ({announcement.id})",
                url=announcement.html_url,
                description=cleanhtml(announcement.message),
                timestamp=datetime.datetime.strptime(announcement.posted_at, "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_footer(text=f"{announcement_course.course_code}")

            channel = await bot.fetch_channel(870019149743669288)
            await channel.send(embed=embed)


post_announcements.start()

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

    bot.run(token)
