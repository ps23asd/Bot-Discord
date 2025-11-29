import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import db
from datetime import datetime

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_channel_id = None
        self.stats_message_id = None
    
    async def create_stats_embed(self):
        stats = await db.get_stats()
        accounts = await db.get_all_accounts()
        
        e = discord.Embed(title="📊 الإحصائيات", color=0x9B59B6, timestamp=discord.utils.utcnow())
        e.add_field(name="💰 المبيعات", value=f"{stats.get('total_sales', 0)}", inline=True)
        e.add_field(name="💵 الأرباح", value=f"{stats.get('total_revenue', 0):,.0f} ج", inline=True)
        e.add_field(name="🎮 الحسابات", value=f"{len(accounts)}", inline=True)
        return e
    
    @app_commands.command(name="setup_stats", description="إعداد الإحصائيات")
    @app_commands.default_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            cat = discord.utils.get(guild.categories, name="📈 الإحصائيات")
            if not cat:
                cat = await guild.create_category("📈 الإحصائيات")
            
            old = discord.utils.get(guild.text_channels, name="📊│احصائيات")
            if old:
                await old.delete()
            
            ch = await guild.create_text_channel("📊│احصائيات", category=cat, overwrites=overwrites)
            e = await self.create_stats_embed()
            m = await ch.send(embed=e)
            
            self.stats_channel_id = ch.id
            self.stats_message_id = m.id
            
            await interaction.followup.send("✅ Done!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="stats", description="عرض الإحصائيات")
    async def stats(self, interaction: discord.Interaction):
        e = await self.create_stats_embed()
        await interaction.response.send_message(embed=e, ephemeral=True)
    
    @app_commands.command(name="update_stats", description="تحديث الإحصائيات")
    @app_commands.default_permissions(administrator=True)
    async def update_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        ch = discord.utils.get(interaction.guild.text_channels, name="📊│احصائيات")
        if ch:
            async for m in ch.history(limit=5):
                if m.author == interaction.guild.me:
                    await m.delete()
            e = await self.create_stats_embed()
            await ch.send(embed=e)
            await interaction.followup.send("✅ Updated!")
        else:
            await interaction.followup.send("❌ Channel not found!")

async def setup(bot):
    await bot.add_cog(StatsCog(bot))