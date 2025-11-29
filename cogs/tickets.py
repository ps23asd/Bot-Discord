import discord
from discord.ext import commands
from discord import app_commands

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_tickets", description="إعداد نظام التذاكر")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            from views.ticket_views import TicketPanelView
            
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            for n in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
                if not discord.utils.get(guild.categories, name=n):
                    await guild.create_category(n)
            
            cat = discord.utils.get(guild.categories, name="🎫 التذاكر")
            
            if not discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة"):
                ch = await guild.create_text_channel("🎫│فتح-تذكرة", category=cat, overwrites=overwrites)
                e = discord.Embed(title="🎫 نظام التذاكر", description="اختر رانك الحساب", color=0x9B59B6)
                await ch.send(embed=e, view=TicketPanelView())
            
            await interaction.followup.send("✅ Done!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="close_ticket", description="إغلاق التذكرة")
    async def close_ticket(self, interaction: discord.Interaction):
        if "🎫" in interaction.channel.name:
            await interaction.response.send_message("🔒 Closing...")
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Not a ticket!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
