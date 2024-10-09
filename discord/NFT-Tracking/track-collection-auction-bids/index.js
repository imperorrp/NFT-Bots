//OpenSea Auction Thread Bot
//Listens to new auctions/listings, creates new Discord thread for it, then feeds the thread with bids/sell or buy offers made for it as they come in

const Discord = require('discord.js')
const fs = require('fs');
const _ = require('lodash');
const { ethers } = require('ethers');
const axios = require('axios');

const TOKEN = fs.readFileSync("bottoken.txt").toString(); 
const { Client, Intents } = require('discord.js');
const client = new Client({ intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES] });

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

const prefix="=";

//Flow: After a listing, create thread with info of initial listing and auction type, and add 
// token-id/asset-contract-address/thread-id object to an array. Then check that array every x seconds and 
// check api for new bids and offers for each asset. If any found, post them to the relevant thread. 

//List of token ids with auctions to check:
var auctions= [];

function auction_obj(token_id, asset_contract_address, name){
    var ob ={};
    ob["token_id"]=token_id;
    ob["asset_contract_address"]=asset_contract_address;
    ob["name"]=name;
    console.log('auction object made');
    return ob;
}

function push_auction_obj(token_id, asset_contract_address, name){
    const obj=auction_obj(token_id, asset_contract_address, name);
    auctions.push(obj);
    console.log('auction X pushed to auctions[]!');
}

function secondsToDhms(seconds) {
    if (seconds === null){
        return 'N/A'
    }
    else {
        seconds = Number(seconds);
        var d = Math.floor(seconds / (3600*24));
        var h = Math.floor(seconds % (3600*24) / 3600);
        var m = Math.floor(seconds % 3600 / 60);
        var s = Math.floor(seconds % 60);
        
        var dDisplay = d > 0 ? d + (d == 1 ? " day, " : " days, ") : "";
        var hDisplay = h > 0 ? h + (h == 1 ? " hour, " : " hours, ") : "";
        var mDisplay = m > 0 ? m + (m == 1 ? " minute, " : " minutes, ") : "";
        var sDisplay = s > 0 ? s + (s == 1 ? " second" : " seconds") : "";
        return dDisplay + hDisplay + mDisplay + sDisplay;
    }
}
var abc=0;
async function create_auction_thread(event, channel){
    //
    console.log("Preparing to send embed...");
    const tokenName = _.get(event, ['asset', 'name']);
    const openseaLink = _.get(event, ['asset', 'permalink']);
    const startPrice = _.get(event, 'starting_price');
    const usdValue = _.get(event, ['payment_token', 'usd_price']);
    const fEthPrice = ethers.utils.formatEther(startPrice.toString());
    const fUsdPrice = (fEthPrice * usdValue).toFixed(2);
    const time = _.get(event, ['asset', 'asset_contract', 'created_date']);
    const username = _.get(event, ['from_account', 'user', 'username']);
    const image = _.get(event, ['asset', 'image_preview_url']);
    const auction_type = _.get(event, 'auction_type');
    const duration = _.get(event, 'duration');
    const fduration = secondsToDhms(duration);
    const token_id = _.get(event, ['asset', 'token_id']);
    const name_with_hash = tokenName + ' ' + token_id + ' on sale';
    const name = name_with_hash.replace('#', '');
    const thread = await channel.threads.create({
        name: name,
        autoArchiveDuration: 60,
        reason: 'Thread created for new auction',
    });
    console.log(`Created thread: ${thread.name}`);
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
            name: "Type of Auction",
            value: `${auction_type}`
        })
        .addFields({
            name: "Amount(Starting Price)",
            value: `Eth: ${fEthPrice}, USD: ${fUsdPrice}`
        })
        .addFields({
            name: "Auction Duration",
            value: `${fduration}`
        })
        .addFields({
            name: "Listing Date/Time",
            value: `${time} x`
        });
    const string = tokenName.replace(/ /g, "-");
    const link = 'https://cryptotitties.fun/titty/'+string+'/';
    //thread.send({content: link});
    thread.send({content: link});
    thread.send({embeds: [embed]});
    console.log('Thread initial message + website link sent.');
    const asset_contract_address = _.get(event, ['asset', 'asset_contract', 'address']);
    push_auction_obj(token_id, asset_contract_address, name);
    abc = 1;
    console.log('Auction obj stored\n');
}

