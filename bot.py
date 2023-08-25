import os
import discord
from discord.ext import commands
from datetime import datetime

from commissioner_bot.mongodb import MongoDatabase, MongoCollection
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

db = MongoDatabase(os.environ['MONGODB_CONNECTION_URL'], 'commissioner_bot')
reaction_collection = MongoCollection(db, 'reactions')
guild_preferences_collection = MongoCollection(db, 'guild_preferences')
dm_collection = MongoCollection(db, 'direct_messages')


@bot.event
async def on_ready():
    await bot.tree.sync()
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


@bot.event
async def on_message(message: discord.Message):
    if message.author != bot.user:
        if isinstance(message.channel, discord.DMChannel):
            dm_history = dm_collection.get({'user_id': message.author.id})
            if dm_history is None:
                return
            guild_id = dm_history['guild_id']
            guild_preferences = guild_preferences_collection.get({'guild_id': guild_id})
            if guild_preferences is None:
                sleeper_username = message.content
                success, sleeper_user = Sleeper.get_user_from_username(sleeper_username)
                if success and sleeper_user is not None:
                    sleeper_user_id = sleeper_user['user_id']
                    success, nfl_state = Sleeper.get_nfl_state()
                    if success and nfl_state is not None:
                        year = nfl_state['season']
                        success, leagues = Sleeper.get_leagues_from_user(sleeper_user_id, year)
                        if success and leagues and len(leagues) > 0:
                            view = discord.ui.View()
                            for league in leagues:
                                buttons = discord.ui.Button(label=league['name'], custom_id=league['league_id'])
                                view.add_item(buttons)
                            await message.author.send(content="What league would you like to set up?", view=view)


async def main():
    await Sleeper(league_id, bot).process_transactions(7)


bot.run(TOKEN)