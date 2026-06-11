# Built-in modules
import os, socket, threading
from datetime import datetime

# Third-party modules
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from waitress import serve

from utils import *

def embed_to_discord(embed):
    discord_embed = discord.Embed(
        title=embed["title"],
        url=embed["title_url"],
        description=embed["content"][:4096], # Discord embed description limit
        color=0x2f323a,
        timestamp=datetime.fromisoformat(embed["timestamp"]) if embed["timestamp"] else None
    )
    discord_embed.set_author(
        name=embed["author_name"],
        url=embed["author_url"],
        icon_url=image_proxy(embed["author_img"], use_http_proxy=False)
    )
    if embed["image"]:
        discord_embed.set_image(url=embed["image"])
    return discord_embed

def main():
    load_dotenv()
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

    class URLModal(discord.ui.Modal, title="CPTDB Post Embedder"):
        url = discord.ui.TextInput(
            label="Comment URL",
            placeholder="https://cptdb.ca/topic/TOPIC/page/PAGE/#comment-COMMENT",
            required=True
        )

        async def on_submit(self, interaction: discord.Interaction):
            embed = comment_to_embed(self.url.value)
            if isinstance(embed, str):
                await interaction.response.send_message(embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed_to_discord(embed))
    
    @bot.tree.command(name="cptdb", description="Show a CPTDB comment as an embed")
    async def cptdb(interaction: discord.Interaction):
        await interaction.response.send_modal(URLModal())

    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f"Logged in as {bot.user}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", int(os.getenv("FLASK_PORT")))) != 0:
            flask_app = Flask(__name__)
            flask_app.route("/dataurlsvg", methods=["GET"])(dataURLsvg_to_png)
            threading.Thread(target=lambda: serve(flask_app, host="0.0.0.0", port=int(os.getenv("FLASK_PORT"))), daemon=True).start()

    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    main()