function checkapi(lastcheck, channel, collection){
    var x = 0;
    const options = {
        method: 'GET',
        url: 'https://api.opensea.io/api/v1/events',
        params: {
            /*asset_contract_address: '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',
            collection_slug: 'boredapeyachtclub',
            token_id: '1747',*/
            //Working example assset request^
            collection_slug: collection,
            event_type: 'created',
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
        console.log(`${events.length} new listings/auctions since last check/`);
        _.each(events, (event) => {
            console.log('Auctions event loop beginning...')
            create_auction_thread(event, channel);
        });
        x =1;
    }).catch(function (error) {
        console.error(error);
    });
    console.log('New auctions checked. Now checking for new auction orders...\n');
    return x;
}

function update_auction_thread(bid, name, channel, bid_num){
    //
    const lc = Math.round(Date.now() / 1000);
    lastcheck_bids = lc.toString();
    const bid_amount = _.get(bid, 'bid_amount');
    const usdValue = _.get(bid, ['payment_token', 'usd_price']);
    const bid_amount_eth = ethers.utils.formatEther(bid_amount.toString());
    const bid_amount_usd = (bid_amount_eth * usdValue).toFixed(2);
    const bid_date = _.get(bid, 'created_date');
    const bid_user_wallet = _.get(bid, ['from_account', 'address']);
    const bid_user_url = 'https://opensea.io/'+bid_user_wallet+'/';
    const username = _.get(bid, ['from_account','user','username']);
    const user_image = _.get(bid, ['from_account', 'profile_image_url']);
    const embed = new Discord.MessageEmbed()
        .setTitle(`Bid ${bid_num} made!`)
        .setColor(0x00AE86)
        .setAuthor(`${username}`, user_image)
        .setFooter('Listed on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
        .setTimestamp()
        .addFields({
            name: "Bid Account URL",
            value: `${bid_user_url}`
        })
        .addFields({
            name: "Bid Amount",
            value: `Eth: ${bid_amount_eth}, USD: ${bid_amount_usd}`
        })
        .addFields({
            name: "Bid made at",
            value: `${bid_date}`
        })
        .addFields({
            name: "Bid User Wallet",
            value: `${bid_user_wallet}`
        });
    console.log(`thread name = "${name}"`)
    const thread = channel.threads.cache.find(x => x.name === name);
    if (thread.setArchived===true){
        thread.setArchived(false);
    }
    thread.send({embeds: [embed]});
}

function checkapi_bids(lastcheck, channel){
    //request events for individual NFTs in var auctions, iterating through list of auction objs and 
    // new bids created (calling another function)
    for(let i = 0; i < auctions.length; i++){ 
        console.log('Auctions array iteration.');
        const asset_contract_address=auctions[i]["asset_contract_address"];
        const token_id=auctions[i]["token_id"];
        const name = auctions[i]["name"];
        const options = {
            method: 'GET',
            url: 'https://api.opensea.io/api/v1/events',
            params: {
                asset_contract_address: asset_contract_address,
                token_id: token_id,
                event_type: 'bid_entered',
                only_opensea: 'false',
                offset: '0',
                limit: '20',
                occurred_after: lastcheck
            },
            headers: {Accept: 'application/json'}
        };
        console.log('Data received. Extracting...');
        axios.request(options).then(function (response) {
            console.log("Bids data extracted");
            const bids = _.get(response, ['data', 'asset_events']);
            console.log(`${bids.length} new bids since last check.`);
            let bid_num = 1;
            _.each(bids, (bid) => {
                console.log('Bids embed loop beginning...')
                update_auction_thread(bid, name, channel, bid_num);
                bid_num+=1;
            });
        }).catch(function (error) {
            console.error(error);
        });
    }
} 

function update_auction_thread_offers(order, name, channel, order_num){
    //
    const order_amount = _.get(order, 'base_price');
    const usdValue = _.get(order, ['payment_token_contract', 'usd_price']);
    const order_amount_eth = ethers.utils.formatEther(order_amount.toString());
    const order_amount_usd = (order_amount_eth * usdValue).toFixed(2);
    const order_creating_date = _.get(order, 'created_date');
    const order_closing_date = _.get(order, 'closing_date');//check if sell or buy order:
    const buy_or_sell = _.get(order, 'side');
    if (buy_or_sell === 1){
        //sell order embed
        console.log('Retrieved sell offer. Embedding...\n')
        var user_wallet = _.get(order, ['maker','address']);
        var username = _.get(order, ['maker', 'user','username']);
        var user_url = 'https://opensea.io/'+user_wallet+'/';
        var type = 'Sell offer';
    }
    else if (buy_or_sell === 0){
        //buy order embed
        console.log('Retrieved buy offer. Embedding...\n')
        var user_wallet = _.get(order, ['maker','address']);
        var username = _.get(order, ['maker', 'user','username']);
        var user_url = 'https://opensea.io/'+user_wallet+'/';
        var type = 'Buy offer';
    }
    const embed = new Discord.MessageEmbed()
        .setTitle(`Offer ${order_num} made! (${type})`)
        .setColor(0x00AE86)
        .setAuthor(`${username}`)
        .setFooter('Offer made on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
        .setTimestamp()
        .addFields({
            name: "Offer Account URL",
            value: `${user_url}`
        })
        .addFields({
            name: "Offer Amount",
            value: `Eth: ${order_amount_eth}, USD: ${order_amount_usd}`
        })
        .addFields({
            name: "Offer created at",
            value: `${order_creating_date}`
        })
        .addFields({
            name: "Offer expires at",
            value: `${order_closing_date}`
        })
        .addFields({
            name: "Offer user's wallet",
            value: `${user_wallet}`
        });
    console.log(`thread name = "${name}"`)
    const thread = channel.threads.cache.find(x => x.name === name);
    if (thread.setArchived===true){
        thread.setArchived(false);
    }
    thread.send({embeds: [embed]});
}

function checkapi_offers(lastcheck, channel){
    for(let i = 0; i < auctions.length; i++){ 
        console.log('Auctions array iteration.');
        const asset_contract_address=auctions[i]["asset_contract_address"];
        const token_id=auctions[i]["token_id"];
        const name = auctions[i]["name"];
        const options = {
            method: 'GET',
            url: 'https://api.opensea.io/wyvern/v1/orders',
            params: {
                asset_contract_address: asset_contract_address,
                bundled: 'false',
                include_bundled: 'false',
                include_invalid: 'false',
                listed_after: lastcheck,
                token_id: token_id,
                limit: '20',
                offset: '0',
                order_by: 'created_date',
                order_direction: 'desc'
            },
            headers: {Accept: 'application/json'}
        };
        console.log('Offers data received. Extracting...');
        axios.request(options).then(function (response) {
            const num_orders = _.get(response, ['data','count']);
            console.log(`${num_orders} offers data extracted`);
            const orders = _.get(response, ['data', 'orders']);
            let order_num=1;
            _.each(orders, (order) => {
                console.log('Order embed loop beginning...')
                update_auction_thread_offers(order, name, channel, order_num);
                order_num+=1;
            })
        }).catch(function (error) {
            console.error(error);
        });
    }
}
 
client.on('messageCreate', message => {
    if(!message.content.startsWith(prefix) || message.author.bot) return;
    console.log('Raw command received');
    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const command = args.shift().toLowerCase();

    //Loading data from config.json:
    const data = JSON.parse(fs.readFileSync("config.json"));
    const startepoch = data.startepoch;//14th sept 2021
    const collection = data.collection_slug;

    var lastcheck = startepoch;
    var lastcheck2 = startepoch;
    var lc2= lastcheck2;
    console.log('Command received');
    if (command === "check_auctions"){
        count = 1
        const channel = message.channel;
        setInterval(function(){
            console.log(`Check ${count}:\n`);
            count+=1; 
            const lc = Math.round(Date.now() / 1000);
            const returned = checkapi(lastcheck, channel, collection);
            if (abc === 1) {
                function a(lastcheck2, channel){
                    checkapi_bids(lastcheck2, channel);
                    checkapi_offers(lastcheck2, channel);
                    lc2 = Math.round(Date.now()/1000);
                    console.log('New bids and orders checked. \n\n');
                }
                a(lastcheck2, channel);
            }
            lastcheck2 = lc2.toString();
            lastcheck = lc.toString();
        },10000)
    }
    else if(command === "ping"){
        message.channel.send("pong!");    
    }
});

client.login(TOKEN);