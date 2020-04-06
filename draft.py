from discord import *
import asyncio
import json
import random
from session import DraftSession

client: Client = Client()

COMMAND_PREFIX = "!"
SESSIONS = {}

async def main() -> None:
	# Open secrets file and start with bot token
	token = ""
	with open("token.secret", "r") as f:
		token = f.read()

	if token != "":
		await client.start(token)

@client.event
async def on_ready() -> None:
	print("Bot Online")

@client.event
async def on_message(message: Message) -> None:
	# print(message.author, message.content)
	if message.author.bot:
		return

	if message.content[0] == COMMAND_PREFIX:
		command = message.content.split(' ')[0][1:]

		if command == "help":
			await help_command(message)

		elif command == "draft":
			await draft_command(message)

		elif command == "join":
			await join_command(message)

		else:
			channel = await set_channel(message)
			await channel.send("!" + command + " is not recognized as a command")

# set channel, check if a dm exists or create dm
async def set_channel(message):
	if not message.author.dm_channel:
		await message.author.create_dm()
	return message.author.dm_channel

async def help_command(message):
	channel = await set_channel(message)

	await channel.send(
		"```!help : pull of this very dialog\n!draft : start a draft\n!join [session id] : join an existing session```"
	)

async def draft_command(message):
	channel = await set_channel(message)

	# creating session and adding it to active sessions
	session = DraftSession()
	SESSIONS[str(session.session_id)] = session

	await channel.send(
		"- SETTING UP DRAFT -\nShare Session ID with Opposing Captian: `" + str(session.session_id) + "`"
	)

async def join_command(message):
	channel = await set_channel(message)
	split_message = message.content.split(' ')

	# check if valid session
	if split_message[1] in SESSIONS.keys():
		await channel.send("nice")
	else:
		await channel.send("not a valid session id")

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
