import discord
from discord import ui
from config import COLORS, ADMIN_ROLE_ID
from database import db

class AccountInfoModal(ui.Modal, title="📝 إضافة حساب جديد"):
    account_info = ui.TextInput(
        label="معلومات الحساب كاملة",
        placeholder="اكتب كل معلومات الحساب:\nالإيميل:\nالباسورد:\nأي معلومات أخرى...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1024
    )
    
    current_level = ui.TextInput(
        label="اللفل الحالي",
        placeholder="مثال: 10",
        required=True
    )
    
    opened_by = ui.TextInput(
        label="مين فاتح الحساب",
        placeholder="اسم الشخص",
        required=True
    )
    
    notes = ui.TextInput(
        label="ملاحظات إضافية",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.current_level.value)
        except:
            await interaction.response.send_message("❌ اللفل لازم يكون رقم!", ephemeral=True)
            return
        
        account_data = {
            'account_info': self.account_info.value,
            'current_level': level,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value or "لا يوجد",
            'added_by': interaction.user.id,
            'added_by_name': interaction.user.name
        }
        
        account_id = await db.add_account(account_data)
        
        # Send to backup channel - كل التفاصيل
        backup_channel = discord.utils.get(interaction.guild.channels, name="🔒│backup-accounts")
        if backup_channel:
            backup_embed = discord.Embed(
                title=f"💾 نسخة احتياطية - {account_id}",
                color=COLORS['purple']
            )
            backup_embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
            backup_embed.add_field(name="📋 معلومات الحساب", value=f"```\n{self.account_info.value}\n```", inline=False)
            backup_embed.add_field(name="📊 اللفل", value=f"`{level}`", inline=True)
            backup_embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
            backup_embed.add_field(name="➕ أضافه", value=interaction.user.mention, inline=True)
            if self.notes.value:
                backup_embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
            backup_embed.set_footer(text=f"أضيف بواسطة {interaction.user.name}")
            backup_embed.timestamp = discord.utils.utcnow()
            await backup_channel.send(embed=backup_embed)
        
        # Find the appropriate channel
        if level >= 15:
            target_channel = discord.utils.get(interaction.guild.channels, name="✅│level-15-done")
            status = "finished"
            color = COLORS['success']
            title_prefix = "✅"
            is_done = True
        else:
            target_channel = discord.utils.get(interaction.guild.channels, name="⏳│level-15-not-finish")
            status = "not_finished"
            color = COLORS['warning']
            title_prefix = "⏳"
            is_done = False
        
        # Update status in database
        await db.update_account(account_id, {'status': status})
        
        # Create account embed - كل التفاصيل ظاهرة للجميع
        embed = discord.Embed(
            title=f"{title_prefix} حساب جديد - {account_id}",
            color=color
        )
        embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
        embed.add_field(name="📋 معلومات الحساب", value=f"```\n{self.account_info.value}\n```", inline=False)
        embed.add_field(name="📊 اللفل الحالي", value=f"`{level}`", inline=True)
        embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
        embed.add_field(name="➕ أضافه", value=interaction.user.mention, inline=True)
        embed.add_field(name="📅 التاريخ", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=True)
        if self.notes.value:
            embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
        embed.set_footer(text=f"أضيف بواسطة {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        
        if target_channel:
            await target_channel.send(embed=embed, view=AccountControlView(account_id, is_done=is_done))
            await interaction.response.send_message(
                f"✅ تم إضافة الحساب بنجاح! {target_channel.mention}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ القناة المطلوبة غير موجودة! استخدم `/setup_level15`",
                ephemeral=True
            )

class AccountControlView(ui.View):
    def __init__(self, account_id: str = "", is_done: bool = False):
        super().__init__(timeout=None)
        self.account_id = account_id
        self.is_done = is_done
        
        # إضافة الأزرار بـ custom_id مختلفة
        if not is_done:
            # زرار النقل (فقط للحسابات الغير مكتملة)
            move_btn = ui.Button(
                label="✅ نقل لـ Done",
                style=discord.ButtonStyle.success,
                custom_id=f"move_to_done_{account_id or 'temp'}"
            )
            move_btn.callback = self.move_to_done_callback
            self.add_item(move_btn)
        
        # زرار التعديل
        edit_btn = ui.Button(
            label="📝 تعديل",
            style=discord.ButtonStyle.primary,
            custom_id=f"edit_account_{account_id or 'temp'}"
        )
        edit_btn.callback = self.edit_callback
        self.add_item(edit_btn)
        
        # زرار الحذف
        delete_btn = ui.Button(
            label="🗑️ حذف",
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_account_{account_id or 'temp'}"
        )
        delete_btn.callback = self.delete_callback
        self.add_item(delete_btn)
    
    async def edit_callback(self, interaction: discord.Interaction):
        # Get account from message embed
        if interaction.message.embeds:
            embed = interaction.message.embeds[0]
            for field in embed.fields:
                if field.name == "🆔 ID":
                    self.account_id = field.value.strip("`")
                    break
        
        account = await db.get_account(self.account_id)
        if account:
            await interaction.response.send_modal(EditAccountModal(self.account_id, account, interaction.message))
        else:
            await interaction.response.send_message("❌ الحساب مش موجود!", ephemeral=True)
    
    async def move_to_done_callback(self, interaction: discord.Interaction):
        # Get account from message embed
        if interaction.message.embeds:
            embed = interaction.message.embeds[0]
            for field in embed.fields:
                if field.name == "🆔 ID":
                    self.account_id = field.value.strip("`")
                    break
        
        account = await db.get_account(self.account_id)
        if not account:
            await interaction.response.send_message("❌ الحساب مش موجود!", ephemeral=True)
            return
        
        # Update account status
        await db.update_account(self.account_id, {'status': 'finished', 'current_level': 15})
        
        # Find done channel
        done_channel = discord.utils.get(interaction.guild.channels, name="✅│level-15-done")
        if done_channel:
            embed = discord.Embed(
                title=f"✅ حساب مكتمل - {self.account_id}",
                color=COLORS['success']
            )
            embed.add_field(name="🆔 ID", value=f"`{self.account_id}`", inline=False)
            embed.add_field(name="📋 معلومات الحساب", value=f"```\n{account.get('account_info', 'N/A')}\n```", inline=False)
            embed.add_field(name="📊 اللفل", value="`15`", inline=True)
            embed.add_field(name="👤 فاتحه", value=account['opened_by'], inline=True)
            embed.add_field(name="✅ اكتمل", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=True)
            if account.get('notes') and account.get('notes') != "لا يوجد":
                embed.add_field(name="📝 ملاحظات", value=account.get('notes'), inline=False)
            embed.set_footer(text=f"نُقل بواسطة {interaction.user.name}")
            embed.timestamp = discord.utils.utcnow()
            
            # إنشاء View بدون زرار النقل
            await done_channel.send(embed=embed, view=AccountControlView(self.account_id, is_done=True))
            await interaction.response.send_message("✅ تم نقل الحساب لقناة Done!", ephemeral=True)
            
            # Delete from current channel
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ قناة Done مش موجودة!", ephemeral=True)
    
    async def delete_callback(self, interaction: discord.Interaction):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role and admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ الأدمن فقط يمكنه الحذف!", ephemeral=True)
            return
        
        # Get account from message embed
        if interaction.message.embeds:
            embed = interaction.message.embeds[0]
            for field in embed.fields:
                if field.name == "🆔 ID":
                    self.account_id = field.value.strip("`")
                    break
        
        await interaction.response.send_modal(DeleteAccountConfirmModal(self.account_id, interaction.message))

class EditAccountModal(ui.Modal, title="📝 تعديل الحساب"):
    def __init__(self, account_id: str, account_data: dict, message: discord.Message):
        super().__init__()
        self.account_id = account_id
        self.message = message
        self.account_info.default = account_data.get('account_info', '')
        self.current_level.default = str(account_data.get('current_level', ''))
        self.opened_by.default = account_data.get('opened_by', '')
        self.notes.default = account_data.get('notes', '')
    
    account_info = ui.TextInput(
        label="معلومات الحساب",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1024
    )
    
    current_level = ui.TextInput(
        label="اللفل الحالي",
        required=True
    )
    
    opened_by = ui.TextInput(
        label="مين فاتح الحساب",
        required=True
    )
    
    notes = ui.TextInput(
        label="ملاحظات",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.current_level.value)
        except:
            await interaction.response.send_message("❌ اللفل لازم يكون رقم!", ephemeral=True)
            return
        
        await db.update_account(self.account_id, {
            'account_info': self.account_info.value,
            'current_level': level,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value,
            'edited_by': interaction.user.id,
            'edited_by_name': interaction.user.name
        })
        
        await interaction.response.send_message("✅ تم تحديث الحساب!", ephemeral=True)
        
        # Update the message embed
        if self.message and self.message.embeds:
            current_embed = self.message.embeds[0]
            
            # تحديث الحقول
            current_embed.set_field_at(1, name="📋 معلومات الحساب", value=f"```\n{self.account_info.value}\n```", inline=False)
            current_embed.set_field_at(2, name="📊 اللفل الحالي", value=f"`{level}`", inline=True)
            current_embed.set_field_at(3, name="👤 فاتحه", value=self.opened_by.value, inline=True)
            
            # تحديث الملاحظات إذا موجودة
            for i, field in enumerate(current_embed.fields):
                if field.name == "📝 ملاحظات":
                    if self.notes.value:
                        current_embed.set_field_at(i, name="📝 ملاحظات", value=self.notes.value, inline=False)
                    else:
                        # حذف الحقل إذا فارغ
                        current_embed.remove_field(i)
                    break
            else:
                # إضافة حقل الملاحظات إذا لم يكن موجوداً
                if self.notes.value:
                    current_embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
            
            current_embed.set_footer(text=f"آخر تعديل بواسطة {interaction.user.name}")
            current_embed.timestamp = discord.utils.utcnow()
            
            await self.message.edit(embed=current_embed)

class DeleteAccountConfirmModal(ui.Modal, title="⚠️ تأكيد حذف الحساب"):
    def __init__(self, account_id: str, message: discord.Message):
        super().__init__()
        self.account_id = account_id
        self.message = message
    
    confirm = ui.TextInput(
        label="اكتب 'حذف' للتأكيد",
        placeholder="حذف",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value == "حذف":
            await db.delete_account(self.account_id)
            await interaction.response.send_message("✅ تم حذف الحساب!", ephemeral=True)
            await self.message.delete()
        else:
            await interaction.response.send_message("❌ كلمة التأكيد غير صحيحة!", ephemeral=True)

class Level15NotFinishView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="➕ إضافة حساب", style=discord.ButtonStyle.success, custom_id="add_account_nf_main", emoji="🎮")
    async def add_account(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AccountInfoModal())

class Level15DoneView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="➕ إضافة حساب مكتمل", style=discord.ButtonStyle.success, custom_id="add_account_done_main", emoji="✅")
    async def add_account(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DoneAccountModal())

