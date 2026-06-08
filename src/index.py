import discord
import asyncio
import os
from dotenv import load_dotenv

from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot está vivo y pingueando! 🚀"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CARGA DE CONFIGURACIÓN ---
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
# Convertimos el ID del canal a entero (int)
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
# Convertimos la lista de IDs de texto a una lista de enteros
raw_owners = os.getenv("OWNER_IDS")
OWNER_IDS = [int(id.strip()) for id in raw_owners.split(",")]

INTERVALO = 1

intents = discord.Intents.default()
intents.message_content = True  
client = discord.Client(intents=intents)

loop_activo = False 
usuario_actual = None

# Función que envía los pings periódicos
async def mandar_mensaje():
    global loop_activo, usuario_actual
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        try:
            channel = await client.fetch_channel(CHANNEL_ID)
        except Exception:
            pass
    
    while loop_activo:
        if usuario_actual:
            if channel:
                try:
                    await channel.send(f"{usuario_actual.mention} fah u manige 🗣️🔥🔥🔥")
                except discord.HTTPException as e:
                    print(f"❌ Error al enviar mensaje: {e}")
            else:
                print("❌ No se encontró el canal. Revisa el CHANNEL_ID.")
                break
        await asyncio.sleep(INTERVALO)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    
    # Intentamos obtener el nombre del canal
    canal = client.get_channel(CHANNEL_ID)
    nombre_canal = canal.name if canal else f"ID: {CHANNEL_ID} (Canal no encontrado)"
    print(f"📡 Canal objetivo: #{nombre_canal}")

    # Traducimos los IDs de los Owners a nombres reales
    nombres_owners = []
    for owner_id in OWNER_IDS:
        try:
            user = await client.fetch_user(owner_id)
            nombres_owners.append(user.name) # O user.display_name para el apodo
        except Exception:
            nombres_owners.append(f"Desconocido({owner_id})")
    
    # Unimos los nombres con comas para que se vea bonito
    print(f"👑 Owners autorizados: {', '.join(nombres_owners)}")
    print("------------------------------------------")
@client.event
async def on_message(message):
    global loop_activo, usuario_actual

    if message.author == client.user:
        return

    if message.author.id not in OWNER_IDS:
        return  

    content = message.content.strip()

    if content.lower().startswith("!i"):
        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await message.channel.send("❌ Debes especificar un ID o mención de usuario. Ejemplo: `!i <id_del_usuario>`")
            return

        argumento = parts[1].strip()
        target_user = None

        if message.mentions:
            target_user = message.mentions[0]
        else:
            cleaned_id = "".join(c for c in argumento if c.isdigit())
            if cleaned_id:
                try:
                    user_id = int(cleaned_id)
                    target_user = await client.fetch_user(user_id)
                except (ValueError, discord.NotFound, discord.HTTPException):
                    pass

        if not target_user:
            await message.channel.send("❌ No pude encontrar a ese usuario.")
            return

        usuario_actual = target_user

        if not loop_activo:
            loop_activo = True
            await message.channel.send(f"**Bot ON**: ah con que el hpta de {target_user.mention} no contesta")
            asyncio.create_task(mandar_mensaje())
        else:
            await message.channel.send(f"**Usuario objetivo cambiado a**: {target_user.mention}.")

    elif content.lower() == "!p":
        if loop_activo:
            loop_activo = False
            await message.channel.send("**Bot OFF**: El bucle se detuvo.")
        else:
            await message.channel.send("El bucle ya estaba apagado.")

keep_alive()
client.run(TOKEN)