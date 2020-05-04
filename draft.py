from discord import *
import asyncio
import json
import random
from session import DraftSession, DraftState
from errors import *

client: Client = Client()

COMMAND_PREFIX = "!"
SESSIONS = {}
CAPTAINS = {}
DRAFT_CHANNEL_ID = 698678134085779466
GUILD = 599028066991341578
NAIL_BOT_ID = 704663040682885134
# dio channel 698678134085779466
# GVD channel 696551201642119208
# dio guild 599028066991341578
# GVD guild 696542790942851132

async def main() -> None:
    global COMMANDS

    # List of commands and their associated methods
    COMMANDS = {
        "help": help_command,
        "draft": draft_command,
        "join": join_command,
        "ban": pick_command,
        "b": pick_command,
        "pick": pick_command,
        "p": pick_command,
        "exit": exit_command,
    }

    # Open secrets file and start with bot token
    token = ""
    with open("token.secret", "r") as f:
        token = f.read()

    if token != "":
        await client.start(token)

@client.event
async def on_ready() -> None:
    reset_draft_channel = False

    async for message in client.get_channel(DRAFT_CHANNEL_ID).history():
        if not message.author.bot or reset_draft_channel:
            await message.delete()
        elif message.embeds:
            if message.embeds[0].color.value == 16753152:
                await message.delete()

    print("Bot Online")

@client.event
async def on_message(message: Message) -> None:
    if message.author.id == NAIL_BOT_ID:
        await nailbot(message)

    if message.author.bot:
        return

    if not message.content:
        return

    if not message.channel.id == DRAFT_CHANNEL_ID and type(message.channel) is not DMChannel:
        return

    print(message.author, message.content)
    content = message.content;

    if message.channel.id == DRAFT_CHANNEL_ID:
        await message.delete()

    if content[0] == COMMAND_PREFIX:
        await set_channel(message)
        command = content.split(' ')[0][1:].lower()

        if command in COMMANDS.keys():
            await COMMANDS[command](message)
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
    draft_channel = client.get_channel(DRAFT_CHANNEL_ID)

    if message.author.id in CAPTAINS.keys():
        await channel.send("Sorry, you are already in a draft. Exit with `!exit`")
        return

    # creating session and adding it to active sessions
    session = DraftSession()
    session.captain1 = message.author
    CAPTAINS[session.captain1.id] = session.session_id
    SESSIONS[session.session_id] = session

    await channel.send(
        "- SETTING UP DRAFT -\nShare Session ID with Opposing Captain\t>>>\t`" + str(session.session_id) + "`"
    )
    await draft_channel.send('```' + session.session_id + '\nINIT DRAFT\n```')

    async for msg in draft_channel.history():
        if msg.content[3:9] == session.session_id:
            session.draft_message_id = msg.id
            break

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

    # put captain into the draft
    session.captain2 = message.author
    if session.captain1.id in CAPTAINS.keys():
        CAPTAINS[session.captain2.id] = session.session_id
    else:
        CAPTAINS[session.captain1.id] = session.session_id

    await start_draft(session)

async def start_draft(session: DraftSession) -> None:
    session.update_table()

    # delete history and message captains
    await delete_dm_history(session)

    await session.captain1.dm_channel.send("- STARTING DRAFT -", embed = session.table)
    await session.captain1.dm_channel.send("Phase 1: Bans (Please ban with `!ban champ`)")
    await session.captain2.dm_channel.send("- STARTING DRAFT -", embed = session.table)
    await session.captain2.dm_channel.send("Phase 1: Bans (Please ban with `!ban champ`)")

    # post draft to draft channel
    draft_channel = client.get_channel(DRAFT_CHANNEL_ID)

    async for msg in draft_channel.history():
        if msg.id == session.draft_message_id:
            await msg.edit(content = "", embed = session.table)
            break

