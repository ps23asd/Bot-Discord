import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import os
import json
import aiofiles
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

# ============ CONFIG ============
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))

COLORS = {
    "success": 0x00FF00,
    "error": 0xFF0000,
    "info": 0x00BFFF,
    "warning": 0xFFFF00,
    "purple": 0x9B59B6
}

RANK_CATEGORIES = {
    "Bronze": ["Bronze 3", "Bronze 2", "Bronze 1"],
    "Silver": ["Silver 3", "Silver 2", "Silver 1"],
    "Gold": ["Gold 3", "Gold 2", "Gold 1"],
    "Platinum": ["Platinum 3", "Platinum 2", "Platinum 1"],
    "Diamond": ["Diamond 3", "Diamond 2", "Diamond 1"],
    "Vibranium": ["Vibranium 3", "Vibranium 2", "Vibranium 1"],
    "Grandmaster": ["Grandmaster 3", "Grandmaster 2", "Grandmaster 1"],
    "Celestial": ["Celestial 3", "Celestial 2", "Celestial 1"],
    "One Above All": ["One Above All 3", "One Above All 2", "One Above All 1"],
    "Eternity": ["Eternity 3", "Eternity 2", "Eternity 1"]
}

RANK_EMOJIS = {
    "Bronze": "🟫", "Silver": "⚪", "Gold": "🟨", "Platinum": "⬜",
    "Diamond": "💎", "Vibranium": "🟣", "Grandmaster": "🔴",
    "Celestial": "⭐", "One Above All": "👑", "Eternity": "♾️"
}

# ============ DATABASE ============
DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

