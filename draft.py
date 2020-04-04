from discord import *
import asyncio
import json

client: Client = Client()

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
    channel = message.channel

    print(message.author, message.content)

    if message.content == "test":
        await channel.send("Response to test")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())