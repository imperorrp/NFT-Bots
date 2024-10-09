# bot for opensea collection sales/listings/collection stats updates to discord
# format 1, without svg


# (v6.0)--------------------------------------------------------------------------------------
# (23rd May 2022)
# added trait tracking feature

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
import prettytable
import threading

import requests

# Bot set-up->
client = commands.Bot(command_prefix="!")
TOKEN = open("Bot_D3/opseabot_token.txt", "r").readline()
# Make sure opseabot_token.txt and config.json are in same folder
f = open(
    "Bot_D3/config.json",
)
cfg = json.load(f)


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))


def load_jsons_s():
    # loading some past asset event (sales) IDs from json->
    f3 = open(
        "Bot_D3/txn_sale.json",
    )
    global id_sale
    id_sale = json.load(f3)
    f3.close()
    # if empty, latest check will add latest sale event's id^


load_jsons_s()

# total supply = total supply of nfts in the collection. Edit this for each new collection for valid trait rarity %age.
global total_supply
total_supply = cfg["total_supply"]  # total NFTs in collection in circulation

# traits retrieval function->
num_of_exception = 0


def get_traits(asset_contract_addr, token_id):
    #
    print(f"%d get_traits() invoked. Trying to retrieve...")
    global num_of_exception
    try:
        op_api_key = cfg["opensea_api_key"]
        api_key = op_api_key
        url = (
            "https://api.opensea.io/api/v1/asset/"
            + asset_contract_addr
            + "/"
            + token_id
            + "/?include_orders=false"
        )
        headers = {"X-API-KEY": api_key}
        response = requests.get(url, headers=headers)
        asset_data = json.loads(response.text)
        traits = asset_data["traits"]
        reply = ""
        for trait in traits:
            type = trait["trait_type"]
            value = trait["value"]
            count = trait["trait_count"]
            # (formulae for trait rarity %: count/total_supply *100 )
            rarity_percent = int((count / total_supply) * 100)
            reply = reply + f"{type} : {value} ({rarity_percent}%)\n"
            # reply = reply+ f"{type} : {value}\n"
        reply = reply
        return reply
    except Exception as e:
        print(f"%d get_traits() Exception ocurred: \n")
        print(e)
        num_of_exception += 1
        if num_of_exception <= 2:
            print(f"%d trying get_traits() again...")
            get_traits(asset_contract_addr, token_id)
        else:
            print(f"%d get_traits() error persists. Moving on.")
            return 0


