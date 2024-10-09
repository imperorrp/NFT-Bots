#OpenSea Discord bot to check Sales/listings with X check config
#config: reads from config.json file
#v1.3
# (issue: 1.0 Sales/listings keeps stopping after a while because of throttled requests, order is reversed, floor price for some collections cannot be retrieved)
# (fix: 1.1 empty request json data forces a continue, next check checks from last checkpoint (time) as well
#       1.2 no json request data/or something other than a json return (completely failed request) also forces a continue, order of embeds is reversed, and upto 50 random asset owners are checked to retrieve floor price)
#       1.3 botched api call/json format for collections forces a pass and tries again next loop (set default/manual floor price on line 233)
#README: For setup, get a Discord bot token, put it in a text file named 'opseabot_token.txt', and update config.json as necessary. Also install all dependencies.

#Importing dependencies->
import discord
from discord.ext import commands
import time 
from datetime import datetime
import requests
from web3 import Web3
import json
import dateutil.parser
from datetime import date,datetime

#Bot set-up->
client=commands.Bot(command_prefix='!')
TOKEN = open("opseabot_token.txt","r").readline() 
#Make sure opseabot_token.txt and config.json are in same folder
f = open("config.json",)
cfg = json.load(f)
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

#embed_sender_lists (async function to generate and post embed from filtered lists data)
async def embed_sender_lists(listobj, floor_price, channel, ctx):
    print(f'Creating embed...')
    if (listobj['asset']['name'] is None):
        titlename = listobj['asset']['asset_contract']['name'] + ' '+listobj['asset']['token_id'] + ' listed!'
    else: 
        titlename = listobj['asset']['name'] + ' listed!'
    embed = discord.Embed(
        title = titlename,
        timestamp = dateutil.parser.isoparse(listobj['created_date']),
        url = listobj['asset']['permalink'],
        colour = discord.Colour.blue())
    embed.set_author(name=client.user.display_name,  
        icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=listobj['asset']['collection']['image_url'])
    embed.add_field(name='Name', value=listobj['asset']['name'], inline=False)
    price = Web3.fromWei(int(listobj['starting_price']), 'ether')
    embed.add_field(name='Listed For', value=str(price) + 'Ξ', inline=True)
    embed.add_field(name='Floor Price', value=str(floor_price) + 'Ξ', inline=True)
    date_obj = datetime.strptime(listobj['created_date'],"%Y-%m-%dT%H:%M:%S.%f")
    embed.add_field(name='Date Listed', value=date_obj.strftime('%d %b, %Y %H:%M:%S'), inline=False)
    embed.set_image(url=listobj['asset']['image_url'])
    embed.set_footer(text='Listed on OpenSea', icon_url='https://files.readme.io/566c72b-opensea-logomark-full-colored.png')
    await channel.send(embed=embed)
    print(f'Embed sent\n# # # # # # #\n')

#get_lists (async function to retrieve recent listings from the collection, provided they meet condition X)
async def get_lists(collection_slug, last_check_time, api_key, floor_price, factor, channel, ctx):
    url = "https://api.opensea.io/api/v1/events"
    querystring = {"collection_slug":collection_slug,"event_type":"created","only_opensea":"true","offset":"0","limit":"100","occurred_after":last_check_time}
    headers = {'X-API-KEY': api_key}
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(f'Listings data retrieved. Trying to extract-')
    try: 
        sales = json.loads(response.text)
        #Check sales dict for 'asset_events' key to check if call was a success 
        key = 'asset_events'
        x = 0
        if key in sales.keys():
            print(f'Key exists- API call successful')
            list1=sales['asset_events']
            print(f'json data loaded')
            if (len(list1)==0):
                print(f'No recent lists since last check')
            else: 
                print(f'Recent lists have been made. Embedding... ')
                i=len(list1)-1
                for item in list1:
                    print(f'Array iteration '+str(i))
                    listobj=list1[i]
                    #Apply filter to check if listing meets condition (if x, => (below statement))
                    price = listobj['starting_price']
                    eth_formatted_price = Web3.fromWei(int(listobj['starting_price']), 'ether')
                    if (eth_formatted_price<=(floor_price+float(factor))):
                        print(f'X<Y+factor. Generating embed...\n')
                        await embed_sender_lists(listobj, floor_price, channel, ctx)
                    i-=1
            x=1
            return x
        else: 
            print(f'Key does not exist- API call unsuccessfull. Trying again next iteration')
            return x
    except: 
        print(f'Error: Json string could not be loaded from response. Trying again next iteration')
        return 0

