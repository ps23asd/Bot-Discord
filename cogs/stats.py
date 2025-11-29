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
        self.auto_update.start()
    
    def cog_unload(self):
        self.auto_update.cancel()
    
    @tasks.loop(minutes=5)
    async def auto_update(self):
        """تحديث الإحصائيات كل 5 دقائق"""
        if self.stats_channel_id and self.stats_message_id:
            try:
                channel = self.bot.get_channel(self.stats_channel_id)
                if channel:
                    message = await channel.fetch_message(self.stats_message_id)
                    embed = await self.create_stats_embed()
                    await message.edit(embed=embed)
            except:
                pass
    
    @auto_update.before_loop
    async def before_auto_update(self):
        await self.bot.wait_until_ready()
    
    async def create_stats_embed(self) -> discord.Embed:
        stats = await db.get_stats()
        accounts = await db.get_all_accounts()
        
        embed = discord.Embed(
            title="📊 إحصائيات النظام",
            description="*يتم التحديث كل 5 دقائق*",
            color=COLORS['purple'],
            timestamp=discord.utils.utcnow()
        )
        
        # Stats
        finished = len([a for a in accounts if a.get('status') == 'finished'])
        not_finished = len([a for a in accounts if a.get('status') == 'not_finished'])
        
        embed.add_field(
            name="💰 المبيعات",
            value=f"```\nالإجمالي: {stats.get('total_sales', 0)}\nالأرباح: {stats.get('total_revenue', 0):,.0f} ج\n```",
            inline=True
        )
        
        embed.add_field(
            name="🎮 الحسابات",
            value=f"```\nالكل: {len(accounts)}\nمكتمل: {finished}\nجاري: {not_finished}\n```",
            inline=True
        )
        
        # Today
        today = datetime.now().strftime('%Y-%m-%d')
        daily = stats.get('daily_stats', {}).get(today, {'sales': 0, 'revenue': 0})
        
        embed.add_field(
            name="📅 اليوم",
            value=f"```\nمبيعات: {daily.get('sales', 0)}\nأرباح: {daily.get('revenue', 0):,.0f} ج\n```",
            inline=True
        )
        
        embed.set_footer(text="🔄 آخر تحديث")
        
        return embed
    
    @app_commands.command(name="setup_stats", description="إعداد قناة الإحصائيات")
    @app_commands.default_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        
        try:
            category = discord.utils.get(guild.categories, name="📈 الإحصائيات")
            if not category:
                category = await guild.create_category("📈 الإحصائيات")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Delete old if exists
            old = discord.utils.get(guild.text_channels, name="📊│احصائيات")
            if old:
                await old.delete()
            
            channel = await guild.create_text_channel("📊│احصائيات", category=category, overwrites=overwrites)
            
            embed = await self.create_stats_embed()
            message = await channel.send(embed=embed)
            
            self.stats_channel_id = channel.id
            self.stats_message_id = message.id
            
            await interaction.followup.send("✅ تم إعداد قناة الإحصائيات!", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="stats", description="عرض الإحصائيات")
    async def stats(self, interaction: discord.Interaction):
        embed = await self.create_stats_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="update_stats", description="تحديث الإحصائيات يدوياً")
    @app_commands.default_permissions(administrator=True)
    async def update_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        channel = discord.utils.get(interaction.guild.text_channels, name="📊│احصائيات")
        if channel:
            async for msg in channel.history(limit=5):
                if msg.author == interaction.guild.me:
                    await msg.delete()
            
            embed = await self.create_stats_embed()
            message = await channel.send(embed=embed)
            self.stats_channel_id = channel.id
            self.stats_message_id = message.id
            
            await interaction.followup.send("✅ تم التحديث!", ephemeral=True)
        else:
            await interaction.followup.send("❌ القناة غير موجودة!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
