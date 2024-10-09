//Index.js (v1.1)

//Index.js 
//README:
//Discord opensea 'listing' and 'minted' detection and automatic/manual attempted buying of NFTs (at list price, as soon as listed)
//Download dependencies, set up config.json, get a discord bot token and put in file named "token.txt" 

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

//create schedulings for minted assets to buy for when listed->
function sched_asset(asset_contract_address, token_id){
    this.asset_contract_address=asset_contract_address;
    this.token_id=token_id;
}
var schedule = []

//Buy_sched->
function buy_sched(asset_contract_address, token_id){
    const obj = sched_asset(asset_contract_address, token_id);
    schedule.push(obj);
} 


//Search for asset sell_order, matches with buy_order->
async function buy_now(asset_contract_address, token_id, accountAddress, message) {
    console.log("Buy now order being made.");
    const order = await seaport.api.getOrder({   // Extracting order to fulfill
            asset_contract_address,
            token_id,
            side: 1 
    });
    const ltime = order.listingTime;
    const exp_time = order.expirationTime;
    const price = order.currentPrice;
    const fEthPrice = ethers.utils.formatEther(price.toString());
    await message.channel.send(`Order: \nListing TIme: ${ltime}\nExpiration Time: ${exp_time}\nCurrent Price: ${fEthPrice}ETH\n`);
    console.log('Corresponding sell order retrieved. Attempting to buy...');
    await message.channel.send('Attempting to buy...');
    let isBuySuccess = false;
    try {
        const transactionHash = await seaport.fulfillOrder({ //Fulfilling order
            order,
            accountAddress,
        });
        isBuySuccess = true;
    } catch (error) {
        print_error(error);
    }
    if (isBuySuccess){
        console.log(transactionHash);
        console.log('Buy order made successfully!');
        message.channel.send("Buy order successful!");
    }
    else {
        console.log('Buy order unsuccessful!')
        message.channel.send("Buy order unsuccessful!");
    }
    return; 
};

//check an asset via seaport opensea api->
async function confirm_asset(tokenAddress, tokenId, message){
    var asset = await seaport.api.getAsset({
        tokenAddress: tokenAddress,
        tokenId: tokenId,
    });
    const name=asset.name;
    const image_url=asset.imagePreviewUrl;
    const num_orders = asset.sellOrders.length;
    const owner_link = asset.owner.address;
    const asset_link = asset.openseaLink;
    var count = 0;
    const embed = new Discord.MessageEmbed()
        .setTitle(`${name} asset found`)
        .setColor(0x00AE86)
        .setImage(`${image_url}`)
        .setTimestamp()
        .setURL(`${asset_link}`)
        .addFields({
            name: "Name",
            value: `${name}.`
        })
        .addFields({
            name: "Owner",
            value: `${owner_link}`
        });
    await message.channel.send(embed);
    for (var i = 0; i < num_orders; i++) {
        count++;
        console.log(`Checking order ${count}`);
        const sell_order=asset.sellOrders[i];
        //const ctime = sell_order.createdTime;
        const ltime = sell_order.listingTime;
        var exp_time = sell_order.expirationTime;
        const price = sell_order.currentPrice;
        const fEthPrice = ethers.utils.formatEther(price.toString());
        if (exp_time === 0){
            exp_time='N/A'
        }
        await message.channel.send(`Sell Order ${count}: \nListing TIme: ${ltime}\nExpiration Time: ${exp_time}\nCurrent Price: ${fEthPrice}ETH\n`);
        await message.channel.send('Use `buy_now {asset-contract-address} {asset-token-id}` to fulfill this order!')
    }
}

