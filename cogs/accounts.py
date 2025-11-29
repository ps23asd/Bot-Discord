import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, ADMIN_ROLE_ID
from database import db
from views.account_views import Level15NotFinishView, Level15DoneView, AccountControlView

class AccountsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_level15", description="إعداد نظام Level 15")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_level15(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Create category
        category = discord.utils.get(guild.categories, name="📊 Level 15 System")
        if not category:
            category = await guild.create_category("📊 Level 15 System")
        
        # Create backup channel (hidden)
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        backup_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if admin_role:
            backup_overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True)
        
        backup_channel = await guild.create_text_channel(
            name="🔒│backup-accounts",
            category=category,
            overwrites=backup_overwrites
        )
        
        # Create Level 15 Not Finish channel
        not_finish_overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
        }
        
        not_finish_channel = await guild.create_text_channel(
            name="⏳│level-15-not-finish",
            category=category,
            overwrites=not_finish_overwrites
        )
        
        # Pin message for not finish
        nf_embed = discord.Embed(
            title="⏳ حسابات لم تصل لفل 15",
            description="هنا يتم وضع الحسابات اللي لسه ما وصلتش لفل 15\n\n**يرجى تحديث اللفل ومين فاتح الحساب**",
            color=COLORS['warning']
        )
        nf_msg = await not_finish_channel.send(embed=nf_embed, view=Level15NotFinishView())
        await nf_msg.pin()
        
        # Create Level 15 Done channel
        done_channel = await guild.create_text_channel(
            name="✅│level-15-done",
            category=category,
            overwrites=not_finish_overwrites
        )
        
        # Pin message for done
        done_embed = discord.Embed(
            title="✅ حسابات وصلت لفل 15",
            description="هنا يتم وضع الحسابات اللي وصلت لفل 15 وجاهزة للبيع",
            color=COLORS['success']
        )
        done_msg = await done_channel.send(embed=done_embed, view=Level15DoneView())
        await done_msg.pin()
        
        await interaction.response.send_message("✅ تم إعداد نظام Level 15!", ephemeral=True)
    
    @app_commands.command(name="add_account", description="إضافة حساب جديد")
    async def add_account(self, interaction: discord.Interaction):
        from views.account_views import AccountInfoModal
        await interaction.response.send_modal(AccountInfoModal())
    
    @app_commands.command(name="account_info", description="عرض معلومات حساب")
    @app_commands.describe(account_id="رقم الحساب")
    async def account_info(self, interaction: discord.Interaction, account_id: str):
        account = await db.get_account(account_id)
        if not account:
            await interaction.response.send_message("❌ الحساب غير موجود!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎮 معلومات الحساب - {account_id}",
            color=COLORS['info']
        )
        embed.add_field(name="📧 الإيميل", value=account.get('email', 'N/A'), inline=True)
        embed.add_field(name="📊 اللفل", value=str(account.get('current_level', 'N/A')), inline=True)
        embed.add_field(name="👤 فاتحه", value=account.get('opened_by', 'N/A'), inline=True)
        embed.add_field(name="📋 الحالة", value=account.get('status', 'N/A'), inline=True)
        embed.add_field(name="📝 ملاحظات", value=account.get('notes', 'لا يوجد'), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ban_account", description="حظر حساب")
    @app_commands.describe(account_id="رقم الحساب", reason="سبب الحظر")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban_account(self, interaction: discord.Interaction, account_id: str, reason: str = "لم يتم تحديد سبب"):
        account = await db.get_account(account_id)
        if not account:
            await interaction.response.send_message("❌ الحساب غير موجود!", ephemeral=True)
            return
        
        await db.update_account(account_id, {
            'status': 'banned',
            'ban_reason': reason,
            'banned_by': interaction.user.id
        })
        
        await interaction.response.send_message(f"🚫 تم حظر الحساب {account_id}\nالسبب: {reason}")
    
    @app_commands.command(name="list_accounts", description="عرض قائمة الحسابات")
    @app_commands.describe(status="حالة الحسابات")
    @app_commands.choices(status=[
        app_commands.Choice(name="الكل", value="all"),
        app_commands.Choice(name="لم تنتهي", value="not_finished"),
        app_commands.Choice(name="مكتملة", value="finished"),
        app_commands.Choice(name="محظورة", value="banned")
    ])
    async def list_accounts(self, interaction: discord.Interaction, status: str = "all"):
        if status == "all":
            accounts = await db.get_all_accounts()
        else:
            accounts = await db.get_all_accounts(status)
        
        if not accounts:
            await interaction.response.send_message("📭 لا توجد حسابات!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📋 قائمة الحسابات ({len(accounts)})",
            color=COLORS['info']
        )
        
        for acc in accounts[:25]:  # Discord limit
            embed.add_field(
                name=f"🆔 {acc['id']}",
                value=f"Level: {acc.get('current_level', 'N/A')} | Status: {acc.get('status', 'N/A')}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AccountsCog(bot))