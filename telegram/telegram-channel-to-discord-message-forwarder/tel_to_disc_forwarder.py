#Telegram groups to discord message forwarder
#v3.0
#last edit: 27th Jan 2022
#USAGE: in terminal- 'python tel_to_disc_forwarder.py config.yml' without quotes
#----------------------------------------------------------------------

#importing dependencies->
from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel
import yaml
import sys
import logging
import subprocess
import time

print('\n------------------------------------------\nTELEGRAM TO DISCORD MESSAGE FORWARD BOT\n----------------------------------------------')

#logging->
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)

#execution code->

#setup->
def start(config):

    # Telegram Client Init
    client = TelegramClient(config["session_name"], 
                            config["api_id"], 
                            config["api_hash"])
    # Telegram Client Start
    client.start()

    #Input Messages Telegram Channels will be stored in these empty Entities
    input_channels_entities = []
    input_channels_names =[]
    file = open('dialogs.txt', 'a+')
    for dialog in client.iter_dialogs():
        strx = str(dialog.name)+ 'has ID' +str(dialog.id)
        print(dialog.name, 'has ID', dialog.id)
        try:
            #writing to dialog.txt file with list of available channels, channel names and channel IDs
            file.write(strx)
            file.write('\n')
            #Use this text file to get correct channel names and IDs^
        except:
            continue
    file.close()

    # Iterating over dialogs and finding new entities and pushing them to our empty entities list above
    for d in client.iter_dialogs():
        print(f'{config["input_channel_ids"]}')
        if d.name in config["input_channel_names"] or d.entity.id in config["input_channel_ids"]:
            input_channels_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
            input_channels_names.append(d.name)
            print(f'dialog {d.name} (id: {d.id}) found in config. Added to input_channel_entities/names\n')
        if str(d.id) in config["input_channel_ids"]:
            input_channels_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
            input_channels_names.append(d.name)
            print(f'%dialog {d.name} (id: {d.id}) found in config. Added to input_channel_entities/names\n')

    if not input_channels_entities:
        logger.error(f"Could not find any input channels in the user's dialogs")
        sys.exit(1)
    
    # Use logging and print messages on your console.     
    logging.info(f"Listening on {len(input_channels_entities)} channels.")
    print(f'Client on bit...')

    def message_iterate(channel_entity, channel_name):
        #iterates over list of one of input_channels_entities' last few chats, checks if the message ID already exists and stores the message ID to a text file if not
        print('\n----------------------')
        #Opens text file (r+ form) for channel_entity->
        file_name = str(channel_name) + ".txt"
        print(f'Opening file "{file_name}"')
        file_obj = open(file_name,"r+")
        last_msg_id = file_obj.read()
        print(f'Last message ID = "{last_msg_id}"')
        file_obj.close()
        list_new = []
        for message in client.iter_messages(entity = channel_entity, limit = 1):
            msg_text = message.message 
            msg_id = str(message.id)
            list_new.append(msg_id)
            if (msg_id == last_msg_id):
                print(f'Message exists. Not forwarded.')
            else:
                #forward to discord
                msg_text = f'**Message from Telegram channel "'+ channel_name+'":**\n\n'+msg_text 
                subprocess.call(["python", "discord_messenger.py", str(msg_text)])
                print(f'Subprocess discord_messenger.py called\n')
                logging.info(f'Message: "{str(msg_text)}", Message ID: "{msg_id}" forwarded.')
            #print(f'Message text = {msg_text}')
        file_obj2 = open(file_name,"w+")
        file_obj2.write(msg_id)
        print(f'Msg ID = {msg_id}')
        file_obj2.close()
        print('-----------------------\n')
        
    def iterationx():
        #creating text files to store message IDs in:
        for channel_name in input_channels_names:
            file_name = str(channel_name) + ".txt"
            file_obj = open(file_name,"w+")
            print(f'Created file "{file_name}"')
            file_obj.close()
        while True:
            #iterates over every channel to check
            count = 1
            for channel_entity in input_channels_entities:
                print(f'\niteration {count}: ')
                x =count-1
                channel_name = input_channels_names[x]
                message_iterate(channel_entity, channel_name)
                count+=1
            time.sleep(5)
            #reruns after 5 second intervals^

    #client.run_until_disconnected()
    with client:
        client.loop.run_until_complete(iterationx())

#main function->
if __name__ == "__main__":
    with open("config.yml", "rb") as f:
        config = yaml.safe_load(f)
        print(f'Config.yml file loaded. Initialising...')
    start(config)
