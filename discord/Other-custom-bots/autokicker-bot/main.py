#Discord bot to kick members without roles + kick specified member 

#v2.0(20th Jan 2022)------------------------------------------------------------------------------------
#Bot logic: 0. Runs loop iterating over servers (list)
#           1. Runs loop iterating over server(guild) members, checks each for roles and 'joined_at' time
#           2. If joined_at <= allowed_time, continue, else kick if roles not present
#           3. Auto-kick loop repeats at 30s sleep intervals
#           4. async kick {@member} {reason}(optional) command always available if user has kick perms=true

#loading modules->
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import asyncio
import time
import json

#loading config->
f = open('config.json',)
cfg = json.load(f)
admin_role = cfg["admin_role"] #role that can ask this bot to kick members directly
allowed_time = cfg["allowed_time"]#eg 3600 in seconds =6 hours
guild_ids = cfg["guild_ids"]
token = open('kickbot_token.txt','r').readline()
channel_ids = cfg["admin_channel_ids"] #id to which 'kick' updates will be posted. 

#initiating client->
intents = discord.Intents.default()
intents.members = True #grabbing .members intent to retrieve guild members, member roles
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    print('---------------------------------------------------------------\n')
    print('DISCORD KICK BOT\n')
    print('---------------------------------------------------------------\n')

#@has_permissions(kick_members=True)
@client.command(pass_context=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    commander = ctx.message.author
    print(f'Member {commander.name} tried to use !kick command.')
    j=1
    a_role = discord.utils.find(lambda r: r.name == admin_role, ctx.message.guild.roles)
    list = commander.roles
    for role in list:
        print(f'Role: {j} = {role}')
        j+=1
    if (a_role in list):
        print(f'Member {commander.name} has admin role {admin_role}. Kicking authorized. Kicking...')
        await member.kick(reason=reason)
        await ctx.send(f'User {member} has been kicked.')
        print (f'--------------\nUser {member} has been kicked directly\n-----------------')
    else:
        print(f'Member {commander.name} does not have admin role {admin_role}. Unauthorized. Not kicking.')
        await ctx.send(f'Error. {admin_role} role required to kick. {member} has not been kicked. ')
        print('-------------------------------------------------------\n')

@kick.error
async def kick_error(error, ctx):
   if isinstance(error, MissingPermissions):
        await ctx.send("You don't have permission to do that!")


async def auto_kick_iterator():
    await client.wait_until_ready()
    x = 1
    while not client.is_closed():
        i = 0
        print(f'-------------Iteration {x}----------------')
        for server in guild_ids:
            print(f'--------Checking Server ID: {server}--------')
            channel = client.get_channel(id=channel_ids[i])
            guild = client.get_guild(server)
            async for member in guild.fetch_members(limit=None):
                a=1
                joined_at = member.joined_at
                j_a_epoch = joined_at.timestamp()
                current_time = time.time()
                print(f'\nCurrent time(epoch): {current_time}')
                print(f'Member {member.name} (joined at {joined_at} UTC, Epoch at "{j_a_epoch}"")')
                print(f'Number of roles[] of member: {len(member.roles)-1}')
                i = 0
                for role in member.roles:
                    role_name = role.name
                    print(f'{i}. {role_name}')
                    i+=1
                if (len(member.roles)<=1):
                    if (current_time - j_a_epoch >= allowed_time):
                        print(f'Kicking member.')
                        reason = 'Member has no roles, been in server over allowed_time'
                        name = member.name
                        await member.kick(reason=reason)
                        await channel.send(f'User {name} has been kicked.')
                        print(f'User {name} has been kicked.')
                    else:
                        print('Member has no roles, but within allowed_time. Not kicking.')
                else:
                    print(f'Member has role/s, not kicking.')
            print('-----------------------------\n-------------------------\n')
        x+=1
        await asyncio.sleep(30)

client.loop.create_task(auto_kick_iterator())

client.run(token)