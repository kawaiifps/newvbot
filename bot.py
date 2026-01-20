import discord
from discord import app_commands
from discord.ext import tasks
import os
from flask import Flask
from threading import Thread

# --- SERVEUR WEB POUR RENDER (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Kawail_FPS Bot est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN")  # À configurer dans les Secrets sur Render
GUILD_ID = 1461846612367380707
LOG_RECRU_ID = 1462047465090973698
RECRUT_CHANNEL_ID = 1461851553001504809
FOUNDER_ROLE_ID = 1461848068780458237

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.stats = {"accept": 0, "refuse": 0, "waiting": 0}
        self.last_actions = {}

    async def setup_hook(self):
        # Synchro des commandes slash pour ton serveur
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")
        if not self.update_status.is_running():
            self.update_status.start()
        await self.check_recruitment_post()

    @tasks.loop(minutes=10)
    async def update_status(self):
        guild = self.get_guild(GUILD_ID)
        if guild:
            await self.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=f"{guild.member_count} membres"
            ))

    async def check_recruitment_post(self):
        channel = self.get_channel(RECRUT_CHANNEL_ID)
        if channel:
            async for message in channel.history(limit=10):
                if message.author == self.user and message.embeds:
                    return
            
            embed = discord.Embed(
                title="━━━ 🌟 RECRUTEMENT : KAWAIL_FPS 🌟 ━━━",
                description="✨ **REJOINS L'ÉQUIPE !** ✨\n\nClique sur le bouton ci-dessous pour candidater !",
                color=0xFF69B4
            )
            embed.set_footer(text="Système de recrutement automatique")
            view = RecruitmentView(self)
            await channel.send(embed=embed, view=view)

# --- VUES ET MODAL ---
class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="apply_btn")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class CandidatureModal(discord.ui.Modal, title="Dossier Staff"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge", placeholder="Ex: Kawail_FPS, 17 ans")
    motive = discord.ui.TextInput(label="Tes motivations", style=discord.TextStyle.paragraph)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        self.bot.stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="❤️ Motivations", value=self.motive.value)
        
        view = AdminView(self.bot, interaction.user.id)
        await log_chan.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Dossier envoyé avec succès !", ephemeral=True)

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("Seul le Fondateur peut faire ça.", ephemeral=True)
        
        self.bot.stats["accept"] += 1
        self.bot.stats["waiting"] -= 1
        self.bot.last_actions[self.user_id] = "accept"
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("Tu as été **accepté** sur le serveur **kawail_fps** !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("Seul le Fondateur peut faire ça.", ephemeral=True)
        
        self.bot.stats["refuse"] += 1
        self.bot.stats["waiting"] -= 1
        self.bot.last_actions[self.user_id] = "refuse"
        
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("Oh non, tu n'as pas été **accepté**, retente ta chance !")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

# --- COMMANDES ---
bot = MyBot()

@bot.tree.command(name="list", description="Stats recrutement")
async def list_stats(interaction: discord.Interaction):
    if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("Accès refusé.", ephemeral=True)
    s = bot.stats
    await interaction.response.send_message(f"📊 **Stats :**\n✅ Acceptés : {s['accept']}\n❌ Refusés : {s['refuse']}\n⏳ En attente : {s['waiting']}")

@bot.tree.command(name="annuler", description="Annule le dernier choix")
async def annuler(interaction: discord.Interaction, membre: discord.Member):
    if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("Accès refusé.", ephemeral=True)
    
    action = bot.last_actions.get(membre.id)
    if not action: return await interaction.response.send_message("Aucune action trouvée.", ephemeral=True)
    
    if action == "accept": bot.stats["accept"] -= 1
    else: bot.stats["refuse"] -= 1
    bot.stats["waiting"] += 1
    del bot.last_actions[membre.id]
    await interaction.response.send_message(f"🔄 Action annulée pour {membre.name}.")

# Lancement
keep_alive()
bot.run(TOKEN)
