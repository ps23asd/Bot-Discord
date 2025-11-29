import discord
from discord.ext import commands, tasks
from discord import app_commands
from config import COLORS
from database import db
from datetime import datetime

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_channel_id = None
        self.stats_message_id = None
        self.auto_update_stats.start()  # Auto update every 5 minutes
    
    def cog_unload(self):
        self.auto_update_stats.cancel()
    
    @tasks.loop(minutes=5)
    async def auto_update_stats(self):
        """تحديث الإحصائيات تلقائياً كل 5 دقائق"""
        if self.stats_channel_id and self.stats_message_id:
            try:
                channel = self.bot.get_channel(self.stats_channel_id)
                if channel:
                    message = await channel.fetch_message(self.stats_message_id)
                    if message:
                        embed = await self.create_stats_embed()
                        await message.edit(embed=embed)
                        print("📊 Stats updated automatically")
            except Exception as e:
                print(f"❌ Auto update error: {e}")
    
    @auto_update_stats.before_loop
    async def before_auto_update(self):
        await self.bot.wait_until_ready()
    
    async def create_stats_embed(self) -> discord.Embed:
        """إنشاء embed الإحصائيات"""
        stats = await db.get_stats()
        accounts = await db.get_all_accounts()
        
        embed = discord.Embed(
            title="📊 إحصائيات النظام",
            description="*يتم التحديث تلقائياً كل 5 دقائق*",
            color=COLORS['purple'],
            timestamp=discord.utils.utcnow()
        )
        
        # General Stats
        finished = len([a for a in accounts if a.get('status') == 'finished'])
        not_finished = len([a for a in accounts if a.get('status') == 'not_finished'])
        banned = len([a for a in accounts if a.get('status') == 'banned'])
        
        embed.add_field(
            name="💰 إحصائيات المبيعات",
            value=f"```yaml\n"
                  f"المبيعات الكلية: {stats.get('total_sales', 0)}\n"
                  f"الأرباح الكلية: {stats.get('total_revenue', 0):,.0f} جنيه\n"
                  f"متوسط السعر: {stats.get('total_revenue', 0) / max(stats.get('total_sales', 1), 1):,.0f} جنيه\n"
                  f"```",
            inline=False
        )
        
        # Account Stats
        embed.add_field(
            name="🎮 إحصائيات الحسابات",
            value=f"```yaml\n"
                  f"إجمالي الحسابات: {len(accounts)}\n"
                  f"مكتملة ✅: {finished}\n"
                  f"غير مكتملة ⏳: {not_finished}\n"
                  f"محظورة 🚫: {banned}\n"
                  f"```",
            inline=True
        )
        
        # Today Stats
        today = datetime.now().strftime('%Y-%m-%d')
        daily = stats.get('daily_stats', {}).get(today, {'sales': 0, 'revenue': 0})
        
        embed.add_field(
            name="📅 إحصائيات اليوم",
            value=f"```yaml\n"
                  f"المبيعات: {daily.get('sales', 0)}\n"
                  f"الأرباح: {daily.get('revenue', 0):,.0f} جنيه\n"
                  f"```",
            inline=True
        )
        
        # Top Sellers (Top 5)
        seller_stats = stats.get('seller_stats', {})
        if seller_stats:
            top_sellers = sorted(seller_stats.items(), key=lambda x: x[1]['sales'], reverse=True)[:5]
            sellers_text = ""
            for i, (seller, data) in enumerate(top_sellers, 1):
                sellers_text += f"{i}. {seller}: {data['sales']} ({data['revenue']:,.0f} ج)\n"
        else:
            sellers_text = "لا توجد مبيعات بعد"
        
        embed.add_field(
            name="🏆 أفضل البائعين (Top 5)",
            value=f"```\n{sellers_text}```",
            inline=False
        )
        
        # Top Ranks (Top 5)
        rank_stats = stats.get('rank_stats', {})
        if rank_stats:
            top_ranks = sorted(rank_stats.items(), key=lambda x: x[1]['sales'], reverse=True)[:5]
            ranks_text = ""
            for i, (rank, data) in enumerate(top_ranks, 1):
                ranks_text += f"{i}. {rank}: {data['sales']} ({data['revenue']:,.0f} ج)\n"
        else:
            ranks_text = "لا توجد مبيعات بعد"
        
        embed.add_field(
            name="📊 أكثر الرانكات مبيعاً (Top 5)",
            value=f"```\n{ranks_text}```",
            inline=False
        )
        
        # Last 5 Sales
        accounts_sold = stats.get('accounts_sold', [])
        if accounts_sold:
            last_sales = accounts_sold[-5:][::-1]  # Last 5 reversed
            sales_text = ""
            for sale in last_sales:
                sales_text += f"• {sale.get('rank', 'N/A')} - {sale.get('price', 0):,.0f} ج - {sale.get('seller', 'N/A')}\n"
        else:
            sales_text = "لا توجد مبيعات بعد"
        
        embed.add_field(
            name="🛒 آخر 5 مبيعات",
            value=f"```\n{sales_text}```",
            inline=False
        )
        
        embed.set_footer(text="🔄 آخر تحديث")
        
        return embed
    
    @app_commands.command(name="setup_stats", description="إعداد قناة الإحصائيات")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        category = discord.utils.get(guild.categories, name="📈 الإحصائيات")
        if not category:
            category = await guild.create_category("📈 الإحصائيات")
        
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
        
        # Delete old stats channel if exists
        old_channel = discord.utils.get(guild.text_channels, name="📊│احصائيات")
        if old_channel:
            await old_channel.delete()
        
        stats_channel = await guild.create_text_channel(
            name="📊│احصائيات",
            category=category,
            overwrites=overwrites
        )
        
        embed = await self.create_stats_embed()
        message = await stats_channel.send(embed=embed)
        
        # Save channel and message IDs
        self.stats_channel_id = stats_channel.id
        self.stats_message_id = message.id
        
        await interaction.response.send_message("✅ تم إعداد قناة الإحصائيات بنجاح!", ephemeral=True)
    
    @app_commands.command(name="update_stats", description="تحديث الإحصائيات يدوياً")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Find stats channel
        guild = interaction.guild
        stats_channel = discord.utils.get(guild.text_channels, name="📊│احصائيات")
        
        if not stats_channel:
            await interaction.followup.send("❌ قناة الإحصائيات غير موجودة! استخدم `/setup_stats`", ephemeral=True)
            return
        
        # Delete old messages and send new
        async for message in stats_channel.history(limit=10):
            if message.author == guild.me:
                await message.delete()
        
        embed = await self.create_stats_embed()
        message = await stats_channel.send(embed=embed)
        
        # Update saved IDs
        self.stats_channel_id = stats_channel.id
        self.stats_message_id = message.id
        
        await interaction.followup.send("✅ تم تحديث الإحصائيات!", ephemeral=True)
    
    @app_commands.command(name="stats", description="عرض الإحصائيات")
    async def stats(self, interaction: discord.Interaction):
        embed = await self.create_stats_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="daily_stats", description="إحصائيات اليوم")
    async def daily_stats(self, interaction: discord.Interaction):
        stats = await db.get_stats()
        today = datetime.now().strftime('%Y-%m-%d')
        daily = stats.get('daily_stats', {}).get(today, {'sales': 0, 'revenue': 0})
        
        embed = discord.Embed(
            title=f"📅 إحصائيات {today}",
            color=COLORS['info']
        )
        embed.add_field(name="💰 المبيعات", value=str(daily.get('sales', 0)), inline=True)
        embed.add_field(name="💵 الأرباح", value=f"{daily.get('revenue', 0):,.0f} جنيه", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="reset_stats", description="إعادة تعيين الإحصائيات")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_stats(self, interaction: discord.Interaction):
        await db.reset_stats()
        await interaction.response.send_message("✅ تم إعادة تعيين الإحصائيات!", ephemeral=True)
        
        # Update stats display
        if self.stats_channel_id and self.stats_message_id:
            try:
                channel = self.bot.get_channel(self.stats_channel_id)
                message = await channel.fetch_message(self.stats_message_id)
                embed = await self.create_stats_embed()
                await message.edit(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(StatsCog(bot))