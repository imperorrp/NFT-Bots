README:
OpenSea Bot

To: Search through new listed NFTs of a collection and buys NFTs at a specific price or lower when listed

Algorithm: 
	1. retrieve assets that meet criteria (price < X), 
	1.5. post embed of asset to discord, 
	2a. retrieve asset's listing sale_order, 
	2b. fulfill/match that order

Set-up and Execution:
1. Get infura API key (Follow guide at https://ethereumico.io/knowledge-base/infura-api-key-guide/)
2. Create a Discord Bot, get Discord bot token, add bot to server you have admin priveleges in
3. Fill out config.json
4. Make sure you have node.js, and version 14.15.5 (Switch to this if not)
5. Navigate to this folder (command prompt), run 'node index.js'
6. On Discord server the bot's been added to, try '!ping' to check if online
7. Do '!start_check' to begin execution.

Config.json format: 
"buyer_wallet_address" : "",  ->Your metamask/other wallet address
"wallet_mnemonic":"",         ->Your unique wallet mnemonic (Never share with anyone, keep private)
"infura_api_key":"",          ->Infura API Key
"collection_slug":"",         ->Name of collection to search for (suggestion: find out precise name by looking at the opensea url on that collection's page)
"init_check_time":"",         ->Initial time from which onwards the bot checks for new listings. Enter current time to start checking listings from time of run. Format: unix/epoch time (Get epoch timestamp from readable date/time at https://www.epochconverter.com/) 
"price_below_eth":""          ->Price below which's listings you want purchased. 