class Database:
    def __init__(self):
        ensure_data_dir()
        self.accounts_file = f"{DATA_DIR}/accounts.json"
        self.tickets_file = f"{DATA_DIR}/tickets.json"
        self.stats_file = f"{DATA_DIR}/stats.json"
        self._init_files()
    
    def _init_files(self):
        defaults = {
            self.accounts_file: {"accounts": [], "backup": []},
            self.tickets_file: {"tickets": [], "closed_tickets": []},
            self.stats_file: {"total_sales": 0, "total_revenue": 0, "accounts_sold": [], "daily_stats": {}, "seller_stats": {}, "rank_stats": {}}
        }
        for path, data in defaults.items():
            if not os.path.exists(path):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def load_json(self, path):
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return json.loads(await f.read())
        except:
            return {}
    
    async def save_json(self, path, data):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    
    async def add_account(self, account_data):
        data = await self.load_json(self.accounts_file)
        if 'accounts' not in data: data['accounts'] = []
        if 'backup' not in data: data['backup'] = []
        
        account_id = f"ACC-{len(data['accounts']) + 1:04d}"
        account_data['id'] = account_id
        account_data['created_at'] = datetime.now().isoformat()
        account_data['status'] = account_data.get('status', 'not_finished')
        
        data['accounts'].append(account_data)
        data['backup'].append(account_data.copy())
        await self.save_json(self.accounts_file, data)
        return account_id
    
    async def get_account(self, account_id):
        data = await self.load_json(self.accounts_file)
        for acc in data.get('accounts', []):
            if acc.get('id') == account_id:
                return acc
        return None
    
    async def update_account(self, account_id, updates):
        data = await self.load_json(self.accounts_file)
        for i, acc in enumerate(data.get('accounts', [])):
            if acc.get('id') == account_id:
                data['accounts'][i].update(updates)
                await self.save_json(self.accounts_file, data)
                return True
        return False
    
    async def delete_account(self, account_id):
        data = await self.load_json(self.accounts_file)
        accounts = data.get('accounts', [])
        for i, acc in enumerate(accounts):
            if acc.get('id') == account_id:
                del accounts[i]
                data['accounts'] = accounts
                await self.save_json(self.accounts_file, data)
                return True
        return False
    
    async def get_all_accounts(self, status=None):
        data = await self.load_json(self.accounts_file)
        accounts = data.get('accounts', [])
        if status:
            return [a for a in accounts if a.get('status') == status]
        return accounts
    
    async def create_ticket(self, ticket_data):
        data = await self.load_json(self.tickets_file)
        if 'tickets' not in data: data['tickets'] = []
        if 'closed_tickets' not in data: data['closed_tickets'] = []
        
        ticket_id = f"TKT-{len(data['tickets']) + len(data['closed_tickets']) + 1:04d}"
        ticket_data['id'] = ticket_id
        ticket_data['created_at'] = datetime.now().isoformat()
        ticket_data['status'] = 'open'
        
        data['tickets'].append(ticket_data)
        await self.save_json(self.tickets_file, data)
        return ticket_id
    
    async def get_ticket(self, ticket_id):
        data = await self.load_json(self.tickets_file)
        for t in data.get('tickets', []):
            if t.get('id') == ticket_id:
                return t
        return None
    
    async def update_ticket(self, ticket_id, updates):
        data = await self.load_json(self.tickets_file)
        for i, t in enumerate(data.get('tickets', [])):
            if t.get('id') == ticket_id:
                data['tickets'][i].update(updates)
                await self.save_json(self.tickets_file, data)
                return True
        return False
    
    async def add_sale(self, sale_data):
        data = await self.load_json(self.stats_file)
        data['total_sales'] = data.get('total_sales', 0) + 1
        data['total_revenue'] = data.get('total_revenue', 0) + sale_data.get('price', 0)
        
        if 'accounts_sold' not in data: data['accounts_sold'] = []
        data['accounts_sold'].append({**sale_data, 'date': datetime.now().isoformat()})
        
        today = datetime.now().strftime('%Y-%m-%d')
        if 'daily_stats' not in data: data['daily_stats'] = {}
        if today not in data['daily_stats']:
            data['daily_stats'][today] = {'sales': 0, 'revenue': 0}
        data['daily_stats'][today]['sales'] += 1
        data['daily_stats'][today]['revenue'] += sale_data.get('price', 0)
        
        await self.save_json(self.stats_file, data)
    
    async def get_stats(self):
        data = await self.load_json(self.stats_file)
        return {
            "total_sales": data.get("total_sales", 0),
            "total_revenue": data.get("total_revenue", 0),
            "accounts_sold": data.get("accounts_sold", []),
            "daily_stats": data.get("daily_stats", {}),
            "seller_stats": data.get("seller_stats", {}),
            "rank_stats": data.get("rank_stats", {})
        }

db = Database()

# ============ VIEWS ============

# --- Ticket Views ---
class RankCategorySelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, value=cat, emoji=RANK_EMOJIS.get(cat, "🎮"))
            for cat in list(RANK_CATEGORIES.keys())[:25]
        ]
        super().__init__(placeholder="🎯 اختر فئة الرانك...", options=options, custom_id="rank_cat_select")
    
    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        view = RankLevelView(cat)
        embed = discord.Embed(title=f"{RANK_EMOJIS.get(cat, '🎮')} {cat}", description="اختر المستوى:", color=COLORS['info'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class RankLevelSelect(ui.Select):
    def __init__(self, category):
        self.category = category
        ranks = RANK_CATEGORIES.get(category, [])
        options = [discord.SelectOption(label=r, value=r, emoji=RANK_EMOJIS.get(category, "🎮")) for r in ranks]
        super().__init__(placeholder=f"اختر مستوى {category}...", options=options, custom_id=f"rank_lvl_{category}")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketInfoModal(self.values[0]))

class RankLevelView(ui.View):
    def __init__(self, category):
        super().__init__(timeout=60)
        self.add_item(RankLevelSelect(category))

class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RankCategorySelect())

