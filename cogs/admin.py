import discord
from discord.ext import commands
from discord import app_commands
import os

GUILD_ID = int(os.getenv('GUILD_ID', 0))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))

COLORS = {
    "success": 0x00FF00,
    "error": 0xFF0000,
    "info": 0x00BFFF,
    "warning": 0xFFFF00,
    "purple": 0x9B59B6
}

RANK_CATEGORIES = {
    "Bronze": ["Bronze 3", "Bronze 2", "Bronze 1"],
    "Silver": ["Silver 3", "Silver 2", "Silver 1"],
    "Gold": ["Gold 3", "Gold 2", "Gold 1"],
    "Platinum": ["Platinum 3", "Platinum 2", "Platinum 1"],
    "Diamond": ["Diamond 3", "Diamond 2", "Diamond 1"]
}

RANK_EMOJIS = {
    "Bronze": "🟫", "Silver": "⚪", "Gold": "🟨",
    "Platinum": "⬜", "Diamond": "💎"
}

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="اختبار البوت")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong! {round(self.bot.latency * 1000)}ms")
    
    @app_commands.command(name="sync", description="مزامنة الأوامر")
    @app_commands.default_permissions(administrator=True)
    async def sync_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
            else:
                synced = await self.bot.tree.sync()
            await interaction.followup.send(f"✅ Synced {len(synced)} commands!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="setup_voice", description="إنشاء قنوات صوتية")
    @app_commands.default_permissions(administrator=True)
    async def setup_voice(self, interaction: discord.Interaction, count: int = 3):
        await interaction.response.defer(ephemeral=True)
        
        cat = discord.utils.get(interaction.guild.categories, name="🔊 Voice Channels")
        if not cat:
            cat = await interaction.guild.create_category("🔊 Voice Channels")
        
        for i in range(1, count + 1):
            if not discord.utils.get(interaction.guild.voice_channels, name=f"🔊│Voice {i}"):
                await interaction.guild.create_voice_channel(f"🔊│Voice {i}", category=cat)
        
        await interaction.followup.send(f"✅ Created {count} voice channels!")
    
    @app_commands.command(name="setup_all", description="إعداد كل شيء")
    @app_commands.default_permissions(administrator=True)
    async def setup_all(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        status = []
        
        try:
            # Import views here
            from views.ticket_views import TicketPanelView
            from views.account_views import Level15NotFinishView, Level15DoneView
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # 1. Voice
            cat = discord.utils.get(guild.categories, name="🔊 Voice Channels")
            if not cat:
                cat = await guild.create_category("🔊 Voice Channels")
            for i in range(1, 4):
                if not discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}"):
                    await guild.create_voice_channel(f"🔊│Voice {i}", category=cat)
            status.append("✅ Voice Channels")
            
            # 2. Tickets
            for n in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
                if not discord.utils.get(guild.categories, name=n):
                    await guild.create_category(n)
            
            tcat = discord.utils.get(guild.categories, name="🎫 التذاكر")
            if not discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة"):
                ch = await guild.create_text_channel("🎫│فتح-تذكرة", category=tcat, overwrites=overwrites)
                e = discord.Embed(title="🎫 نظام التذاكر", description="اختر رانك الحساب لفتح تذكرة", color=0x9B59B6)
                await ch.send(embed=e, view=TicketPanelView())
            status.append("✅ Tickets")
            
            # 3. Level 15
            lcat = discord.utils.get(guild.categories, name="📊 Level 15 System")
            if not lcat:
                lcat = await guild.create_category("📊 Level 15 System")
            
            if not discord.utils.get(guild.text_channels, name="🔒│backup-accounts"):
                await guild.create_text_channel("🔒│backup-accounts", category=lcat, overwrites=overwrites)
            
            if not discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish"):
                ch = await guild.create_text_channel("⏳│level-15-not-finish", category=lcat, overwrites=overwrites)
                e = discord.Embed(title="⏳ حسابات لم تصل لفل 15", color=0xFFFF00)
                m = await ch.send(embed=e, view=Level15NotFinishView())
                await m.pin()
            
            if not discord.utils.get(guild.text_channels, name="✅│level-15-done"):
                ch = await guild.create_text_channel("✅│level-15-done", category=lcat, overwrites=overwrites)
                e = discord.Embed(title="✅ حسابات وصلت لفل 15", color=0x00FF00)
                m = await ch.send(embed=e, view=Level15DoneView())
                await m.pin()
            status.append("✅ Level 15")
            
            # 4. Stats
            scat = discord.utils.get(guild.categories, name="📈 الإحصائيات")
            if not scat:
                scat = await guild.create_category("📈 الإحصائيات")
            if not discord.utils.get(guild.text_channels, name="📊│احصائيات"):
                ch = await guild.create_text_channel("📊│احصائيات", category=scat, overwrites=overwrites)
                e = discord.Embed(title="📊 الإحصائيات", description="سيتم التحديث تلقائياً", color=0x9B59B6)
                await ch.send(embed=e)
            status.append("✅ Stats")
            
            await interaction.followup.send(embed=discord.Embed(
                title="✅ تم الإعداد!",
                description="\n".join(status),
                color=0x00FF00
            ))
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="clean_channels", description="حذف كل القنوات")
    @app_commands.default_permissions(administrator=True)
    async def clean_channels(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        deleted = 0
        for name in ["🔊 Voice Channels", "🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس", "📊 Level 15 System", "📈 الإحصائيات"]:
            cat = discord.utils.get(interaction.guild.categories, name=name)
            if cat:
                for ch in cat.channels:
                    await ch.delete()
                    deleted += 1
                await cat.delete()
                deleted += 1
        
        await interaction.followup.send(f"✅ Deleted {deleted} channels!")
    
    @app_commands.command(name="list_ranks", description="عرض الرانكات")
    async def list_ranks(self, interaction: discord.Interaction):
        e = discord.Embed(title="📋 الرانكات", color=0x00BFFF)
        for cat, ranks in RANK_CATEGORIES.items():
            e.add_field(name=f"{RANK_EMOJIS.get(cat, '🎮')} {cat}", value="\n".join(ranks), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)
    
    @app_commands.command(name="bot_info", description="معلومات البوت")
    async def bot_info(self, interaction: discord.Interaction):
        e = discord.Embed(title="🤖 Marvel Bot", color=0x9B59B6)
        e.add_field(name="Name", value=self.bot.user.name, inline=True)
        e.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        e.add_field(name="Latency", value=f"{round(self.bot.latency*1000)}ms", inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))