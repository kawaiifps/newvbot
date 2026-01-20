import discord
from discord import app_commands
from discord.ext import tasks
import os
from flask import Flask
from threading import Thread

# --- SERVEUR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot Live"
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

stats = {"accept": 0, "refuse": 0, "waiting": 0}
last_actions = {}

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        global stats
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        stats["accept"] += 1
        stats["waiting"] -= 1
        last_actions[self.user_id] = "accept"
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("✅ Tu as été **accepté** sur le serveur **kawail_fps** !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        global stats
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        stats["refuse"] += 1
        stats["waiting"] -= 1
        last_actions[self.user_id] = "refuse"
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("❌ Candidature refusée.")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

class CandidatureModal(discord.ui.Modal, title="Dossier Staff Kawail_FPS"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge")
    dispo = discord.ui.TextInput(label="Dispos")
    exp = discord.ui.TextInput(label="Expériences", style=discord.TextStyle.paragraph)
    apport = discord.ui.TextInput(label="Apport", style=discord.TextStyle.paragraph)
    motive = discord.ui.TextInput(label="Motivations", style=discord.TextStyle.paragraph)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        global stats
        stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        if not log_chan:
            return await interaction.response.send_message("Erreur : Salon de logs introuvable.", ephemeral=True)
            
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="❤️ Motivations", value=self.motive.value)
        
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.response.send_message("✅ Envoyé !", ephemeral=True)

class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="btn_apply_v4")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all()) # On met ALL pour être sûr
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(RecruitmentView(self))
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"✅ Bot prêt : {self.user}")
        channel = self.get_channel(RECRUT_CHANNEL_ID)
        if channel:
            async for m in channel.history(limit=5):
                if m.author.id == self.user.id: return
            embed = discord.Embed(title="🌟 RECRUTEMENT KAWAIL_FPS", description="Clique ci-dessous !", color=0xFF69B4)
            await channel.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

@bot.tree.command(name="list", description="Stats")
async def list_stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"⏳ Attente: {stats['waiting']} | ✅ Acceptés: {stats['accept']} | ❌ Refusés: {stats['refuse']}")

keep_alive()
bot.run(TOKEN)