class TicketInfoModal(ui.Modal, title="📝 معلومات التذكرة"):
    def __init__(self, rank):
        super().__init__()
        self.rank = rank
    
    account_info = ui.TextInput(label="معلومات الحساب", placeholder="الإيميل، الباسورد، أي معلومات...", style=discord.TextStyle.paragraph, required=True)
    notes = ui.TextInput(label="ملاحظات", style=discord.TextStyle.paragraph, required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name="🎫 التذاكر")
        if not cat:
            cat = await guild.create_category("🎫 التذاكر")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        
        ch_name = f"🎫│{self.rank.replace(' ', '-')}│{interaction.user.name}"[:50]
        channel = await cat.create_text_channel(name=ch_name, overwrites=overwrites)
        
        ticket_id = await db.create_ticket({
            'user_id': interaction.user.id,
            'user_name': interaction.user.name,
            'channel_id': channel.id,
            'rank': self.rank,
            'account_info': self.account_info.value,
            'notes': self.notes.value or ""
        })
        
        embed = discord.Embed(title=f"🎫 تذكرة - {self.rank}", color=COLORS['info'])
        embed.add_field(name="🆔 ID", value=ticket_id, inline=True)
        embed.add_field(name="👤 المستخدم", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎮 الرانك", value=self.rank, inline=True)
        embed.add_field(name="📋 المعلومات", value=f"```{self.account_info.value}```", inline=False)
        if self.notes.value:
            embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView(ticket_id))
        await interaction.response.send_message(f"✅ تم إنشاء التذكرة! {channel.mention}", ephemeral=True)

