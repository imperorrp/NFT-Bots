# discord forwarder portion py
# v1.0
# last edit: 01st Jan 2022
# -------------------------------------------------

# importing dependencies->
import yaml
import sys
import logging
import discord
import time

# init discord client->
discord_client = discord.Client()
with open("config.yml", "rb") as f:
    config = yaml.safe_load(f)

# receiving parsed_response from tel_to_disc_forwarder.py script->
message = sys.argv[1]


# forwarder function->
@discord_client.event
async def on_ready():

    print("We have logged in as {0.user}".format(discord_client))
    print("Sending Telegram Message...")

    channel_1 = discord_client.get_channel(config["discord_1_channel"])
    # channel_2 = discord_client.get_channel(config["discord_2_channel"])
    # channel_3 = discord_client.get_channel(config["discord_3_channel"])
    # channel_4 = discord_client.get_channel(config["discord_4_channel"])
    try:
        # discord_client.loop.create_task(channel_1.send(message))
        print(f"Message sent to discord successfully.")
        await channel_1.send(message)
        # add 'await channel_2.send(message)', etc. to forward to more than one Discord channel
    except:
        print(f"Error: Unable to send message {message} to discord")

    quit()


discord_client.run(config["discord_bot_token"])
