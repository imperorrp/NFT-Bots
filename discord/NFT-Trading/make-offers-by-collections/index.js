//OpenSea bot for mass offers of X price, X duration, on each asset in each of X collections
//^where X is configurable
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
const { isNull } = require('lodash');

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

function retrieveCollection(collection_slug, message){
    //
    const options = {
        method: 'GET',
        url: 'https://api.opensea.io/api/v1/events',
        params: {
            collection_slug: collection_slug,
            only_opensea: 'false', 
            offset: '0', 
            limit: '1'
        },
        headers: {Accept: 'application/json'}
    };
    axios.request(options).then(function (response) {
        console.log(`Some event for ${collection_slug} collection retrieved.`);
        const events = _.get(response, ['data', 'asset_events']);
        console.log(`${events.length} event retrieved\n`);
        if(events.length===0){
            return 0;
        }
        else {
            _.each(events, (event) => {
                console.log('Event loop.');
                const collection_banner = _.get(event, ['asset', 'collection', 'banner_image_url']);
                const description = _.get(event, ['asset', 'collection', 'description']);
                const collection_url = 'https://opensea.io/collection/'+collection_slug;
                const embed = new Discord.MessageEmbed()
                    .setTitle(`${collection_slug} Collection`)
                    .setColor(0x00AE86)
                    .setFooter('Collection on OpenSea', 'https://opensea.io/static/images/logos/opensea.svg')
                    .setImage(`${collection_banner}`)
                    .setTimestamp()
                    .setURL(`${collection_url}`)
                    .addFields({
                        name: "URL",
                        value: `${collection_url}`
                    })
                    .addFields({
                        name: "Description",
                        value: `${description}`
                    });
                message.channel.send(embed);
            });
            return 1;
        }   
    }).catch(function (error) {
        console.error(error);
    });
}

async function createOfferOnAsset(tokenAddress, tokenId, offerAmount) {
    const offer = {
        accountAddress: WALLET_ADDRESS,
        startAmount: offerAmount,
        asset: {
            tokenAddress: tokenAddress,
            tokenId: tokenId,
        },
    };

    try {
        const response = await sdk.createOffer(offer);
        console.log("Successfully created an offer with orderHash:", response.orderHash);
    } catch (error) {
        console.error("Error in createOffer:", error);
    }
}

async function makeOffersOnCollectionAssets(collection_slug, offerAmount, offerDuration, message) {
    try {
        const assets = await fetchAssetsInCollection(collection_slug);
        if (assets.length === 0) {
            message.channel.send('No assets found in this collection.');
            return;
        }

        // Iterate over each asset in the collection
        for (const asset of assets) {
            const tokenAddress = asset.asset_contract.address;
            const tokenId = asset.token_id;

            console.log(`Making an offer on asset ${tokenId} from collection ${collection_slug}`);
            await createOfferOnAsset(tokenAddress, tokenId, offerAmount);

            // Sleep for a short duration to avoid spamming
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        message.channel.send('All offers have been placed on the assets in the collection.');
    } catch (error) {
        console.error('Error fetching or placing offers:', error);
        message.channel.send('An error occurred while placing offers.');
    }
}

async function fetchAssetsInCollection(collection_slug) {
    const options = {
        method: 'GET',
        url: 'https://api.opensea.io/api/v1/assets',
        params: {
            collection: collection_slug,
            offset: '0',
            limit: '50' // Increase limit as needed
        },
        headers: { Accept: 'application/json' }
    };

    try {
        const response = await axios.request(options);
        console.log(`Retrieved assets for collection: ${collection_slug}`);
        return response.data.assets;
    } catch (error) {
        console.error('Error fetching assets:', error);
        return [];
    }
}


//Discord commands endpoint:
var prefix='!'
client.on('message', message => {
    if(!message.content.startsWith(prefix) || message.author.bot) return;
    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const command = args.shift().toLowerCase();
    const startepoch = data.init_check_time;
    var lastcheck = startepoch;
    const accountAddress = data.buyer_wallet_address;
 
    //Commands: 
    //Configure collection, offer amount, offer duration, and send offers to all assets 
    //User then prompted for confirmation with collection info (in an embed), and then offers are made.
    if (command === "make_offer"){
        const collection_slug = args[0];
        const offer_amount = args[1];
        const offer_duration = args[2];
        if(!_.isNil(collection_slug) && !_.isNil(offer_amount)&&!_.isNil(offer_duration)){
            console.log("Confirming command");
            //Find collection, post details as an embed->
            let check = 0;
            check = retrieveCollection(collection_slug, message);
            if (check === 0){
                message.channel.send('Incorrect collection_slug argument. Please try again.')
            }
            else {
                //Seek confirmation: 
                message.channel.send(`Please confirm command by typing 'Yes' within 10 seconds, or wait for this request to expire.\n\nRequest: To make offers on\nCollection Slug: ${collection_slug}\nOffer Amount: ${offer_amount}\nOffer Duration: ${offer_duration}`);
                const filter = m => m.content.includes('Yes') || m.content.includes('Yes') || m.content.includes('YES') && m.author.id === message.author.id;
                const collector = message.channel.createMessageCollector(filter, { time: 10000 });

                collector.on('collect', m => {
                    console.log(`User confirmation: ${m.content}`);
                    message.channel.send('Retrieving assets and placing offers...');
                    makeOffersOnCollectionAssets(collection_slug, offer_amount, offer_duration, message);
                });

                collector.on('end', collected => {
                    console.log(`User confirmation: No.`);
                    message.channel.send('make_offer command expired');
                });
            }
        }
        else {
            message.channel.send('Please enter required arguments (Format: `!make_offer collection_slug offer_amount offer_duration`)');
        }
    }
    else if(command === "ping"){
        message.reply('pong!');
    }
});

client.login(TOKEN);