class TicketControlView(ui.View):
    def __init__(self, ticket_id=""):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @ui.button(label="✅ تم البيع", style=discord.ButtonStyle.success, custom_id="ticket_sold")
    async def sold(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(SoldModal())
    
    @ui.button(label="🔒 إغلاق", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔒 جاري الإغلاق...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class SoldModal(ui.Modal, title="💰 معلومات البيع"):
    buyer = ui.TextInput(label="اسم المشتري", required=True)
    price = ui.TextInput(label="السعر", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = float(self.price.value)
        except:
            await interaction.response.send_message("❌ السعر لازم رقم!", ephemeral=True)
            return
        
        await db.add_sale({'buyer': self.buyer.value, 'price': price, 'seller': interaction.user.name})
        
        waiting_cat = discord.utils.get(interaction.guild.categories, name="💰 انتظار الفلوس")
        if not waiting_cat:
            waiting_cat = await interaction.guild.create_category("💰 انتظار الفلوس")
        
        await interaction.channel.edit(category=waiting_cat)
        
        embed = discord.Embed(title="💰 تم البيع!", color=COLORS['warning'])
        embed.add_field(name="👤 المشتري", value=self.buyer.value, inline=True)
        embed.add_field(name="💵 السعر", value=f"{price} ج", inline=True)
        embed.add_field(name="🛒 البائع", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, view=WaitingMoneyView())

class WaitingMoneyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="💵 تم التسليم", style=discord.ButtonStyle.success, custom_id="money_done")
    async def done(self, interaction: discord.Interaction, button: ui.Button):
        done_cat = discord.utils.get(interaction.guild.categories, name="✅ تم تسليم الفلوس")
        if not done_cat:
            done_cat = await interaction.guild.create_category("✅ تم تسليم الفلوس")
        
        await interaction.channel.edit(category=done_cat)
        
        embed = discord.Embed(title="✅ تم تسليم الفلوس!", color=COLORS['success'])
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, view=FinalView())

class FinalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="🗑️ حذف", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role and admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ الأدمن فقط!", ephemeral=True)
            return
        await interaction.response.send_message("🗑️ جاري الحذف...")
        await interaction.channel.delete()

# --- Account Views ---
class AccountInfoModal(ui.Modal, title="📝 إضافة حساب"):
    account_info = ui.TextInput(label="معلومات الحساب", placeholder="الإيميل\nالباسورد\nأي معلومات...", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    current_level = ui.TextInput(label="اللفل الحالي", placeholder="مثال: 10", required=True)
    opened_by = ui.TextInput(label="مين فاتح الحساب", required=True)
    notes = ui.TextInput(label="ملاحظات", style=discord.TextStyle.paragraph, required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.current_level.value)
        except:
            await interaction.response.send_message("❌ اللفل لازم رقم!", ephemeral=True)
            return
        
        account_id = await db.add_account({
            'account_info': self.account_info.value,
            'current_level': level,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value or "",
            'added_by': interaction.user.id,
            'added_by_name': interaction.user.name,
            'status': 'finished' if level >= 15 else 'not_finished'
        })
        
        # Backup
        backup_ch = discord.utils.get(interaction.guild.channels, name="🔒│backup-accounts")
        if backup_ch:
            be = discord.Embed(title=f"💾 Backup - {account_id}", color=COLORS['purple'])
            be.add_field(name="📋 المعلومات", value=f"```{self.account_info.value}```", inline=False)
            be.add_field(name="📊 اللفل", value=str(level), inline=True)
            be.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
            be.timestamp = discord.utils.utcnow()
            await backup_ch.send(embed=be)
        
        # Target channel
        if level >= 15:
            target = discord.utils.get(interaction.guild.channels, name="✅│level-15-done")
            color = COLORS['success']
            prefix = "✅"
            is_done = True
        else:
            target = discord.utils.get(interaction.guild.channels, name="⏳│level-15-not-finish")
            color = COLORS['warning']
            prefix = "⏳"
            is_done = False
        
        embed = discord.Embed(title=f"{prefix} حساب - {account_id}", color=color)
        embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
        embed.add_field(name="📋 المعلومات", value=f"```{self.account_info.value[:500]}```", inline=False)
        embed.add_field(name="📊 اللفل", value=f"`{level}`", inline=True)
        embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
        embed.add_field(name="➕ أضافه", value=interaction.user.mention, inline=True)
        if self.notes.value:
            embed.add_field(name="📝 ملاحظات", value=self.notes.value, inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        if target:
            await target.send(embed=embed, view=AccountControlView(account_id, is_done))
            await interaction.response.send_message(f"✅ تم إضافة الحساب! {target.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ القناة مش موجودة! استخدم `/setup_all`", ephemeral=True)

class AccountControlView(ui.View):
    def __init__(self, account_id="", is_done=False):
        super().__init__(timeout=None)
        self.account_id = account_id
        self.is_done = is_done
        
        # Dynamic buttons
        if not is_done:
            move_btn = ui.Button(label="✅ نقل لـ Done", style=discord.ButtonStyle.success, custom_id=f"move_{account_id}")
            move_btn.callback = self.move_callback
            self.add_item(move_btn)
        
        edit_btn = ui.Button(label="📝 تعديل", style=discord.ButtonStyle.primary, custom_id=f"edit_{account_id}")
        edit_btn.callback = self.edit_callback
        self.add_item(edit_btn)
        
        del_btn = ui.Button(label="🗑️ حذف", style=discord.ButtonStyle.danger, custom_id=f"del_{account_id}")
        del_btn.callback = self.delete_callback
        self.add_item(del_btn)
    
    async def move_callback(self, interaction: discord.Interaction):
        acc_id = None
        if interaction.message.embeds:
            for f in interaction.message.embeds[0].fields:
                if f.name == "🆔 ID":
                    acc_id = f.value.strip("`")
                    break
        
        if not acc_id:
            await interaction.response.send_message("❌ Error!", ephemeral=True)
            return
        
        account = await db.get_account(acc_id)
        if not account:
            await interaction.response.send_message("❌ الحساب مش موجود!", ephemeral=True)
            return
        
        await db.update_account(acc_id, {'status': 'finished', 'current_level': 15})
        
        done_ch = discord.utils.get(interaction.guild.channels, name="✅│level-15-done")
        if done_ch:
            embed = discord.Embed(title=f"✅ حساب - {acc_id}", color=COLORS['success'])
            embed.add_field(name="🆔 ID", value=f"`{acc_id}`", inline=False)
            embed.add_field(name="📋 المعلومات", value=f"```{account.get('account_info', 'N/A')}```", inline=False)
            embed.add_field(name="📊 اللفل", value="`15`", inline=True)
            embed.add_field(name="👤 فاتحه", value=account.get('opened_by', 'N/A'), inline=True)
            embed.timestamp = discord.utils.utcnow()
            
            await done_ch.send(embed=embed, view=AccountControlView(acc_id, True))
            await interaction.response.send_message("✅ تم النقل!", ephemeral=True)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ القناة مش موجودة!", ephemeral=True)
    
    async def edit_callback(self, interaction: discord.Interaction):
        acc_id = None
        if interaction.message.embeds:
            for f in interaction.message.embeds[0].fields:
                if f.name == "🆔 ID":
                    acc_id = f.value.strip("`")
                    break
        
        account = await db.get_account(acc_id) if acc_id else None
        if account:
            await interaction.response.send_modal(EditAccountModal(acc_id, account, interaction.message))
        else:
            await interaction.response.send_message("❌ الحساب مش موجود!", ephemeral=True)
    
    async def delete_callback(self, interaction: discord.Interaction):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role and admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ الأدمن فقط!", ephemeral=True)
            return
        
        acc_id = None
        if interaction.message.embeds:
            for f in interaction.message.embeds[0].fields:
                if f.name == "🆔 ID":
                    acc_id = f.value.strip("`")
                    break
        
        if acc_id:
            await db.delete_account(acc_id)
            await interaction.response.send_message("✅ تم الحذف!", ephemeral=True)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ Error!", ephemeral=True)

class EditAccountModal(ui.Modal, title="📝 تعديل الحساب"):
    def __init__(self, account_id, account_data, message):
        super().__init__()
        self.account_id = account_id
        self.message = message
        self.account_info.default = account_data.get('account_info', '')
        self.current_level.default = str(account_data.get('current_level', ''))
        self.opened_by.default = account_data.get('opened_by', '')
        self.notes.default = account_data.get('notes', '')
    
    account_info = ui.TextInput(label="المعلومات", style=discord.TextStyle.paragraph, required=True)
    current_level = ui.TextInput(label="اللفل", required=True)
    opened_by = ui.TextInput(label="فاتحه", required=True)
    notes = ui.TextInput(label="ملاحظات", style=discord.TextStyle.paragraph, required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.current_level.value)
        except:
            await interaction.response.send_message("❌ اللفل لازم رقم!", ephemeral=True)
            return
        
        await db.update_account(self.account_id, {
            'account_info': self.account_info.value,
            'current_level': level,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value
        })
        
        await interaction.response.send_message("✅ تم التحديث!", ephemeral=True)

class Level15NotFinishView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="➕ إضافة حساب", style=discord.ButtonStyle.success, custom_id="add_acc_nf", emoji="🎮")
    async def add(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AccountInfoModal())

class Level15DoneView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="➕ إضافة حساب مكتمل", style=discord.ButtonStyle.success, custom_id="add_acc_done", emoji="✅")
    async def add(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DoneAccountModal())

class DoneAccountModal(ui.Modal, title="📝 إضافة حساب مكتمل"):
    account_info = ui.TextInput(label="المعلومات", style=discord.TextStyle.paragraph, required=True)
    opened_by = ui.TextInput(label="فاتحه", required=True)
    notes = ui.TextInput(label="ملاحظات", style=discord.TextStyle.paragraph, required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        account_id = await db.add_account({
            'account_info': self.account_info.value,
            'current_level': 15,
            'opened_by': self.opened_by.value,
            'notes': self.notes.value or "",
            'status': 'finished',
            'added_by': interaction.user.id
        })
        
        embed = discord.Embed(title=f"✅ حساب - {account_id}", color=COLORS['success'])
        embed.add_field(name="🆔 ID", value=f"`{account_id}`", inline=False)
        embed.add_field(name="📋 المعلومات", value=f"```{self.account_info.value}```", inline=False)
        embed.add_field(name="📊 اللفل", value="`15`", inline=True)
        embed.add_field(name="👤 فاتحه", value=self.opened_by.value, inline=True)
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed, view=AccountControlView(account_id, True))

# ============ BOT ============
class MarvelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
    
    async def setup_hook(self):
        # Add views
        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())
        self.add_view(WaitingMoneyView())
        self.add_view(FinalView())
        self.add_view(Level15NotFinishView())
        self.add_view(Level15DoneView())
        self.add_view(AccountControlView())
        
        # Sync commands
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    
    async def on_ready(self):
        print(f"{'='*50}")
        print(f"🤖 BOT READY: {self.user.name}")
        print(f"🆔 ID: {self.user.id}")
        print(f"📊 Servers: {len(self.guilds)}")
        print(f"📝 Commands: {len(self.tree.get_commands())}")
        print(f"{'='*50}")
        
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Marvel Accounts 🎮"))

