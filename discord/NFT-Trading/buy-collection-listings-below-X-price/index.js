//OpenSea Bot 
//Search through new listed NFTs of a collection and buys NFTs at a specific price or lower when listed
//(Algo: 1. retrieve assets that meet criteria (price < X), 1.5. post embed of asset to discord, 2a. retrieve asset's listing sale_order, 2b. fulfill that order)
//With Discord interface

//Loading dependencies (node v14.5, discord.js v12)
const axios = require('axios');
const { ethers } = require('ethers');
const _ = require('lodash');
const fs = require('fs');
const TOKEN = fs.readFileSync("token.txt").toString(); 
const Discord = require('discord.js'); //v-12
const client = new Discord.Client();
const data = JSON.parse(fs.readFileSync("config.json"));

//Begin->
client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});
  
//Setting up OpenSea-js' seaport, provider-engine, wallet-access, etc.->
const Web3 = require('web3');
const opensea = require("opensea-js");
const hdwallet_provider = require('@truffle/hdwallet-provider');

//some utilities
function print_sea_log(text) {
    arg_seaverb=True;
    if (arg_seaverb) {
      console.log(
        '\n   OpenSea:  ' +
        `${text}`.replace('\n', '\n             '));
    }
}
function print_error(error) {
    const text = error.message ? `Error:  ${error.message}` : `${error}`;
    console.log(text);
}

//Init for seaport+provider->
const network='mainnet';//or rinkeby
const mnemonic=data.wallet_mnemonic;
const node_key=data.infura_api_key;
function init_seaport(){
    try{
        const network_name = network === 'mainnet' || network === 'live' ? 'mainnet' : 'rinkeby';
        const providerEngine = new hdwallet_provider({
        mnemonic: {
            phrase: mnemonic
        },
        providerOrUrl: 'https://' + network_name + '.infura.io/v3/' + node_key
    });
    var api_config = {
        networkName:
          network === 'mainnet' || network === 'live'
            ? opensea.Network.Main
            : opensea.Network.Rinkeby,
        //apiKey: opensea_key (optional)
    };

    console.log('Initializing...\n')
    return new opensea.OpenSeaPort(
        providerEngine,
        api_config,
        (arg) => print_sea_log(arg)
    );
  
    } catch (error) {
      console.log(error);
    }
    return null;
}
console.log('Initializing OpenSea SDK...');
const seaport = init_seaport();
console.log('Seaport initialized!\n')

//Seaport initialized^

prefix = "!";

//buy_asset()
async function buy_asset(tokenAddress, tokenId, message){
    //
    accountAddress = data.buyer_wallet_address;
    console.log("Buy now order being made.");
    asset_contract_address=tokenAddress;
    token_id = tokenId;
    const order = await seaport.api.getOrder({   // Extracting order to fulfill
            asset_contract_address,
            token_id,
            side: 1 
    });
    await message.channel.send('Attempting to buy...');
    let isBuySuccess = false;
    try {
        const transactionHash = await seaport.fulfillOrder({ //Fulfilling order
            order,
            accountAddress,
        });
        isBuySuccess = true;
        console.log(transactionHash);
    } catch (error) {
        print_error(error);
    }
    if (isBuySuccess){
        console.log(transactionHash);
        console.log('Buy order made successfully!');
        await message.channel.send("Buy order successful!");
    }
    else {
        console.log('Buy order unsuccessful!')
        await message.channel.send("Buy order unsuccessful!");
    }
}

//sendSellOrder()
async function sendSellOrder(tokenAddress, tokenId, message){
    const asset = await seaport.api.getAsset({
        tokenAddress: tokenAddress,
        tokenId: tokenId,
    });
    const num_orders = asset.sellOrders.length;
    let count=0;
    for (var i = 0; i < num_orders; i++) {
        count++;
        console.log(`Checking order ${count}`);
        const sell_order=asset.sellOrders[i];
        //const ctime = sell_order.createdTime;
        const ltime = sell_order.listingTime;
        const exp_time = sell_order.expirationTime;
        const price = sell_order.currentPrice;
        const fEthPrice = ethers.utils.formatEther(price.toString());
        if (exp_time === 0){
            exp_time='N/A'
        }
        await message.channel.send(`Sell Order ${count}: \nListing TIme: ${ltime}\nExpiration Time: ${exp_time}\nCurrent Price: ${fEthPrice}ETH\n`);
    }
}

