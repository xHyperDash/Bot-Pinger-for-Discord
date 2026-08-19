import discord
import asyncio
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- SERVIDOR FLASK PARA KEEP ALIVE ---
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
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

raw_owners = os.getenv("OWNER_IDS")
OWNER_IDS = [int(id.strip()) for id in raw_owners.split(",")]

# Subimos el intervalo a 1.5 segundos para evitar bloqueos por Rate Limit / Cloudflare
INTERVALO = 1.5

intents = discord.Intents.default()
intents.message_content = True  
client = discord.Client(intents=intents)

loop_activo = False 
usuario_actual = None
mensaje_personalizado = ""

# --- BUCLE PRINCIPAL DE MENSAJES ---
async def mandar_mensaje():
    global loop_activo, usuario_actual, mensaje_personalizado
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
                    await channel.send(f"{usuario_actual.mention} {mensaje_personalizado}")
                except discord.HTTPException as e:
                    print(f"❌ Error al enviar mensaje en bucle: {e}")
            else:
                print("❌ No se encontró el canal. Revisa el CHANNEL_ID.")
                break
        await asyncio.sleep(INTERVALO)

# --- EVENTOS DEL BOT ---
@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    
    canal = client.get_channel(CHANNEL_ID)
    nombre_canal = canal.name if canal else f"ID: {CHANNEL_ID} (Canal no encontrado)"
    print(f"📡 Canal objetivo: #{nombre_canal}")

    nombres_owners = []
    for owner_id in OWNER_IDS:
        try:
            user = await client.fetch_user(owner_id)
            nombres_owners.append(user.name)
        except Exception:
            nombres_owners.append(f"Desconocido({owner_id})")
    
    print(f"👑 Owners autorizados: {', '.join(nombres_owners)}")
    print("------------------------------------------")

@client.event
async def on_message(message):
    global loop_activo, usuario_actual, mensaje_personalizado

    if message.author == client.user:
        return

    if message.author.id not in OWNER_IDS:
        return  

    content = message.content.strip()

    if content.lower().startswith("!i"):
        parts = content.split(maxsplit=2)
        if len(parts) < 3:
            try:
                await message.channel.send("❌ Formato incorrecto. Debes usar: `!i <ping/ID> <mensaje>`")
            except discord.HTTPException as e:
                print(f"❌ Error al responder por sintaxis: {e}")
            return

        argumento = parts[1].strip()
        mensaje = parts[2].strip()
        target_user = None

        cleaned_id = "".join(c for c in argumento if c.isdigit())
        if cleaned_id:
            try:
                user_id = int(cleaned_id)
                target_user = discord.utils.get(message.mentions, id=user_id)
                if not target_user:
                    target_user = client.get_user(user_id)
                if not target_user:
                    target_user = await client.fetch_user(user_id)
            except (ValueError, discord.NotFound, discord.HTTPException):
                pass

        if not target_user:
            try:
                await message.channel.send("❌ No pude encontrar a ese usuario.")
            except discord.HTTPException as e:
                print(f"❌ Error al responder por usuario no encontrado: {e}")
            return

        usuario_actual = target_user
        mensaje_personalizado = mensaje

        if not loop_activo:
            loop_activo = True
            try:
                await message.channel.send(f"**Bot ON**: ah con que el hpta de {target_user.mention} no contesta")
            except discord.HTTPException as e:
                print(f"❌ Error al encender el bot: {e}")
            asyncio.create_task(mandar_mensaje())
        else:
            try:
                await message.channel.send(f"**Usuario objetivo cambiado a**: {target_user.mention}. **Mensaje**: {mensaje_personalizado}")
            except discord.HTTPException as e:
                print(f"❌ Error al actualizar objetivo: {e}")

    elif content.lower() == "!p":
        if loop_activo:
            loop_activo = False
            try:
                await message.channel.send("**Bot OFF**: El bucle se detuvo.")
            except discord.HTTPException as e:
                print(f"❌ Error al apagar el bot: {e}")
        else:
            try:
                await message.channel.send("El bucle ya estaba apagado.")
            except discord.HTTPException as e:
                print(f"❌ Error de respuesta: {e}")

# --- INICIALIZACIÓN ---
keep_alive()
client.run(TOKEN)