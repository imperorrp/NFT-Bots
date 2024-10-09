#v4 music bot discord
#Music bot for discord (via youtube_dl)
#features:
#join/leave vc, play, play_queue, pause/resume, add/remove from queue, skip, volume, clear, loop, shuffle

#v1.4(3rd March 2022)-----------------------------------------------------------------------------
#added 'help' and 'search' functionalities- searching for keywords specified and retrieving the top 
#result from Youtube
#also added parsing and storing song 'duration' for convenience.


#loading dependencies->
import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio 
from discord import TextChannel
from youtube_dl import YoutubeDL
import random
from time import gmtime
from time import strftime

#config and setup->
token = open('musicbot_token.txt','r').readline()
client = commands.Bot(command_prefix='!')  # prefix our commands with '.'
#youtube_dl and ffmpeg audio conversion settings->
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

queue_item_example = {"Name":"name-of-song", "URL":"url-here", "Length":"length-of-song"}
queue = [] #list of songs go here
loop_on = False #whether to loop queue or not 
queue_pos_current = 0 #for skipping when loop is on

#bot init event-> 
@client.event  
async def on_ready():
    print('--------------------\nMusic Bot online\n--------------------')

#search keywords on youtube, retrieve song->
async def search(keywords):
  with YoutubeDL(YDL_OPTIONS) as ydl:
    try:
      info = ydl.extract_info("ytsearch:%s" % keywords, download=False)["entries"][0]
    except Exception:
      return False
    duration = strftime("%H:%M:%S", gmtime(info["duration"]))
    return {
        "source_url": info["formats"][0]["url"],
        "title": info["title"],
        "song_length": duration
    }

#clears queue->
@client.command()
async def clear(ctx):
  print(f'-clear queue command called')
  global queue
  queue = []
  print(f'Queue cleared.')
  await ctx.send('Queue cleared!')

@client.command()
async def loop(ctx):
  print(f'-loop queue command called')
  global loop_on
  loop_on = True
  print(f'Queue looped.')
  await ctx.send('Queue looped!')

@client.command()
async def shuffle(ctx):
  print(f'-shuffle queue command called')
  random.shuffle(queue)
  print(f'Queue shuffled.')
  await ctx.send('Queue shuffled!')

#join voice channel of user invoking->
@client.command()
async def join(ctx):
    print(f'-Join channel command called')
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
        await ctx.send(f'Moved to your voice channel!')
    else:
        voice = await channel.connect()
        await ctx.send(f'Joined your voice channel!')

#leave voice channel->
@client.command()
async def leave(ctx):
    print(f'-Leave channel command called')
    await ctx.voice_client.disconnect()
    print(f'Voice channel left')
    await ctx.send('Left voice channel!')

#add song to queue (with youtube url)
@client.command()
async def add(ctx, keywords):
  print(f'-Add song command called')
  a = await search(keywords)
  if (a==False):
    print(f'Could not find/download song. Exception at search')
    await ctx.send(f'Could not find this song. Try some other keywords!')
  else:
  #with YoutubeDL(YDL_OPTIONS) as ydl:
  #    info = ydl.extract_info(url, download=False)
  #URL = info['url']
  #name = info['title']
    name = a["title"]
    URL = a["source_url"]
    length = a["song_length"]

    queue_obj = {"Name":name, "URL":URL, "Length":length}
    queue.append(queue_obj)
    print(f'Title "{name}" pushed to queue. Duration: {length}')
    await ctx.send(f'Title "{name}" added to queue. Duration: {length}')

#view queue 
@client.command()
async def q(ctx):
  print(f'-Displaying current queue')
  queue_text = ""
  i = 1
  if loop_on==False:
    queue_text = queue_text + "(Loop inactive)"
    for queue_obj in queue:
      name = queue_obj["Name"]
      length = queue_obj["Length"]
      queue_text = queue_text + f"\n**({i})** - *{name}* `Duration: {length}`"
      i+=1
  elif loop_on==True:
    queue_text = queue_text + "(Loop active)"
    for queue_obj in queue:
      name = queue_obj["Name"]
      length = queue_obj["Length"]
      queue_text = queue_text + f"\n**({i})** - *{name}* `Duration: {length}`"
      i+=1
  await ctx.send(f'Current queue: \n{queue_text}')

