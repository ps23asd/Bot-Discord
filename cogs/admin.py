import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, MARVEL_RANKS, ADMIN_ROLE_ID, RANK_CATEGORIES, RANK_EMOJIS
from database import db
from views.ticket_views import TicketPanelView
from views.account_views import Level15NotFinishView, Level15DoneView

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_voice", description="إنشاء قنوات صوتية")
    @app_commands.describe(count="عدد القنوات الصوتية")
    @app_commands.default_permissions(administrator=True)
    async def setup_voice(self, interaction: discord.Interaction, count: int = 3):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        
        category = discord.utils.get(guild.categories, name="🔊 Voice Channels")
        if not category:
            category = await guild.create_category("🔊 Voice Channels")
        
        created = 0
        for i in range(1, count + 1):
            existing = discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}")
            if not existing:
                await guild.create_voice_channel(f"🔊│Voice {i}", category=category)
                created += 1
        
        await interaction.followup.send(f"✅ تم إنشاء {created} قنوات صوتية!", ephemeral=True)
    
    @app_commands.command(name="setup_all", description="إعداد كل شيء")
    @app_commands.default_permissions(administrator=True)
    async def setup_all(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        status = []
        
        try:
            # 1. Voice Channels
            voice_cat = discord.utils.get(guild.categories, name="🔊 Voice Channels")
            if not voice_cat:
                voice_cat = await guild.create_category("🔊 Voice Channels")
            for i in range(1, 4):
                if not discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}"):
                    await guild.create_voice_channel(f"🔊│Voice {i}", category=voice_cat)
            status.append("✅ Voice Channels")
            
            # 2. Ticket Categories
            for cat_name in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
                if not discord.utils.get(guild.categories, name=cat_name):
                    await guild.create_category(cat_name)
            
            # 3. Ticket Panel
            tickets_cat = discord.utils.get(guild.categories, name="🎫 التذاكر")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            if not discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة"):
                panel = await guild.create_text_channel("🎫│فتح-تذكرة", category=tickets_cat, overwrites=overwrites)
                embed = discord.Embed(
                    title="🎫 نظام التذاكر",
                    description="اختر رانك الحساب من القائمة لفتح تذكرة جديدة",
                    color=COLORS['purple']
                )
                embed.add_field(name="📋 التعليمات", value="1️⃣ اختر الرانك\n2️⃣ املأ المعلومات\n3️⃣ انتظر الرد", inline=False)
                await panel.send(embed=embed, view=TicketPanelView())
            status.append("✅ Tickets System")
            
            # 4. Level 15 System
            level_cat = discord.utils.get(guild.categories, name="📊 Level 15 System")
            if not level_cat:
                level_cat = await guild.create_category("📊 Level 15 System")
            
            # Backup channel
            if not discord.utils.get(guild.text_channels, name="🔒│backup-accounts"):
                await guild.create_text_channel("🔒│backup-accounts", category=level_cat, overwrites=overwrites)
            
            # Not Finish channel
            if not discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish"):
                nf_channel = await guild.create_text_channel("⏳│level-15-not-finish", category=level_cat, overwrites=overwrites)
                embed = discord.Embed(title="⏳ حسابات لم تصل لفل 15", description="اضغط الزر لإضافة حساب", color=COLORS['warning'])
                msg = await nf_channel.send(embed=embed, view=Level15NotFinishView())
                await msg.pin()
            
            # Done channel
            if not discord.utils.get(guild.text_channels, name="✅│level-15-done"):
                done_channel = await guild.create_text_channel("✅│level-15-done", category=level_cat, overwrites=overwrites)
                embed = discord.Embed(title="✅ حسابات وصلت لفل 15", description="اضغط الزر لإضافة حساب مكتمل", color=COLORS['success'])
                msg = await done_channel.send(embed=embed, view=Level15DoneView())
                await msg.pin()
            status.append("✅ Level 15 System")
            
            # 5. Stats Channel
            stats_cat = discord.utils.get(guild.categories, name="📈 الإحصائيات")
            if not stats_cat:
                stats_cat = await guild.create_category("📈 الإحصائيات")
            
            if not discord.utils.get(guild.text_channels, name="📊│احصائيات"):
                stats_channel = await guild.create_text_channel("📊│احصائيات", category=stats_cat, overwrites=overwrites)
                stats_cog = self.bot.get_cog('StatsCog')
                if stats_cog:
                    embed = await stats_cog.create_stats_embed()
                    msg = await stats_channel.send(embed=embed)
                    stats_cog.stats_channel_id = stats_channel.id
                    stats_cog.stats_message_id = msg.id
            status.append("✅ Stats Channel")
            
            # Final Message
            embed = discord.Embed(
                title="✅ تم إعداد كل شيء!",
                description="\n".join(status),
                color=COLORS['success']
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="clean_channels", description="حذف كل القنوات المنشأة")
    @app_commands.default_permissions(administrator=True)
    async def clean_channels(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        deleted = 0
        
        categories = ["🔊 Voice Channels", "🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس", "📊 Level 15 System", "📈 الإحصائيات"]
        
        for cat_name in categories:
            category = discord.utils.get(guild.categories, name=cat_name)
            if category:
                for channel in category.channels:
                    await channel.delete()
                    deleted += 1
                await category.delete()
                deleted += 1
        
        await interaction.followup.send(f"✅ تم حذف {deleted} قناة/فئة!", ephemeral=True)
    
    @app_commands.command(name="sync", description="مزامنة الأوامر")
    @app_commands.default_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            from config import GUILD_ID
            if GUILD_ID and GUILD_ID != 0:
                guild = discord.Object(id=GUILD_ID)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
            else:
                synced = await self.bot.tree.sync()
            
            await interaction.followup.send(f"✅ تم مزامنة {len(synced)} أمر!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}", ephemeral=True)
    
    @app_commands.command(name="list_ranks", description="عرض قائمة الرانكات")
    async def list_ranks(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📋 قائمة الرانكات", color=COLORS['info'])
        
        for category, ranks in RANK_CATEGORIES.items():
            emoji = RANK_EMOJIS.get(category, "🎮")
            embed.add_field(name=f"{emoji} {category}", value="\n".join([f"• {r}" for r in ranks]), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="bot_info", description="معلومات عن البوت")
    async def bot_info(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📊 معلومات البوت", color=COLORS['info'])
        
        embed.add_field(
            name="🤖 البوت",
            value=f"```\nالاسم: {self.bot.user.name}\nID: {self.bot.user.id}\n```",
            inline=True
        )
        
        embed.add_field(
            name="🏰 السيرفر",
            value=f"```\nالأعضاء: {interaction.guild.member_count}\nالقنوات: {len(interaction.guild.channels)}\n```",
            inline=True
        )
        
        accounts = await db.get_all_accounts()
        stats = await db.get_stats()
        
        embed.add_field(
            name="💾 البيانات",
            value=f"```\nالحسابات: {len(accounts)}\nالمبيعات: {stats.get('total_sales', 0)}\n```",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
