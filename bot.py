import discord
from discord import app_commands
from discord.ext import tasks
import os
from flask import Flask, request
from threading import Thread

# --- SERVEUR WEB (KEEP ALIVE + GITHUB WEBHOOK) ---
app = Flask('')

@app.route('/')
def home(): return "Bot Kawail_FPS en ligne !"

@app.route('/github', methods=['POST'])
def github_webhook():
    data = request.json
    if 'commits' in data:
        repo_name = data['repository']['name']
        for commit in data['commits']:
            author = commit['author']['name']
            message = commit['message']
            url = commit['url']
            bot.loop.create_task(send_github_update(author, message, url, repo_name))
    return "OK", 200

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION (TES IDS) ---
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1461846612367380707
LOG_RECRU_ID = 1462047465090973698
RECRUT_CHANNEL_ID = 1461851553001504809
FOUNDER_ROLE_ID = 1461848068780458237
CAT_INFO_ID = 1461849328237809774  # Catégorie Information
GITHUB_CHAN_NAME = "🤖〡changement-bot"

stats = {"accept": 0, "refuse": 0, "waiting": 0}

# --- VUES RECRUTEMENT ---
class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="apply_v7")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok_v7")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Fondateur uniquement.", ephemeral=True)
        global stats
        stats["accept"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("✅ Candidature acceptée !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no_v7")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Fondateur uniquement.", ephemeral=True)
        global stats
        stats["refuse"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("❌ Candidature refusée.")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

class CandidatureModal(discord.ui.Modal, title="Dossier Staff Kawail_FPS"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge")
    dispo = discord.ui.TextInput(label="Disponibilités")
    exp = discord.ui.TextInput(label="Expériences", style=discord.TextStyle.paragraph)
    apport = discord.ui.TextInput(label="Apport", style=discord.TextStyle.paragraph)
    motive = discord.ui.TextInput(label="Motivations", style=discord.TextStyle.paragraph, min_length=20)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        global stats
        stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="❤️ Motivations", value=self.motive.value)
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.response.send_message("✅ Dossier envoyé !", ephemeral=True)

# --- FONCTIONS SYSTÈME ---
async def send_github_update(author, message, url, repo):
    guild = bot.get_guild(GUILD_ID)
    category = guild.get_channel(CAT_INFO_ID)
    channel = discord.utils.get(category.text_channels, name=GITHUB_CHAN_NAME)
    if not channel:
        channel = await guild.create_text_channel(GITHUB_CHAN_NAME, category=category)
    
    embed = discord.Embed(title=f"🛠️ GitHub Update : {repo}", description=f"**Auteur:** {author}\n**Message:** {message}", color=0x2b2d31, url=url)
    await channel.send(embed=embed)

# --- BOT CLASS ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(RecruitmentView(self))
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"✅ Bot prêt : {self.user}")
        chan = self.get_channel(RECRUT_CHANNEL_ID)
        if chan:
            async for m in chan.history(limit=5):
                if m.author.id == self.user.id: return
            embed = discord.Embed(
                title="━━━ 🌟 RECRUTEMENT : KAWAIL_FPS 🌟 ━━━",
                description="✨ **REJOINS L'ÉQUIPE DU SERVEUR !** ✨\n\nTu souhaites t'investir avec **Kawail_FPS** ?\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n👇 **CLIQUE CI-DESSOUS POUR CANDIDATER !**",
                color=0xFF69B4
            )
            await chan.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

@bot.tree.command(name="list", description="Stats recrutement")
async def list_stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"⏳: {stats['waiting']} | ✅: {stats['accept']} | ❌: {stats['refuse']}")

# LANCEMENT
keep_alive()
bot.run(TOKEN)
