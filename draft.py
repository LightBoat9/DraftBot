from discord import *
import asyncio
import json
import random

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
	print(message.author, message.content)

	if message.content == "Start Draft":

		# set channel, check if a dm exists or create dm
		channel = message.author.dm_channel
		if not channel:
			await message.author.create_dm()
			channel = message.author.dm_channel

		await channel.send("Starting Draft")

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())