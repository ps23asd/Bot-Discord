import discord
from discord.ext import commands
from discord import app_commands
from database import db

class AccountsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_level15", description="إعداد نظام Level 15")
    @app_commands.default_permissions(administrator=True)
    async def setup_level15(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            from views.account_views import Level15NotFinishView, Level15DoneView
            
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            cat = discord.utils.get(guild.categories, name="📊 Level 15 System")
            if not cat:
                cat = await guild.create_category("📊 Level 15 System")
            
            if not discord.utils.get(guild.text_channels, name="🔒│backup-accounts"):
                await guild.create_text_channel("🔒│backup-accounts", category=cat, overwrites=overwrites)
            
            if not discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish"):
                ch = await guild.create_text_channel("⏳│level-15-not-finish", category=cat, overwrites=overwrites)
                e = discord.Embed(title="⏳ حسابات لم تصل لفل 15", color=0xFFFF00)
                m = await ch.send(embed=e, view=Level15NotFinishView())
                await m.pin()
            
            if not discord.utils.get(guild.text_channels, name="✅│level-15-done"):
                ch = await guild.create_text_channel("✅│level-15-done", category=cat, overwrites=overwrites)
                e = discord.Embed(title="✅ حسابات وصلت لفل 15", color=0x00FF00)
                m = await ch.send(embed=e, view=Level15DoneView())
                await m.pin()
            
            await interaction.followup.send("✅ Done!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="add_account", description="إضافة حساب")
    async def add_account(self, interaction: discord.Interaction):
        from views.account_views import AccountInfoModal
        await interaction.response.send_modal(AccountInfoModal())
    
    @app_commands.command(name="list_accounts", description="عرض الحسابات")
    async def list_accounts(self, interaction: discord.Interaction):
        accounts = await db.get_all_accounts()
        if not accounts:
            await interaction.response.send_message("📭 No accounts!", ephemeral=True)
            return
        
        e = discord.Embed(title=f"📋 Accounts ({len(accounts)})", color=0x00BFFF)
        for a in accounts[:10]:
            e.add_field(name=a['id'], value=f"Level: {a.get('current_level', '?')}", inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AccountsCog(bot))