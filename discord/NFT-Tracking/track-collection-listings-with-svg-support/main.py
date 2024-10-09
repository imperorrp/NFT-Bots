# bot for opensea collection listings updates to discord
# format 1, with svg (forcing hard passes upon svg->png conversion exceptions)
# also using svg images not from ipfs pinata, but from https://d23fdhqc1jb9no.cloudfront.net/_Realms/8.svg, etc.
# to retrieve SVGs for png conversion (currently for lootrealms specifically- svg images from ipfs pinata (linked to somewhere in the opensea api response))

# (v2.0s)--------------------------------------------------------------------------------------
# (11th April 2022)

# Importing dependencies->
import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks
import time
from datetime import datetime, timezone
import requests
from web3 import Web3
import json
import dateutil.parser
from datetime import date, datetime

# dependencies for svg->png conversion
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import requests

# Bot set-up->
client = commands.Bot(command_prefix="!")
TOKEN = open("opseabot_token.txt", "r").readline()
# Make sure opseabot_token.txt and config.json are in same folder
f = open(
    "config.json",
)
cfg = json.load(f)


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))


# loading some past asset event (listings) IDs from json->
f3 = open(
    "txn_list.json",
)
id_list = json.load(f3)
f3.close()
# if empty, latest check will add latest listing event's id^


def load_jsons():
    # loading some past asset event (listings) IDs from json->
    f3 = open(
        "txn_list.json",
    )
    global id_list
    id_list = json.load(f3)
    f3.close()
    # if empty, latest check will add latest listing event's id^


# embed_sender_sales (async function to generate and post embed from listings data)
async def embed_sender_lists(listobj, channel):
    print(f"Creating embed...")
    if listobj["asset"]["name"] is None:
        titlename = (
            listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + " listed!"
        )
    else:
        titlename = (
            listobj["asset"]["name"]
            + "("
            + listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + ") listed!"
        )
    embed = discord.Embed(
        title=titlename,
        timestamp=dateutil.parser.isoparse(listobj["created_date"]),
        url=listobj["asset"]["permalink"],
        colour=discord.Colour.blue(),
    )
    # embed.set_author(name=client.user.display_name,
    #    icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=listobj["asset"]["collection"]["image_url"])
    # embed.set_thumbnail(url=listobj['asset']['image_url'])
    if listobj["asset"]["name"] is None:
        q = 1
    else:
        embed.add_field(name="Name", value=listobj["asset"]["name"], inline=False)
    price = Web3.fromWei(int(listobj["starting_price"]), "ether")
    usdvalue = float(listobj["payment_token"]["usd_price"])
    usd_eth = str(int(usdvalue * float(price)))
    embed.add_field(
        name="Listed For",
        value="" + str(price) + "Ξ | $" + usd_eth + " USD",
        inline=True,
    )
    # usd_floor = str(int(usdvalue*float(floor_price)))
    # embed.add_field(name='Current Floor', value=''+str(floor_price) + 'Ξ | $'+usd_floor + ' USD', inline=True)
    date_obj = datetime.strptime(listobj["created_date"], "%Y-%m-%dT%H:%M:%S.%f")
    # embed.add_field(name='Timestamp', value=date_obj.strftime('%d %b, %Y at %H:%M') + ' UTC', inline=False)
    embed.add_field(
        name="At", value="" + date_obj.strftime("%d %b, %Y - %H:%M UTC"), inline=False
    )
    seller = listobj["seller"]["address"]
    seller_link = "https://opensea.io/" + seller
    embed.add_field(name="Lister:", value=f"[{seller}]({seller_link})", inline=False)
    # embed.set_image(url=listobj['asset']['image_url'])
    # embed.set_image(url=listobj['asset']['image_url'])

    # svg to png bit->
    name = listobj["asset"]["name"]
    # url = listobj['asset']['image_original_url']
    asset_id = listobj["asset"]["token_id"]
    url = "https://d23fdhqc1jb9no.cloudfront.net/_Realms/" + asset_id + ".svg"

    print(f"Downloading svg from {url}...")
    r = requests.get(url, allow_redirects=True)
    open(f"input/image_{name}.svg", "wb").write(r.content)
    print(f"Svg downloaded. Converting to png...")
    drawing = svg2rlg(f"input/image_{name}.svg")
    print(f"SVG retrieved. Converting to png...")
    try:
        renderPM.drawToFile(drawing, f"output/image_{name}.png", fmt="PNG")
        # renderPM.drawToFile(drawing, f'output/image.png', fmt='PNG')
        print(f"Converted svg to png. Uploading to Discord...")
        # embed.add_field(name='Image:', value='*Embedded*', inline=False)
        file = discord.File(f"output/image_{name}.png", filename=f"image.png")
        # await asyncio.sleep(3)
        print(f"Uploaded as Discord file")
        embed.set_image(url=f"attachment://image.png")
        # embed.set_image(url=url)
        print(f"Png file uploaded to latest Discord embed.")
    except:
        print(f"Rendering to png failed.")
        embed.add_field(
            name="Image:", value="*Image could not be rendered. View here:* " + url
        )
    embed.set_footer(
        text="Listed on OpenSea",
        icon_url="https://files.readme.io/566c72b-opensea-logomark-full-colored.png",
    )
    print(f"Embed created. Preparing to send...")
    await channel.send(file=file, embed=embed)
    print(f"Embed sent\n# # # # # # #\n")


