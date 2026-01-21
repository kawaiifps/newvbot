import discord
from discord import app_commands
import os
import json
from flask import Flask, request
from threading import Thread

# --- SERVEUR WEB (KEEP ALIVE + WEBHOOK GITHUB) ---
app = Flask('')

@app.route('/')
def home(): return "Bot Kawail_FPS en ligne !"

@app.route('/github', methods=['POST'])
def github_webhook():
    # Correction erreur 415 : lit le JSON même si le header est mal configuré
    data = request.get_json(silent=True)
    if not data and request.form.get('payload'):
        data = json.loads(request.form.get('payload'))
    
    if data and 'commits' in data:
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
CAT_INFO_ID = 1461849328237809774 
GITHUB_CHAN_NAME = "🤖〡changement-bot"

stats = {"accept": 0, "refuse": 0, "waiting": 0}
last_actions = {}

# --- VUES (BOUTONS) ---
class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="kawail_v12")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok_v12")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
        global stats
        stats["accept"] += 1
        stats["waiting"] -= 1
        last_actions[self.user_id] = "accept"
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("✅ Ta candidature a été **acceptée** sur **Kawail_FPS** !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no_v12")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
        global stats
        stats["refuse"] += 1
        stats["waiting"] -= 1
        last_actions[self.user_id] = "refuse"
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("❌ Ta candidature sur **Kawail_FPS** a été refusée.")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

# --- FORMULAIRE ---
class CandidatureModal(discord.ui.Modal, title="Dossier Staff Kawail_FPS"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge", placeholder="Ton nom, ton âge")
    dispo = discord.ui.TextInput(label="Disponibilités", placeholder="Ex: Lundi au Vendredi")
    exp = discord.ui.TextInput(label="Expériences passées", style=discord.TextStyle.paragraph)
    apport = discord.ui.TextInput(label="Ton apport au serveur", style=discord.TextStyle.paragraph)
    motive = discord.ui.TextInput(label="Tes motivations", style=discord.TextStyle.paragraph, min_length=20)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        global stats
        stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="⏰ Dispos", value=self.dispo.value)
        embed.add_field(name="📚 Expériences", value=self.exp.value, inline=False)
        embed.add_field(name="💡 Apport", value=self.apport.value, inline=False)
        embed.add_field(name="❤️ Motivations", value=self.motive.value, inline=False)
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.response.send_message("✅ Ton dossier a été envoyé !", ephemeral=True)

# --- SYSTÈME GITHUB ---
async def send_github_update(author, message, url, repo):
    guild = bot.get_guild(GUILD_ID)
    category = guild.get_channel(CAT_INFO_ID)
    channel = discord.utils.get(guild.channels, name=GITHUB_CHAN_NAME)
    
    if not channel:
        channel = await guild.create_text_channel(GITHUB_CHAN_NAME, category=category)
    
    embed = discord.Embed(
        title=f"🛠️ GitHub Update : {repo}", 
        description=f"**Auteur:** {author}\n**Message:** {message}", 
        color=0x2b2d31, 
        url=url
    )
    embed.set_footer(text="Webhook Kawail_FPS")
    await channel.send(embed=embed)

# --- BOT MAIN ---
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
        print(f"✅ Bot Kawail_FPS en ligne !")
        chan = self.get_channel(RECRUT_CHANNEL_ID)
        if chan:
            async for m in chan.history(limit=5):
                if m.author.id == self.user.id: return
            
            embed = discord.Embed(
                title="━━━ 🌟 RECRUTEMENT : KAWAIL_FPS 🌟 ━━━",
                description=(
                    "✨ **REJOINS L'ÉQUIPE DU SERVEUR !** ✨\n\n"
                    "Tu souhaites t'investir dans le projet avec **Kawail_FPS** ? C'est ici !\n\n"
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
                    "🏆 **POURQUOI NOUS REJOINDRE ?**\n"
                    "> • Travaille en direct avec le Staff.\n"
                    "> • Aide au développement de la communauté.\n\n"
                    "📑 **COMMENT POSTULER ?**\n"
                    "Clique sur le bouton ci-dessous et remplis le formulaire.\n\n"
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
                    "👇 **CLIQUE CI-DESSOUS POUR CANDIDATER !**"
                ),
                color=0xFF69B4
            )
            await chan.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

@bot.tree.command(name="list", description="Stats recrutement")
async def list_stats(interaction: discord.Interaction):
    if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
    await interaction.response.send_message(f"📊 **Stats :**\n⏳ Attente : `{stats['waiting']}`\n✅ Acceptés : `{stats['accept']}`\n❌ Refusés : `{stats['refuse']}`")

@bot.tree.command(name="annuler", description="Annule le dernier choix")
async def annuler(interaction: discord.Interaction, membre: discord.Member):
    global stats
    if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
    action = last_actions.get(membre.id)
    if not action: return await interaction.response.send_message("Aucune action trouvée.", ephemeral=True)
    if action == "accept": stats["accept"] -= 1
    else: stats["refuse"] -= 1
    stats["waiting"] += 1
    del last_actions[membre.id]
    await interaction.response.send_message(f"🔄 Action annulée pour {membre.name}.")

keep_alive()
bot.run(TOKEN)
