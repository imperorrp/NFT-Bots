README:

Bot Purpose: Listens to new auctions/listings from a collection, creates threads in a Discord channel, feeds the thread with bids/buy offers/sell offers as made as they are made

Setup:
1. Fill in config.json with required collection/initial start time (Initial start time can be any time in unix epoch format. Enter current time to make the bot make live updates from present onwards)
2. Enter custom discord bot token
3. Invite the bot to a server (make sure bot has necessary perms-messages, threads, embedding)
4. Initiate with =check_auctions