#embed_sender_sales (async function to generate and post embed from sales data)
async def embed_sender_sales(listobj, channel, ctx):
    print(f'Creating embed...')
    if (listobj['asset']['name'] is None):
        titlename = listobj['asset']['asset_contract']['name'] + ' '+listobj['asset']['token_id'] + ' sold!'
    else: 
        titlename = listobj['asset']['name'] + ' sold!'
    embed = discord.Embed(
        title = titlename,
        timestamp = dateutil.parser.isoparse(listobj['created_date']),
        url = listobj['asset']['permalink'],
        colour = discord.Colour.blue())
    embed.set_author(name=client.user.display_name,  
        icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=listobj['asset']['collection']['image_url'])
    embed.add_field(name='Name', value=listobj['asset']['name'], inline=False)
    price = Web3.fromWei(int(listobj['total_price']), 'ether')
    embed.add_field(name='Sold For', value=str(price) + 'Ξ', inline=True)
    date_obj = datetime.strptime(listobj['created_date'],"%Y-%m-%dT%H:%M:%S.%f")
    embed.add_field(name='Date Sold', value=date_obj.strftime('%d %b, %Y %H:%M:%S'), inline=True)
    buyer = listobj['winner_account']['address'] 
    seller = listobj['seller']['address']
    buyer_link= 'https://opensea.io/'+buyer
    seller_link='https://opensea.io/'+seller
    embed.add_field(name='Buyer', value= buyer_link, inline=False)
    embed.add_field(name='Seller', value=seller_link, inline=False)
    txn=listobj['transaction']['transaction_hash']
    txn_link= 'https://etherscan.io/tx/'+str(txn)
    embed.add_field(name='Transaction Hash:', value=txn_link, inline=False)
    embed.set_image(url=listobj['asset']['image_url'])
    embed.set_footer(text='Sold on OpenSea', icon_url='https://files.readme.io/566c72b-opensea-logomark-full-colored.png')
    #print(f'Embed created. Preparing to send...')
    await channel.send(embed=embed)
    print(f'Embed sent\n# # # # # # #\n')

#get_sales (async function to retrieve recent sales data from a collection)
async def get_sales(collection_slug, last_check_time, api_key, channel, ctx):
    url = "https://api.opensea.io/api/v1/events"
    querystring = {"collection_slug":collection_slug,"event_type":"successful","only_opensea":"true","offset":"0","limit":"100","occurred_after":last_check_time}
    headers = {'X-API-KEY': api_key}
    current_time1=time.time()
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(f'Sales data retrieved. Trying to extract-')
    try: 
        sales = json.loads(response.text)
        #Check sales dict for 'asset_events' key to check if call was a success
        key = 'asset_events'
        x = 0
        if key in sales.keys():
            print(f'Key exists- API call successful')
            list1=sales['asset_events']
            print(f'json data loaded')
            if (len(list1)==0):
                print(f'No recent sales since last check. Last check time= {last_check_time}')
                print(f'Current time: {current_time1}')
                await channel.send(content=f'No recent sales since last check. Last check time= {last_check_time}\nCurrent time: {current_time1}')
            else: 
                print(f'Recent sales have been made. Embedding... ')
                print(f'Last check time= {last_check_time}')
                print(f'Current time: {current_time1}')
                await channel.send(content=f'Recent sales have been made. Embedding... Last check time= {last_check_time}\nCurrent time: {current_time1}')
                i=len(list1)-1
                for item in list1:
                    print(f'Array iteration '+str(i))
                    listobj=list1[i]
                    await embed_sender_sales(listobj, channel, ctx)
                    i-=1
            x=1
            return x, current_time1
        else:
            print(f'Key does not exist- API call unsuccessfull. Trying again next iteration')
            return x, current_time1
    except: 
        print(f'Error: Json string could not be loaded from response. Trying again next iteration')
        return 0, current_time1

