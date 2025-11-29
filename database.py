import json
import os
import aiofiles
from datetime import datetime
from typing import Optional, Dict, List, Any

DATA_DIR = "data"

def ensure_data_dir():
    """التأكد من وجود مجلد البيانات"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created directory: {DATA_DIR}/")

class Database:
    def __init__(self):
        ensure_data_dir()
        self.accounts_file = f"{DATA_DIR}/accounts.json"
        self.tickets_file = f"{DATA_DIR}/tickets.json"
        self.stats_file = f"{DATA_DIR}/stats.json"
        self._init_files()
    
    def _init_files(self):
        """إنشاء ملفات JSON الأساسية"""
        files_config = {
            self.accounts_file: {
                "accounts": [],
                "backup": []
            },
            self.tickets_file: {
                "tickets": [],
                "closed_tickets": []
            },
            self.stats_file: {
                "total_sales": 0,
                "total_revenue": 0,
                "accounts_sold": [],
                "daily_stats": {},
                "seller_stats": {},
                "rank_stats": {}
            }
        }
        
        for file_path, default_data in files_config.items():
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, ensure_ascii=False, indent=4)
                    print(f"✅ Created file: {file_path}")
                except Exception as e:
                    print(f"❌ Error creating {file_path}: {e}")
    
    async def load_json(self, file_path: str) -> dict:
        """تحميل بيانات JSON"""
        try:
            if not os.path.exists(file_path):
                self._init_files()
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error in {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            return {}
    
    async def save_json(self, file_path: str, data: dict):
        """حفظ بيانات JSON"""
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
        except Exception as e:
            print(f"❌ Error saving {file_path}: {e}")
    
    # ============ Accounts Functions ============
    async def add_account(self, account_data: dict) -> str:
        """إضافة حساب جديد"""
        try:
            data = await self.load_json(self.accounts_file)
            
            # التأكد من وجود المفاتيح
            if 'accounts' not in data:
                data['accounts'] = []
            if 'backup' not in data:
                data['backup'] = []
            
            account_id = f"ACC-{len(data['accounts']) + 1:04d}"
            account_data['id'] = account_id
            account_data['created_at'] = datetime.now().isoformat()
            account_data['status'] = account_data.get('status', 'not_finished')
            
            data['accounts'].append(account_data)
            data['backup'].append(account_data.copy())
            
            await self.save_json(self.accounts_file, data)
            return account_id
        except Exception as e:
            print(f"❌ Error adding account: {e}")
            return "ERROR"
    
    async def get_account(self, account_id: str) -> Optional[dict]:
        """الحصول على حساب بواسطة ID"""
        try:
            data = await self.load_json(self.accounts_file)
            accounts = data.get('accounts', [])
            
            for acc in accounts:
                if acc.get('id') == account_id:
                    return acc
            return None
        except Exception as e:
            print(f"❌ Error getting account: {e}")
            return None
    
    async def update_account(self, account_id: str, updates: dict) -> bool:
        """تحديث بيانات حساب"""
        try:
            data = await self.load_json(self.accounts_file)
            accounts = data.get('accounts', [])
            
            for i, acc in enumerate(accounts):
                if acc.get('id') == account_id:
                    accounts[i].update(updates)
                    accounts[i]['updated_at'] = datetime.now().isoformat()
                    data['accounts'] = accounts
                    await self.save_json(self.accounts_file, data)
                    return True
            return False
        except Exception as e:
            print(f"❌ Error updating account: {e}")
            return False
    
    async def delete_account(self, account_id: str) -> bool:
        """حذف حساب"""
        try:
            data = await self.load_json(self.accounts_file)
            accounts = data.get('accounts', [])
            
            for i, acc in enumerate(accounts):
                if acc.get('id') == account_id:
                    del accounts[i]
                    data['accounts'] = accounts
                    await self.save_json(self.accounts_file, data)
                    return True
            return False
        except Exception as e:
            print(f"❌ Error deleting account: {e}")
            return False
    
    async def get_all_accounts(self, status: str = None) -> List[dict]:
        """الحصول على جميع الحسابات"""
        try:
            data = await self.load_json(self.accounts_file)
            accounts = data.get('accounts', [])
            
            if status:
                return [acc for acc in accounts if acc.get('status') == status]
            return accounts
        except Exception as e:
            print(f"❌ Error getting all accounts: {e}")
            return []
    
    async def get_backup_accounts(self) -> List[dict]:
        """الحصول على النسخ الاحتياطية"""
        try:
            data = await self.load_json(self.accounts_file)
            return data.get('backup', [])
        except Exception as e:
            print(f"❌ Error getting backup accounts: {e}")
            return []
    
    # ============ Tickets Functions ============
    async def create_ticket(self, ticket_data: dict) -> str:
        """إنشاء تذكرة جديدة"""
        try:
            data = await self.load_json(self.tickets_file)
            
            # التأكد من وجود المفاتيح
            if 'tickets' not in data:
                data['tickets'] = []
            if 'closed_tickets' not in data:
                data['closed_tickets'] = []
            
            ticket_id = f"TKT-{len(data['tickets']) + len(data['closed_tickets']) + 1:04d}"
            ticket_data['id'] = ticket_id
            ticket_data['created_at'] = datetime.now().isoformat()
            ticket_data['status'] = 'open'
            
            data['tickets'].append(ticket_data)
            await self.save_json(self.tickets_file, data)
            return ticket_id
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return "ERROR"
    
    async def get_ticket(self, ticket_id: str) -> Optional[dict]:
        """الحصول على تذكرة بواسطة ID"""
        try:
            data = await self.load_json(self.tickets_file)
            tickets = data.get('tickets', [])
            
            for ticket in tickets:
                if ticket.get('id') == ticket_id:
                    return ticket
            return None
        except Exception as e:
            print(f"❌ Error getting ticket: {e}")
            return None
    
    async def update_ticket(self, ticket_id: str, updates: dict) -> bool:
        """تحديث بيانات تذكرة"""
        try:
            data = await self.load_json(self.tickets_file)
            tickets = data.get('tickets', [])
            
            for i, ticket in enumerate(tickets):
                if ticket.get('id') == ticket_id:
                    tickets[i].update(updates)
                    data['tickets'] = tickets
                    await self.save_json(self.tickets_file, data)
                    return True
            return False
        except Exception as e:
            print(f"❌ Error updating ticket: {e}")
            return False
    
    async def close_ticket(self, ticket_id: str, close_data: dict) -> bool:
        """إغلاق تذكرة"""
        try:
            data = await self.load_json(self.tickets_file)
            tickets = data.get('tickets', [])
            closed_tickets = data.get('closed_tickets', [])
            
            for i, ticket in enumerate(tickets):
                if ticket.get('id') == ticket_id:
                    ticket.update(close_data)
                    ticket['closed_at'] = datetime.now().isoformat()
                    closed_tickets.append(ticket)
                    del tickets[i]
                    
                    data['tickets'] = tickets
                    data['closed_tickets'] = closed_tickets
                    await self.save_json(self.tickets_file, data)
                    return True
            return False
        except Exception as e:
            print(f"❌ Error closing ticket: {e}")
            return False
    
    # ============ Stats Functions ============
    async def add_sale(self, sale_data: dict):
        """إضافة عملية بيع للإحصائيات"""
        try:
            data = await self.load_json(self.stats_file)
            
            # التأكد من وجود المفاتيح
            if 'total_sales' not in data:
                data['total_sales'] = 0
            if 'total_revenue' not in data:
                data['total_revenue'] = 0
            if 'accounts_sold' not in data:
                data['accounts_sold'] = []
            if 'daily_stats' not in data:
                data['daily_stats'] = {}
            if 'seller_stats' not in data:
                data['seller_stats'] = {}
            if 'rank_stats' not in data:
                data['rank_stats'] = {}
            
            data['total_sales'] += 1
            data['total_revenue'] += sale_data.get('price', 0)
            
            sale_record = {
                **sale_data,
                'date': datetime.now().isoformat()
            }
            data['accounts_sold'].append(sale_record)
            
            # Daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in data['daily_stats']:
                data['daily_stats'][today] = {'sales': 0, 'revenue': 0}
            data['daily_stats'][today]['sales'] += 1
            data['daily_stats'][today]['revenue'] += sale_data.get('price', 0)
            
            # Seller stats
            seller = sale_data.get('seller', 'Unknown')
            if seller not in data['seller_stats']:
                data['seller_stats'][seller] = {'sales': 0, 'revenue': 0}
            data['seller_stats'][seller]['sales'] += 1
            data['seller_stats'][seller]['revenue'] += sale_data.get('price', 0)
            
            # Rank stats
            rank = sale_data.get('rank', 'Unknown')
            if rank not in data['rank_stats']:
                data['rank_stats'][rank] = {'sales': 0, 'revenue': 0}
            data['rank_stats'][rank]['sales'] += 1
            data['rank_stats'][rank]['revenue'] += sale_data.get('price', 0)
            
            await self.save_json(self.stats_file, data)
        except Exception as e:
            print(f"❌ Error adding sale: {e}")
    
    async def get_stats(self) -> dict:
        """الحصول على الإحصائيات"""
        try:
            data = await self.load_json(self.stats_file)
            
            # التأكد من وجود كل المفاتيح
            default_stats = {
                "total_sales": 0,
                "total_revenue": 0,
                "accounts_sold": [],
                "daily_stats": {},
                "seller_stats": {},
                "rank_stats": {}
            }
            
            for key, value in default_stats.items():
                if key not in data:
                    data[key] = value
            
            return data
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {
                "total_sales": 0,
                "total_revenue": 0,
                "accounts_sold": [],
                "daily_stats": {},
                "seller_stats": {},
                "rank_stats": {}
            }
    
    async def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        try:
            default_stats = {
                "total_sales": 0,
                "total_revenue": 0,
                "accounts_sold": [],
                "daily_stats": {},
                "seller_stats": {},
                "rank_stats": {}
            }
            await self.save_json(self.stats_file, default_stats)
        except Exception as e:
            print(f"❌ Error resetting stats: {e}")

# إنشاء instance واحدة
db = Database() 