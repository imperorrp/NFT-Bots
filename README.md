# Bot Portfolio 

These are a few of the the older bots I'd made while freelancing for NFT communities starting late 2021 onwards -my first real experience writing real-use code and getting paid for it. I'm open sourcing some of them. 

I did some cleaning up and gathered them together here: More code on Github = more data for AI copilots to train on (Doing my part to accelerate the coming of the Singularity).

There's myriad functionalities across them, but they are built to interact with the APIs of and work on Discord, Telegram and Twitter. There's other APIs called by them too, especially Opensea, so make sure to get keys for each if running these. Otherwise, these are free to build upon, adapt, and modify further.  

## Organization 

Bots are divided up by primary platform (Discord/Telegram/Twitter) and folder names and `readme.md` files added to each have an overview of what they do. Some might have `readme.txt` files too- those are a bit more detailed. Changelogs in some exist too. 

**Folder tree**:

```
discord/
    NFT-Tracking/
        track-collection-auction-bids/
        track-collection-listings-with-svg-support/
        track-collection-sales-with-svg-support/
        track-collections-sales-listings-and-acc-listings-by-condition-floor/
        track-collections-sales-listings-and-daily-stats/
        track-collections-sales-listings-floor/
        track-listings-by-traits-and-price/
    NFT-Trading/
        buy-collection-listings-below-X-price/
        buy-newly-minted-and-listed-nfts/
        make-offers-by-collections/
    Other-custom-bots/
        autokicker-bot/
        music-bot/
telegram/
    telegram-channel-to-discord-message-forwarder/
    telegram-groups-and-channels-scraper-to-centralized-channel/
twitter/
    track-collection-sales-listings-and-daily-stats/
```

## Tech Stack 

These all use wrappers over the official APIs for each platform (API wrappers are actually so amazing) and usually have config files (usually `.json`s, some `.yaml`s) and placeholders for sensitive secrets like bot tokens in `.txt` files. 

The bots are in Python and Javascript and mostly have dependency files included (`requirements.txt` for Python and `package.json` for Javascript)

Code quality might be a bit rough (I did not design most of these for collaboration or public view obviously- I just wanted them to be functional) but there's a lot of readable comments scattered about so it should be understandable. 

## Setup/Run:

- Install dependencies
- Set up config files
- Get relevant bot tokens and API keys (Discord, Opensea, etc.)
- Run with Python or Node js. 

Some updates may be required- the Twitter (Now X) API, for example, has seen a lot of changes in the last couple of years under new leadership. Some things may be deprecated. 

# Screenshots/Links 

## Twitter NFT collection tracking bot: 

Tracks an NFT collection's sales and posts data about it and the sale including NFT traits. I had a demo up running on a personal VPS (shoutout to Pebblehost!) to showcase functionality to potential clients until mid-2023, which can be viewed here: https://x.com/EthImperor 

![twitter-track-collection](image.png)
![twitter-track-collection-2](image-1.png)
![twitter-track-collection-3](image-2.png)

<br>

---------------------------

<br>
<br>

 ## Some of the Discord bots:

- Buy newly minted and listed NFTs via Discord:

![buy-newly-minted-and-listed-nfts](image-3.png)

<br>
<br>

- Track updates to NFT collection auctions on Opensea 

![track-collection-auction-bids](nft_auction_tracking.gif)

<br>
<br>

- Make offers on all NFTs in a collection
 
![make-offers-by-collections](image-4.png)

<br>
<br>

- Track NFT collection listings by traits and price

![track-listings-by-traits-and-price](image-5.png)

<br>
<br>

- Track NFT collection sales that have NFT images stored as SVGs

![track-collection-sales-with-svg-render](image-6.png)

<br>
<br>

- Track NFT collection listings 

![track-collection-listings](image-7.png)

<br>
<br>

- Track NFT collection sales, listings, and daily stats

![track-collection-sales-listings-and-daily-stats-1](https://github.com/user-attachments/assets/6e73dc5c-0ecf-44c3-b759-ad1502cdc2f3)

![track-collections-sales-listings-and-daily-stats-2](image-9.png)

![track-collection-sales-listings-and-daily-stats-3](https://github.com/user-attachments/assets/f27d462b-f5d4-4a21-9460-3165d18eda81)

<br>
<br>

- Automod for Discord servers 

![image](https://github.com/user-attachments/assets/c9ab0240-292c-4f48-9179-df601d2798b4)

<br>
<br>

- Music Bot for Discord servers

![image](https://github.com/user-attachments/assets/d05b6141-45ce-4b75-908b-6c67ab63e58e)

![image](https://github.com/user-attachments/assets/2ca6bc8c-6806-41f8-a05b-a9982d302130)

![image](https://github.com/user-attachments/assets/a6f63a8f-4846-46ab-843e-2b3cf82fd5bf) 


<br> 
<br>


--------------------------

<br>


