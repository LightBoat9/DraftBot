from discord import *
import asyncio
import json
import random
from session import DraftSession

client: Client = Client()

COMMAND_PREFIX = "!"
SESSIONS = {}
CAPTAINS = {}

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
		await set_channel(message)
		command = message.content.split(' ')[0][1:]

		if command == "help":
			await help_command(message)

		elif command == "draft":
			await draft_command(message)

		elif command == "join":
			await join_command(message)

		elif command == "ban":
			await ban_command(message)

		elif command == "pick":
			await pick_command(message)

		else:
			await channel.send("!" + command + " is not recognized as a command")

# set channel, check if a dm exists or create dm
async def set_channel(message: Message) -> None:
	if not message.author.dm_channel:
		await message.author.create_dm()

async def help_command(message: Message) -> None:
	await message.author.dm_channel.send(
		"```!help : pull of this very dialog\n!draft : start a draft\n!join [session id] : join a draft```"
	)

async def draft_command(message: Message) -> None:
	channel = message.author.dm_channel

	# creating session and adding it to active sessions
	session = DraftSession()
	SESSIONS[str(session.session_id)] = session

	await channel.send(
		"- SETTING UP DRAFT -\nShare Session ID with Opposing Captain\t>>>\t`" + str(session.session_id) + "`"
	)

	session.captain1 = message.author

async def join_command(message: Message) -> None:
	channel = message.author.dm_channel

	split_message = message.content.split(' ')

	# check if valid session
	if split_message[1] in SESSIONS.keys():
		session = SESSIONS[split_message[1]]

		# prevent more than one person joining
		if session.captain2:
			await channel.send("Sorry, someone already joined " + split_message[1] + ".")
			return

		session.captain2 = message.author

		await start_draft(session)
	else:
		await channel.send(split_message[1] + " is not a valid session id.")

async def start_draft(session: DraftSession) -> None:
	await session.captain1.dm_channel.send("- STARTING DRAFT -\nPhase 1: Bans\nPlease ban with !ban champ")
	await session.captain2.dm_channel.send("- STARTING DRAFT -\nPhase 1: Bans\nPlease ban with !ban champ")

	CAPTAINS[session.captain1] = session.session_id
	CAPTAINS[session.captain2] = session.session_id

async def ban_command(message: Message) -> None:
	channel = message.author.dm_channel

	if message.author not in CAPTAINS.keys():
		await channel.send("Sorry, you are not currently in a draft")
		return

	session = SESSIONS[CAPTAINS[message.author]]

	await channel.send(str(session.captain1) + str(session.captain2))

async def pick_command(message: Message) -> None:
	channel = message.author.dm_channel
	print("banning")

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
