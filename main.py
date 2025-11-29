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
    print("⚠️ keep_alive.py not found")

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
        
        self.synced = False
    
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
    
    async def on_ready(self):
        # Sync commands once
        if not self.synced:
            try:
                if GUILD_ID and GUILD_ID != 0:
                    guild = discord.Object(id=GUILD_ID)
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    print(f"✅ Synced {len(synced)} commands to guild {GUILD_ID}")
                else:
                    synced = await self.tree.sync()
                    print(f"✅ Synced {len(synced)} commands globally")
                self.synced = True
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")
        
        print(f"{'='*50}")
        print(f"🤖 Bot is ready!")
        print(f"📛 Logged in as: {self.user.name}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"📊 Servers: {len(self.guilds)}")
        print(f"⏰ Running on GitHub Actions")
        print(f"{'='*50}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Marvel Accounts 🎮"
            )
        )
    
    async def close(self):
        print("\n🛑 Shutting down...")
        print("💾 Saving data...")
        await asyncio.sleep(1)
        print("✅ Shutdown complete")
        await super().close()

def signal_handler(sig, frame):
    print(f"\n⚠️ Received signal {sig}")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("="*50)
    print("🚀 Starting Marvel Discord Bot")
    print("📍 Environment: GitHub Actions")
    print("="*50 + "\n")
    
    if KEEP_ALIVE_ENABLED:
        keep_alive()
    
    try:
        bot = MarvelBot()
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
