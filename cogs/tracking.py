import datetime
import re
import sqlite3

import discord
from discord.ext import commands, tasks
import asyncio
from canvasapi import Canvas

conn = sqlite3.connect(r"bot.db")
c = conn.cursor()

sql_create_modules_table = """ CREATE TABLE IF NOT EXISTS modules (id INT PRIMARY KEY, guild_id INT NOT NULL, channel_id INT NOT NULL, course_id INT NOT NULL, last_module_id INT NOT NULL);"""
sql_create_announcement_table = """ CREATE TABLE IF NOT EXISTS announcements (id INT PRIMARY KEY, guild_id INT NOT NULL, channel_id INT NOT NULL, course_id INT NOT NULL, last_announcement_id INT NOT NULL);"""

c.execute(sql_create_announcement_table)
c.execute(sql_create_modules_table)


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class Tracking(commands.Cog, name="Tracking"):
    def __init__(self, bot):
        self.bot = bot
        self.post_announcements.start()
        self.post_modules.start()

    @commands.group(name="track")
    async def track(self, ctx):
        pass

    @track.command(name="announcements", brief="Tracks given course announcements in channel command is sent")
    async def _announcements(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        c.execute(""" SELECT * FROM announcements WHERE guild_id = ? AND course_id = ?""", (ctx.guild.id, course_id))
        data = c.fetchall()
        print(data)
        if len(data) != 0:
            await ctx.send("Already tracking course")
            return

        c.execute('SELECT COUNT(*) from announcements')
        c_result = c.fetchone()
        if c_result is None:
            row = 0
        else:
            row = c_result[0]

        c.execute(
            """ INSERT INTO announcements(id, guild_id, channel_id, course_id, last_announcement_id) VALUES(?, ?, ?, ?, ?)""",
            (row, ctx.guild.id, ctx.channel.id, course_id, 0))

        announcement_ids = []

        announcements = self.bot.canvas.get_announcements(context_codes=[course_id])

        announcement_objects = []
        for announcement in announcements:
            announcement_objects.insert(0, announcement)

        for announcement in announcement_objects:
            embed = discord.Embed(
                title=f"{course.course_code} Announcement: ({announcement.id})",
                url=announcement.html_url,
                description=cleanhtml(announcement.message),
                timestamp=datetime.datetime.strptime(announcement.posted_at, "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_footer(text=f"{course.course_code}")

            await ctx.send(embed=embed)
            await asyncio.sleep(1)
            announcement_ids.append(announcement.id)

        c.execute(""" UPDATE announcements SET last_announcement_id = ? WHERE guild_id = ? AND course_id = ?""",
                  (announcement_ids[-1], ctx.guild.id, course_id))
        conn.commit()

    @track.command(name="modules", brief="Tracks given courses modules in channel command is posted in")
    async def _modules(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        c.execute(""" SELECT * FROM modules WHERE guild_id = ? AND course_id = ?""", (ctx.guild.id, course_id))
        data = c.fetchall()
        print(data)
        if len(data) != 0:
            await ctx.send("Already tracking course")
            return

        c.execute('SELECT COUNT(*) from modules')
        c_result = c.fetchone()
        if c_result is None:
            row = 0
        else:
            row = c_result[0]

        c.execute(
            """ INSERT INTO modules(id, guild_id, channel_id, course_id, last_module_id) VALUES(?, ?, ?, ?, ?)""",
            (row, ctx.guild.id, ctx.channel.id, course_id, 0))

        modules = course.get_modules()
        highest_module_id = 0

        for module in modules:
            if module.position > highest_module_id:
                highest_module_id = module.position
            embed = discord.Embed(
                title=f"{course.course_code} Module: ({module.id})",
                description=module.name,
            )
            items = module.get_module_items()
            for item in items:
                try:
                    embed.url = item.html_url
                    break
                except AttributeError as error:
                    pass

            embed.set_footer(text=f"{course.course_code}")

            await ctx.send(embed=embed)
            await asyncio.sleep(1)

        c.execute(""" UPDATE modules SET last_module_id = ? WHERE guild_id = ? AND course_id = ?""",
                  (highest_module_id, ctx.guild.id, course_id))
        conn.commit()

    @tasks.loop(seconds=30)
    async def post_announcements(self):
        c.execute(""" SELECT * FROM announcements""")
        rows = c.fetchall()
        guilds = []
        channels = []
        courses = []
        last_announcements = []
        for row in rows:
            guilds.append(row[1])
            channels.append(row[2])
            courses.append(row[3])
            last_announcements.append(row[4])

        if not courses:
            return

        announcements = self.bot.canvas.get_announcements(context_codes=courses, latest_only=True)

        for announcement in announcements:
            s = announcement.html_url
            start = s.find("/courses/") + len("/courses/")
            end = s.find("/discussion_topics/")
            course_id = int(s[start:end])
            for guild, channel, course, last_announcement in zip(guilds, channels, courses, last_announcements):
                if course_id == course:
                    if announcement.id != last_announcement:
                        announcement_course = self.bot.canvas.get_course(course)
                        embed = discord.Embed(
                            title=f"{announcement_course.course_code} Announcement: ({announcement.id})",
                            url=announcement.html_url,
                            description=cleanhtml(announcement.message),
                            timestamp=datetime.datetime.strptime(announcement.posted_at, "%Y-%m-%dT%H:%M:%SZ")
                        )
                        embed.set_footer(text=f"{announcement_course.course_code}")

                        channel = await self.bot.fetch_channel(channel)
                        await channel.send(embed=embed)

                        c.execute(
                            """ UPDATE announcements SET last_announcement_id = ? WHERE guild_id = ? AND course_id = ?""",
                            (announcement.id, guild, course_id))
                    continue
        conn.commit()

    @tasks.loop(seconds=30)
    async def post_modules(self):
        c.execute(""" SELECT * FROM modules""")
        rows = c.fetchall()
        guilds = []
        channels = []
        courses = []
        module_positions = []
        for row in rows:
            guilds.append(row[1])
            channels.append(row[2])
            courses.append(row[3])
            module_positions.append(row[4])

        for guild, channel, course, module_position in zip(guilds, channels, courses, module_positions):
            course = self.bot.canvas.get_course(course)
            modules = course.get_modules()

            for module in modules:
                if module.position > module_position:
                    highest_module_id = module.position
                    embed = discord.Embed(
                        title=f"{course.course_code} Module: ({module.id})",
                        description=module.name,
                    )
                    items = module.get_module_items()
                    for item in items:
                        try:
                            embed.url = item.html_url
                            break
                        except AttributeError as error:
                            pass

                    embed.set_footer(text=f"{course.course_code}")

                    channel = await self.bot.fetch_channel(channel)
                    await channel.send(embed=embed)

                    await channel.send(embed=embed)

                    c.execute(""" UPDATE modules SET last_module_id = ? WHERE guild_id = ? AND course_id = ?""",
                              (highest_module_id, guild, course))

        conn.commit()


def setup(bot):
    bot.add_cog(Tracking(bot))
