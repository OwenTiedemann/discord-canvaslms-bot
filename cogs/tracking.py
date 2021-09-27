import datetime
import re

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

        exists = False
        guild_collection = self.bot.database[str(ctx.guild.id)]
        if await guild_collection.count_documents({"_id": str(course_id)}, limit=1) == 0:
            course_dict = {
                "_id": str(course_id),
                "guild_id": ctx.guild.id,
                "announcements": {
                    "channel_id": 0,
                    "last_announcement_id": 0
                },
                "modules": {
                    "channel_id": 0,
                    "modules_ids": []
                },
                "assignments": {
                    "channel_id": ctx.channel.id,
                    "assignment_ids": []
                }
            }
        else:
            exists = True
            course_dict = await guild_collection.find_one({"_id": str(course_id)})
            if course_dict['assignments']['channel_id'] != 0:
                await ctx.send('Already tracking assignments for that course!')
                return
            else:
                course_dict['assignments']['channel_id'] = ctx.channel.id

        assignments = course.get_assignments()

        for assignment in assignments:
            course_dict['assignments']['assignment_ids'].append(assignment.id)
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

        if exists:
            await guild_collection.update_one({"_id": str(course_id)},
                                              {"$set": {
                                                  "assignments": course_dict['assignments']
                                              }})
        else:
            await guild_collection.insert_one(course_dict)

    @track.command(name="announcements", brief="Tracks given course announcements in channel command is sent")
    @commands.is_owner()
    async def _announcements(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        exists = False

        guild_collection = self.bot.database[str(ctx.guild.id)]
        if await guild_collection.count_documents({"_id": str(course_id)}, limit=1) == 0:
            course_dict = {
                "_id": str(course_id),
                "guild_id": ctx.guild.id,
                "announcements": {
                    "channel_id": ctx.channel.id,
                    "last_announcement_id": 0
                },
                "modules": {
                    "channel_id": 0,
                    "modules_ids": []
                },
                "assignments": {
                    "channel_id": 0,
                    "assignment_ids": []
                }
            }
        else:
            exists = True
            course_dict = await guild_collection.find_one({"_id": str(course_id)})
            if course_dict['announcements']['channel_id'] != 0:
                await ctx.send('Already tracking announcements for that course!')
                return
            else:
                course_dict['announcements']['channel_id'] = ctx.channel.id

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

        if announcement_ids:
            latest_announcement = announcement_ids[-1]
        else:
            latest_announcement = 0

        course_dict['announcements']['last_announcement_id'] = latest_announcement

        if exists:
            await guild_collection.update_one({"_id": str(course_id)},
                                              {"$set": {
                                                  "announcements": course_dict['announcements']
                                              }})
        else:
            await guild_collection.insert_one(course_dict)

    @track.command(name="modules", brief="Tracks given courses modules in channel command is posted in")
    @commands.is_owner()
    async def _modules(self, ctx, course_id):
        try:
            course = self.bot.canvas.get_course(course_id)
        except Exception as error:
            print(error)
            await ctx.send("Couldn't find that course, try again.")
            return

        exists = False

        guild_collection = self.bot.database[str(ctx.guild.id)]
        if await guild_collection.count_documents({"_id": str(course_id)}, limit=1) == 0:
            course_dict = {
                "_id": str(course_id),
                "guild_id": ctx.guild.id,
                "announcements": {
                    "channel_id": 0,
                    "last_announcement_id": 0
                },
                "modules": {
                    "channel_id": ctx.channel.id,
                    "modules_ids": []
                },
                "assignments": {
                    "channel_id": 0,
                    "assignment_ids": []
                }
            }
        else:
            exists = True
            course_dict = await guild_collection.find_one({"_id": str(course_id)})
            if course_dict['modules']['channel_id'] != 0:
                await ctx.send('Already tracking modules for that course!')
                return
            else:
                course_dict['modules']['channel_id'] = ctx.channel.id

        modules = course.get_modules()

        for module in modules:
            if module.state == "locked":
                continue
            course_dict['modules']['modules_ids'].append(module.id)
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

        if exists:
            await guild_collection.update_one({"_id": str(course_id)},
                                              {"$set": {
                                                  "modules": course_dict['modules']
                                              }})
        else:
            await guild_collection.insert_one(course_dict)

    @tasks.loop(seconds=600)
    async def post_announcements(self):
        collections = self.bot.database.list_collection_names()

        courses = []
        course_ids = []

        for collection in await collections:
            courses_cursor = self.bot.database[str(collection)].find({"announcements.channel_id": {'$gt': 0}})
            for course in await courses_cursor.to_list(length=None):
                x = CourseAnnouncement(guild_id=int(course['guild_id']),
                                       course_id=int(course['_id']),
                                       channel_id=int(course['announcements']['channel_id']),
                                       announcement_id=int(course['announcements']['last_announcement_id']))
                courses.append(x)
                course_ids.append(int(course['_id']))

        if not courses:
            return

        try:
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

                            await self.bot.database[str(course.guild)].update_one({"_id": str(course.course)},
                                                                                  {"$set":
                                                                                       {"announcements"
                                                                                        ".last_announcement_id":
                                                                                            announcement.id}})
        except Exception as error:
            print(error)

    @tasks.loop(seconds=600)
    async def post_modules(self):
        collections = self.bot.database.list_collection_names()

        courses = []
        course_ids = []

        for collection in await collections:
            courses_cursor = self.bot.database[str(collection)].find({"modules.channel_id": {'$gt': 0}})
            for course in await courses_cursor.to_list(length=None):
                x = CourseModules(guild_id=int(course['guild_id']),
                                  course_id=int(course['_id']),
                                  channel_id=int(course['modules']['channel_id']),
                                  module_ids=course['modules']['modules_ids'])
                courses.append(x)
                course_ids.append(int(course['_id']))

        if not courses:
            return

        try:
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

                        course_dict = await self.bot.database[str(course.guild)].find_one({"_id": str(course.course)})
                        course_modules = course_dict['modules']['modules_ids']
                        course_modules.append(module.id)
                        await self.bot.database[str(course.guild)].update_one({"_id": str(course.course)}, {"$set": {
                            "modules.modules_ids": course_modules
                        }})
        except Exception as error:
            print(error)

    @tasks.loop(seconds=600)
    async def post_assignments(self):
        collections = self.bot.database.list_collection_names()

        courses = []
        course_ids = []

        for collection in await collections:
            courses_cursor = self.bot.database[str(collection)].find({"assignments.channel_id": {'$gt': 0}})
            for course in await courses_cursor.to_list(length=None):
                x = CourseAssignments(guild_id=int(course['guild_id']),
                                      course_id=int(course['_id']),
                                      channel_id=int(course['assignments']['channel_id']),
                                      assignment_ids=course['assignments']['assignment_ids'])
                courses.append(x)
                course_ids.append(int(course['_id']))

        if not courses:
            return

        try:
            for course in courses:
                course_object = self.bot.canvas.get_course(course.course)
                assignments = course_object.get_assignments()

                for assignment in assignments:
                    if assignment.id not in course.assignments:
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

                        course_dict = await self.bot.database[str(course.guild)].find_one({"_id": str(course.course)})
                        course_assignments = course_dict['assignments']['assignment_ids']
                        course_assignments.append(assignment.id)
                        await self.bot.database[str(course.guild)].update_one({"_id": str(course.course)}, {"$set": {
                            "assignments.assignment_ids": course_assignments
                        }})
        except Exception as error:
            print(error)


def setup(bot):
    bot.add_cog(Tracking(bot))
