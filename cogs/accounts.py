import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, ADMIN_ROLE_ID
from database import db
from views.account_views import Level15NotFinishView, Level15DoneView, AccountControlView, AccountInfoModal

class AccountsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_level15", description="إعداد نظام Level 15")
    @app_commands.default_permissions(administrator=True)
    async def setup_level15(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        
        try:
            # Create category
            category = discord.utils.get(guild.categories, name="📊 Level 15 System")
            if not category:
                category = await guild.create_category("📊 Level 15 System")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Backup channel
            if not discord.utils.get(guild.text_channels, name="🔒│backup-accounts"):
                await guild.create_text_channel("🔒│backup-accounts", category=category, overwrites=overwrites)
            
            # Not Finish channel
            if not discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish"):
                nf_channel = await guild.create_text_channel("⏳│level-15-not-finish", category=category, overwrites=overwrites)
                embed = discord.Embed(
                    title="⏳ حسابات لم تصل لفل 15",
                    description="هنا يتم وضع الحسابات اللي لسه ما وصلتش لفل 15\n\n**اضغط الزر لإضافة حساب**",
                    color=COLORS['warning']
                )
                msg = await nf_channel.send(embed=embed, view=Level15NotFinishView())
                await msg.pin()
            
            # Done channel
            if not discord.utils.get(guild.text_channels, name="✅│level-15-done"):
                done_channel = await guild.create_text_channel("✅│level-15-done", category=category, overwrites=overwrites)
                embed = discord.Embed(
                    title="✅ حسابات وصلت لفل 15",
                    description="هنا يتم وضع الحسابات اللي وصلت لفل 15\n\n**اضغط الزر لإضافة حساب مكتمل**",
                    color=COLORS['success']
                )
                msg = await done_channel.send(embed=embed, view=Level15DoneView())
                await msg.pin()
            
            await interaction.followup.send("✅ تم إعداد نظام Level 15!", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="add_account", description="إضافة حساب جديد")
    async def add_account(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AccountInfoModal())
    
    @app_commands.command(name="account_info", description="عرض معلومات حساب")
    @app_commands.describe(account_id="رقم الحساب")
    async def account_info(self, interaction: discord.Interaction, account_id: str):
        account = await db.get_account(account_id)
        if not account:
            await interaction.response.send_message("❌ الحساب غير موجود!", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"🎮 معلومات الحساب - {account_id}", color=COLORS['info'])
        embed.add_field(name="📋 المعلومات", value=f"```\n{account.get('account_info', 'N/A')}\n```", inline=False)
        embed.add_field(name="📊 اللفل", value=str(account.get('current_level', 'N/A')), inline=True)
        embed.add_field(name="👤 فاتحه", value=account.get('opened_by', 'N/A'), inline=True)
        embed.add_field(name="📋 الحالة", value=account.get('status', 'N/A'), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="list_accounts", description="عرض قائمة الحسابات")
    @app_commands.describe(status="حالة الحسابات")
    @app_commands.choices(status=[
        app_commands.Choice(name="الكل", value="all"),
        app_commands.Choice(name="لم تنتهي", value="not_finished"),
        app_commands.Choice(name="مكتملة", value="finished")
    ])
    async def list_accounts(self, interaction: discord.Interaction, status: str = "all"):
        if status == "all":
            accounts = await db.get_all_accounts()
        else:
            accounts = await db.get_all_accounts(status)
        
        if not accounts:
            await interaction.response.send_message("📭 لا توجد حسابات!", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"📋 الحسابات ({len(accounts)})", color=COLORS['info'])
        
        for acc in accounts[:20]:
            embed.add_field(
                name=f"🆔 {acc['id']}",
                value=f"Level: {acc.get('current_level', 'N/A')} | {acc.get('status', 'N/A')}",
                inline=True
            )
        
        if len(accounts) > 20:
            embed.set_footer(text=f"وأكثر... ({len(accounts) - 20} حساب إضافي)")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AccountsCog(bot))
