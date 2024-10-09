# opensea nft tracking bot for twitter

# uses oauth1 to get access tokens for a sales bot twitter acc, post tweet updates
# v4.0(30th April 2022)-----------------------------------------

# importing dependencies->
from regex import E
import tweepy
from tweepy.auth import OAuthHandler
import time
import requests
from web3 import Web3
import json
from dateutil import parser
import asyncio
from datetime import datetime
import threading


# loading config.json file data->
f = open(
    "Bot_T/config.json",
)
cfg = json.load(f)

# opensea api key->
op_api_key = cfg["opensea_api_key"]

# opensea collection to monitor for sales updates->
collection_name = cfg["collection_name"]

# loading access token/secret json file data->
f2 = open(
    "Bot_T/access.json",
)
acc = json.load(f2)

# twitter api configuring->
consumer_key = cfg["consumer_key"]
consumer_secret = cfg["consumer_secret"]

access_token = acc["access_token"]
access_token_secret = acc["access_token_secret"]
toOauth = False
if access_token == "0" or access_token_secret == "0":
    print(
        f"--------------------\nAccess token: {access_token}\nAccess token secret: {access_token_secret}\n"
    )
    print(
        "OAuth required. Proceed to url to get one-time PIN...\n----------------------"
    )
    toOauth = True
else:
    print(
        f"--------------------\nAccess token: {access_token}\nAccess token secret: {access_token_secret}\n"
    )
    print(
        "Access exists. Using token/secret pair to log in...\n-----------------------"
    )
    toOauth = False
# oauth url posted + PIN to be accepted by code if access token/secret pair is empty^
# ^i.e. if toOauth = False

if toOauth == False:
    print("Passing consumer and access to OAuthHandler...")
    # auth = tweepy.OAuth1UserHandler(
    #    consumer_key, consumer_secret,
    #    access_token, access_token_secret
    # )
    # api = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    print("API tweepy client authorized.\n--------------------------")
else:
    print(f"Passing consumer to OAuthHandler...")
    oauth1_user_handler = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, callback="oob"
    )
    print(f"Authorize below:")
    print(oauth1_user_handler.get_authorization_url())
    verifier = input("Input PIN: ")
    access_token, access_token_secret = oauth1_user_handler.get_access_token(verifier)
    f2.close()
    acc["access_token"] = access_token
    acc["access_token_secret"] = access_token_secret

    f2 = open("Bot_T/access.json", "w")
    json.dump(acc, f2)
    f2.close()
    print(
        f"Access token/secret generated and saved to access.json. Initializing client..."
    )
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    print("API tweepy client authorized.\n--------------------------")

# loading some past asset event (sales) IDs from json->
f3 = open(
    "Bot_T/txn_sale.json",
)
id_sale = json.load(f3)
f3.close()
# if empty, latest check will add latest sale event's id^


def load_jsons():
    # loading some past asset event (sales) IDs from json->
    f3 = open(
        "Bot_T/txn_sale.json",
    )
    global id_sale
    id_sale = json.load(f3)
    f3.close()
    # if empty, latest check will add latest sale event's id^


# functions->


