import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, ADMIN_ROLE_ID
from database import db
from views.ticket_views import TicketPanelView

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_tickets", description="إعداد نظام التذاكر")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        
        try:
            # Create categories
            for cat_name in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
                if not discord.utils.get(guild.categories, name=cat_name):
                    await guild.create_category(cat_name)
            
            tickets_category = discord.utils.get(guild.categories, name="🎫 التذاكر")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Create ticket panel
            if not discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة"):
                panel = await guild.create_text_channel("🎫│فتح-تذكرة", category=tickets_category, overwrites=overwrites)
                
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
                
                await panel.send(embed=embed, view=TicketPanelView())
            
            await interaction.followup.send("✅ تم إعداد نظام التذاكر!", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="close_ticket", description="إغلاق التذكرة الحالية")
    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("🎫"):
            await interaction.response.send_message("❌ هذا الأمر يعمل فقط في قنوات التذاكر!", ephemeral=True)
            return
        
        await interaction.response.send_message("🔒 جاري إغلاق التذكرة...")
        await interaction.channel.delete()

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
