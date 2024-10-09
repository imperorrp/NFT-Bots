#BOT1 
#Telethon bot to: join groups, leave groups, show list of groups, and scrape messages from those groups
#and send them to one main channel (with custom messages based on the group scraped from)
#Bot should function with a menu that allows edits to the config. (also stop/start the bot after config updates are complete)
#Menu functions: 1. Active (display active groups)
#                2. Add (add channel/group and custom message. Use 'N/A' for no custom message.
#                3. Remove (remove channel/group)
#Bot logic: At start and after config updates, bot first does join_group() to ensure all are joined, 
#           then starts iterating through list of groups and stores updating list of latest message-IDs
#           from each. If match found from previous iteration, continue, else push with custom message 
#           if any to main telegram channel. Config updates are listened to from messages from an admin group.


#v1.0 (14th Jan 2022)----------------------------------------------------------------------------

#Loading dependencies->
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import time 
import json
import asyncio

#Loading config data from config file
f = open("config.json",)
cfg = json.load(f)
main_channel = cfg['main_channel']
active_channels = cfg['active_channels']
custom_messages = cfg['custom_messages']
phone = cfg['phone_number']
admin_group = cfg['admin_group_name']
#also defining init() func to init again for local variables
async def init():
    f = open("config.json",)
    cfg = json.load(f)
    main_channel = cfg['main_channel']
    active_channels = cfg['active_channels']
    custom_messages = cfg['custom_messages']
    phone = cfg['phone_number']
    admin_group = cfg['admin_group_name']

#Auth stuff (get your values from my.telegram.org)
api_id = cfg['api_id']
api_hash = open("hash_id.txt","r").readline()
client = TelegramClient('anon', api_id, api_hash)
client.start()

#Storing latest message IDs from each group->
latest_msg_id_dict = {}
#{'channel1':'some_msg_id', 'channel2':'another_msg_id', ...}
#latest_msg_id_dict['channelx'] = 'new_msg_id'

#Ensure all groups are joined from the active_channels list->
async def join_groups(me):
    i = 0
    for item in active_channels:
        await client(JoinChannelRequest(active_channels[i]))
        time.sleep(2)
        print(f'Joined group id: '+active_channels[i]+'\n')
        i+=1
    print(f'All groups joined\n')

#function to send new channel messages with custom text added to main group->
async def send_messages(message, channel):
    active_channels = cfg['active_channels']
    custom_messages = cfg['custom_messages']
    ct_pos = active_channels.index(channel)
    custom_text = custom_messages[ct_pos]
    sending_text = ""
    if (custom_text == "N/A"):
        sending_text = message.message
        print(f'Not adding custom message...')
    else:
        sending_text = message.message + "\n"+custom_text 
        print(f'Adding custom message "{custom_text}"...')
    print(f'Sending text = {sending_text}')
    await client.send_message(main_channel, sending_text)
    print(f'Message sent to main channel.')


#Main() function->
async def main():

    print('In main function. Joining groups init')
    me = await client.get_me()
    await join_groups(me)
    print('join_groups() ran. \nBeginning message retrieval loop...')
    while True:
        print('%--------Message retrieval loop------')
        await init()
        print('%--------Init() called--------%')
        #reload active_channels from cfg (to account for admin via-menu updates)
        active_channels = cfg['active_channels']
        for channel in active_channels:
            print(f'Checking last message send to {channel} channel')
            async for message in client.iter_messages(channel, limit =1):
                #msg_text = message.message
                msg_id = str(message.id)
                if channel in latest_msg_id_dict:
                    if (latest_msg_id_dict[channel] == msg_id):
                        print(f'Message ID: {msg_id} already exists, not sent.')
                    else: 
                        print(f'Old message ID: {latest_msg_id_dict[channel]}.')
                        print(f'Sending new message ID:{msg_id} to main group...')
                        await send_messages(message, channel)
                        print('Message sent.')
                        latest_msg_id_dict[channel] = msg_id
                        print(f'Message ID updated')
                else:
                    latest_msg_id_dict[channel] = msg_id
                    print(f'Dict entry created for {channel}')
                    print(f'Sending new message ID:{msg_id} to main group...')
                    await send_messages(message, channel)
                    print('Message sent.')
                    #creating dictionary entry for new channel if doesn't exist^
                print(f'Message ID added')
        #sleeps 20 seconds before next loop iter->
        await asyncio.sleep(30)
        #send config update menu to admin
       
