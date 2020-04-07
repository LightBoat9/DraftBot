from discord import *
import asyncio
import json
import random
from session import DraftSession, DraftState
from errors import *
from prettytable import PrettyTable

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

    async for message in client.get_channel(696551201642119208).history():
        await message.delete()

@client.event
async def on_message(message: Message) -> None:
    # print(message.author, message.content)
    if message.author.bot:
        return

    if not message.channel.id == 696551201642119208 and message.channel is DMChannel:
        return

    if message.channel.id == 696551201642119208:
        await message.delete()

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
            await pick_command(message)

        elif command == "pick":
            await pick_command(message)

        elif command == "exit":
            await exit_command(message)

        else:
            channel = message.author.dm_channel
            await channel.send("!" + command + " is not recognized as a command")

# set channel, check if a dm exists or create dm
async def set_channel(message: Message) -> None:
    if not message.author.dm_channel:
        await message.author.create_dm()

async def help_command(message: Message) -> None:
    await message.author.dm_channel.send(
        "`!help` : pull up this very dialog\n" \
        "`!draft` : start a draft\n" \
        "`!join [draft id]` : join a draft\n" \
        "`!ban [champion]` : during ban phase used to ban a champion\n" \
        "`!pick [champion]` : during pick phase used to pick a champion\n" \
        "`!exit` : exit the current draft you are in"
    )

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
        return

    session = SESSIONS[split_message[1]]

    # prevent more than one person joining
    if session.captain2:
        await channel.send("Sorry, someone already joined " + split_message[1] + ".")
        return

    session.captain2 = message.author

    await start_draft(session)

async def start_draft(session: DraftSession) -> None:
    session.table.field_names = ["Captains", session.captain1.display_name, session.captain2.display_name]
    session.table.add_row(["Ban", "...", "..."])
    session.table.add_row(["Pick", "...", "..."])
    session.table.add_row(["Pick", "...", "..."])
    session.table.add_row(["Ban", "...", "..."])
    session.table.add_row(["Pick", "...", "..."])

    await session.captain1.dm_channel.send(
        "- STARTING DRAFT -\n```\n" + str(session.table) +
        "```\nPhase 1: Bans (Please ban with `!ban champ`)"
    )
    await session.captain2.dm_channel.send(
        "- STARTING DRAFT -\n```\n" + str(session.table) +
        "```\nPhase 1: Bans (Please ban with `!ban champ`)"
    )

    CAPTAINS[session.captain1.id] = session.session_id
    CAPTAINS[session.captain2.id] = session.session_id

async def pick_command(message: Message) -> None:
    channel = message.author.dm_channel
    split_message = message.content.split(' ')
    command = split_message[0][1:]

    if message.author.id not in CAPTAINS.keys():
        await channel.send("Sorry, you are not currently in a draft. Try `!draft`")
        return

    session = SESSIONS[CAPTAINS[message.author.id]]
    phase = "ban" if str(session.state)[-3:] == "BAN" else "pick"

    # check if user input the correct command
    if phase != command:
        if phase == "ban":
            await channel.send("Sorry, you are not currently picking. Try `!ban champ`")
        else:
            await channel.send("Sorry, you are not currently banning. Try `!pick champ`")
        return

    # pick
    try:
        session.pick(message.author.id, " ".join(split_message[1:]))
    except NonexistantChampion:
        await channel.send(" ".join(split_message[1:]) + " is not a valid champ, Luke.")
        return
    except BannedChampion:
        await channel.send(" ".join(split_message[1:]) + " is banned by the opposing captain")
        return
    except DuplicateChampion:
        await channel.send(" ".join(split_message[1:]) + " is already picked")
        return
    except DuplicateBan:
        await channel.send(" ".join(split_message[1:]) + " is already banned")
        return
    except LateBan:
        await channel.send(" ".join(split_message[1:]) + " is picked by the opposing captain")
        return

    if not session.check_state():
        await channel.send("Waiting for opposing captain's " + phase)
        return

    pick1 = str(session.picks[session.state][session.captain1.id]).capitalize()
    pick2 = str(session.picks[session.state][session.captain2.id]).capitalize()

    if session.state == DraftState.FIRST_BAN:
        for i in range(4, -1, -1):
            session.table.del_row(i)
        session.table.add_row([phase.capitalize(), pick1, pick2])
        session.table.add_row(["Pick", "...", "..."])
        session.table.add_row(["Pick", "...", "..."])
        session.table.add_row(["Ban", "...", "..."])
        session.table.add_row(["Pick", "...", "..."])
    elif session.state == DraftState.FIRST_PICK:
        for i in range(4, 0, -1):
            session.table.del_row(i)
        session.table.add_row([phase.capitalize(), pick1, pick2])
        session.table.add_row(["Pick", "...", "..."])
        session.table.add_row(["Ban", "...", "..."])
        session.table.add_row(["Pick", "...", "..."])
    elif session.state == DraftState.SECOND_PICK:
        for i in range(4, 1, -1):
            session.table.del_row(i)
        session.table.add_row([phase.capitalize(), pick1, pick2])
        session.table.add_row(["Ban", "...", "..."])
        session.table.add_row(["Pick", "...", "..."])
    elif session.state == DraftState.SECOND_BAN:
        session.table.del_row(4)
        session.table.del_row(3)
        session.table.add_row([phase.capitalize(), pick1, pick2])
        session.table.add_row(["Pick", "...", "..."])
    else session.state == DraftState.THIRD_PICK:
        session.table.del_row(4)
        session.table.add_row([phase.capitalize(), pick1, pick2])

    session.advance_state()
    next_phase = str(session.state)[11:].lower()

    # check if draft is over
    if next_phase == "complete":
        await session.captain1.send("```\n" + str(session.table) + "```\n" + "Draft is now complete")
        await session.captain2.send("```\n" + str(session.table) + "```\n" + "Draft is now complete")
        close_session(session)
        return

    if next_phase == "second_ban":
        next_phase = next_phase + " (Please ban with `!ban champ`)"
    else:
        next_phase = next_phase + " (Please pick with `!pick champ`)"

    await session.captain1.send("```\n" + str(session.table) + "```\n" + next_phase)
    await session.captain2.send("```\n" + str(session.table) + "```\n" + next_phase)

def close_session(session: DraftSession) -> None:
    del SESSIONS[CAPTAINS[session.captain1.id]]
    del CAPTAINS[session.captain1.id]
    pass

async def exit_command(message: Message) -> None:

    if message.author.id not in CAPTAINS.keys():
        await channel.send("You are not in a draft. Draft with `!draft`")

    print("exiting")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
