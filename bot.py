import os
import discord
import asyncio

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
client = discord.Client(intents=intents)

db = MongoDatabase(os.environ['MONGODB_CONNECTION_URL'], 'commissioner_bot')
reaction_collection = MongoCollection(db, 'reactions')


@client.event
async def on_ready():
    await main()


@client.event
async def on_message(message):
    if message.author == client.user:
        return message.content


@client.event
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


async def main():
    await Sleeper(league_id, client).process_transactions(7)


client.run(TOKEN)