import discord
from discord import app_commands
from discord.ext import tasks
import os
from flask import Flask
from threading import Thread

# --- SERVEUR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot en ligne !"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1461846612367380707
LOG_RECRU_ID = 1462047465090973698
RECRUT_CHANNEL_ID = 1461851553001504809
FOUNDER_ROLE_ID = 1461848068780458237

# --- VUES ---
class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None) # Vital
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="kawail_apply_unique")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        # On utilise une réponse différée pour éviter le timeout
        await interaction.response.send_modal(CandidatureModal(self.bot))

class CandidatureModal(discord.ui.Modal, title="Dossier Staff Kawail_FPS"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge", placeholder="Ex: Kawail_FPS, 17 ans")
    motive = discord.ui.TextInput(label="Tes motivations", style=discord.TextStyle.paragraph, min_length=10)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="❤️ Motivations", value=self.motive.value)
        
        # On envoie dans les logs avec les boutons Accepter/Refuser
        view = AdminView(self.bot, interaction.user.id)
        await log_chan.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Ton dossier a été transmis au staff !", ephemeral=True)

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("Fondateur uniquement.", ephemeral=True)
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("Tu as été **accepté** sur le serveur **kawail_fps** !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("Fondateur uniquement.", ephemeral=True)
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("Oh non, tu n'as pas été **accepté**.")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

# --- BOT ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # CECI enregistre les boutons pour qu'ils marchent après reboot
        self.add_view(RecruitmentView(self))
        # Important : On ne met PAS AdminView ici car elle est créée par candidature
        
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"✅ Connecté : {self.user}")
        if not self.update_status.is_running():
            self.update_status.start()
        await self.check_recruitment_post()

    @tasks.loop(minutes=10)
    async def update_status(self):
        guild = self.get_guild(GUILD_ID)
        if guild:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{guild.member_count} membres"))

    async def check_recruitment_post(self):
        channel = self.get_channel(RECRUT_CHANNEL_ID)
        if not channel: return
        
        # On cherche si le bot a déjà posté
        found = False
        async for m in channel.history(limit=10):
            if m.author.id == self.user.id and m.embeds:
                found = True
                break
        
        if not found:
            embed = discord.Embed(title="🌟 RECRUTEMENT KAWAIL_FPS", description="Clique ci-dessous pour postuler !", color=0xFF69B4)
            await channel.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

# Commande list simple
@bot.tree.command(name="list", description="Stats")
async def list_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("Commande en cours de dev.")

keep_alive()
bot.run(TOKEN)
