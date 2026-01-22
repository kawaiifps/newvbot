import discord
from discord import app_commands
import os, json, asyncio, datetime, random
from flask import Flask, request
from threading import Thread

app = Flask('')

@app.route('/')
def home(): return "Bot en ligne !"

@app.route('/github', methods=['POST'])
def github_webhook():
    data = request.get_json(silent=True) or (json.loads(request.form.get('payload')) if request.form.get('payload') else None)
    if data and 'commits' in data:
        repo_name = data['repository']['name']
        branch = data.get('ref', '').split('/')[-1]
        for commit in data['commits']:
            bot.loop.create_task(send_github_update(commit['author']['name'], commit['message'], commit['url'], repo_name, branch, len(commit.get('added', [])), len(commit.get('removed', [])), len(commit.get('modified', []))))
    return "OK", 200

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1461846612367380707
LOG_RECRU_ID = 1462047465090973698
RECRUT_CHANNEL_ID = 1461851553001504809
FOUNDER_ROLE_ID = 1461848068780458237
CAT_INFO_ID = 1461849328237809774 
GITHUB_CHAN_NAME = "🤖〡changement-bot"
BANNED_WORDS = ["insulte1", "insulte2", "fdp"]

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.blurple, custom_id="join_giveaway")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            return await interaction.response.send_message("Tu es déjà inscrit !", ephemeral=True)
        self.participants.append(interaction.user.id)
        await interaction.response.send_message("✅ Inscription validée !", ephemeral=True)

class RecruitmentView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⭐ Postuler maintenant ⭐", style=discord.ButtonStyle.success, custom_id="kawail_v21")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CandidatureModal(self.bot))

class AdminView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="ACCEPTER", style=discord.ButtonStyle.success, custom_id="adm_ok_v21")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("✅ Ta candidature a été **acceptée** sur **Kawail_FPS** !")
        except: pass
        await interaction.response.edit_message(content=f"✅ Admis par {interaction.user.name}", view=None)

    @discord.ui.button(label="REFUSER", style=discord.ButtonStyle.danger, custom_id="adm_no_v21")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == FOUNDER_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Réservé au Fondateur.", ephemeral=True)
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("❌ Ta candidature sur **Kawail_FPS** a été refusée.")
        except: pass
        await interaction.response.edit_message(content=f"❌ Refusé par {interaction.user.name}", view=None)

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
        log_chan = self.bot.get_channel(LOG_RECRU_ID)
        embed = discord.Embed(title="📥 NOUVELLE CANDIDATURE", color=0xF1C40F)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Candidat", value=interaction.user.mention)
        embed.add_field(name="🎮 Pseudo/Âge", value=self.pseudo.value)
        embed.add_field(name="❤️ Motivations", value=self.motive.value[:1024], inline=False)
        await log_chan.send(embed=embed, view=AdminView(self.bot, interaction.user.id))
        await interaction.response.send_message("✅ Ton dossier a été envoyé !", ephemeral=True)

async def send_github_update(author, message, url, repo, branch, added, removed, modified):
    guild = bot.get_guild(GUILD_ID)
    if not guild: return
    channel = discord.utils.get(guild.channels, name=GITHUB_CHAN_NAME)
    if not channel: channel = await guild.create_text_channel(GITHUB_CHAN_NAME, category=guild.get_channel(CAT_INFO_ID))
    embed = discord.Embed(title="🚀 Nouveau Push !", description=f"```fix\n{message}```", color=0x2ecc71, url=url, timestamp=discord.utils.utcnow())
    embed.add_field(name="🌿 Branche", value=f"`{branch}`", inline=True)
    embed.add_field(name="📊 Fichiers", value=f"🟢 {added} | 🟠 {modified} | 🔴 {removed}", inline=True)
    embed.set_author(name=f"Auteur: {author}")
    await channel.send(embed=embed)

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(RecruitmentView(self))
        self.add_view(GiveawayView())
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Kawail_FPS 🛠️"))
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

    async def on_message(self, message):
        if message.author.bot: return
        is_staff = any(role.id == FOUNDER_ROLE_ID for role in message.author.roles)
        if not is_staff:
            if "http://" in message.content or "https://" in message.content or "discord.gg/" in message.content:
                await message.delete()
                return await message.channel.send(f"⚠️ {message.author.mention}, les liens sont interdits !", delete_after=3)
            if any(word in message.content.lower() for word in BANNED_WORDS):
                await message.delete()
                return await message.channel.send(f"⚠️ {message.author.mention}, surveille ton langage !", delete_after=3)

bot = MyBot()

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune"):
    await membre.kick(reason=raison)
    await interaction.response.send_message(f"👞 **{membre.name}** a été expulsé.")

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune"):
    await membre.ban(reason=raison)
    await interaction.response.send_message(f"🔨 **{membre.name}** a été banni.")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, membre: discord.Member, minutes: int, raison: str = "Aucune"):
    duration = datetime.timedelta(minutes=minutes)
    await membre.timeout(duration, reason=raison)
    await interaction.response.send_message(f"⏳ **{membre.name}** est en sourdine pour {minutes} min.")

@bot.tree.command(name="giveaway")
@app_commands.checks.has_permissions(manage_messages=True)
async def giveaway(interaction: discord.Interaction, lot: str, secondes: int):
    view = GiveawayView()
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"Lot : **{lot}**\nFinit dans : <t:{int(datetime.datetime.now().timestamp() + secondes)}:R>", color=0x00FFFF)
    await interaction.response.send_message(embed=embed, view=view)
    await asyncio.sleep(secondes)
    if not view.participants: return await interaction.followup.send(f"😭 Personne n'a participé.")
    gagnant = await bot.fetch_user(random.choice(view.participants))
    await interaction.followup.send(f"🎊 Félicitations {gagnant.mention}, tu as gagné **{lot}** !")

keep_alive()
bot.run(TOKEN)
