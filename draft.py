from discord import *
import asyncio
import json
import random
from session import DraftSession, DraftState
from errors import *
from prettytable import PrettyTable
#from art import text2art

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
    reset_draft_channel = False

    async for message in client.get_channel(696551201642119208).history():
        if not message.author.bot or reset_draft_channel:
            await message.delete()
        elif message.content[:6] == "```fix":
            await message.delete()

    print("Bot Online")

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
        "`!join draft id` : join a draft\n" \
        "`!ban champ` : during ban phase used to ban a champion\n" \
        "`!pick champ` : during pick phase used to pick a champion\n" \
        "`!exit` : exit the current draft you are in"
    )

async def draft_command(message: Message) -> None:
    channel = message.author.dm_channel

    if message.author.id in CAPTAINS.keys():
        await channel.send("Sorry, you are already in a draft. Exit with `!exit`")
        return

    # creating session and adding it to active sessions
    session = DraftSession()
    CAPTAINS[message.author.id] = session.session_id
    SESSIONS[session.session_id] = session

    session.captain1 = message.author
    
    await delete_dm_history(session)

    await channel.send(
        "- SETTING UP DRAFT -\nShare Session ID with Opposing Captain\t>>>\t`" + str(session.session_id) + "`"
    )

async def join_command(message: Message) -> None:
    channel = message.author.dm_channel
    split_message = message.content.split(' ')

    # in the future discern from you existing in another draft and you joining your own draft
    if message.author.id in CAPTAINS.keys():
        await channel.send("Sorry, you are already in a draft. Exit with `!exit`")
        return

    if len(split_message) == 1:
        await channel.send("You did not specify a draft id. Try `!join [draft id]`")
        return

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

    # delete history and message captains
    await delete_dm_history(session)
    await session.captain1.dm_channel.send("- STARTING DRAFT -")
    await session.captain1.dm_channel.send("```fix\n" + str(session.table) + "```\nPhase 1: Bans (Please ban with `!ban champ`)")
    await session.captain2.dm_channel.send("- STARTING DRAFT -")
    await session.captain2.dm_channel.send("```fix\n" + str(session.table) + "```\nPhase 1: Bans (Please ban with `!ban champ`)")

    # delete unfinished drafts and post draft
    server_channel = client.get_channel(696551201642119208)
    await server_channel.send("```fix\n" + session.session_id + "\n" + str(session.table) + "```")

    if session.captain1.id in CAPTAINS.keys():
        CAPTAINS[session.captain2.id] = session.session_id
    else:
        CAPTAINS[session.captain1.id] = session.session_id

async def pick_command(message: Message) -> None:
    channel = message.author.dm_channel
    draft_channel = client.get_channel(696551201642119208)
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

    if len(split_message) == 1:
        await channel.send("You did not specify a champ. Try `!" + phase + " champ`")
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
    else:
        session.table.del_row(4)
        session.table.add_row([phase.capitalize(), pick1, pick2])

    session.advance_state()
    next_phase = str(session.state)[11:].lower()

    # check if draft is over
    if next_phase == "complete":
        await delete_dm_history(session)
        await session.captain1.send("```css\n" + str(session.table) + "```")
        await session.captain2.send("```css\n" + str(session.table) + "```")

        # update draft-channel table
        async for msg in draft_channel.history():
            if msg.content[7:13] == session.session_id:
                await msg.edit(content="```css\n" + str(session.table) + "```")
        await close_session(message)
        return

    if next_phase == "second_ban":
        next_phase = next_phase + " (Please **ban** with `!ban champ`)"
    else:
        next_phase = next_phase + " (Please **pick** with `!pick champ`)"

    await delete_dm_history(session)

    await session.captain1.send("```fix\n" + str(session.table) + "```\n" + next_phase)
    await session.captain2.send("```fix\n" + str(session.table) + "```\n" + next_phase)

    # update draft-channel table
    async for msg in draft_channel.history():
        if msg.content[7:13] == session.session_id:
            await msg.edit(content="```fix\n" + session.session_id + "\n"+ str(session.table) + "```")

async def delete_dm_history(session):
    if session.captain1:
        if not session.captain1.dm_channel:
            await session.captain2.create_dm()

        async for hist_message in session.captain1.dm_channel.history():
            if hist_message.author == client.user and hist_message.content[:6] != "```css":
                await hist_message.delete()

    if session.captain2:
        if not session.captain2.dm_channel:
            await session.captain2.create_dm()

        async for hist_message in session.captain2.dm_channel.history():
            if hist_message.author == client.user and hist_message.content[:6] != "```css":
                await hist_message.delete()

async def close_session(message: Message) -> None:
    session = SESSIONS[CAPTAINS[message.author.id]]
    cap1 = None
    cap2 = None

    await delete_dm_history(session)

    # remove other player
    if session.captain1:
        cap1 = session.captain1
    if session.captain2:
        cap2 = session.captain2

    if CAPTAINS[message.author.id] in SESSIONS.keys():
        del SESSIONS[CAPTAINS[message.author.id]]

    if cap1:
        await cap1.dm_channel.send("Exiting draft.")
        del CAPTAINS[cap1.id]
    if cap2:
        await cap2.dm_channel.send("Exiting draft.")
        del CAPTAINS[cap2.id]

async def exit_command(message: Message) -> None:
    channel = message.author.dm_channel

    if message.author.id not in CAPTAINS.keys():
        await channel.send("You are not in a draft. Draft with `!draft`")
        return

    # delete draft table from draft-channel if session exists
    if CAPTAINS[message.author.id] in SESSIONS.keys():
        async for msg in client.get_channel(696551201642119208).history():
            if msg.content[7:13] == SESSIONS[CAPTAINS[message.author.id]].session_id:
                await msg.delete()
                break

    await close_session(message)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
