import discord
from discord import app_commands
from discord.ext import tasks
import os
from flask import Flask
from threading import Thread

# --- SERVEUR WEB (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Kawail_FPS en ligne !"

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

# --- VARIABLES DE STATS ---
stats = {"accept": 0, "refuse": 0, "waiting": 0}

# --- VUES ---
class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="kawail_apply_v3")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class CandidatureModal(discord.ui.Modal, title="Dossier de Candidature Staff"):
    pseudo = discord.ui.TextInput(label="Pseudo & Âge", placeholder="Ex: Kawail_FPS, 17 ans", required=True)
    dispo = discord.ui.TextInput(label="Tes disponibilités", placeholder="Ex: Soir et week-end", required=True)
    exp = discord.ui.TextInput(label="Expériences passées", style=discord.TextStyle.paragraph, required=True)
    apport = discord.ui.TextInput(label="Ton apport au serveur", style=discord.TextStyle.paragraph, required=True)
    motive = discord.ui.TextInput(label="Tes motivations", style=discord.TextStyle.paragraph, min_length=20, required=True)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        stats["waiting"] += 1
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value, inline=True)
        embed.add_field(name="⏰ Dispos", value=self.dispo.value, inline=True)
        embed.add_field(name="📚 Expériences", value=self.exp.value, inline=False)
        embed.add_field(name="💡 Apport", value=self.apport.value, inline=False)
        embed.add_field(name="❤️ Motivations", value=self.motive.value, inline=False)
        embed.set_timestamp()
        
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.response.send_message("✅ Ton dossier a été envoyé avec succès au staff !", ephemeral=True)

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok_v3")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        stats["accept"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send(f"Tu as été **accepté** sur le serveur **kawail_fps** ! Bienvenue dans l'équipe !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no_v3")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Seul le Fondateur peut faire ça.", ephemeral=True)
        
        stats["refuse"] += 1
        stats["waiting"] -= 1
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send(f"Oh non, tu n'as pas été **accepté** sur le serveur **kawail_fps**. Retente ta chance !")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

# --- CLASSE PRINCIPALE ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(RecruitmentView(self))
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"✅ Kawail_FPS Bot est en ligne : {self.user}")
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
        
        found = False
        async for m in channel.history(limit=5):
            if m.author.id == self.user.id and m.embeds:
                found = True
                break
        
        if not found:
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
            embed.set_thumbnail(url=self.user.display_avatar.url)
            embed.set_footer(text="Candidature Rapide • Kawail_FPS")
            await channel.send(embed=embed, view=RecruitmentView(self))

bot = MyBot()

@bot.tree.command(name="list", description="Affiche les statistiques de recrutement")
async def list_stats(interaction: discord.Interaction):
    if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Accès réservé au Fondateur.", ephemeral=True)
    
    embed = discord.Embed(title="📊 Statistiques de Recrutement", color=0x3498DB)
    embed.add_field(name="✅ Acceptés", value=str(stats["accept"]), inline=True)
    embed.add_field(name="❌ Refusés", value=str(stats["refuse"]), inline=True)
    embed.add_field(name="⏳ En attente", value=str(stats["waiting"]), inline=True)
    await interaction.response.send_message(embed=embed)

keep_alive()
bot.run(TOKEN)