async def embed_sender_acc_lists(listobj, channel3, ctx):
    #
    print(f'Creating acc listing embed...')
    if (listobj['asset']['name'] is None):
        titlename = listobj['asset']['asset_contract']['name'] + ' '+listobj['asset']['token_id'] + ' listed!'
    else: 
        titlename = listobj['asset']['name'] + ' listed!'
    embed = discord.Embed(
        title = titlename,
        timestamp = dateutil.parser.isoparse(listobj['created_date']),
        url = listobj['asset']['permalink'],
        colour = discord.Colour.blue())
    embed.set_author(name=client.user.display_name,  
        icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=listobj['asset']['collection']['image_url'])
    embed.add_field(name='Name', value=listobj['asset']['name'], inline=False)
    price = Web3.fromWei(int(listobj['starting_price']), 'ether')
    embed.add_field(name='Listed For', value=str(price) + 'Ξ', inline=True)
    date_obj = datetime.strptime(listobj['created_date'],"%Y-%m-%dT%H:%M:%S.%f")
    embed.add_field(name='Date Listed', value=date_obj.strftime('%d %b, %Y %H:%M:%S'), inline=False)
    embed.set_image(url=listobj['asset']['image_url'])
    embed.set_footer(text='Listed on OpenSea', icon_url='https://files.readme.io/566c72b-opensea-logomark-full-colored.png')
    await channel3.send(embed=embed)
    print(f'Account-listing embed sent\n# # # # # # #\n')

async def get_acc_lists(acc, last_check_time, api_key, channel3, ctx):
    url = "https://api.opensea.io/api/v1/events"
    querystring = {"account_address":acc,"event_type":"created","only_opensea":"false","offset":"0","limit":"20","occurred_after":last_check_time}
    headers = {'X-API-KEY': api_key}
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(f'Account listings data retrieved. Trying to extract-')
    try: 
        acc_lists = json.loads(response.text)
        #Check sales dict for 'asset_events' key to check if call was a success
        key = 'asset_events'
        x = 0
        if key in acc_lists.keys():
            print(f'Key exists- API call successful')
            acc_list = acc_lists['asset_events']
            print(f'json data loaded')
            if (len(acc_list)==0):
                print(f'No recent lists since last check')
            else: 
                print(f'Recent lists have been made. Embedding... ')
                i=len(acc_list)-1
                for item in acc_list:
                    print(f'Array iteration '+str(i))
                    listobj=acc_list[i]
                    await embed_sender_acc_lists(listobj, channel3, ctx)
                    i-=1
            x=1
            return x
        else: 
            print(f'Key does not exist- API call unsuccessfull. Trying again next iteration')
            return x
    except: 
        print(f'Error: Json string could not be loaded from response. Trying again next iteration')
        return 0


#get_floor_price from collection (Every 60 seconds)
def get_floor_price(collection_slug, api_key):

    default_f_price = 0 #replace this with manual floor price
    f_price = -1 
    try: 
        #recursive function, checking several random asset owners until one is found that can retrieve floor price
        def random_owner(collection_slug, api_key, j):
            #https://api.opensea.io/api/v1/assets
            url = "https://api.opensea.io/api/v1/assets"
            querystring = {"order_direction": 'desc', "offset": '0', "limit": '50', "collection": collection_slug}
            headers = {'X-API-KEY': api_key}
            response = requests.request("GET", url, headers=headers, params=querystring)
            print(f'Random asset owner address retrieved.')
            assets = json.loads(response.text)
            assetobj=assets['assets'][j]
            print(f'json data loaded\n')
            #some_owner = assetobj['collection']['payout_address'] 
            some_owner = assetobj['owner']['address']
            return some_owner
        
        j=0
        some_owner = random_owner(collection_slug, api_key, j)

        #Passing random owner account address to collections-search api endpoint

        #url = "https://api.opensea.io/api/v1/collections/"+collection_slug+'/'
        def retrieve_floor(some_owner, api_key, f_price, j):
                print(f'Trying iteration/random owner {j+1} for retrieving floor price')
                url2 = "https://api.opensea.io/api/v1/collections/"
                querystring2 = {"asset_owner":some_owner,"offset":"0","limit":"50"}
                headers2 = {"X-API-KEY": api_key}
                response2 = requests.request("GET", url2, headers=headers2, params=querystring2)
                print(f'Collections with that owner retrieved.')
                col = json.loads(response2.text)
                print(col)
                collectionsarr = col
                #f_price = col['collection']['stats']['floor_price']
                i = 0
                #f_price = 0
                for item in collectionsarr:
                    slug = collectionsarr[i]['slug']
                    if (slug == collection_slug):
                        f_price = collectionsarr[i]['stats']['floor_price']
                        break
                    i+=1
                if (f_price !=-1):
                    return f_price
                else:
                    j+=1
                    some_owner = random_owner(collection_slug, api_key, j)
                    f_price = retrieve_floor(some_owner, api_key, f_price, j)
                    return f_price
        while (f_price==-1):
            f_price = retrieve_floor(some_owner, api_key, f_price, j)
        print(f'Floor price retrieved. (={f_price}\n----------------')
        return f_price
    except:
        print(f'Floor price retrieval failed. Setting manual floor price to {default_f_price}')
        return default_f_price


