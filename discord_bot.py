# Built-in modules
import os
from datetime import datetime

# Third-party modules
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import comment_to_embed

load_dotenv()

def embed_to_discord(embed):
    discord_embed = discord.Embed(
        title=embed["title"],
        url=embed["title_url"],
        description=embed["content"],
        color=0x2f323a,
        timestamp=datetime.fromisoformat(embed["timestamp"]) if embed["timestamp"] else None
    )
    discord_embed.set_author(
        name=embed["author_name"],
        url=embed["author_url"],
        icon_url=embed["author_img"]
    )
    if embed["image"]:
        discord_embed.set_image(url=embed["image"])
    return discord_embed

def main():
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

    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    main()