//sendAssetEmbed()
async function sendAssetEmbed(event, accountAddress, message){
    //
    console.log("Preparing to send embed...");
    const tokenName = _.get(event, ['asset', 'name']);
    const openseaLink = _.get(event, ['asset', 'permalink']);
    const totalPrice = _.get(event, 'starting_price');
    const usdValue = _.get(event, ['payment_token', 'usd_price']);
    const fEthPrice = ethers.utils.formatEther(totalPrice.toString());
    const fUsdPrice = (fEthPrice * usdValue).toFixed(2);
    const time = _.get(event, ['asset', 'asset_contract', 'created_date']);
    const username = _.get(event, ['from_account', 'user', 'username']);
    const image = _.get(event, ['asset', 'image_preview_url']);
    //const channel = client.channels.cache.get(data.listing_channel_id);
    const embed = new Discord.MessageEmbed()
        .setTitle(`${tokenName} listed for below ${data.price_below_eth}!`)
        .setColor(0x00AE86)
        .setAuthor(`${username}`, "https://storage.googleapis.com/opensea-static/opensea-profile/9.png")
        .setFooter('Listed on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
        .setImage(`${image}`)
        .setTimestamp()
        .setURL(`${openseaLink}`)
        .addFields({
            name: "Name",
            value: `${tokenName}`
        })
        .addFields({
            name: "Amount(Starting Price)",
            value: `Eth: ${fEthPrice}, USD: ${fUsdPrice}`
        })
        .addFields({
            name: "Listing Date/Time",
            value: `${time}`
        });;
    message.channel.send(embed);
    console.log('Listing embed sent\n');
    const tokenId = _.get(event, ['asset', 'token_id']);
    const tokenAddress = _.get(event, ['asset', 'asset_contract', 'address']);
    console.log('Retrieving sell orders: ');
    sendSellOrder(tokenAddress, tokenId, message);
    console.log('Fulfilling sell order: ');
    buy_asset(tokenAddress, tokenId, message);
}

//checkapi() 
function checkapi(lastcheck, accountAddress, message){
    const options = {
        method: 'GET',
        url: 'https://api.opensea.io/api/v1/events',
        params: {
            collection_slug: data.collection_slug,
            event_type: 'created',
            only_opensea: 'false', 
            offset: '0', 
            limit: '20', 
            occurred_after: lastcheck
        },
        headers: {Accept: 'application/json'}
    };
    axios.request(options).then(function (response) {
        console.log("New listings data extracted.");
        const events = _.get(response, ['data', 'asset_events']);
        console.log(`${events.length} listings since last check.\n`);
        _.each(events, (event) => {
            console.log('Event loop.');
            const price = _.get(event, 'starting_price');
            const fEthPrice = ethers.utils.formatEther(price.toString());//price in eth
            const usdValue = _.get(event, ['payment_token', 'usd_price']);
            const fUsdPrice = (fEthPrice * usdValue).toFixed(2);
            if (fEthPrice < parseFloat(data.price_below_eth)){
                sendAssetEmbed(event, accountAddress, message);//post embed of asset to Discord
            }
        });
    }).catch(function (error) {
        console.error(error);
    });
}


//Discord commands endpoint:
client.on('message', message => {
    if(!message.content.startsWith(prefix) || message.author.bot) return;
    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const command = args.shift().toLowerCase();
    const startepoch = data.init_check_time;
    var lastcheck = startepoch;
    const accountAddress = data.buyer_wallet_address;

    if (command === "start_check"){  
        count = 1
        setInterval(async function(){
            console.log(`Check ${count}`);
            count+=1; 
            var lc = Math.round(Date.now() / 1000);
            checkapi(lastcheck, accountAddress, message); //Checks 'events' via the opensea api for new 'listings'
            lastcheck = lc.toString();
        },10000)
    }
    else if(command === "ping"){
        message.reply('pong!');
    }
});

client.login(TOKEN);