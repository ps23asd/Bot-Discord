import discord
from discord import ui
from config import RANK_CATEGORIES, RANK_EMOJIS, COLORS, ADMIN_ROLE_ID
from database import db

# ============ Step 1: Choose Rank Category ============
class RankCategorySelectMenu(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category,
                value=category,
                emoji=RANK_EMOJIS.get(category, "🎮"),
                description=f"{ranks[0]} - {ranks[-1]}"
            )
            for category, ranks in RANK_CATEGORIES.items()
        ]
        super().__init__(
            placeholder="🎯 اختر فئة الرانك أولاً...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="rank_category_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        # Show rank level selection
        view = RankLevelView(category)
        
        embed = discord.Embed(
            title=f"{RANK_EMOJIS.get(category, '🎮')} {category}",
            description="اختر المستوى:",
            color=COLORS['info']
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

# ============ Step 2: Choose Rank Level ============
class RankLevelSelectMenu(ui.Select):
    def __init__(self, category: str):
        self.category = category
        ranks = RANK_CATEGORIES.get(category, [])
        
        options = [
            discord.SelectOption(
                label=rank,
                value=rank,
                emoji=RANK_EMOJIS.get(category, "🎮")
            )
            for rank in ranks
        ]
        
        super().__init__(
            placeholder=f"اختر مستوى {category}...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"rank_level_select_{category}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        rank = self.values[0]
        await interaction.response.send_modal(TicketInfoModal(rank))

class RankLevelView(ui.View):
    def __init__(self, category: str):
        super().__init__(timeout=60)
        self.add_item(RankLevelSelectMenu(category))
    
    @ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎫 نظام التذاكر",
                description="اختر فئة الرانك من القائمة",
                color=COLORS['purple']
            ),
            view=TicketPanelView()
        )

# ============ Ticket Info Modal ============
class TicketInfoModal(ui.Modal, title="📝 معلومات التذكرة"):
    def __init__(self, rank: str):
        super().__init__()
        self.rank = rank
    
    account_info = ui.TextInput(
        label="معلومات الحساب",
        placeholder="ادخل معلومات الحساب (إيميل، باسورد، إلخ)",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    notes = ui.TextInput(
        label="ملاحظات إضافية",
        placeholder="أي ملاحظات إضافية...",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Create ticket channel
        category = discord.utils.get(guild.categories, name="🎫 التذاكر")
        if not category:
            category = await guild.create_category("🎫 التذاكر")
        
        # Set permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True
            )
        }
        
        # Add admin role permissions
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True
            )
        
        channel_name = f"🎫│{self.rank.replace(' ', '-')}│{interaction.user.name}"
        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
        
        # Save ticket to database
        ticket_data = {
            'user_id': interaction.user.id,
            'user_name': interaction.user.name,
            'channel_id': ticket_channel.id,
            'rank': self.rank,
            'account_info': self.account_info.value,
            'notes': self.notes.value or "لا يوجد"
        }
        ticket_id = await db.create_ticket(ticket_data)
        
        # Create ticket embed
        embed = discord.Embed(
            title=f"🎫 تذكرة جديدة - {self.rank}",
            color=COLORS['info']
        )
        embed.add_field(name="🆔 رقم التذكرة", value=ticket_id, inline=True)
        embed.add_field(name="👤 صاحب التذكرة", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎮 الرانك", value=self.rank, inline=True)
        embed.add_field(name="📋 معلومات الحساب", value=f"```{self.account_info.value}```", inline=False)
        embed.add_field(name="📝 ملاحظات", value=self.notes.value or "لا يوجد", inline=False)
        embed.set_footer(text=f"تم الإنشاء بواسطة {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await ticket_channel.send(embed=embed, view=TicketControlView(ticket_id))
        
        await interaction.response.send_message(
            f"✅ تم إنشاء التذكرة بنجاح! {ticket_channel.mention}",
            ephemeral=True
        )

# ============ Ticket Panel View ============
class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RankCategorySelectMenu())

# ============ Sold Info Modal ============
class SoldInfoModal(ui.Modal, title="💰 معلومات البيع"):
    def __init__(self, ticket_id: str):
        super().__init__()
        self.ticket_id = ticket_id
    
    buyer_name = ui.TextInput(
        label="اسم المشتري",
        placeholder="مين اللي اشترى الحساب؟",
        required=True
    )
    
    price = ui.TextInput(
        label="السعر",
        placeholder="الحساب اتباع بكام؟",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = float(self.price.value)
        except:
            await interaction.response.send_message("❌ السعر لازم يكون رقم!", ephemeral=True)
            return
        
        ticket = await db.get_ticket(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ التذكرة مش موجودة!", ephemeral=True)
            return
        
        # Update ticket
        await db.update_ticket(self.ticket_id, {
            'status': 'sold',
            'buyer': self.buyer_name.value,
            'price': price,
            'sold_by': interaction.user.id,
            'sold_by_name': interaction.user.name
        })
        
        # Add sale to stats
        await db.add_sale({
            'ticket_id': self.ticket_id,
            'rank': ticket.get('rank'),
            'buyer': self.buyer_name.value,
            'price': price,
            'seller': interaction.user.name
        })
        
        # Move channel to waiting money category
        guild = interaction.guild
        waiting_category = discord.utils.get(guild.categories, name="💰 انتظار الفلوس")
        if not waiting_category:
            waiting_category = await guild.create_category("💰 انتظار الفلوس")
        
        await interaction.channel.edit(category=waiting_category)
        
        embed = discord.Embed(
            title="💰 تم البيع - في انتظار الفلوس",
            color=COLORS['warning']
        )
        embed.add_field(name="👤 المشتري", value=self.buyer_name.value, inline=True)
        embed.add_field(name="💵 السعر", value=f"{price} جنيه", inline=True)
        embed.add_field(name="🛒 البائع", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"تم البيع بواسطة {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed, view=WaitingMoneyView(self.ticket_id))

# ============ Ticket Control View ============
class TicketControlView(ui.View):
    def __init__(self, ticket_id: str = ""):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @ui.button(label="✅ تم البيع", style=discord.ButtonStyle.success, custom_id="sold_button")
    async def sold_button(self, interaction: discord.Interaction, button: ui.Button):
        tickets_data = await db.load_json(db.tickets_file)
        ticket_id = None
        for ticket in tickets_data.get('tickets', []):
            if ticket.get('channel_id') == interaction.channel.id:
                ticket_id = ticket.get('id')
                break
        
        if ticket_id:
            await interaction.response.send_modal(SoldInfoModal(ticket_id))
        else:
            await interaction.response.send_message("❌ لم يتم العثور على التذكرة!", ephemeral=True)
    
    @ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔒 سيتم إغلاق التذكرة خلال 5 ثواني...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

class EditTicketModal(ui.Modal, title="📝 تعديل معلومات التذكرة"):
    def __init__(self, ticket_id: str, ticket_data: dict):
        super().__init__()
        self.ticket_id = ticket_id
        self.account_info.default = ticket_data.get('account_info', '')
        self.notes.default = ticket_data.get('notes', '')
    
    account_info = ui.TextInput(
        label="معلومات الحساب",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    notes = ui.TextInput(
        label="ملاحظات",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await db.update_ticket(self.ticket_id, {
            'account_info': self.account_info.value,
            'notes': self.notes.value,
            'edited_by': interaction.user.id
        })
        await interaction.response.send_message("✅ تم تحديث المعلومات!", ephemeral=True)

class WaitingMoneyView(ui.View):
    def __init__(self, ticket_id: str = ""):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @ui.button(label="💵 تم تسليم الفلوس", style=discord.ButtonStyle.success, custom_id="money_received")
    async def money_received(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        done_category = discord.utils.get(guild.categories, name="✅ تم تسليم الفلوس")
        if not done_category:
            done_category = await guild.create_category("✅ تم تسليم الفلوس")
        
        await interaction.channel.edit(category=done_category)
        
        tickets_data = await db.load_json(db.tickets_file)
        ticket_id = None
        for ticket in tickets_data.get('tickets', []):
            if ticket.get('channel_id') == interaction.channel.id:
                ticket_id = ticket.get('id')
                break
        
        if ticket_id:
            await db.update_ticket(ticket_id, {
                'status': 'completed',
                'money_received_by': interaction.user.id
            })
            
            await db.close_ticket(ticket_id, {
                'final_status': 'completed',
                'closed_by': interaction.user.id
            })
        
        embed = discord.Embed(
            title="✅ تم تسليم الفلوس بنجاح!",
            description="التذكرة مكتملة",
            color=COLORS['success']
        )
        embed.set_footer(text=f"تم بواسطة {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed, view=FinalView())

class FinalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="🗑️ حذف التذكرة", style=discord.ButtonStyle.danger, custom_id="delete_ticket_final")
    async def delete_ticket(self, interaction: discord.Interaction, button: ui.Button):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role and admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ الأدمن فقط يمكنه حذف التذكرة!", ephemeral=True)
            return
        await interaction.response.send_modal(DeleteConfirmModal())

class DeleteConfirmModal(ui.Modal, title="⚠️ تأكيد الحذف"):
    confirm = ui.TextInput(
        label="اكتب 'حذف' للتأكيد",
        placeholder="حذف",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value == "حذف":
            await interaction.response.send_message("🗑️ جاري حذف التذكرة...")
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ كلمة التأكيد غير صحيحة!", ephemeral=True)