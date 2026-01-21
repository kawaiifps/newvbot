import discord
from discord import app_commands
import os
from flask import Flask
from threading import Thread

# --- SERVEUR WEB POUR RENDER/KOYEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot en ligne"

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

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok_v6")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        global stats
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True) # Évite l'erreur de timeout
        stats["accept"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("✅ Candidature acceptée pour **Kawail_FPS** !")
        except: pass
        await interaction.edit_original_response(content=f"✅ Admis par {interaction.user.name}")

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no_v6")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        global stats
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        stats["refuse"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("❌ Candidature refusée.")
        except: pass
        await interaction.edit_original_response(content=f"❌ Refusé par {interaction.user.name}")

class CandidatureModal(discord.ui.Modal, title="Dossier Staff Kawail_FPS"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge", placeholder="Kawail_FPS, 17 ans")
    dispo = discord.ui.TextInput(label="Dispos", placeholder="Soirs et week-end")
    exp = discord.ui.TextInput(label="Expériences", style=discord.TextStyle.paragraph)
    apport = discord.ui.TextInput(label="Apport", style=discord.TextStyle.paragraph)
    motive = discord.ui.TextInput(label="Motivations", style=discord.TextStyle.paragraph, min_length=10)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        global stats
        # On dit à Discord qu'on traite la demande
        await interaction.response.defer(ephemeral=True)
        
        stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="⏰ Dispos", value=self.dispo.value)
        embed.add_field(name="📚 Expériences", value=self.exp.value, inline=False)
        embed.add_field(name="❤️ Motivations", value=self.motive.value, inline=False)
        
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.followup.send("✅ Dossier envoyé avec succès !", ephemeral=True)

class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="btn_apply_v6")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        # On envoie le formulaire DIRECTEMENT sans defer ici
        await interaction.response.send_modal(CandidatureModal(self.bot))

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
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
            # Nettoyage automatique : on vérifie si le message est déjà là
            async for m in channel.history(limit=5):
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
            await channel.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

@bot.tree.command(name="list", description="Stats recrutement")
async def list_stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"📊 Stats : ⏳ En attente: {stats['waiting']} | ✅ Acceptés: {stats['accept']} | ❌ Refusés: {stats['refuse']}")

keep_alive()
bot.run(TOKEN)