async def pick_command(message: Message) -> None:
    channel = message.author.dm_channel
    draft_channel = client.get_channel(DRAFT_CHANNEL_ID)
    split_message = message.content.split(' ')
    command = split_message[0][1:]

    if message.author.id not in CAPTAINS.keys():
        await channel.send("Sorry, you are not currently in a draft. Try `!draft`")
        return

    session = SESSIONS[CAPTAINS[message.author.id]]
    phase = "ban" if str(session.state)[-3:].lower() == "ban" else "pick"

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
        await channel.send(" ".join(split_message[1:]) + " is not a valid champ.")
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

    session.update_table()
    session.advance_state()
    next_phase = str(session.state)[11:].lower()

    # check if draft is over
    if next_phase == "complete":
        session.table.color = 3210243

        # update dms
        await delete_dm_history(session)
        await session.captain1.send(embed = session.table)
        await session.captain2.send(embed = session.table)

        # update draft-channel
        async for msg in draft_channel.history():
            if msg.embeds:
                if msg.id == session.draft_message_id:
                    await msg.edit(embed = session.table)
                    break

        # dm nailbot if it was a naildraft
        misc_channel = client.get_channel(705836678891307089)
        champ_picks = session.get_champ_picks()
        if session.nail_draft:
            await misc_channel.send(str(session.session_id) + ',' + ','.join(champ_picks))
        else:
            await misc_channel.send('0,' + ','.join(champ_picks))


        await close_session(message)
        return

    if next_phase == "second_ban":
        next_phase = next_phase + " (Please **ban** with `!ban champ`)"
    else:
        next_phase = next_phase + " (Please **pick** with `!pick champ`)"

    await delete_dm_history(session)

    await session.captain1.send(embed = session.table)
    await session.captain1.send(next_phase)
    await session.captain2.send(embed = session.table)
    await session.captain2.send(next_phase)

    # update draft-channel table
    async for msg in draft_channel.history():
        if msg.embeds:
            if msg.id == session.draft_message_id:
                await msg.edit(embed = session.table)
                break

async def delete_dm_history(session):
    async for hist_message in session.captain1.dm_channel.history():
        if hist_message.author == client.user:
            if hist_message.content[:6] != "```css" and not hist_message.embeds:
                await hist_message.delete()
            elif hist_message.embeds:
                if hist_message.embeds[0].color.value != 3210243:
                    await hist_message.delete()

    async for hist_message in session.captain2.dm_channel.history():
        if hist_message.author == client.user:
            if hist_message.content[:6] != "```css" and not hist_message.embeds:
                await hist_message.delete()
            elif hist_message.embeds:
                if hist_message.embeds[0].color.value != 3210243:
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
        async for msg in client.get_channel(DRAFT_CHANNEL_ID).history():
            if msg.embeds:
                if msg.id == SESSIONS[CAPTAINS[message.author.id]].draft_message_id:
                    await msg.delete()
                    break

    await close_session(message)

async def nailbot(message: Message) -> None:
    if not message.channel.id == DRAFT_CHANNEL_ID:
        return

    await message.delete()

    split_message = message.content.split(' ')

    guild = client.get_guild(GUILD)
    captain1 = guild.get_member(int(split_message[1]))
    captain2 = guild.get_member(int(split_message[2]))

    session = DraftSession()
    session.session_id = split_message[0]
    session.nail_draft = True
    session.captain1 = captain1
    session.captain2 = captain2
    CAPTAINS[session.captain1.id] = session.session_id
    CAPTAINS[session.captain2.id] = session.session_id
    SESSIONS[session.session_id] = session

    if not captain1.dm_channel:
        await captain1.create_dm()
    if not captain2.dm_channel:
        await captain2.create_dm()

    draft_channel = client.get_channel(DRAFT_CHANNEL_ID)
    await draft_channel.send('```' + session.session_id + '\nINIT DRAFT\n```')

    async for msg in draft_channel.history():
        if msg.content[3:3+len(str(session.session_id))] == session.session_id:
            session.draft_message_id = msg.id
            break

    await start_draft(session)
    return

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
