# Discord opensea listings check bot
#
# User adds collections to monitor (with trait, price limit data)
# Sample command: !track notoriousfrogs cloak "wizard cloak" 0.5 (+!untrack ... to untrack)
# format: !track (arg1 = name of collection) (arg2 = trait category) (arg3 = name of trait, within double quotes) (arg4 = price limit)
# Embed requirements: (to optimise for speed)
# OS link, image
# Trait, Price
# Floor Price of the Trait. To scrape from url like: (https://opensea.io/collection/thewynlambo?search[stringTraits][0][name]=Mouth&search[stringTraits][0][values][0]=Mecha%20Mouth)
#
# Algo:
# 1. Bot will add list of things (+associated data) to track to a csv file upon Discord command to track,
# 2. then read it every time its run and make the api calls
# 3. +Also web scrape trait-floor-price data from url

#!start_check initiates the bot

# Getting dependencies->
import discord
from discord.ext import commands
import time
from datetime import datetime
import requests
from web3 import Web3
import json
import dateutil.parser
from datetime import date, datetime
import csv
from csv import reader
from bs4 import BeautifulSoup
import re
import cfscrape


# Web scraping floor price for a certain trait->
# https://opensea.io/collection/thewynlambo?search[stringTraits][0][name]=Eyewear&search[stringTraits][0][values][0]=Wyn%20Sidekick
def get_example_scrapable_url():
    url_s1 = "https://opensea.io/collection/thewynlambo?search[stringTraits][0][name]="
    url_s2 = "&search[stringTraits][0][values][0]="
    # replace the ' ' gap in between multi-worded traits with '%20'
    trait_cat = "Eyewear"
    trait = "Wyn Sidekick"
    trait_f = trait.replace(" ", "%20")
    scrapable_url = url_s1 + trait_cat + url_s2 + trait_f
    print(f"Scrapable url: {scrapable_url}")


# Checking listings/track+untrack:

# Bot set-up->
client = commands.Bot(command_prefix="!")
TOKEN = open("token.txt", "r").readline()
# Make sure token.txt and config.json are in same folder
f = open(
    "config.json",
)  # For api key (optional, makes faster)
cfg = json.load(f)


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))


# embed_sender_lists (async function to generate and post embed from filtered lists data)->
async def embed_sender_lists(trait_type, trait_name, scraped_trait_floor, listobj, ctx):
    print(f"Creating embed...")
    if listobj["asset"]["name"] is None:
        titlename = (
            listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + " listed!"
        )
    else:
        titlename = listobj["asset"]["name"] + " listed!"
    embed = discord.Embed(
        title=titlename,
        timestamp=dateutil.parser.isoparse(listobj["created_date"]),
        url=listobj["asset"]["permalink"],
        colour=discord.Colour.blue(),
    )
    embed.set_author(name=client.user.display_name, icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=listobj["asset"]["collection"]["image_url"])
    embed.add_field(name="Name", value=listobj["asset"]["name"], inline=False)
    price = Web3.fromWei(int(listobj["starting_price"]), "ether")
    embed.add_field(name="Listed For", value=str(price) + "Ξ", inline=True)
    embed.add_field(name="Trait Category", value=trait_type, inline=True)
    embed.add_field(name="Trait", value=trait_name, inline=True)
    embed.add_field(name="Scraped Trait Floor Price", value=scraped_trait_floor)
    # embed.add_field(name='Floor Price', value=str(floor_price) + 'Ξ', inline=True)
    date_obj = datetime.strptime(listobj["created_date"], "%Y-%m-%dT%H:%M:%S.%f")
    embed.add_field(
        name="Date Listed", value=date_obj.strftime("%d %b, %Y %H:%M:%S"), inline=False
    )
    embed.set_image(url=listobj["asset"]["image_url"])
    embed.set_footer(
        text="Listed on OpenSea",
        icon_url="https://files.readme.io/566c72b-opensea-logomark-full-colored.png",
    )
    await ctx.channel.send(embed=embed)
    print(f"Embed sent\n# # # # # # #\n")


