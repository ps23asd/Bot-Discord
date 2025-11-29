import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, CATEGORIES, ADMIN_ROLE_ID
from database import db
from views.ticket_views import TicketPanelView, TicketControlView

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_tickets", description="إعداد نظام التذاكر")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Create categories
        for cat_name in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
            if not discord.utils.get(guild.categories, name=cat_name):
                await guild.create_category(cat_name)
        
        # Create ticket panel channel
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
        await interaction.response.send_message("✅ تم إعداد نظام التذاكر!", ephemeral=True)
    
    @app_commands.command(name="close_ticket", description="إغلاق التذكرة الحالية")
    async def close_ticket(self, interaction: discord.Interaction):
        # Check if in ticket channel
        if not interaction.channel.name.startswith("🎫"):
            await interaction.response.send_message("❌ هذا الأمر يعمل فقط في قنوات التذاكر!", ephemeral=True)
            return
        
        await interaction.response.send_message("🔒 جاري إغلاق التذكرة...")
        await interaction.channel.delete()
    
    @app_commands.command(name="change_status", description="تغيير حالة التذكرة")
    @app_commands.describe(status="الحالة الجديدة")
    @app_commands.choices(status=[
        app_commands.Choice(name="تم البيع", value="sold"),
        app_commands.Choice(name="الحساب خلص", value="finished"),
        app_commands.Choice(name="تم تسليم الفلوس", value="completed")
    ])
    async def change_status(self, interaction: discord.Interaction, status: str):
        channel_name = interaction.channel.name
        
        if status == "sold":
            category = discord.utils.get(interaction.guild.categories, name="💰 انتظار الفلوس")
        elif status == "completed":
            category = discord.utils.get(interaction.guild.categories, name="✅ تم تسليم الفلوس")
        else:
            category = discord.utils.get(interaction.guild.categories, name="🎫 التذاكر")
        
        if category:
            await interaction.channel.edit(category=category)
            await interaction.response.send_message(f"✅ تم تغيير الحالة إلى: {status}")
        else:
            await interaction.response.send_message("❌ الفئة غير موجودة!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))