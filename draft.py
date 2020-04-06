from discord import *
import asyncio
import json
import random
from session import DraftSession

client: Client = Client()

# Global Variables
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
	split_message = message.content.split(' ')

	if message.content == COMMAND_PREFIX + "help":
		channel = await set_channel(message)

		await channel.send(
			"```!help : pull of this very dialog\n!draft : start a draft\n!join [session id] : join an existing session```"
		)

	if message.content == COMMAND_PREFIX + "draft":
		channel = await set_channel(message)

		# creating session and adding it to active sessions
		session = DraftSession()
		SESSIONS[str(session.session_id)] = session
		await channel.send(
			"- SETTING UP DRAFT -\nShare Session ID with Opposing Captian: `" + str(session.session_id) + "`"
		)

	if split_message[0] == COMMAND_PREFIX + "join":
		channel = await set_channel(message)

		# check if valid session
		if split_message[1] in SESSIONS.keys():
			await channel.send("nice")
		else:
			await channel.send("not a valid session id")

# set channel, check if a dm exists or create dm
async def set_channel(M):
	if not M.author.dm_channel:
		await M.author.create_dm()
	return M.author.dm_channel

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
