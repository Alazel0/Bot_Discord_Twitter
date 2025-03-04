import discord
import tweepy
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# 🔹 Configuración de Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # ID del canal a monitorear

# 🔹 Configuración de Twitter API v2
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Autenticación con Twitter API v1.1 (solo para subir imágenes)
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
twitter_api = tweepy.API(auth)

# Autenticación con Twitter API v2 (para publicar tweets)
twitter_client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_SECRET
)

# 🔹 Configuración del bot de Discord
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Necesario para leer mensajes

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')


@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return  # Ignorar mensajes de otros canales

    print(f"📩 Mensaje recibido en {message.channel.id}: {message.content}")

    if not message.attachments:
        print("❌ No hay imágenes adjuntas en el mensaje.")
        return

    for attachment in message.attachments:
        # Extraer la extensión del archivo
        file_extension = os.path.splitext(attachment.filename)[1].lower()
        if file_extension not in (".png", ".jpg", ".jpeg", ".gif"):
            print(f"❌ Archivo {attachment.filename} no es una imagen válida.")
            continue

        print(f"✅ Imagen detectada: {attachment.filename}")

        try:
            # Descargar la imagen
            print("🌐 Descargando imagen...")
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(attachment.url, headers=headers)
            response.raise_for_status()  # Lanza error si la descarga falla

            image = BytesIO(response.content)
            print(f"✅ Imagen descargada correctamente ({image.getbuffer().nbytes} bytes)")

            # Subir imagen a Twitter
            print("📤 Subiendo imagen a Twitter...")
            media = twitter_api.media_upload(filename="image.jpg", file=image)
            print(f"✅ Imagen subida con ID: {media.media_id}")

            # Publicar tweet
            tweet_text = message.content if message.content else "Nueva imagen compartida en Discord"
            print(f"📝 Publicando tweet: {tweet_text}")

            response = twitter_client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            tweet_id = response.data["id"]

            print(f"🎉 Tweet publicado exitosamente!")
            print(f"🔗 Enlace al tweet: https://twitter.com/user/status/{tweet_id}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error al descargar la imagen: {e}")
        except tweepy.TweepyException as e:
            print(f"❌ Error al publicar el tweet: {e}")


# Ejecutar el bot de Discord
client.run(DISCORD_TOKEN)
