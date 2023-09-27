import asyncio
import os
import time
import discord
from discord.ext import commands
from commissioner_bot.discord_bot import Discord


from commissioner_bot.mongodb import reaction_collection, guild_preferences_collection, dm_collection
from commissioner_bot.sleeper import Sleeper

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
league_id = os.environ['LEAGUE_ID']
options = ["✅", "❌"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)
players_last_updated = time.time()

@bot.event
async def on_ready():
    await bot.tree.sync()
    schedule_tasks()
    print('Bot is ready')


@bot.tree.command(name='setup', description='Set Up the bot to message for your league')
async def setup(interaction: discord.Interaction) -> None:
    if interaction.guild.owner.id == interaction.user.id:
        guild_preferences = guild_preferences_collection.get({'guild_id': interaction.guild.id})
        # Check if the guild has already been set up
        if guild_preferences and guild_preferences['complete']:
            await interaction.response.send_message("This server has already been set up", ephemeral=True)
            return

        dm_history = dm_collection.get({'user_id': interaction.user.id})
        interaction_timestamp = interaction.created_at.timestamp()
        # If the user has never sent a message, send a setup message
        if dm_history is None:
            dm_collection.insert({
                'user_id': interaction.user.id,
                'message_time': interaction_timestamp,
                'guild_id': interaction.guild.id
            })
            await interaction.user.send("What is your sleeper username?")
            await interaction.response.send_message("I sent you a direct message with next steps", ephemeral=True)
            return

        # Compare the time stamp of the last message to now
        last_message_time = dm_history['message_time']
        time_difference = interaction_timestamp - last_message_time
        print(time_difference)
        # If the last message was less than 15 minutes ago, send a message saying that they already have a setup in process
        if time_difference < 900:
            embed = discord.Embed(title="You already have a setup in process", description="Check your direct messages for next steps", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # If the last message was more than 15 minutes ago, send a setup message
        else:
            dm_collection.delete({'user_id': interaction.user.id})
            dm_collection.insert({
                'user_id': interaction.user.id,
                'message_time': interaction_timestamp,
                'guild_id': interaction.guild.id
            })
            await interaction.response.send_message("I sent you a direct message with next steps", ephemeral=True)
            await interaction.user.send("What is your sleeper username?")
            return
    else:
        await interaction.response.send_message("Only server owners can set up a league", ephemeral=True)


@bot.event
async def on_guild_join(guild: discord.Guild):
    await guild.owner.send()


@bot.event
async def on_reaction_add(reaction, user):
    print(reaction, user)
    # Ignore if the reaction is added by a bot or a message created by a user
    if user.bot or reaction.message.author.bot is False:
        return

    # Check if the reaction is on a poll message
    message_id = reaction.message.id
    guild_id = reaction.message.guild.id
    reaction_collection.insert({
        'guild_id': guild_id,
        'message_id': message_id,
        'user_id': user.id,
        'reaction': reaction.emoji
    })
    reactions = reaction_collection.get_all({
        'guild_id': guild_id,
        'message_id': message_id,
        'user_id': user.id
    })
    if len(reactions) > 1:
        for item in reactions:
            if item['reaction'] != reaction.emoji:
                await reaction.message.remove_reaction(item['reaction'], user)
                reaction_collection.delete({
                    'guild_id': guild_id,
                    'message_id': message_id,
                    'user_id': user.id,
                    'reaction': item['reaction']
                })


# Callback for poll time limit select buttons
async def poll_time_callback(interaction: discord.Interaction, button: discord.ui.Button):
    dm_history = dm_collection.get({'user_id': interaction.user.id})
    if dm_history is None:
        return
    guild_id = dm_history['guild_id']
    guild_preferences_collection.update({'guild_id': guild_id}, {'$set': {'poll_time': int(button.custom_id), 'complete': True}})
    message_string = f"You selected {button.label} for your poll time limit!" if button.label != "NONE" else "You selected no time limit for your polls!"
    await interaction.response.edit_message(content=message_string, view=None)
    await interaction.user.send(content="Your server is now set up!")


# Callback for Trade channel select buttons
async def trade_channel_callback(interaction: discord.Interaction, button: discord.ui.Button):
    dm_history = dm_collection.get({'user_id': interaction.user.id})
    if dm_history is None:
        return
    guild_id = dm_history['guild_id']
    guild_preferences_collection.update({'guild_id': guild_id}, {'$set': {'trades_channel_id': button.custom_id}})
    await interaction.response.edit_message(content=f"You selected {button.label} channel to send Trade alerts to!", view=None)
    view = discord.ui.View()
    time_options = [6, 12, 24, 0]
    for option in time_options:
        time_string = f"{option} HOURS" if option > 0 else "NONE"
        button = discord.ui.Button(label=time_string, custom_id=option.__str__())
        button.callback = lambda i, b=button: poll_time_callback(i, b)
        view.add_item(button)
    await interaction.user.send(content="How long do you want to allow the veto polls to last?", view=view)


# Callback for Free Agency channel select buttons
async def fa_channel_callback(interaction: discord.Interaction, button: discord.ui.Button):
    dm_history = dm_collection.get({'user_id': interaction.user.id})
    if dm_history is None:
        return
    guild_id = dm_history['guild_id']
    guild_preferences_collection.update({'guild_id': guild_id}, {'$set': {'fa_channel_id': button.custom_id}})
    await interaction.response.edit_message(content=f"You selected {button.label} channel to send Free Agency alerts to!", view=None)
    guild = await bot.fetch_guild(guild_id)
    if guild is not None:
        channels = await guild.fetch_channels()
        text_channels = [channel for channel in channels if isinstance(channel, discord.TextChannel)]
        view = discord.ui.View()
        for channel in text_channels:
            button = discord.ui.Button(label=channel.name, custom_id=channel.id.__str__())
            button.callback = lambda i, b=button: trade_channel_callback(i, b)
            view.add_item(button)
        await interaction.user.send(content="What channel would you like to use for trades?", view=view)


# Callback for league select buttons
async def league_name_callback(interaction: discord.Interaction, button: discord.ui.Button):
    dm_history = dm_collection.get({'user_id': interaction.user.id})
    if dm_history is None:
        return
    guild_id = dm_history['guild_id']
    guild_preferences_collection.update({'guild_id': guild_id}, {'$set': {'league_id': button.custom_id, 'league_name': button.label}})
    await interaction.response.edit_message(content=f"You selected {button.label}!", view=None)
    guild = await bot.fetch_guild(guild_id)
    if guild is not None:
        # Get all text channels in the guild
        channels = await guild.fetch_channels()
        text_channels = [channel for channel in channels if isinstance(channel, discord.TextChannel)]
        view = discord.ui.View()
        for channel in text_channels:
            button = discord.ui.Button(label=channel.name, custom_id=channel.id.__str__())
            button.callback = lambda i, b=button: fa_channel_callback(i, b)
            view.add_item(button)
        await interaction.user.send(content="What channel would you like to use for free agency?", view=view)


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user:
        if isinstance(message.channel, discord.DMChannel):
            message_content = message.content
            if message_content.lower() == "restart":
                dm_history = dm_collection.get({'user_id': message.author.id})
                if dm_history is None:
                    return
                guild_id = dm_history['guild_id']
                guild_preferences = guild_preferences_collection.get({'guild_id': guild_id})
                if guild_preferences and guild_preferences['complete']:
                    await message.author.send(content="Your server has already been set up")
                    return
                guild_preferences_collection.delete({'guild_id': guild_id})
                await message.author.send(content="What is your sleeper username?")
                return
            dm_history = dm_collection.get({'user_id': message.author.id})
            if dm_history is None:
                return
            guild_id = dm_history['guild_id']
            # Guild preferences should contain the sleeper username, league id, channel id for free agency, channel id for trades,
            # a poll time length (in minutes), a timestamp for the last time the managers were updated, and a boolean for if the setup is complete
            guild_preferences = guild_preferences_collection.get({'guild_id': guild_id})
            if guild_preferences:
                if guild_preferences['complete']:
                    await message.author.send(content="Your server has already been set up")
                    return
                await message.author.send(content="Your server setup has already started. Please finish or message `restart` if you want to start from the beginning.")
                return
            sleeper_username = message_content
            success, sleeper_user = Sleeper.get_user_from_username(sleeper_username)

            # Verify that the sleeper user was retrieved successfully
            if not success or sleeper_user is None:
                await message.author.send(content="We couldn't find that username. Please try again.")
                return
            sleeper_user_id = sleeper_user['user_id']
            success, nfl_state = Sleeper.get_nfl_state()

            # Verify that the NFL state was retrieved successfully
            if not success or nfl_state is None:
                await message.author.send(content="The server had an issue. Please try again.")
                return
            year = nfl_state['season']
            success, leagues = Sleeper.get_leagues_from_user(sleeper_user_id, year)
            if not success or not leagues or len(leagues) == 0:
                await message.author.send(content="We couldn't find any leagues for that username. Please try again.")
                return

            view = discord.ui.View()
            for league in leagues:
                button = discord.ui.Button(label=league['name'], custom_id=league['league_id'])
                button.callback = lambda i, b=button: league_name_callback(i, b)
                view.add_item(button)
            guild_preferences_collection.insert({
                'guild_id': guild_id,
                'sleeper_username': sleeper_username,
                'sleeper_user_id': sleeper_user_id,
                'league_id': None,
                'league_name': None,
                'fa_channel_id': None,
                'trades_channel_id': None,
                'poll_time': None,
                'updated_managers': None,
                'complete': False
            })
            await message.author.send(content="What league would you like to set up?", view=view)


async def message_guilds():
    succeeded, nfl_state = Sleeper.get_nfl_state()
    if not succeeded or nfl_state is None:
        print("Could not get NFL state")
        return
    guilds = guild_preferences_collection.get_all({'complete': True})
    now = int(time.time())
    for guild in guilds:
        discord_class = Discord(bot=bot, guild=guild['guild_id'], trade_channel=guild['trades_channel_id'], free_agency_channel=guild['fa_channel_id'])
        sleeper_bot = Sleeper(league_id=guild['league_id'], discord=discord_class)
        last_updated = guild.get('updated_managers')
        time_since_last_update = now - last_updated if last_updated is not None else now
        if last_updated is None or time_since_last_update >= 604800:
            sleeper_bot.update_league_managers()
            guild_preferences_collection.update({'guild_id': guild['guild_id']}, {'$set': {'updated_managers': now}})

        await sleeper_bot.process_transactions(nfl_state['week'])

    global players_last_updated
    if players_last_updated is None or now - players_last_updated >= 604800:
        # Update the players in the database which does not need any discord interaction or guild data
        Sleeper.update_players()
        players_last_updated = now


def schedule_tasks():
    asyncio.ensure_future(message_guilds())
    bot.loop.call_later(60, schedule_tasks)


bot.run(TOKEN)