#remove song from queue 
@client.command()
async def remove(ctx, index):
  print(f'-Remove song command called')
  index-=1
  name = queue[index]["Name"]
  queue.pop(index)
  print(f'Removed title "{name}" from queue.')
  await ctx.send(f'Removed title "{name}" from queue.')

#play one-time song->
@client.command()
async def play(ctx, keywords):
    print(f'-play one-time song command called')
    voice = get(client.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        a = await search(keywords)
        if (a==False):
          print(f'Could not find/download song. Exception at search')
          await ctx.send(f'Could not find this song. Try some other keywords!')
        else:
        #with YoutubeDL(YDL_OPTIONS) as ydl:
        #    info = ydl.extract_info(url, download=False)
        #URL = info['url']
        #print(info)
          name = a["title"]
          URL = a["source_url"]
          length = a["song_length"]
          voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
          #voice.is_playing()
          #name = info['title']
          print(f'Playing... "{name}". Duration: {length}')
          await ctx.send(f'Playing... "{name}". Duration: {length}')
#check if the bot is already playing
    else:
        print(f'Already playing a song.')
        await ctx.send("Bot is already playing")
        return

#play queue's songs->
@client.command()
async def play_queue(ctx):
    print(f'-play queue song command called')
    voice = get(client.voice_clients, guild=ctx.guild)
    #q_zero_iter = 0
    if not voice.is_playing():
        #while(len(queue)>=1):
        #while True:
          #if(q_zero_iter == 0):
        #if len(queue)==0:
          #print(f'No titles in queue. Stopping...')
          #await ctx.send(f'No titles in queue. Stopping...')
        if loop_on==False:
          q_exhaust = 1
          for item in queue:
            URL = item["URL"]
            voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
            #voice.is_playing()
            name = item["Name"]
            length = item["Length"]
            print(f'Now playing... "{name}" (Duration: {length}) from queue')
            await ctx.send(f'Now playing... "{name}" (Duration: {length}) from queue')
            queue.pop(0)
            print(f'Removed currently playing title "{name}" from queue.')
            if len(queue)==0:
              q_exhaust = 0
          if q_exhaust==0:
            print(f'No titles in queue. Stopped.')
            await ctx.send(f'No titles in queue. Stopped!')
          #print(f'No titles in queue. Stopped.')
          #await ctx.send(f'No titles in queue. Stopped!')
        elif loop_on==True:
          while True:
            global queue_pos_current
            for item in queue:
              URL = item["URL"]
              queue_pos_current = queue.index(item)
              voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
              #voice.is_playing()
              name = item["Name"]
              length = item["Length"]
              print(f'Now playing... "{name}" (Duration: {length}) from queue')
              await ctx.send(f'Now playing... "{name}" (Duration: {length}) from queue')
              #queue.pop(0)
              #print(f'Removed currently playing title "{name}" from queue.')
            #q_zero_iter =1 
            #print(f'q_zero_iter updated from 0 to 1.')
        #voice.stop()
        #print(f'Queue exhausted, voice stopped.')

  #check if the bot is already playing
    else:
        print(f'Aleady playing a song.')
        await ctx.send("Bot is already playing")
        return

#skip current song in queue->
@client.command()
async def skip(ctx):
  print(f'-skip command called')
  voice = get(client.voice_clients, guild=ctx.guild)
  #if voice.is_playing():
  name = queue[0]["Name"]
  voice.stop()
  print(f'Stopped voice.')
  print(f'Skipped current queue song to next title')
  await ctx.send(f'Skipped current song to next title')
  q_exhaust = 1
  if loop_on==False:
    for item in queue:
      URL = item["URL"]
      voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
      #voice.is_playing()
      name = item["Name"]
      length = item["Length"]
      print(f'Now playing... "{name}" (Duration: {length}) from queue')
      await ctx.send(f'Now playing... "{name}" (Duration: {length}) from queue')
      queue.pop(0)
      print(f'Removed currently playing title "{name}" (Duration: {length}) from queue.')
      if len(queue)==0:
        q_exhaust = 0
  elif loop_on==True:
    while True:
      global queue_pos_current
      item = queue[queue_pos_current]
      a = len(queue)-1
      if(queue_pos_current==a):
        queue_pos_current = 0
      else:
        queue_pos_current+=1
      URL = item["URL"]
      voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
      #voice.is_playing()
      name = item["Name"]
      length = item["Length"]
      print(f'Now playing... "{name}" (Duration: {length}) from queue')
      await ctx.send(f'Now playing... "{name}" (Duration: {length}) from queue')
  if q_exhaust==0:
    print(f'No titles in queue. Stopped.')
    await ctx.send(f'No titles in queue. Stopped!')
  #await play_queue(ctx)

#resume audio->
@client.command()
async def resume(ctx):
  print(f'-resume command called')
  voice = get(client.voice_clients, guild=ctx.guild)

  if not voice.is_playing():
      voice.resume()
      print('Resumed.')
      await ctx.send('Resumed!')
  #else: 
  #    print('Play something first.')
  #    await ctx.send('Play something first!')

#pause audio->
@client.command()
async def pause(ctx):
  print(f'-pause command called')
  voice = get(client.voice_clients, guild=ctx.guild)

  if voice.is_playing():
      voice.pause()
      print('Paused.')
      await ctx.send('Paused!')
  else:
      print('Play something first.')
      await ctx.send('Play something first!')

#stop voice->
@client.command()
async def stop(ctx):
  print(f'-stop audio command called')
  voice = get(client.voice_clients, guild=ctx.guild)

  if voice.is_playing():
      voice.stop()
      print('Stopped.')
      await ctx.send('Stopped!')
  else:
      print('Play something first.')
      await ctx.send('Play something first!')

#set volume (0-100)->
@client.command()
async def volume(ctx, volume: int):
  voice = get(client.voice_clients, guild=ctx.guild)
  if voice.is_playing():
    if 0 > volume > 100:
      return await ctx.send('Volume must be between 0 and 100')
    else:
      voice.pause()
      voice.source.volume = volume / 100
      voice.resume()
      print('Volume set to {}%'.format(volume))
      await ctx.send('Volume set to {}%!'.format(volume))
  else: 
    print('Play something first.')
    await ctx.send('Play something first!')

#help embed with list of commands and explanations->
@client.command()
async def helper(ctx):
  print(f'-helper command called')
  embed = discord.Embed(
    title = 'List of Commands:',
    colour = discord.Colour.greyple()
  )
  embed.add_field(name = '!join', value = 'Join the voice channel invoker is in', inline = False)
  embed.add_field(name = '!leave', value = 'Leave voice channel', inline = False)
  embed.add_field(name = '!play [some-song-keyword/s]', value = 'Play a song once (Searches on YouTube). If there are multiple keywords, enclose within double quotes("...")', inline = False)
  embed.add_field(name = '!pause', value = 'Pause audio', inline = False)
  embed.add_field(name = '!resume', value = 'Resume audio', inline = False)
  embed.add_field(name = '!stop', value = 'Stop playing audio', inline = False)
  embed.add_field(name = '!play_queue', value = 'Start playing from music queue', inline = False)
  embed.add_field(name = '!add [some-song-keyword/s]', value = 'Add a song to queue (Searches on YouTube). If there are multiple keywords, enclose within double quotes("...")', inline = False)
  embed.add_field(name = '!remove [index-number-from-current-queue]', value = 'Remove a song from specified queue index', inline = False)
  embed.add_field(name = '!q', value = 'View current queue', inline = False)
  embed.add_field(name = '!shuffle', value = 'Shuffles queue sequence', inline = False)
  embed.add_field(name = '!clear', value = 'Empties queue', inline = False)
  embed.add_field(name = '!skip', value = 'Skips current song to next in queue', inline = False)
  embed.add_field(name = '!loop', value = 'Turns loop on for queue', inline = False)
  embed.add_field(name = '!volume [value from 0-100]', value = 'Adjust audio volume', inline = False)
  embed.add_field(name = '!helper', value = 'View available commands', inline = False)
  await ctx.send(embed=embed)
  print(f'Helper embed sent.')

client.run(token)