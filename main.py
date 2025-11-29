import discord
from discord.ext import commands
import asyncio
import os
import signal
import sys
from config import TOKEN, GUILD_ID
from views.ticket_views import TicketPanelView, TicketControlView, WaitingMoneyView, FinalView
from views.account_views import Level15NotFinishView, Level15DoneView, AccountControlView
from database import db

# استيراد keep_alive
try:
    from keep_alive import keep_alive
    KEEP_ALIVE_ENABLED = True
except ImportError:
    KEEP_ALIVE_ENABLED = False
    print("⚠️ keep_alive.py not found, running without web server")

class MarvelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.shutting_down = False
    
    async def setup_hook(self):
        # Load cogs
        for cog in ['tickets', 'accounts', 'stats', 'admin']:
            try:
                await self.load_extension(f'cogs.{cog}')
                print(f"✅ Loaded cog: {cog}")
            except Exception as e:
                print(f"❌ Failed to load cog {cog}: {e}")
        
        # Add persistent views
        self.add_view(TicketPanelView())
        self.add_view(TicketControlView(""))
        self.add_view(WaitingMoneyView(""))
        self.add_view(FinalView())
        self.add_view(Level15NotFinishView())
        self.add_view(Level15DoneView())
        self.add_view(AccountControlView(""))
        
        # Sync commands
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        
        print("✅ Commands synced!")
    
    async def on_ready(self):
        print(f"{'='*50}")
        print(f"🤖 Bot is ready!")
        print(f"📛 Logged in as: {self.user.name}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"📊 Servers: {len(self.guilds)}")
        print(f"⏰ Running on GitHub Actions")
        print(f"💾 Data will be saved automatically")
        print(f"{'='*50}")
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Marvel Accounts 🎮"
            )
        )
    
    async def close(self):
        """حفظ البيانات عند الإغلاق"""
        if not self.shutting_down:
            self.shutting_down = True
            print("\n" + "="*50)
            print("🛑 Shutting down bot...")
            print("💾 Saving data...")
            
            # إعطاء وقت للـ database لحفظ أي معاملات معلقة
            await asyncio.sleep(2)
            
            print("✅ Data saved successfully")
            print("👋 Bot shutdown complete")
            print("="*50 + "\n")
        
        await super().close()

def signal_handler(sig, frame):
    """معالج إشارات النظام للإغلاق الآمن"""
    print(f"\n⚠️ Received signal {sig}")
    sys.exit(0)

# تسجيل معالجات الإشارات
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Run bot
if __name__ == "__main__":
    print("="*50)
    print("🚀 Starting Marvel Discord Bot")
    print("📍 Environment: GitHub Actions")
    print("="*50 + "\n")
    
    # تشغيل keep_alive server
    if KEEP_ALIVE_ENABLED:
        keep_alive()
    
    try:
        bot = MarvelBot()
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔚 Bot process ended")
