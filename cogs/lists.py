import datetime
import re

import discord
from discord.ext import commands, tasks
import asyncio


class Lists(commands.Cog, name="Lists"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="list")
    async def list(self, ctx):
        pass

    @list.command(name="courses", brief="Lists enrolled courses")
    @commands.is_owner()
    async def _courses(self, ctx):
        user = self.bot.canvas.get_user(63424)

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


def setup(bot):
    bot.add_cog(Lists(bot))
