import datetime
import re
import json

import discord
from discord.ext import commands, tasks
import asyncio


class CourseAnnouncement:
    def __init__(self, guild_id, course_id, channel_id, announcement_id):
        self.guild = guild_id
        self.course = course_id
        self.channel = channel_id
        self.announcement = announcement_id


class CourseModules:
    def __init__(self, guild_id, course_id, channel_id, module_ids):
        self.guild = guild_id
        self.course = course_id
        self.channel = channel_id
        self.modules = module_ids


class CourseAssignments:
    def __init__(self, guild_id, course_id, channel_id, assignment_ids):
        self.guild = guild_id
        self.course = course_id
        self.channel = channel_id
        self.assignments = assignment_ids


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class Tracking(commands.Cog, name="Tracking"):
    def __init__(self, bot):
        self.bot = bot
        self.post_announcements.start()
        self.post_modules.start()
        self.post_assignments.start()

    @commands.group(name="track")
    async def track(self, ctx):
        pass

    @track.command(name="assignments", brief="Lists all currently posted assignments")
    @commands.is_owner()
    async def _assignments(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        if str(ctx.guild.id) in guilds_dict:
            if 'assignments' in guilds_dict[str(ctx.guild.id)]:
                if str(course_id) in guilds_dict[str(ctx.guild.id)]['assignments']:
                    await ctx.send('Already tracking that course!')
                    return
                else:
                    guilds_dict[str(ctx.guild.id)]['assignments'][str(course_id)] = {"channel_id": ctx.channel.id,
                                                                                     "assignment_ids": []}
            else:
                guilds_dict[str(ctx.guild.id)]['assignments'] = {str(course_id): {
                    "channel_id": ctx.channel.id,
                    "assignment_ids": []
                }
                }
        else:
            guilds_dict[str(ctx.guild.id)] = {"assignments": {
                str(course_id): {
                    "channel_id": ctx.channel.id,
                    "assignment_ids": []
                }
            }}

        assignments = course.get_assignments()

        for assignment in assignments:
            guilds_dict[str(ctx.guild.id)]['assignments'][str(course_id)]['assignment_ids'].append(assignment.id)
            embed = discord.Embed(
                title=f"{course.course_code} Assignment: ({assignment.id})",
                url=assignment.html_url,
                description=assignment.name,
            )
            embed.set_footer(text=f"{course.course_code}")

            if assignment.due_at is not None:
                embed.timestamp = datetime.datetime.strptime(assignment.due_at, "%Y-%m-%dT%H:%M:%SZ")

            await asyncio.sleep(1)
            await ctx.send(embed=embed)

        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)

    @track.command(name="announcements", brief="Tracks given course announcements in channel command is sent")
    @commands.is_owner()
    async def _announcements(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        if str(ctx.guild.id) in guilds_dict:
            if 'announcements' in guilds_dict[str(ctx.guild.id)]:
                if str(course_id) in guilds_dict[str(ctx.guild.id)]['announcements']:
                    await ctx.send('Already tracking that course!')
                    return
                else:
                    guilds_dict[str(ctx.guild.id)]['announcements'][str(course_id)] = {"channel_id": ctx.channel.id,
                                                                                       "last_announcement_id": 0}
            else:
                guilds_dict[str(ctx.guild.id)]['announcements'] = {str(course_id): {
                    "channel_id": ctx.channel.id,
                    "last_announcement_id": 0
                }
                }
        else:
            guilds_dict[str(ctx.guild.id)] = {"announcements": {
                str(course_id): {
                    "channel_id": ctx.channel.id,
                    "last_announcement_id": 0
                }
            }}

        announcement_ids = []

        announcements = self.bot.canvas.get_announcements(context_codes=[course_id])

        announcement_objects = []
        for announcement in announcements:
            announcement_objects.insert(0, announcement)

        for announcement in announcement_objects:
            embed = discord.Embed(
                title=f"{course.course_code} Announcement: ({announcement.id})",
                url=announcement.html_url,
                description=announcement.title + "\n\n" + cleanhtml(announcement.message),
                timestamp=datetime.datetime.strptime(announcement.posted_at, "%Y-%m-%dT%H:%M:%SZ")
            )
            embed.set_footer(text=f"{course.course_code}")

            await ctx.send(embed=embed)
            await asyncio.sleep(1)
            announcement_ids.append(announcement.id)

        guilds_dict[str(ctx.guild.id)]['announcements'][str(course_id)]['last_announcement_id'] = announcement_ids[-1]
        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)

    @track.command(name="modules", brief="Tracks given courses modules in channel command is posted in")
    @commands.is_owner()
    async def _modules(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        if str(ctx.guild.id) in guilds_dict:
            if 'modules' in guilds_dict[str(ctx.guild.id)]:
                if str(course_id) in guilds_dict[str(ctx.guild.id)]['modules']:
                    await ctx.send('Already tracking that course!')
                    return
                else:
                    guilds_dict[str(ctx.guild.id)]['modules'][str(course_id)] = {"channel_id": ctx.channel.id,
                                                                                 "module_ids": []}
            else:
                guilds_dict[str(ctx.guild.id)]['modules'] = {str(course_id): {
                    "channel_id": ctx.channel.id,
                    "module_ids": []
                }
                }
        else:
            guilds_dict[str(ctx.guild.id)] = {"modules": {
                str(course_id): {
                    "channel_id": ctx.channel.id,
                    "module_ids": []
                }
            }}

        modules = course.get_modules()

        for module in modules:
            if module.state == "locked":
                continue
            guilds_dict[str(ctx.guild.id)]['modules'][str(course_id)]["module_ids"].append(module.id)
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
                    print(error)
                    pass

            embed.set_footer(text=f"{course.course_code}")

            await ctx.send(embed=embed)
            await asyncio.sleep(1)

        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)

    @tasks.loop(seconds=30)
    async def post_announcements(self):
        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        courses = []
        course_ids = []

        for guild_id, tracking_types in guilds_dict.items():
            if "announcements" in tracking_types:
                for course_id, values in tracking_types['announcements'].items():
                    x = CourseAnnouncement(guild_id=int(guild_id),
                                           course_id=int(course_id),
                                           channel_id=values['channel_id'],
                                           announcement_id=values['last_announcement_id'])
                    courses.append(x)
                    course_ids.append(int(course_id))

        if not courses:
            return

        announcements = self.bot.canvas.get_announcements(context_codes=course_ids, latest_only=True)

        for announcement in announcements:
            s = announcement.html_url
            start = s.find("/courses/") + len("/courses/")
            end = s.find("/discussion_topics/")
            course_id = int(s[start:end])
            for course in courses:
                if course_id == course.course:
                    if announcement.id != course.announcement:
                        announcement_course = self.bot.canvas.get_course(course.course)
                        embed = discord.Embed(
                            title=f"{announcement_course.course_code} Announcement: ({announcement.id})",
                            url=announcement.html_url,
                            description=cleanhtml(announcement.message),
                            timestamp=datetime.datetime.strptime(announcement.posted_at, "%Y-%m-%dT%H:%M:%SZ")
                        )
                        embed.set_footer(text=f"{announcement_course.course_code}")

                        channel = await self.bot.fetch_channel(course.channel)
                        await channel.send(embed=embed)

                        guilds_dict[str(course.guild)]['announcements'][str(course.course)]['last_announcement_id'] = \
                            announcement.id

                    continue

        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)

    @tasks.loop(seconds=300)
    async def post_modules(self):
        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        courses = []
        course_ids = []

        for guild_id, tracking_types in guilds_dict.items():
            if "modules" in tracking_types:
                for course_id, values in tracking_types['modules'].items():
                    x = CourseModules(guild_id=int(guild_id),
                                      course_id=int(course_id),
                                      channel_id=values['channel_id'],
                                      module_ids=values['module_ids'])
                    courses.append(x)
                    course_ids.append(int(course_id))

        if not courses:
            return

        for course in courses:
            course_object = self.bot.canvas.get_course(course.course)
            modules = course_object.get_modules()

            for module in modules:
                if module.state == "locked":
                    continue
                if module.id not in course.modules:
                    embed = discord.Embed(
                        title=f"{course_object.course_code} Module: ({module.id})",
                        description=module.name,
                    )
                    items = module.get_module_items()
                    for item in items:
                        try:
                            embed.url = item.html_url
                            break
                        except AttributeError as error:
                            print(error)
                            pass

                    embed.set_footer(text=f"{course_object.course_code}")

                    channel = await self.bot.fetch_channel(course.channel)
                    await channel.send(embed=embed)

                    guilds_dict[str(course.guild)]['modules'][str(course.course)]["module_ids"].append(module.id)

        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)

    @tasks.loop(seconds=30)
    async def post_assignments(self):
        with open('guilds.json', 'r') as openfile:
            guilds_dict = json.load(openfile)

        courses = []
        course_ids = []

        for guild_id, tracking_types in guilds_dict.items():
            if "assignments" in tracking_types:
                for course_id, values in tracking_types['assignments'].items():
                    x = CourseAssignments(guild_id=int(guild_id),
                                          course_id=int(course_id),
                                          channel_id=values['channel_id'],
                                          assignment_ids=values['assignment_ids'])
                    courses.append(x)
                    course_ids.append(int(course_id))

        if not courses:
            return

        for course in courses:
            course_object = self.bot.canvas.get_course(course.course)
            assignments = course_object.get_assignments()

            for assignment in assignments:
                if assignment.id not in course.assignments:
                    guilds_dict[str(course.guild)]['assignments'][str(course.course)]['assignment_ids'].append(
                        assignment.id)
                    embed = discord.Embed(
                        title=f"{course_object.course_code} Assignment: ({assignment.id})",
                        url=assignment.html_url,
                        description=assignment.name,
                    )
                    embed.set_footer(text=f"{course_object.course_code}")

                    if assignment.due_at is not None:
                        embed.timestamp = datetime.datetime.strptime(assignment.due_at, "%Y-%m-%dT%H:%M:%SZ")

                    channel = await self.bot.fetch_channel(course.channel)
                    await channel.send(embed=embed)

                    await asyncio.sleep(1)

        with open("guilds.json", "w") as outfile:
            json.dump(guilds_dict, outfile)


def setup(bot):
    bot.add_cog(Tracking(bot))