# floor_price_scrape() (Scrape floor price trait wise with base url + collection_slug + trait category + trait name)
async def floor_price_scrape(ctx, collection_slug, trait_cat, trait):
    base_url1 = (
        "https://opensea.io/collection/"
        + collection_slug
        + "?search[stringTraits][0][name]="
    )
    base_url2 = "&search[stringTraits][0][values][0]="
    trait_f = trait.replace(" ", "%20")
    scrapable_url = base_url1 + trait_cat + base_url2 + trait_f
    print(f"Scrapable url: {scrapable_url}")
    await ctx.channel.send(
        content=f"Scraping trait floor price from: {scrapable_url}\n"
    )

    # Using cfscrape to bypass Cloudflare protection
    scraper = cfscrape.create_scraper()
    r = scraper.get(scrapable_url)

    if r.status_code != 200:
        print("Error fetching the page.")
        return "Retrieval Failed"

    soup = BeautifulSoup(r.content, "html.parser")

    # Parsing the HTML to find the lowest listed price
    grids = soup.findAll("div", attrs={"role": "grid"})
    x = "Retrieval Failed"  # Default value in case no price is found

    for grid in grids:
        price_elements = grid.findAll(
            "div", text=re.compile(r"Ξ")
        )  # Searching for elements that contain the Ethereum symbol (Ξ)
        if price_elements:
            # Extracting the first price found (lowest)
            x = price_elements[0].text.strip()
            break

    print(f"Scraped floor price: {x}")
    return x


# asset_check (apply filter to make asset api call and check for trait/price condition)
async def asset_check(
    listobj, token_id, collection_slug, trait_cat, trait, api_key, ctx
):
    url = "https://api.opensea.io/api/v1/assets"
    querystring = {
        "token_ids": token_id,
        "order_by": "pk",
        "order_direction": "desc",
        "offset": "0",
        "limit": "50",
        "collection": collection_slug,
    }
    headers = {"X-API-KEY": api_key}
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(f"Asset data retrieved. Checking conditions...")
    assets = json.loads(response.text)
    asset_obj = assets["assets"][0]
    # Checking traits
    i = 0
    print(len(asset_obj["traits"]))
    for item in asset_obj["traits"]:
        trait_type = asset_obj["traits"][i]["trait_type"]
        if trait_type == trait_cat:
            trait_name = asset_obj["traits"][i]["value"]
            if trait_name == trait:
                print(f"Matching trait/trait category found.")
                # await floor_price_scrape()
                scraped_trait_floor = 0  # default value
                scraped_trait_floor = await floor_price_scrape(
                    ctx, collection_slug, trait_cat, trait
                )
                # calc rarity by trait_count and comparing with total number of assets in the collection, pass to/call from asset_check
                # scrape trait rarities by scraping from base url+asset contract address+token id
                await embed_sender_lists(
                    trait_type, trait_name, scraped_trait_floor, listobj, ctx
                )
            else:
                print(f"Matching asset not found for trait {trait_type} {trait_name}")
        i += 1


