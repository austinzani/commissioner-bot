import os
import discord

from commissioner_bot.sleeper import Sleeper

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
league_id = os.environ['LEAGUE_ID']

# intents = discord.Intents.default()
# intents.message_content = True
# intents.members = True
# intents.presences = True
# client = discord.Client(intents=intents)
#
# print(TOKEN)
# print("Starting bot...")
#
#
# @client.event
# async def on_ready():
#     guild = discord.utils.get(client.guilds, name=GUILD)
#     if guild is not None:
#         print(guild.channels)
#         channel_id = None
#         for channel in guild.channels:
#             if channel.name == "general":
#                 channel_id = channel.id
#                 break
#         if channel_id is not None:
#             target_channel = guild.get_channel(channel_id)
#             if target_channel is not None:
#                 # Send the message
#                 message = await target_channel.send("This is a message with reactions.")
#
#                 # Add reactions to the message
#                 reactions = ['✅', '❌']
#                 for emoji in reactions:
#                     await message.add_reaction(emoji)
#
#
# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return message.content
#
#
# @client.event
# async def on_reaction_add(reaction, user):
#     print(reaction.message.reactions)
#     for reaction_emoji in reaction.message.reactions:
#         print(reaction_emoji.users)
#     # Dictionary to keep track of users who have reacted
#     reacted_users = {}
#     if user != client.user:
#         # Check if the reaction is on the message sent by the bot
#         if reaction.message.author == client.user:
#             # Check if the user has already reacted
#             if user.id not in reacted_users:
#                 reacted_users[user.id] = True
#             else:
#                 # Remove the extra reaction
#                 await reaction.remove(user)
#                 return
#
# client.run(TOKEN)
Sleeper(league_id).process_transactions(9)