# embed_sender_sales (async function to generate and post embed from sales data)
async def embed_sender_sales(listobj, floor_price, channel):
    print(f"Creating embed...")
    if listobj["asset"]["name"] is None:
        titlename = (
            listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + " sold!"
        )
    else:
        titlename = (
            listobj["asset"]["name"]
            + "("
            + listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + ") sold!"
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
    price = Web3.fromWei(int(listobj["total_price"]), "ether")
    usdvalue = float(listobj["payment_token"]["usd_price"])
    usd_eth = str(int(usdvalue * float(price)))
    embed.add_field(
        name="Sold For", value="" + str(price) + "Ξ | $" + usd_eth + " USD", inline=True
    )
    usd_floor = str(int(usdvalue * float(floor_price)))
    embed.add_field(
        name="Current Floor",
        value="" + str(floor_price) + "Ξ | $" + usd_floor + " USD",
        inline=True,
    )
    date_obj = datetime.strptime(listobj["created_date"], "%Y-%m-%dT%H:%M:%S.%f")
    # embed.add_field(name='Timestamp', value=date_obj.strftime('%d %b, %Y at %H:%M') + ' UTC', inline=False)
    embed.add_field(
        name="At", value="" + date_obj.strftime("%d %b, %Y - %H:%M UTC"), inline=False
    )

    asset_contract_addr = listobj["asset"]["asset_contract"]["address"]
    token_id = listobj["asset"]["token_id"]
    response = get_traits(
        asset_contract_addr, token_id
    )  # returns a 'reply' with list of
    # trait categories and corresponding trait rarity %es
    embed.add_field(name="Traits:", value=response, inline=False)

    buyer = listobj["winner_account"]["address"]
    seller = listobj["seller"]["address"]
    buyer_link = "https://opensea.io/" + buyer
    seller_link = "https://opensea.io/" + seller
    embed.add_field(name="Buyer:", value=f"[{buyer}]({buyer_link})", inline=False)
    embed.add_field(name="Seller:", value=f"[{seller}]({seller_link})", inline=False)
    txn = listobj["transaction"]["transaction_hash"]
    txn_link = "https://etherscan.io/tx/" + str(txn)
    embed.add_field(name="Transaction:", value=txn_link, inline=False)
    embed.set_image(url=listobj["asset"]["image_url"])
    # embed.set_image(url=listobj['asset']['image_url'])

    embed.set_footer(
        text="Sold on OpenSea • Bot by @ImperorEth(Twitter)",
        icon_url="https://files.readme.io/566c72b-opensea-logomark-full-colored.png",
    )
    print(f"Embed created. Preparing to send...")
    await channel.send(embed=embed)
    print(f"Embed sent\n# # # # # # #\n")


# get_sales2 (async function to retrieve recent sales from the collection)
async def get_sales2(collection_slug, api_key, floor_price, channel):
    load_jsons_s()
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
                    + "&event_type=successful"
                )
            print(f"get_sales() Iteration: {i+1} | url: {url}\n")
            response = requests.request("GET", url, headers=headers)
            print(f"Sales data page {i+1} retrieved. Trying to extract-")
            sales = json.loads(response.text)
            key = "asset_events"
            if key in sales.keys():
                print(f"Key exists- API call successful")
                list1 = sales["asset_events"]
                print(f"json data loaded")
                print(f"Checking for last event match in page {i+1}...")
                pos = 0
                j = 0
                new_id = 0
                url = url + f"&cursor={sales['next']}"
                print(f"URL updated to = {url} (cursor next page)")
                # if id_sale["last_sale_id"] is empty, forward latest event only and add that to to the json too
                if id_sale["last_sale_id"] == "":
                    #
                    print(f"Empty txn_sale.json detected- Posting latest sale only...")
                    listobj = list1[0]
                    await embed_sender_sales(listobj, floor_price, channel)
                    latest_id = listobj["id"]
                    latest_cdate = listobj["created_date"]
                    print(
                        f"Adding last sale ID: {latest_id}\n and last sale cdate: {latest_cdate} to txn_sale.json..."
                    )
                    f = open("Bot_D3/txn_sale.json", "r")
                    json_obj = json.load(f)
                    f.close()
                    f = open("Bot_D3/txn_sale.json", "w")
                    json_obj["last_sale_id"] = latest_id
                    json_obj["last_sale_cdate"] = latest_cdate
                    json.dump(json_obj, f)
                    f.close()
                    print(
                        f"New ID: {latest_id}, New CDATE: {latest_cdate} pushed to txn_sale.json"
                    )
                    print(f"---Updated---")
                    event_match_flag = 1
                    successful = 1
                else:
                    # New last_sale_id = latest event's ID
                    latest_id = list1[0]["id"]
                    latest_cdate = list1[0]["created_date"]
                    for item in list1:
                        if item["id"] == id_sale["last_sale_id"]:
                            pos = j
                            print(
                                f'Last event match found at page {i+1}, index {j}. item["id"] = {item["id"]} | id_sale["last_sale_id"] = {id_sale["last_sale_id"]}'
                            )
                            print(
                                f'Old last_sale_id = {id_sale["last_sale_id"]} | New last_sale_id = {latest_id}'
                            )
                            event_match_flag = 1
                            break

                        # if-check here if time of current item > time of last event match. Then force event_match_flag=1 and break
                        date_obj = datetime.strptime(
                            item["created_date"], "%Y-%m-%dT%H:%M:%S.%f"
                        )
                        json_cdate = id_sale["last_sale_cdate"]
                        cdate_dobj = datetime.strptime(
                            json_cdate, "%Y-%m-%dT%H:%M:%S.%f"
                        )
                        print(
                            f"Last current checked event timestamp: {item['created_date']} | Last stored event timestamp: {json_cdate}"
                        )
                        if date_obj < cdate_dobj:
                            print(
                                f"Timestamp of last checked event < recorded timestamp of last sale event. Halting here."
                            )
                            event_match_flag = 1
                            break

                        if j == len(list1) - 1:
                            break
                        j += 1
                    print(f"j = {j} | Len(list1) = {len(list1)}")
                    print(
                        f"Forwarding earlier events in page {i+1} (upto but not including index {j}) to embed_sender_sales()..."
                    )
                    for item in list1:
                        if j <= 0:
                            break
                        print(f" - Sending event index {j-1} on page {i+1}.")
                        listobj = list1[j - 1]
                        await embed_sender_sales(listobj, floor_price, channel)
                        j -= 1
                    print(f"Forwarded all\n")
                    if event_match_flag == 1:
                        print(f"Updating id_sale, cdate in txn_sale.json...")
                        f = open("Bot_D3/txn_sale.json", "r")
                        json_obj = json.load(f)
                        f.close()
                        f = open("Bot_D3/txn_sale.json", "w")
                        json_obj["last_sale_id"] = latest_id
                        json_obj["last_sale_cdate"] = latest_cdate
                        json.dump(json_obj, f)
                        f.close()
                        print(
                            f"New ID: {latest_id}, new CDATE: {latest_cdate} pushed to txn_sale.json"
                        )
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
        print("get_sales() exception occurred: \n")
        print(e)
        # print('Invoking get_sales() again, retrying in 10 seconds...')
        print("Skipping this iteration, emptying txn_sale.json to restart...")
        f = open("Bot_D3/txn_sale.json", "r")
        json_obj = json.load(f)
        f.close()
        f = open("Bot_D3/txn_sale.json", "w")
        json_obj["last_sale_id"] = ""
        json_obj["last_sale_cdate"] = ""
        json.dump(json_obj, f)
        f.close()
        print("txn_sale.json emptied. Recalling get_sales() in 10 seconds...")
        await asyncio.sleep(10)
        await get_sales2(collection_slug, api_key, floor_price, channel)


