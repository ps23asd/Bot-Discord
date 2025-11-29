import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, MARVEL_RANKS, ADMIN_ROLE_ID
from database import db
from views.ticket_views import TicketPanelView
from views.account_views import Level15NotFinishView, Level15DoneView

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_voice", description="إنشاء قنوات صوتية")
    @app_commands.describe(count="عدد القنوات الصوتية")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_voice(self, interaction: discord.Interaction, count: int = 3):
        guild = interaction.guild
        
        category = discord.utils.get(guild.categories, name="🔊 Voice Channels")
        if not category:
            category = await guild.create_category("🔊 Voice Channels")
        
        for i in range(1, count + 1):
            existing = discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}")
            if not existing:
                await guild.create_voice_channel(
                    name=f"🔊│Voice {i}",
                    category=category
                )
        
        await interaction.response.send_message(f"✅ تم إنشاء {count} قنوات صوتية!", ephemeral=True)
    
    @app_commands.command(name="setup_all", description="إعداد كل شيء")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_all(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        status_messages = []
        
        try:
            # ============ 1. Setup Voice Channels ============
            voice_cat = discord.utils.get(guild.categories, name="🔊 Voice Channels")
            if not voice_cat:
                voice_cat = await guild.create_category("🔊 Voice Channels")
            for i in range(1, 4):
                existing = discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}")
                if not existing:
                    await guild.create_voice_channel(f"🔊│Voice {i}", category=voice_cat)
            status_messages.append("✅ تم إنشاء قنوات الصوت")
            
            # ============ 2. Setup Tickets System ============
            for cat_name in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
                if not discord.utils.get(guild.categories, name=cat_name):
                    await guild.create_category(cat_name)
            
            tickets_category = discord.utils.get(guild.categories, name="🎫 التذاكر")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True
                )
            }
            
            existing_panel = discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة")
            if not existing_panel:
                panel_channel = await guild.create_text_channel(
                    name="🎫│فتح-تذكرة",
                    category=tickets_category,
                    overwrites=overwrites
                )
                
                embed = discord.Embed(
                    title="🎫 نظام التذاكر",
                    description="اختر رانك الحساب من القائمة لفتح تذكرة جديدة",
                    color=COLORS['purple']
                )
                embed.add_field(
                    name="📋 التعليمات",
                    value="1️⃣ اختر الرانك من القائمة\n2️⃣ املأ معلومات الحساب\n3️⃣ انتظر الرد",
                    inline=False
                )
                embed.set_footer(text="نظام التذاكر الآلي")
                
                await panel_channel.send(embed=embed, view=TicketPanelView())
            
            status_messages.append("✅ تم إعداد نظام التذاكر")
            
            # ============ 3. Setup Level 15 System ============
            level_category = discord.utils.get(guild.categories, name="📊 Level 15 System")
            if not level_category:
                level_category = await guild.create_category("📊 Level 15 System")
            
            # Backup channel - الجميع يقدر يقرأ
            backup_overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,   # ✅ الجميع يقرأ
                    send_messages=False   # ❌ لا أحد يكتب
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True
                )
            }
            
            existing_backup = discord.utils.get(guild.text_channels, name="🔒│backup-accounts")
            if not existing_backup:
                backup_channel = await guild.create_text_channel(
                    name="🔒│backup-accounts",
                    category=level_category,
                    overwrites=backup_overwrites
                )
                
                # رسالة توضيحية
                info_embed = discord.Embed(
                    title="💾 النسخ الاحتياطية",
                    description="هنا يتم حفظ نسخة احتياطية من كل الحسابات المضافة",
                    color=COLORS['purple']
                )
                info_embed.add_field(
                    name="📝 ملاحظة",
                    value="جميع الحسابات المضافة يتم حفظها هنا تلقائياً\nالجميع يمكنهم القراءة",
                    inline=False
                )
                msg = await backup_channel.send(embed=info_embed)
                await msg.pin()
            
            # Not finish channel - الجميع يقدر يقرأ
            channel_overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,   # ✅ الجميع يقرأ
                    send_messages=False   # ❌ لا أحد يكتب (إلا من خلال الأزرار)
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True
                )
            }
            
            existing_nf = discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish")
            if not existing_nf:
                not_finish_channel = await guild.create_text_channel(
                    name="⏳│level-15-not-finish",
                    category=level_category,
                    overwrites=channel_overwrites
                )
                
                nf_embed = discord.Embed(
                    title="⏳ حسابات لم تصل لفل 15",
                    description="هنا يتم وضع الحسابات اللي لسه ما وصلتش لفل 15\n\n**يرجى تحديث اللفل ومين فاتح الحساب**",
                    color=COLORS['warning']
                )
                nf_embed.add_field(
                    name="📋 كيفية الاستخدام",
                    value="• اضغط 'إضافة حساب' لإضافة حساب جديد\n• اضغط 'تعديل' لتعديل بيانات الحساب\n• اضغط 'نقل لـ Done' عند وصول الحساب لفل 15",
                    inline=False
                )
                nf_msg = await not_finish_channel.send(embed=nf_embed, view=Level15NotFinishView())
                await nf_msg.pin()
            
            # Done channel - الجميع يقدر يقرأ
            existing_done = discord.utils.get(guild.text_channels, name="✅│level-15-done")
            if not existing_done:
                done_channel = await guild.create_text_channel(
                    name="✅│level-15-done",
                    category=level_category,
                    overwrites=channel_overwrites
                )
                
                done_embed = discord.Embed(
                    title="✅ حسابات وصلت لفل 15",
                    description="هنا يتم وضع الحسابات اللي وصلت لفل 15 وجاهزة للبيع",
                    color=COLORS['success']
                )
                done_embed.add_field(
                    name="📋 كيفية الاستخدام",
                    value="• اضغط 'إضافة حساب مكتمل' لإضافة حساب وصل لفل 15\n• اضغط 'تعديل' لتعديل البيانات\n• الحسابات هنا جاهزة للبيع",
                    inline=False
                )
                done_msg = await done_channel.send(embed=done_embed, view=Level15DoneView())
                await done_msg.pin()
            
            status_messages.append("✅ تم إعداد نظام Level 15")
            
            # ============ 4. Setup Stats Channel ============
            stats_category = discord.utils.get(guild.categories, name="📈 الإحصائيات")
            if not stats_category:
                stats_category = await guild.create_category("📈 الإحصائيات")
            
            existing_stats = discord.utils.get(guild.text_channels, name="📊│احصائيات")
            if not existing_stats:
                stats_channel = await guild.create_text_channel(
                    name="📊│احصائيات",
                    category=stats_category,
                    overwrites=channel_overwrites
                )
                
                # سيتم تحديثها من stats cog
                stats_cog = self.bot.get_cog('StatsCog')
                if stats_cog:
                    embed = await stats_cog.create_stats_embed()
                    message = await stats_channel.send(embed=embed)
                    stats_cog.stats_channel_id = stats_channel.id
                    stats_cog.stats_message_id = message.id
            
            status_messages.append("✅ تم إعداد قناة الإحصائيات")
            
            # ============ Final Response ============
            final_embed = discord.Embed(
                title="✅ تم إعداد كل شيء بنجاح!",
                description="\n".join(status_messages),
                color=COLORS['success']
            )
            final_embed.add_field(
                name="📋 الأوامر المتاحة",
                value="```\n"
                      "/setup_tickets - إعداد التذاكر\n"
                      "/setup_level15 - إعداد Level 15\n"
                      "/setup_voice - إعداد الصوت\n"
                      "/setup_stats - إعداد الإحصائيات\n"
                      "/add_account - إضافة حساب\n"
                      "/stats - عرض الإحصائيات\n"
                      "```",
                inline=False
            )
            
            await interaction.followup.send(embed=final_embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="add_rank", description="إضافة رانك جديد")
    @app_commands.describe(rank_name="اسم الرانك")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_rank(self, interaction: discord.Interaction, rank_name: str):
        from config import MARVEL_RANKS
        if rank_name not in MARVEL_RANKS:
            MARVEL_RANKS.append(rank_name)
            await interaction.response.send_message(f"✅ تم إضافة الرانك: {rank_name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ الرانك موجود بالفعل!", ephemeral=True)
    
    @app_commands.command(name="list_ranks", description="عرض قائمة الرانكات")
    async def list_ranks(self, interaction: discord.Interaction):
        from config import RANK_CATEGORIES, RANK_EMOJIS
        
        embed = discord.Embed(
            title="📋 قائمة الرانكات",
            color=COLORS['info']
        )
        
        for category, ranks in RANK_CATEGORIES.items():
            emoji = RANK_EMOJIS.get(category, "🎮")
            ranks_text = "\n".join([f"• {rank}" for rank in ranks])
            embed.add_field(
                name=f"{emoji} {category}",
                value=ranks_text,
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="backup", description="عرض النسخ الاحتياطية")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction):
        backup_accounts = await db.get_backup_accounts()
        
        if not backup_accounts:
            await interaction.response.send_message("📭 لا توجد نسخ احتياطية!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"💾 النسخ الاحتياطية ({len(backup_accounts)})",
            color=COLORS['purple']
        )
        
        for acc in backup_accounts[-10:]:
            embed.add_field(
                name=f"🆔 {acc.get('id', 'N/A')}",
                value=f"📧 {acc.get('email', 'N/A')[:30]}...\nLevel: {acc.get('current_level', 'N/A')}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="move_category", description="نقل قناة لفئة أخرى")
    @app_commands.describe(category_name="اسم الفئة")
    @app_commands.checks.has_permissions(administrator=True)
    async def move_category(self, interaction: discord.Interaction, category_name: str):
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if not category:
            await interaction.response.send_message("❌ الفئة غير موجودة!", ephemeral=True)
            return
        
        await interaction.channel.edit(category=category)
        await interaction.response.send_message(f"✅ تم نقل القناة إلى: {category_name}", ephemeral=True)
    
    @app_commands.command(name="sync", description="مزامنة الأوامر")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.tree.sync()
        await interaction.followup.send("✅ تم مزامنة الأوامر!", ephemeral=True)
    
    @app_commands.command(name="clean_channels", description="حذف كل القنوات المنشأة")
    @app_commands.checks.has_permissions(administrator=True)
    async def clean_channels(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        deleted = 0
        
        categories_to_delete = [
            "🔊 Voice Channels",
            "🎫 التذاكر",
            "💰 انتظار الفلوس",
            "✅ تم تسليم الفلوس",
            "📊 Level 15 System",
            "📈 الإحصائيات"
        ]
        
        for cat_name in categories_to_delete:
            category = discord.utils.get(guild.categories, name=cat_name)
            if category:
                for channel in category.channels:
                    await channel.delete()
                    deleted += 1
                await category.delete()
                deleted += 1
        
        await interaction.followup.send(f"✅ تم حذف {deleted} قناة/فئة!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))