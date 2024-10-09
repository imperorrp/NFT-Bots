bot1 README
-v1.0----------------------------------------------------------------------------------------------------

Features:
Telethon bot to: join channels/groups, leave channels/groups, show list of active channels/groups, and scrape messages from
those groups and send them to one main channel (with custom messages based on the channel/group scraped from)

Menu functions: 1. Active (display active channels/groups. Format: /active)
                2. Add (add channel/group and custom message. Use 'N/A' for no custom message. Format: /add @channel_name "custom message within quotes")
                3. Remove (remove channel/group. Format: /remove @channel_name)

Bot logic: At start and after init() config updates, bot ensures all channels/groups are joined and joins if not, 
           then starts iterating (executed on an async loop, every 30seconds) through list of channels/groups and stores 
	   updating list of latest message-IDs from each. If match found from previous iteration, continue, else push with
	   custom message if any to main telegram channel. Config updates are continuously listened to from messages from an 
	   admin group (Bot1 Admin Group) that the bot must be added to before start, and updates if any (add/remove) 
	   work from next loop iteration onwards.

SETUP:
1. Make sure all dependencies are installed on running system (python v3.5 and up, and py modules in requirements.txt) 
2. Fill out config.json and hash_id.txt: 
	-Go to https://my.telegram.org/auth, grab an api ID and api hash. (Instructions at https://core.telegram.org/api/obtaining_api_id)
	-Add bot's phone number
	-Don't change admin_group_name 
	-Replace/edit main_channel with username of the main channel to post to (bot must be in it and have messaging perms)
	-Replace/edit/add/remove active_channels and corresponding custom_messages as needed, or change them through menu 
	 in Bot1 Admin Group (bot must be in it, again)
3. Make sure bot1.py, hash_id.txt, config.json are in same directory
4. Run bot1.py
5. Once on, bot runs on loop until an error is encountered or script manually closes. Can then use /menu commands to update 
   config.json or stop bot and do manually. 

