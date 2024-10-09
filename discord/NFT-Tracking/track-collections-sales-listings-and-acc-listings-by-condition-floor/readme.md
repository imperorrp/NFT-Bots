## Overview

Bot instance checks:

- New NFT listings (offer to sell) and sales (just sold) for an NFT collection on Opensea 
- New NFT listings made by a particular Opensea user (unique Ethereum wallet address) 

Subject to condition:

- NFT listings should have a price less than `floor_price + factor`, where `factor` is user set (and measured in USD)

and post updates automatically to specified Discord channels in a server with relevant information. 