# get_floor (function to return collection floor price)
def get_floor(collection_slug, api_key):
    print("Retrieving floor price...")
    url = "https://api.opensea.io/api/v1/collection/" + str(collection_slug) + "/stats"
    # querystring = {'collection':collection_slug}
    headers = {"X-API-KEY": api_key}
    response = requests.request("GET", url, headers=headers)
    stats = json.loads(response.text)
    fp = stats["stats"]["floor_price"]
    print(f"Floor price retrieved = {fp}\n")
    return fp


# @client.command()
async def start_check():
    await client.wait_until_ready()
    print(
        f"Initiating api retrieval loop... \n----------------------------------\n\n-----------------------------\n"
    )
    collection_slug = cfg["collection_slug"]
    api_key = cfg["opensea_api_key"]
    chan_id1 = int(cfg["channel_id_sales"])
    channel1 = client.get_channel(id=chan_id1)
    # last_check_time = time.time() - 60
    while not client.is_closed():
        print(f"Beginning opensea data retrieval loop...")
        floor_price = "retrieval error"
        try:
            floor_price = get_floor(collection_slug, api_key)
        except:
            print(
                "Could not retrieve floor price this iteration. Trying again next...\n"
            )
        print(f"Current floor: {floor_price}")
        a = [1]
        for item in a:
            print(f"\n---*----*-----*----*----\nCalling get_sales(): ")
            response = await get_sales2(collection_slug, api_key, floor_price, channel1)
            if response == 1:
                now = datetime.now()
                ctime = now.strftime("%d %b, %Y | %H:%M:%S")
                print(f"Last sales check updated at: {ctime}")
            else:
                print(f"get_sales() response != 1. Trying again next iteration...")
        await asyncio.sleep(30)


collection_name = cfg["collection_slug"]
op_api_key = cfg["opensea_api_key"]

client.loop.create_task(start_check())

client.run(TOKEN)