# formats sales update to send, sends tweet
async def tweet_sender_sales(listobj, collection_name, floor_price):
    if listobj["asset"]["name"] is None:
        titlename = (
            listobj["asset"]["asset_contract"]["name"]
            + " "
            + listobj["asset"]["token_id"]
            + " sold!"
        )
    else:
        # titlename = listobj['asset']['name'] + ' ('+listobj['asset']['asset_contract']['name'] + ' '+listobj['asset']['token_id']+') sold!'
        titlename = listobj["asset"]["name"] + " sold for"
    title = titlename
    text = title
    timestamp = parser.parse(listobj["created_date"])
    url = listobj["asset"]["permalink"]
    price = Web3.fromWei(int(listobj["total_price"]), "ether")
    usdvalue = float(listobj["payment_token"]["usd_price"])
    usd_eth = str(int(usdvalue * float(price)))
    date_obj = datetime.strptime(listobj["created_date"], "%Y-%m-%dT%H:%M:%S.%f")
    timestamp = date_obj.strftime("%d %b, %Y - %H:%M UTC")
    buyer = listobj["winner_account"]["address"]
    seller = listobj["seller"]["address"]
    buyer_link = "https://opensea.io/" + buyer
    # b_name = listobj['winner_account']['user']['username']
    seller_link = "https://opensea.io/" + seller
    text = text + " for: Ξ" + str(price) + " Ether ($" + usd_eth + " USD) 🚀"
    text = text + "\nAt: " + str(timestamp) + " 🕓"
    # text = text + 'From: '+seller_link+'\nTo: '+buyer_link+'\n\n'
    txn = listobj["transaction"]["transaction_hash"]
    link = listobj["asset"]["permalink"]
    # link=listobj['asset']['image_url']
    txn_link = "etherscan.io/tx/" + str(txn)
    text = text + "\n\nTxn: " + txn_link
    collection_name = collection_name.replace("-", "_")
    # text = text + '\n\n#'+collection_name+' #'+collection_name+ '_salesbot #opensea #nft\n'+link
    text = text + "\n\n#Veefriends #Veefriends2 #VeefriendsSeries2 #VF2\n" + link
    # text = text + '\n\n#tinydinos #tinydinos_salesbot #opensea #nft\n'+link
    tweet = text
    # api.update_status(status=(tweet))
    # tweeting via Twitter api v1.1 endpoint^ ('api' in Tweepy)
    ltweet = client.create_tweet(text=tweet)
    print(tweet)
    print(f"Passing tweet, collection contract addr, token id to get_traits()...")
    asset_contract_addr = listobj["asset"]["asset_contract"]["address"]
    token_id = listobj["asset"]["token_id"]
    response = await get_traits(asset_contract_addr, token_id)
    if response == 0:
        print("%t get_traits unsuccessfull for current asset. Sending no tweet reply.")
    else:
        id = ltweet.id
        client.create_tweet(text=response, in_reply_to_tweet_id=id)
        print("%t Traits tweet reply sent.")
        print(f"{response}")
    print("%t-------------\n")


# check_listobj


