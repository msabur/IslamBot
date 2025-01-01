from datetime import datetime, timezone
import random
import discord
from discord.ext import commands, tasks

from dua import dua
from hadith import hadith
from utils.database_utils import ServerDailyPost
from utils.errors import respond_to_interaction_error
from utils.slash_utils import generate_choices_from_list

POST_TYPES = ['dua', 'hadith']
POSSIBLE_COLLECTIONS = { 'forty': 42, 'virtues': 93 } # name : number of narrations

class DailyPost(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.fulfillPendingTasks.start()
    
    @tasks.loop(seconds=50)
    async def fulfillPendingTasks(self):
        pendingTasks = await ServerDailyPost.get_pending_tasks()

        for task in pendingTasks:
            parsedTask = ServerDailyPost.parse_row(task)
            channel = self.bot.get_channel(int(parsedTask['channel']))

            if not isinstance(channel, discord.TextChannel):
                # channel couldn't be found
                continue
            elif channel.permissions_for(channel.guild.me).send_messages == False:
                # don't have permission to post in the channel
                continue
            
            postType, useArabic = parsedTask['post_type'], bool(int(parsedTask['use_arabic']))
            if postType.lower() == 'dua':
                await self.send_random_dua_to_channel(channel)
            elif postType.lower() == 'hadith':
                await self.send_random_hadith_to_channel(channel, useArabic)

            # update last_send_date
            handler = ServerDailyPost(int(parsedTask['server']), parsedTask['post_type'])
            now_utc = datetime.now(tz=timezone.utc)
            formatted_date = now_utc.strftime('%Y-%m-%d')
            await handler.update(int(parsedTask['channel']), parsedTask['daily_time'], 
                                 formatted_date, int(parsedTask['use_arabic']))

    @fulfillPendingTasks.before_loop
    async def waitForReady(self):
        await self.bot.wait_until_ready()
    
    # based on dua.Dua._dua
    async def send_random_dua_to_channel(self, channel: discord.TextChannel):
        req = dua.DuaRequest(random.choice(list(dua.DUAS.keys())))
        await req.fetch()
        return await channel.send(embed=req.make_embed())
    
    # based on hadith.Hadith_Commands.abstract_hadith
    async def send_random_hadith_to_channel(self, channel: discord.TextChannel, arabic: bool):
        collection = random.choice(list(POSSIBLE_COLLECTIONS.keys()))
        limit = POSSIBLE_COLLECTIONS[collection]

        hadith_spec = hadith.HadithSpecifics(
            collection=collection, 
            ref=hadith.Reference(str(random.randint(1, limit))), 
            lang=('ar' if arabic else 'en')
        )

        try:
            embed = await hadith_spec.fetch_hadith()
        except hadith.InvalidHadith:
            return await channel.send("Error: Could not find a hadith to post")

        if hadith_spec.num_pages == 1:
            return await channel.send(embed=embed)

        # If there are multiple pages, construct buttons for their navigation.
        one_day = 24*60*60
        hadith_ui_view = hadith.HadithNavigator(hadith_spec, timeout=one_day)
        hadith_message = await channel.send(embed=embed, view=hadith_ui_view)
        hadith_ui_view.set_message(hadith_message)

    group = discord.app_commands.Group(
        name="dailypost", 
        description="Commands related to daily dua/hadith posts.", 
        allowed_contexts=discord.app_commands.AppCommandContext(
            guild=True,
        ),
        allowed_installs=discord.app_commands.AppInstallationType(
            guild=True,
        )
    )

    @group.command(name="schedule", description="Set time and channel for posting daily dua/hadith.")
    @discord.app_commands.describe(
        postType="Type of post",
        channel="Channel where the post will be sent",
        timeInput="Time (in UTC) for the daily post",
        arabic="Whether to use Arabic when possible"
    )
    @discord.app_commands.rename(timeInput='time', postType='type')
    @discord.app_commands.choices(postType=generate_choices_from_list(POST_TYPES))
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def daily_post_schedule(self, interaction: discord.Interaction, postType: str, channel: discord.TextChannel,
                                  timeInput: str, arabic: bool = False):
        if not interaction.guild:
            # this should not be reached
            await interaction.response.send_message("This command can only be used within a server.", ephemeral=True)
            return
        elif channel.permissions_for(interaction.guild.me).send_messages == False:
            await interaction.response.send_message("warning: **Insufficient permissions.**\n"
                                                    "Please grant the bot permission to send messages "
                                                    f"in <#{channel.id}>, then try again.", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)

        # Try to parse time as 12-hr or 24-hr format
        timeInput = timeInput.strip()
        accepted_formats = ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M") # 2:04 pm, 2:04pm, 2 pm, 2pm, 14:04
        parsedTime = None
        for format in accepted_formats:
            try:
                parsedTime = datetime.strptime(timeInput, format)
                break
            except ValueError:
                continue
        
        if parsedTime is None:
            # unrecognized time format
            raise ValueError
        
        formatted_time = parsedTime.strftime("%H:%M")
        handler = ServerDailyPost(interaction.guild.id, postType)
        await handler.update(channel.id, formatted_time, None, arabic)

        now = datetime.now(tz=timezone.utc)
        minute_difference = (parsedTime.hour * 60 + parsedTime.minute) - (now.hour * 60 + now.minute)

        if minute_difference <= 0:
            message = (f":white_check_mark: **Success! A random {postType.lower()} will be sent "
                       f"in <#{channel.id}> every day at {formatted_time} UTC.**\n"
                       f"The first post will be sent soon, and subsequent posts will occur daily at the chosen time.")
        else:
            message = (f":white_check_mark: **Success! A random {postType.lower()} will be sent "
                       f"in <#{channel.id}> every day at {formatted_time} UTC.**\n"
                       f"Next post in {minute_difference//60}h {minute_difference%60}m.")

        await interaction.followup.send(message)

    
    @group.command(name="stop", description="Stop daily posts")
    @discord.app_commands.describe(postType="Type of post")
    @discord.app_commands.rename(postType="type")
    @discord.app_commands.choices(postType=generate_choices_from_list(POST_TYPES))
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def daily_post_stop(self, interaction: discord.Interaction, postType: str):
        if not interaction.guild:
            # this should not be reached
            await interaction.response.send_message("This command can only be used within a server.", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)

        handler = ServerDailyPost(interaction.guild.id, postType)
        result = await handler.get()
        exists = result[0] != ''

        if exists:
            await handler.delete()
            await interaction.followup.send(f":white_check_mark: **Successfully canceled the daily {postType.lower()} "
                                            f"post schedule.** You will no longer receive daily {postType.lower()} posts.")
        else:
            await interaction.followup.send(f"**No daily {postType.lower()} post was scheduled.** There's nothing to stop.")
    
    @daily_post_schedule.error
    @daily_post_stop.error
    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.errors.CommandInvokeError) and isinstance(error.original, ValueError):
            await interaction.followup.send("warning: **Invalid time format.** Please use 24-hour format (e.g. 14:04)"
                                            "or 12-hour format (e.g. 2:04 pm).")
        else:
            await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(DailyPost(bot))