# get_lists2 (async function to retrieve recent listings from the collection)
async def get_lists2(collection_slug, api_key, channel):
    load_jsons()
    event_match_flag = 0
    i = 0
    url = ""
    headers = {"X-API-KEY": api_key}
    successful = 0
    try:
        while event_match_flag == 0:
            if i == 0:
                url = (
                    "https://api.opensea.io/api/v1/events?collection_slug="
                    + str(collection_slug)
                    + "&event_type=created"
                )
            print(f"get_lists() Iteration: {i+1} | url: {url}\n")
            response = requests.request("GET", url, headers=headers)
            print(f"Listings data page {i+1} retrieved. Trying to extract-")
            lists = json.loads(response.text)
            key = "asset_events"
            if key in lists.keys():
                print(f"Key exists- API call successful")
                list1 = lists["asset_events"]
                print(f"json data loaded")
                print(f"Checking for last event match in page {i+1}...")
                pos = 0
                j = 0
                new_id = 0
                url = url + f"&cursor={lists['next']}"
                print(f"URL updated to = {url} (cursor next page)")
                # if id_list["last_list_id"] is empty, forward latest event only and add that to to the json too
                if id_list["last_listing_id"] == "":
                    #
                    print(
                        f"Empty txn_list.json detected- Posting latest listing only..."
                    )
                    listobj = list1[0]
                    await embed_sender_lists(listobj, channel)
                    latest_id = listobj["id"]
                    print(f"Adding last listing ID: {latest_id} to txn_list.json...")
                    f = open("txn_list.json", "r")
                    json_obj = json.load(f)
                    f.close()
                    f = open("txn_list.json", "w")
                    json_obj["last_listing_id"] = latest_id
                    json.dump(json_obj, f)
                    f.close()
                    print(f"New ID: {latest_id} pushed to txn_list.json")
                    print(f"---Updated---")
                    event_match_flag = 1
                    successful = 1
                else:
                    # New last_listing_id = latest event's ID
                    latest_id = list1[0]["id"]
                    for item in list1:
                        if item["id"] == id_list["last_listing_id"]:
                            pos = j
                            print(
                                f'Last event match found at page {i+1}, index {j}. item["id"] = {item["id"]} | id_list["last_listing_id"] = {id_list["last_listing_id"]}'
                            )
                            print(
                                f'Old last_sale_id = {id_list["last_listing_id"]} | New last_listing_id = {latest_id}'
                            )
                            event_match_flag = 1
                            break
                        if j == len(list1) - 1:
                            break
                        j += 1
                    print(f"j = {j} | Len(list1) = {len(list1)}")
                    print(
                        f"Forwarding earlier events in page {i+1} (upto but not including index {j}) to embed_sender_lists()..."
                    )
                    for item in list1:
                        if j <= 0:
                            break
                        print(f" - Sending event index {j-1} on page {i+1}.")
                        listobj = list1[j - 1]
                        await embed_sender_lists(listobj, channel)
                        j -= 1
                    print(f"Forwarded all\n")
                    if event_match_flag == 1:
                        print(f"Updating id_list in txn_list.json...")
                        f = open("txn_list.json", "r")
                        json_obj = json.load(f)
                        f.close()
                        f = open("txn_list.json", "w")
                        json_obj["last_listing_id"] = latest_id
                        json.dump(json_obj, f)
                        f.close()
                        print(f"New ID: {latest_id} pushed to txn_list.json")
                        print(f"---Updated---")
                    i += 1
                    successful = 1
            else:
                print(
                    f"Key does not exist- API call unsuccessfull. Trying again next iteration"
                )
                successful = 0
                break
        return successful
    except Exception as e:
        print("get_lists() exception occurred: \n")
        print(e)
        print("Invoking get_lists() again, retrying in 2 seconds...")
        await asyncio.sleep(2)
        await get_lists2(collection_slug, api_key, channel)


# @client.command()
async def start_check():
    await client.wait_until_ready()
    print(
        f"Initiating api retrieval loop... \n----------------------------------\n\n-----------------------------\n"
    )
    last_check_time = cfg["last_check_time"]
    collection_slug = cfg["collection_slug"]
    api_key = cfg["opensea_api_key"]
    chan_id1 = int(cfg["channel_id_listings"])
    channel1 = client.get_channel(id=chan_id1)
    # last_check_time = time.time() - 60
    last_check_arr = [last_check_time]
    while not client.is_closed():
        print(f"Beginning opensea data retrieval loop...")
        a = [1]
        for item in a:
            print(f"\n---*----*-----*----*----\nCalling get_sales(): ")
            response = await get_lists2(collection_slug, api_key, channel1)
            if response == 1:
                now = datetime.now()
                ctime = now.strftime("%d %b, %Y | %H:%M:%S")
                print(f"Last listings check updated at: {ctime}")
        await asyncio.sleep(30)


client.loop.create_task(start_check())

client.run(TOKEN)