# get_lists (async function to retrieve recent listings from the collection, provided they meet condition X)
async def get_lists(
    collection_slug, trait_cat, trait, max_price, last_check_time, api_key, ctx
):
    url = "https://api.opensea.io/api/v1/events"
    querystring = {
        "collection_slug": collection_slug,
        "event_type": "created",
        "only_opensea": "true",
        "offset": "0",
        "limit": "100",
        "occurred_after": last_check_time,
    }
    headers = {"X-API-KEY": api_key}
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(f"Listings data retrieved. Trying to extract-")
    sales = json.loads(response.text)
    # Check sales dict for 'asset_events' key to check if call was a success
    key = "asset_events"
    x = 0
    if key in sales.keys():
        print(f"Key exists- API call successful")
        list1 = sales["asset_events"]
        print(f"json data loaded")
        if len(list1) == 0:
            print(f"No recent lists since last check")
        else:
            print(
                f"Recent lists have been made. Making asset check call for traits/price conditions... "
            )
            i = len(list1) - 1
            for item in list1:
                print(f"Array iteration " + str(i))
                listobj = list1[i]
                token_id = listobj["asset"]["token_id"]
                print(f"Formatting price:")
                eth_formatted_price = Web3.fromWei(
                    int(listobj["starting_price"]), "ether"
                )
                print(
                    f"Price formatted. Eth price: {eth_formatted_price}, Max price: {max_price}"
                )
                if eth_formatted_price <= float(max_price):
                    print(f"Price meets condition. Checking traits...")
                    await asset_check(
                        listobj,
                        token_id,
                        collection_slug,
                        trait_cat,
                        trait,
                        api_key,
                        ctx,
                    )
                    print(f"Asset checked. Checking next.")
                    i -= 1
                else:
                    print("Price does not meet condition. Checking next. ")
                    i -= 1
        x = 1
        return x
    else:
        print(
            f"Key does not exist- API call unsuccessfull. Trying again next iteration\n----------\n\n---------------\n"
        )
        return x


# Discord commands endpoint->
@client.command()
async def track(ctx, arg1, arg2, arg3, arg4):
    collection_slug = arg1
    trait_cat = arg2
    trait = arg3
    price_limit = arg4
    with open(("tracking.csv"), "a", encoding="UTF-8") as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow([collection_slug, trait_cat, trait, price_limit])
    print(
        f"Tracking added:\nCollection: {arg1}\nTrait Category: {arg2}\nTrait: {arg3}\nMax Price: {arg4}"
    )
    await ctx.channel.send(
        content=f"Tracking added:\nCollection: {arg1}\nTrait Category: {arg2}\nTrait: {arg3}\nMax Price: {arg4}"
    )
    # print(f'Checking size of collection...')
    # check total number of assets in the collection added to be tracked (to calculate rarity, and store this in the tracking csv)

    # scrape website of asset for rarity % of traits (with base url + asset contract address + token id)


@client.command()
async def start_check(
    ctx, arg1
):  #!start_check now, !start_check 1974962, etc. (unix time format)
    await client.wait_until_ready()
    print(
        f"Start check command received. Beginning now. \n----------------------------------\n\n-----------------------------\n"
    )
    api_key = cfg["api_key"]
    await ctx.channel.send(content=f"List of trackings:")
    with open(("tracking.csv"), "r", encoding="UTF-8") as fobj:
        csv_reader = reader(fobj)
        count = 1
        for row in csv_reader:
            collection_slug = row[0]
            trait_cat = row[1]
            trait = row[2]
            max_price = row[3]
            await ctx.channel.send(
                content=f'({count})- {collection_slug} {trait_cat} "{trait}" at or below {max_price}\n'
            )
            count += 1
    if arg1 == "now":
        last_check_time = time.time()
    else:
        last_check_time = arg1
    await ctx.channel.send(
        content=f"Now checking for listings since {last_check_time}"
    )  # to convert to human readable time
    while not client.is_closed():
        print(f"Beginning data access loop...")
        a = [1]
        response = 0
        # Response (0 for fail, 1 for success) returned from functions determines whether 'last_check_time' will update or not
        for item in a:
            with open(("tracking.csv"), "r", encoding="UTF-8") as fobj:
                csv_reader = reader(fobj)
                print(f"Checking rows of the csv...")
                for row in csv_reader:
                    print(f"Row check start:")
                    collection_slug = row[0]
                    trait_cat = row[1]
                    trait = row[2]
                    max_price = row[3]
                    print(
                        f"\n---*----*-----*----*----\nCalling get_lists() for {collection_slug} {trait_cat} {trait} below {max_price}eth: "
                    )
                    # scrape trait floor price
                    last_check = time.time()
                    response = await get_lists(
                        collection_slug,
                        trait_cat,
                        trait,
                        max_price,
                        last_check_time,
                        api_key,
                        ctx,
                    )
                    if response == 1:
                        last_check_time = last_check
                    time.sleep(1)
        time.sleep(4)


client.run(TOKEN)