# get_sales2 (async function to retrieve recent sales from the collection)
async def get_sales2(collection_slug, api_key, floor_price):
    load_jsons()
    collection_name = collection_slug
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
            print(f"%tget_sales() Iteration: {i+1} | url: {url}\n")
            response = requests.request("GET", url, headers=headers)
            print(f"%tSales data page {i+1} retrieved. Trying to extract-")
            sales = json.loads(response.text)
            key = "asset_events"
            if key in sales.keys():
                print(f"%tKey exists- API call successful")
                list1 = sales["asset_events"]
                print(f"%tjson data loaded")
                print(f"%tChecking for last event match in page {i+1}...")
                pos = 0
                j = 0
                new_id = 0
                url = url + f"&cursor={sales['next']}"
                print(f"%tURL updated to = {url} (cursor next page)")
                # if id_sale["last_sale_id"] is empty, forward latest event only and add that to to the json too
                if id_sale["last_sale_id"] == "":
                    #
                    print(
                        f"%tEmpty txn_sale.json detected- Posting latest sale only..."
                    )
                    listobj = list1[0]
                    await tweet_sender_sales(listobj, collection_name, floor_price)
                    latest_id = listobj["id"]
                    # latest_dobj = datetime.strptime(listobj['created_date'],"%Y-%m-%dT%H:%M:%S.%f")
                    latest_cdate = listobj["created_date"]
                    print(
                        f"%tAdding last sale ID: {latest_id}\n and last sale cdate: {latest_cdate} to txn_sale.json..."
                    )
                    f = open("Bot_T/txn_sale.json", "r")
                    json_obj = json.load(f)
                    f.close()
                    f = open("Bot_T/txn_sale.json", "w")
                    json_obj["last_sale_id"] = latest_id
                    json_obj["last_sale_cdate"] = latest_cdate
                    json.dump(json_obj, f)
                    f.close()
                    print(
                        f"%tNew ID: {latest_id}, New CDATE: {latest_cdate} pushed to txn_sale.json"
                    )
                    print(f"%t---Updated---")
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
                                f'%tLast event match found at page {i+1}, index {j}. item["id"] = {item["id"]} | id_sale["last_sale_id"] = {id_sale["last_sale_id"]}'
                            )
                            print(
                                f'%tOld last_sale_id = {id_sale["last_sale_id"]} | New last_sale_id = {latest_id}'
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
                        if date_obj < cdate_dobj:
                            print(
                                f"%tTimestamp of last checked event < recorded timestamp of last sale event. Halting here."
                            )
                            event_match_flag = 1
                            break

                        if j == len(list1) - 1:
                            break
                        j += 1
                    print(f"%tj = {j} | Len(list1) = {len(list1)}")
                    print(
                        f"%tForwarding earlier events in page {i+1} (upto but not including index {j}) to embed_sender_sales()..."
                    )
                    for item in list1:
                        if j <= 0:
                            break
                        print(f"%t - Sending event index {j-1} on page {i+1}.")
                        listobj = list1[j - 1]
                        await tweet_sender_sales(listobj, collection_name, floor_price)
                        j -= 1
                    print(f"Forwarded all\n")
                    if event_match_flag == 1:
                        print(f"%tUpdating id_sale, cdate in txn_sale.json...")
                        f = open("Bot_T/txn_sale.json", "r")
                        json_obj = json.load(f)
                        f.close()
                        f = open("Bot_T/txn_sale.json", "w")
                        json_obj["last_sale_id"] = latest_id
                        json_obj["last_sale_cdate"] = latest_cdate
                        json.dump(json_obj, f)
                        f.close()
                        print(
                            f"%tNew ID: {latest_id}, new CDATE: {latest_cdate} pushed to txn_sale.json"
                        )
                        print(f"%t---Updated---")
                    i += 1
                    successful = 1
            else:
                print(
                    f"%tKey does not exist- API call unsuccessfull. Trying again next iteration"
                )
                successful = 0
                break
        return successful
    except Exception as e:
        print("%tget_sales() exception occurred: \n")
        print(e)
        # print('%tInvoking get_sales() again, retrying in 20 seconds...')
        print("%t Emptying txn_sale.json to restart.")
        f = open("Bot_T/txn_sale.json", "r")
        json_obj = json.load(f)
        f.close()
        f = open("Bot_T/txn_sale.json", "w")
        json_obj["last_sale_id"] = ""
        json_obj["last_sale_cdate"] = ""
        json.dump(json_obj, f)
        f.close()
        print("%t txn_sale.json cleared. Reinvoking get_sales() in 20 seconds...")
        await asyncio.sleep(20)
        await get_sales2(collection_slug, api_key, floor_price)


# get_floor (function to return collection floor price)
def get_floor(collection_slug, api_key):
    print("%tRetrieving floor price...")
    url = "https://api.opensea.io/api/v1/collection/" + str(collection_slug) + "/stats"
    # querystring = {'collection':collection_slug}
    headers = {"X-API-KEY": api_key}
    try:
        response = requests.request("GET", url, headers=headers)
        stats = json.loads(response.text)
        fp = stats["stats"]["floor_price"]
        print(f"%tFloor price retrieved = {fp}\n")
        return fp
    except Exception as e:
        print("%tget_floor exception occurred: \n")
        print(e)
        fp = "-"
        return fp


total_supply = 0


# traits retrieval function->
async def get_traits(asset_contract_addr, token_id):
    #
    print(f"%t get_traits() invoked. Trying to retrieve...")
    num_of_exception = 0
    try:
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
        reply = f"#{token_id} Traits: \n\n"
        for trait in traits:
            type = trait["trait_type"]
            value = trait["value"]
            count = trait["trait_count"]
            # (formulae for trait rarity %: count/total_supply *100 )
            rarity_percent = (count / total_supply) * 100
            reply = f"{type} : {value} ({rarity_percent})\n"
        return reply
    except Exception as e:
        print(f"%t get_traits() Exception ocurred: \n")
        print(e)
        num_of_exception += 1
        if num_of_exception <= 2:
            print(f"%t trying get_traits() again...")
            get_traits(asset_contract_addr, token_id)
        else:
            print("%t get_traits() error persists. Moving on.")
            return 0


# main function->
async def main():
    a = 1
    while True:
        print(f"%tBeginning main loop...")
        floor_price = get_floor(collection_name, op_api_key)
        print(f"%tFloor price retrieved. FP = {floor_price}")
        print(f"%tCalling get_sales2()...")
        response = await get_sales2(collection_name, op_api_key, floor_price)
        if response == 1:
            now = datetime.now()
            ctime = now.strftime("%d %b, %Y | %H:%M:%S")
            print(f"%tLast sales check updated at: {ctime}")
        # get_sales2(collection_name, op_api_key, floor_price)
        print(f"%tSleeping 60 seconds...")
        await asyncio.sleep(60)


async def stats_tweeter(stat_data, collection_name):
    print("%th starting tweet construction...")
    d_vol = "Ξ" + str(round(stat_data["stats"]["one_day_volume"], 2))
    d_sales = int(stat_data["stats"]["one_day_sales"])
    d_avg = "Ξ" + str(round(stat_data["stats"]["one_day_average_price"], 2))
    w_vol = "Ξ" + str(round(stat_data["stats"]["seven_day_volume"], 2))
    w_sales = int(stat_data["stats"]["seven_day_sales"])
    w_avg = "Ξ" + str(round(stat_data["stats"]["seven_day_average_price"], 2))
    m_vol = "Ξ" + str(round(stat_data["stats"]["thirty_day_volume"], 2))
    m_sales = int(stat_data["stats"]["thirty_day_sales"])
    m_avg = "Ξ" + str(round(stat_data["stats"]["thirty_day_average_price"], 2))
    t_vol = "Ξ" + str(round(stat_data["stats"]["total_volume"], 2))
    t_sales = int(stat_data["stats"]["total_sales"])
    t_avg = "Ξ" + str(round(stat_data["stats"]["average_price"], 2))

    m_cap = "Ξ" + str(round(stat_data["stats"]["market_cap"], 2))
    f_price = "Ξ" + str(round(stat_data["stats"]["floor_price"], 2))
    # text = f"{collection_name} daily update! @{collection_name}\n"
    text = f"{collection_name} daily update! @veefriends\n"
    text = text + f"\nFloor: {f_price} | Market Cap = {m_cap}\n"
    text = text + f"\nDaily S/V = {d_sales} / {d_vol}"
    text = text + f"\nWeekly S/V = {w_sales} / {w_vol}"
    # text = text + f"\nMonthly Sales/Volume = {m_sales}/{m_vol}"
    text = text + f"\nTotal S/V = {t_sales} / {t_vol}"
    collection_name = collection_name.replace("-", "_")
    # text = text + '\n\n#'+collection_name+' #'+collection_name+ '_salesbot #opensea #nft\n'
    text = text + "\n\n#Veefriends #Veefriends2 #VeefriendsSeries2 #VF2\n"
    tweet = text
    print(tweet)
    await client.create_tweet(text=tweet)
    print(tweet)
    print("%th -------------\n")
    c = 1


async def stats(collection_name, op_api_key):
    b = 1
    while True:
        print("%th Beginning thread1 loop...")
        print("%th Retrieving collection stats from OS:")

        url = "https://api.opensea.io/api/v1/collection/" + collection_name + "/stats"
        headers = {"Accept": "application/json", "X-API-KEY": op_api_key}
        response = requests.request("GET", url, headers=headers)
        stat_data = json.loads(response.text)
        print("%th Sending stat_data to stats_tweeter...")
        await stats_tweeter(stat_data, collection_name)
        global total_supply
        total_supply = stat_data["stats"]["total_supply"]
        print("%th returned from stats_tweeter().")

        print("%th Sleeping for 24 hrs...")
        await asyncio.sleep(86400)


# def stats_a(collection_name, op_api_key):
#    stats(collection_name, op_api_key)

# thread1 = threading.Thread(target = stats_a, args = (collection_name, op_api_key))
# thread1.start()

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())

loop = asyncio.get_event_loop()
asyncio.ensure_future(stats(collection_name, op_api_key))
asyncio.ensure_future(main())
loop.run_forever()