function send_embed_listing(event){
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
    var channel = client.channels.cache.get(data.listing_channel_id);
    const embed = new Discord.MessageEmbed()
        .setTitle(`${tokenName} listed!`)
        .setColor(0x00AE86)
        .setAuthor(`${username}`, "https://storage.googleapis.com/opensea-static/opensea-profile/9.png")
        .setFooter('Listed on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
        .setImage(`${image}`)
        .setTimestamp()
        .setURL(`${openseaLink}`)
        .addFields({
            name: "Name",
            value: `${tokenName}.`
        })
        .addFields({
            name: "Amount(Starting Price)",
            value: `Eth: ${fEthPrice}, USD: ${fUsdPrice}`
        })
        .addFields({
            name: "Listing Date/Time",
            value: `${time}`
        });;
    channel.send(embed);
    console.log('Listing embed sent');
}

function send_embed_mint(event){
    console.log("Preparing to send embed...");
    const tokenName = _.get(event, ['asset', 'name']);
    const openseaLink = _.get(event, ['asset', 'permalink']);
    const time = _.get(event, ['asset', 'asset_contract', 'created_date']);
    const image = _.get(event, ['asset', 'image_preview_url']);
    const username = _.get(event, ['to_account', 'user', 'username']);
    const address = _.get(event, ['asset','asset_contract','address']);
    const token_id = _.get(event, ['asset','token_id']);
    var channel = client.channels.cache.get(data.minting_channel_id);
    const embed = new Discord.MessageEmbed()
        .setTitle(`${tokenName} minted!`)
        .setColor(0x00AE86)
        .setAuthor(`${username}`, "https://storage.googleapis.com/opensea-static/opensea-profile/9.png")
        .setFooter('Listed on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
        .setImage(`${image}`)
        .setTimestamp()
        .setURL(`${openseaLink}`)
        .addFields({
            name: "Name",
            value: `${tokenName}.`
        })
        .addFields({
            name: "Asset Contract Address",
            value: `${address}`
        })
        .addFields({
            name: "Token ID",
            value: `${token_id}`
        })
        .addFields({
            name: "Time of Mint",
            value: `${time}`
        })
    channel.send(embed);
    channel.send('(Use `!buy_sched {asset_contract_address} {token_id}` to schedule a matching order for when listed)');
    console.log('Mint embed sent');
}

function checkapi(lastcheck, message, accountAddress){

    const options = {
        method: 'GET',
        url: 'https://api.opensea.io/api/v1/events',
        params: {
            account_address: data.check_opsea_account_address,
            only_opensea: 'false', 
            offset: '0', 
            limit: '20', 
            occurred_after: lastcheck
        },
        headers: {Accept: 'application/json'}
    };
    axios.request(options).then(function (response) {
        console.log("Data extracted");
        const events = _.get(response, ['data', 'asset_events']);
        console.log(`${events.length} listings/mints since last check.`);
        _.each(events, (event) => {
            console.log('Events loop beginning...')
            var type = _.get(event, 'event_type');
            if (type === "created"){
                console.log('Type-"created" detected.\n')
                send_embed_listing(event);
                const asset_contract_address=_.get(event, ['asset','asset_contract','address']);
                const token_id = _.get(event, ['asset','token_id']);
                if (schedule.some(obj => obj.asset_contract_address === asset_contract_address && obj.token_id === token_id)){
                    buy_now(asset_contract_address, token_id, accountAddress, message);
                }
            }
            else if (type === "transfer"){
                var username = _.get(event, ['from_account', 'user', 'username']);
                if (username === "NullAddress"){
                    send_embed_mint(event);
                }
            }
        });
    }).catch(function (error) {
        console.error(error);
    });
}

prefix = "!";

client.on('message', message => {
    if(!message.content.startsWith(prefix) || message.author.bot) return;
    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const command = args.shift().toLowerCase();
    const startepoch = data.init_check_time;
    var lastcheck = startepoch;
    const accountAddress = data.buyer_wallet_address;

    if (command === "start"){
        count = 1
        setInterval(async function(){
            console.log(`Check +${count}`);
            count+=1; 
            var lc = Math.round(Date.now() / 1000);
            checkapi(lastcheck, accountAddress, message);
            lastcheck = lc.toString();
        },10000)
    }
    else if(command === "ping"){
        message.reply('pong!');
    }
    else if(command === "buy_now"){
        const asset_contract_address = args[0];
        const token_id = args[1];
        buy_now(asset_contract_address, token_id, accountAddress, message);
    }
    else if(command === "buy_sched"){
        const asset_contract_address = args[0];
        const token_id = args[1];
        buy_sched(asset_contract_address, token_id);
    }
    else if(command === "check"){
        var tokenAddress = args[0];
        var tokenId = args[1];
        message.channel.send('Checking...');
        confirm_asset(tokenAddress, tokenId, message);
    }
});

client.login(TOKEN);