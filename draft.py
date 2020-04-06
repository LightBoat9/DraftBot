from discord import *
import asyncio
import json
import random
from session import DraftSession, DraftState

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
	await session.captain1.dm_channel.send(
		"- STARTING DRAFT -\nCaptains: " +
		"you" + " and " + session.captain2.display_name +
		"\nPhase 1: Bans (Please ban with `!ban champ`)"
	)
	await session.captain2.dm_channel.send(
		"- STARTING DRAFT -\nCaptains: " +
		session.captain1.display_name + " and " + "you" +
		"\nPhase 1: Bans (Please ban with `!ban champ`)"
	)

	CAPTAINS[session.captain1.id] = session.session_id
	CAPTAINS[session.captain2.id] = session.session_id

async def ban_command(message: Message) -> None:
	channel = message.author.dm_channel
	split_message = message.content.split(' ')

	if message.author.id not in CAPTAINS.keys():
		await channel.send("Sorry, you are not currently in a draft. Try `!draft`")
		return

	session = SESSIONS[CAPTAINS[message.author.id]]

	if not session.check_captains:
		await channel.send(
			"Sorry, the opposing captain has not joined yet. Send them the Session ID\t>>>\t`" + str(session.session_id) + "`"
		)
		return

	if session.state != DraftState.FIRST_BAN and session.state != DraftState.SECOND_BAN:
		await channel.send("Sorry, you are not currently banning. Try `!pick champ`")
		return

	session.pick(message.author.id, split_message[1])

	if not session.check_state():
		await channel.send("Waiting for opposing captain ban.")
		return

	await session.captain1.send(
		"Bans are " + str(session.picks[session.state]) +
		"\nPhase " + str(session.state) + ": " +
		(
			"Picks (Please pick with `!pick champ`)" if
			session.state == DraftState.FIRST_PICK or session.state == DraftState.THIRD_PICK else
			"Bans (Please ban with `!ban champ`)"
		)
	)
	await session.captain2.send(
		"Bans are " + str(session.picks[session.state]) +
		"\nPhase " + str(session.state) + ": " +
		(
			"Picks (Please pick with `!pick champ`)" if
			session.state == DraftState.FIRST_PICK or session.state == DraftState.THIRD_PICK else
			"Bans (Please ban with `!ban champ`)"
		)
	)

async def pick_command(message: Message) -> None:
	channel = message.author.dm_channel
	split_message = message.content.split(' ')

	if message.author.id not in CAPTAINS.keys():
		await channel.send("Sorry, you are not currently in a draft. Try `!draft`")
		return

	session = SESSIONS[CAPTAINS[message.author.id]]

	if session.state != DraftState.FIRST_PICK and session.state != DraftState.SECOND_PICK and session.state != DraftState.THIRD_PICK:
		await channel.send("Sorry, you are not currently picking. Try `!ban champ`")
		return

	session.pick(message.author.id, split_message[1])

	if not session.check_state():
		await channel.send("Waiting for opposing captain pick.")
		return

	await session.captain1.send(
		"Picks are " + str(session.picks[session.state]) +
		"\nPhase " + str(session.state) + ": " +
		(
			"Bans (Please ban with `!ban champ`)" if
			session.state == DraftState.SECOND_BAN else
			"Picks (Please Picks with `!Picks champ`)"
		)
	)
	await session.captain2.send(
		"Picks are " + str(session.picks[session.state]) +
		"\nPhase " + str(session.state) + ": " +
		(
			"Bans (Please ban with `!ban champ`)" if
			session.state == DraftState.SECOND_BAN else
			"Picks (Please Picks with `!Picks champ`)"
		)
	)

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
