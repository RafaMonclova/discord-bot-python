import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
import urllib.parse, urllib.request, re

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!", intents=intents)

    queues = {}
    voice_clients = {}
    youtube_base_url = 'https://www.youtube.com/'
    youtube_results_url = youtube_base_url + 'results?'
    youtube_watch_url = youtube_base_url + 'watch?v='
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

    @client.event
    async def on_ready():
        print(f'{client.user} se ha unido al chat!')
        await client.change_presence(activity=discord.Game(name="!help"))
        

    async def play_next(ctx):
        if queues[ctx.guild.id] != []:
            link = queues[ctx.guild.id].pop(0)
            await play(ctx, link=link)

            
    
    @client.command(name="play", description="Reproduce una canción de YouTube", brief="Reproduce una canción de YouTube", aliases=["p"])
    async def play(ctx, *, link):
        try:
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)

        try:

            if youtube_base_url not in link:
                query_string = urllib.parse.urlencode({
                    'search_query': link
                })

                content = urllib.request.urlopen(
                    youtube_results_url + query_string
                )

                search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())

                link = youtube_watch_url + search_results[0]

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))

            song = data['url']
            player = discord.FFmpegOpusAudio(song, **ffmpeg_options)

            voice_clients[ctx.guild.id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop))
            await ctx.send(f"🎵 Escuchando: {data['title']}  || {ctx.author.voice.channel}")
        except Exception as e:
            print(e)

    @client.command(name="clear_queue", description="Limpia la cola de reproducción", brief="Limpia la cola de reproducción", aliases=["cq"])
    async def clear_queue(ctx):
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
            await ctx.send("Cola reiniciada!")
        else:
            await ctx.send("No hay cola que limpiar")

    @client.command(name="pause", description="Pausa la canción actual", brief="Pausa la canción actual", aliases=["pa"])
    async def pause(ctx):
        try:
            voice_clients[ctx.guild.id].pause()
        except Exception as e:
            print(e)

    @client.command(name="resume", description="Reanuda la canción actual", brief="Reanuda la canción actual", aliases=["r"])
    async def resume(ctx):
        try:
            voice_clients[ctx.guild.id].resume()
        except Exception as e:
            print(e)

    @client.command(name="stop", description="Detiene la reproducción y desconecta del canal de voz", brief="Detiene la reproducción y desconecta del canal de voz", aliases=["s"])
    async def stop(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
            await ctx.send(f"🛑 Desconectado de {ctx.author.voice.channel}")
        except Exception as e:
            print(e)

    @client.command(name="queue", description="Añade una canción a la cola de reproducción", brief="Añade una canción a la cola de reproducción", aliases=["q"])
    async def queue(ctx, *, url):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.send(f"🎵 {url} ha sido añadido a la cola")
        

    client.run(TOKEN)