class DoneAccountModal(ui.Modal, title="📝 إضافة حساب مكتمل (Level 15)"):
    account_info = ui.TextInput(
        label="معلومات الحساب كاملة",
        placeholder="اكتب كل معلومات الحساب:\nالإيميل:\nالباسورد:\nأي معلومات أخرى...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1024
    )
    
    opened_by = ui.TextInput(
        label="مين فاتح الحساب",
        required=True
    )
    
    notes = ui.TextInput(
        label="ملاحظات",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        account_data = {
            'account_info': self.account_info.value,
            'current_level': 15,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value or "لا يوجد",
            'status': 'finished',
            'added_by': interaction.user.id,
            'added_by_name': interaction.user.name
        }
        
        account_id = await db.add_account(account_data)
        
        # Send to backup
        backup_channel = discord.utils.get(interaction.guild.channels, name="🔒│backup-accounts")
        if backup_channel:
            backup_embed = discord.Embed(
                title=f"💾 نسخة احتياطية - {account_id}",
                color=COLORS['purple']
            )
            backup_embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
            backup_embed.add_field(name="📋 معلومات الحساب", value=f"```\n{self.account_info.value}\n```", inline=False)
            backup_embed.add_field(name="📊 اللفل", value="`15`", inline=True)
            backup_embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
            backup_embed.add_field(name="➕ أضافه", value=interaction.user.mention, inline=True)
            if self.notes.value:
                backup_embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
            backup_embed.set_footer(text=f"أضيف بواسطة {interaction.user.name}")
            backup_embed.timestamp = discord.utils.utcnow()
            await backup_channel.send(embed=backup_embed)
        
        embed = discord.Embed(
            title=f"✅ حساب مكتمل - {account_id}",
            color=COLORS['success']
        )
        embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
        embed.add_field(name="📋 معلومات الحساب", value=f"```\n{self.account_info.value}\n```", inline=False)
        embed.add_field(name="📊 اللفل", value="`15`", inline=True)
        embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
        embed.add_field(name="➕ أضافه", value=interaction.user.mention, inline=True)
        embed.add_field(name="📅 التاريخ", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=True)
        if self.notes.value:
            embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
        embed.set_footer(text=f"أضيف بواسطة {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        
        # إنشاء View بدون زرار النقل (لأنه في Done)
        await interaction.response.send_message(embed=embed, view=AccountControlView(account_id, is_done=True))