bot = MarvelBot()

# ============ COMMANDS ============
@bot.tree.command(name="ping", description="اختبار البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="sync", description="مزامنة الأوامر")
@app_commands.default_permissions(administrator=True)
async def sync_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    else:
        synced = await bot.tree.sync()
    await interaction.followup.send(f"✅ Synced {len(synced)} commands!")

@bot.tree.command(name="setup_all", description="إعداد كل شيء")
@app_commands.default_permissions(administrator=True)
async def setup_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    status = []
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    # Voice
    cat = discord.utils.get(guild.categories, name="🔊 Voice Channels")
    if not cat:
        cat = await guild.create_category("🔊 Voice Channels")
    for i in range(1, 4):
        if not discord.utils.get(guild.voice_channels, name=f"🔊│Voice {i}"):
            await guild.create_voice_channel(f"🔊│Voice {i}", category=cat)
    status.append("✅ Voice")
    
    # Tickets
    for n in ["🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس"]:
        if not discord.utils.get(guild.categories, name=n):
            await guild.create_category(n)
    
    tcat = discord.utils.get(guild.categories, name="🎫 التذاكر")
    if not discord.utils.get(guild.text_channels, name="🎫│فتح-تذكرة"):
        ch = await guild.create_text_channel("🎫│فتح-تذكرة", category=tcat, overwrites=overwrites)
        e = discord.Embed(title="🎫 نظام التذاكر", description="اختر رانك الحساب", color=COLORS['purple'])
        await ch.send(embed=e, view=TicketPanelView())
    status.append("✅ Tickets")
    
    # Level 15
    lcat = discord.utils.get(guild.categories, name="📊 Level 15 System")
    if not lcat:
        lcat = await guild.create_category("📊 Level 15 System")
    
    if not discord.utils.get(guild.text_channels, name="🔒│backup-accounts"):
        await guild.create_text_channel("🔒│backup-accounts", category=lcat, overwrites=overwrites)
    
    if not discord.utils.get(guild.text_channels, name="⏳│level-15-not-finish"):
        ch = await guild.create_text_channel("⏳│level-15-not-finish", category=lcat, overwrites=overwrites)
        e = discord.Embed(title="⏳ حسابات لم تصل لفل 15", color=COLORS['warning'])
        m = await ch.send(embed=e, view=Level15NotFinishView())
        await m.pin()
    
    if not discord.utils.get(guild.text_channels, name="✅│level-15-done"):
        ch = await guild.create_text_channel("✅│level-15-done", category=lcat, overwrites=overwrites)
        e = discord.Embed(title="✅ حسابات وصلت لفل 15", color=COLORS['success'])
        m = await ch.send(embed=e, view=Level15DoneView())
        await m.pin()
    status.append("✅ Level 15")
    
    # Stats
    scat = discord.utils.get(guild.categories, name="📈 الإحصائيات")
    if not scat:
        scat = await guild.create_category("📈 الإحصائيات")
    if not discord.utils.get(guild.text_channels, name="📊│احصائيات"):
        ch = await guild.create_text_channel("📊│احصائيات", category=scat, overwrites=overwrites)
        stats = await db.get_stats()
        accounts = await db.get_all_accounts()
        e = discord.Embed(title="📊 الإحصائيات", color=COLORS['purple'])
        e.add_field(name="💰 المبيعات", value=str(stats.get('total_sales', 0)), inline=True)
        e.add_field(name="💵 الأرباح", value=f"{stats.get('total_revenue', 0):,.0f} ج", inline=True)
        e.add_field(name="🎮 الحسابات", value=str(len(accounts)), inline=True)
        await ch.send(embed=e)
    status.append("✅ Stats")
    
    await interaction.followup.send(embed=discord.Embed(title="✅ تم!", description="\n".join(status), color=COLORS['success']))

@bot.tree.command(name="clean_channels", description="حذف القنوات")
@app_commands.default_permissions(administrator=True)
async def clean_channels(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    deleted = 0
    for name in ["🔊 Voice Channels", "🎫 التذاكر", "💰 انتظار الفلوس", "✅ تم تسليم الفلوس", "📊 Level 15 System", "📈 الإحصائيات"]:
        cat = discord.utils.get(interaction.guild.categories, name=name)
        if cat:
            for ch in cat.channels:
                await ch.delete()
                deleted += 1
            await cat.delete()
            deleted += 1
    
    await interaction.followup.send(f"✅ Deleted {deleted}!")

@bot.tree.command(name="stats", description="الإحصائيات")
async def stats(interaction: discord.Interaction):
    stats = await db.get_stats()
    accounts = await db.get_all_accounts()
    
    e = discord.Embed(title="📊 الإحصائيات", color=COLORS['purple'])
    e.add_field(name="💰 المبيعات", value=str(stats.get('total_sales', 0)), inline=True)
    e.add_field(name="💵 الأرباح", value=f"{stats.get('total_revenue', 0):,.0f} ج", inline=True)
    e.add_field(name="🎮 الحسابات", value=str(len(accounts)), inline=True)
    e.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="add_account", description="إضافة حساب")
async def add_account(interaction: discord.Interaction):
    await interaction.response.send_modal(AccountInfoModal())

@bot.tree.command(name="list_accounts", description="قائمة الحسابات")
async def list_accounts(interaction: discord.Interaction):
    accounts = await db.get_all_accounts()
    if not accounts:
        await interaction.response.send_message("📭 لا توجد حسابات!", ephemeral=True)
        return
    
    e = discord.Embed(title=f"📋 الحسابات ({len(accounts)})", color=COLORS['info'])
    for a in accounts[:15]:
        e.add_field(name=a['id'], value=f"Level: {a.get('current_level', '?')} | {a.get('status', '?')}", inline=True)
    
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="list_ranks", description="الرانكات")
async def list_ranks(interaction: discord.Interaction):
    e = discord.Embed(title="📋 الرانكات", color=COLORS['info'])
    for cat, ranks in list(RANK_CATEGORIES.items())[:10]:
        e.add_field(name=f"{RANK_EMOJIS.get(cat, '🎮')} {cat}", value="\n".join(ranks), inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="bot_info", description="معلومات البوت")
async def bot_info(interaction: discord.Interaction):
    e = discord.Embed(title="🤖 Marvel Bot", color=COLORS['purple'])
    e.add_field(name="Name", value=bot.user.name, inline=True)
    e.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    e.add_field(name="Latency", value=f"{round(bot.latency*1000)}ms", inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)

# ============ KEEP ALIVE ============
try:
    from flask import Flask
    from threading import Thread
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "🤖 Bot is running!"
    
    def run():
        app.run(host='0.0.0.0', port=8080)
    
    def keep_alive():
        Thread(target=run, daemon=True).start()
        print("✅ Keep-alive started")
    
    keep_alive()
except:
    print("⚠️ Flask not available")

# ============ RUN ============
if __name__ == "__main__":
    print("🚀 Starting bot...")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ No token!")