print('Starting Bot. \n---------------------------------\n')
print(f'Listening for new messages from admin {admin_group}')
#@client.on(events.NewMessage(chats=("Bot1 Admin Group")))
menu_text = "**MENU:**\n1. Add channel (say '/add {@channel_entity} {custom_message}')\n2. Remove channel (say '/remove @channel_entity)\n3. Active channels (say '/active)\n"

@client.on(events.NewMessage(chats=('Bot1 Main Group')))
async def handler(event):
    print('!!!!!!!!!!Message retrieved.!!!!!!!')
    await init()
    print('!!!---------init() called--------!!!')
    chat_from = event.chat if event.chat else (await event.get_chat()) # telegram MAY not send the chat enity
    chat_title = chat_from.title
    print(f'Message = {event.message.message}, chat_title= {chat_title}')
    msg_text = event.message.message
    msg_1 = msg_text.split()[0]
    if (msg_text == '/Hi' or msg_text == '/Hey'):
        await asyncio.sleep(2)
        await client.send_message(chat_from, 'Hi!')
    elif (msg_text == '/Menu' or msg_text == '/menu' or msg_text == '/MENU'):
        await asyncio.sleep(2)
        await client.send_message(chat_from, menu_text)
    elif (msg_text.split()[0] == '/add' or msg_text.split()[0] == '/Add' or msg_text.split()[0] == '/ADD'):
        msg_2 = msg_text.split()[1]
        msg_3 = msg_text.split('"')[1]
        print(f'/add {msg_2} {msg_3} invoked')
        cfg['active_channels'].append(msg_2)
        active_channels = cfg['active_channels']
        cfg['custom_messages'].append(msg_3)
        custom_messages = cfg['custom_messages']
        print('Config changes made. (addition) Pushing to json file...')
        config_file = open("config.json", "r")
        json_object = json.load(config_file)
        config_file.close()
        json_object['active_channels'] = cfg['active_channels']
        json_object['custom_messages'] = cfg['custom_messages']
        config_file = open("config.json","w")
        json.dump(json_object, config_file)
        config_file.close()
        print('config.json updated.')
        await asyncio.sleep(2)
        await client.send_message(chat_from, f'Added channel "{msg_2}"')
        if (msg_3 != 'N/A'):
            await client.send_message(chat_from, f'With custom message "{msg_3}"')
        else:
            await client.send_message(chat_from, f'With no custom message')
    elif (msg_text.split()[0] == '/remove' or msg_text.split()[0] == '/Remove' or msg_text.split()[0] == '/REMOVE'):
        msg_2 = msg_text.split()[1]
        print(f'/remove {msg_2} invoked')
        ind = cfg['active_channels'].index(msg_2)
        cfg['active_channels'].remove(msg_2)
        active_channels = cfg['active_channels']
        cfg['custom_messages'].pop(ind)
        custom_messages = cfg['custom_messages']
        print('Config changes made. (removal) Pushing to json file...')
        config_file = open("config.json", "r")
        json_object = json.load(config_file)
        config_file.close()
        json_object['active_channels'] = cfg['active_channels']
        json_object['custom_messages'] = cfg['custom_messages']
        config_file = open("config.json","w")
        json.dump(json_object, config_file)
        config_file.close()
        print('config.json updated.')
        await asyncio.sleep(2)
        await client.send_message(chat_from, f'Removed channel "{msg_2}"')
    elif (msg_text == '/active' or msg_text == '/Active' or msg_text == '/ACTIVE'):
        text = '**Currently Active Channels:**\n'
        i = 0
        for channel in cfg['active_channels']:
            text = text + "Channel: "+ channel + " | Custom Message: " + cfg['custom_messages'][i] + "\n"
            i+=1
        print(f'Active list: {text}')
        await asyncio.sleep(2)
        await client.send_message(chat_from, text)
    else: 
        await asyncio.sleep(2)
        await client.send_message(chat_from, f'Could not parse {msg_text} command. Please try again.')
        #with client.conversation(chat_from) as conv:
        #    await conv.send_message(menu_text)
        #    menuoption = conv.get_response()
        #    if (menuoption != '/add' or '/remove' or '/active'):

    #sender = await event.get_sender()
    #await client.send_message(event.input_sender, 'Hi')
    #print('Hi sent\n----------------')
    #asyncio.sleep(10)

#logging in if session files not added yet->
if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))


#client.loop.create_task(main())
#client.start()
#client.run_until_disconnected()
with client:
    client.loop.run_until_complete(main())