#Discord commands endpoint->
@client.command() 
async def start_check(ctx):
  await client.wait_until_ready()
  print(f'Start check command received. Beginning now. \n----------------------------------\n\n-----------------------------\n')
  last_check_time=cfg["last_check_time"]
  collection_slug=cfg["collection_slug"]
  api_key = cfg["opensea_api_key"]
  factor = cfg["factor"]
  acc = cfg['account_address']
  fpcheck_buffer = 0 #To check floor price every 60 seconds
  i = 0
  chan_id1= int(cfg['channel_id_colsales'])
  chan_id2 = int(cfg['channel_id_collists'])
  chan_id3 = int(cfg['channel_id_acclists'])
  channel1 = client.get_channel(id=chan_id1)
  channel2 = client.get_channel(id=chan_id2)
  channel3 = client.get_channel(id=chan_id3)
  await ctx.channel.send(content=f'Config Data:\n-------------------------------\nCollection Slug: {collection_slug}\nAccount Address: {acc}\nCollection Sales Channel ID: {chan_id1}\nCollection Listings Channel ID: {chan_id2}\nAccount Listings Channel ID: {chan_id3}\nInitialization Check Time: (unix format) {last_check_time}\nOpenSea API Key: {api_key}\nFactor(Z): {factor} (X+Y<Z will be checked for, where X=List Price, Y=Current Floor Price)\n')
  floor_price = get_floor_price(collection_slug, api_key)
  last_check_arr = [last_check_time, last_check_time, last_check_time]
  while not client.is_closed():
    if (fpcheck_buffer>=60):
        fpcheck_buffer = 0
        floor_price = get_floor_price(collection_slug, api_key)
    print(f'Beginning opensea sales data access loop...')
    a =[1]
    response = [0,0,0]
    #Response (0 for fail, 1 for success) returned from functions determines whether 'last_check_time' will update or not
    for item in a:
        print(f'\n---*----*-----*----*----\nCalling get_sales(): ')
        a = await get_sales(collection_slug, last_check_arr[0], api_key, channel1, ctx)
        response[0] = a[0]
        if (response[0]==1):
            last_check_arr[0]=a[1]
            print(f'Last check time updated to: {last_check_arr[0]}')
            await channel1.send(content=f'Last check time updated to: {last_check_arr[0]}')
        print(f'\n---*----*-----*----*----\nCalling get_lists(): ')
        response[1] = await get_lists(collection_slug, last_check_arr[1], api_key, floor_price, factor, channel2, ctx)
        if (response[1]==1):
            last_check_arr[1]=time.time()
        print(f'\n---*----*-----*----*----\nCalling get_acc_lists(): ')
        response[2] = await get_acc_lists(acc, last_check_arr[2], api_key, channel3, ctx)
        if (response[2]==1):
            last_check_arr[2]=time.time()
    #last_check_time=time.time()
    fpcheck_buffer +=10
    time.sleep(5)

client.run(TOKEN)