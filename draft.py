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

		elif command == "exit":
			await exit_command(message)

		else:
			await channel.send("!" + command + " is not recognized as a command")

# set channel, check if a dm exists or create dm
async def set_channel(message: Message) -> None:
	if not message.author.dm_channel:
		await message.author.create_dm()

async def help_command(message: Message) -> None:
	await message.author.dm_channel.send("""```
		!help : pull of this very dialog\n
                !draft : start a draft\n
                !join [draft id] : join a draft\n
                !ban [champion] : during ban phase used to ban a champion\n
                !pick [champion] : during pick phase used to pick a champion\n
                !exit : exit the current draft you are in
	```""")
	await message.author.dm_channel.send("""
		`!help` : pull of this very dialog\n
                `!draft` : start a draft\n
                `!join [draft id]` : join a draft\n
                `!ban [champion]` : during ban phase used to ban a champion\n
                `!pick [champion]` : during pick phase used to pick a champion\n
                `!exit` : exit the current draft you are in
	""")

async def draft_command(message: Message) -> None:
	channel = message.author.dm_channel

	if message.author.id in CAPTAINS.keys():
            await channel.send("Sorry, you are already in a draft. Exit with `!exit`")

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

	if message.author.id in CAPTAINS.keys():
            await channel.send("Sorry, you are already in a draft. Exit with `!exit`")

	# check if valid session
	if split_message[1] not in SESSIONS.keys():
            await channel.send("Sorry, `" + split_message[1] + "` is not a valid draft id.")

        session = SESSIONS[split_message[1]]

        # prevent more than one person joining
        if session.captain2:
                await channel.send("Sorry, someone already joined " + split_message[1] + ".")
                return

        session.captain2 = message.author

        await start_draft(session)

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

        bans = str(session.picks[session.state][session.captain1]) + " and " + str(session.picks[session.state][session.captain2])
        next_phase = session.get_state()

        if next_phase == "first_pick" or next_phase == "third_pick":
            next_phase = next_phase + " (Please pick with `!pick champ`)"
        else:
            next_phase = next_phase + " (Please ban with `!ban champ`)"

	await session.captain1.send("Bans are " + bans + next_phase)
	await session.captain2.send("Bans are " + bans + next_phase)

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

        picks = str(session.picks[session.state][session.captain1]) + " and " + str(session.picks[session.state][session.captain2])
        next_phase = session.get_state()

        if next_phase == "second_ban":
            next_phase = next_phase + " (Please ban with `!ban champ`)"
        elif next_phase == "complete":
            next_phase = "\nDraft is now complete"
        else:
            next_phase = next_phase + " (Please pick with `!pick champ`)"

	await session.captain1.send("Picks are " + picks + next_phase)
	await session.captain2.send("Picks are " + picks + next_phase)

async def exit_command(message: Message) -> None:

    if message.author.id not in CAPTAINS.keys():
        await channel.send("You are not in a draft. Draft with `!draft`")

    print("exiting")

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
