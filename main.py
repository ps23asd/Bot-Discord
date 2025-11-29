import discord
from discord.ext import commands
import asyncio
import os
import signal
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
ADMIN_ROLE_ID = os.getenv('ADMIN_ROLE_ID')

if GUILD_ID:
    GUILD_ID = int(GUILD_ID)
if ADMIN_ROLE_ID:
    ADMIN_ROLE_ID = int(ADMIN_ROLE_ID)

# Keep alive
try:
    from keep_alive import keep_alive
    KEEP_ALIVE = True
except:
    KEEP_ALIVE = False

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
    
    async def setup_hook(self):
        print("\n📦 Loading cogs...")
        
        # Load cogs one by one with error details
        cog_files = ['tickets', 'accounts', 'stats', 'admin']
        loaded = 0
        
        for cog in cog_files:
            try:
                await self.load_extension(f'cogs.{cog}')
                print(f"   ✅ Loaded: {cog}")
                loaded += 1
            except Exception as e:
                print(f"   ❌ Failed: {cog}")
                print(f"      Error: {e}")
        
        print(f"\n📊 Loaded {loaded}/{len(cog_files)} cogs")
        
        # Sync commands
        print("\n🔄 Syncing commands...")
        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                print(f"   ✅ Synced {len(synced)} commands to guild {GUILD_ID}")
            else:
                synced = await self.tree.sync()
                print(f"   ✅ Synced {len(synced)} commands globally")
        except Exception as e:
            print(f"   ❌ Sync failed: {e}")
        
        # Add persistent views
        print("\n🎨 Adding views...")
        try:
            from views.ticket_views import TicketPanelView, TicketControlView, WaitingMoneyView, FinalView
            from views.account_views import Level15NotFinishView, Level15DoneView, AccountControlView
            
            self.add_view(TicketPanelView())
            self.add_view(TicketControlView(""))
            self.add_view(WaitingMoneyView(""))
            self.add_view(FinalView())
            self.add_view(Level15NotFinishView())
            self.add_view(Level15DoneView())
            self.add_view(AccountControlView(""))
            print("   ✅ Views added")
        except Exception as e:
            print(f"   ❌ Views failed: {e}")
    
    async def on_ready(self):
        print("\n" + "="*50)
        print("🤖 BOT IS READY!")
        print("="*50)
        print(f"📛 Name: {self.user.name}")
        print(f"🆔 ID: {self.user.id}")
        print(f"📊 Servers: {len(self.guilds)}")
        print(f"📝 Commands: {len(self.tree.get_commands())}")
        print("="*50 + "\n")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Marvel Accounts 🎮"
            )
        )

def main():
    print("="*50)
    print("🚀 STARTING MARVEL DISCORD BOT")
    print("="*50)
    print(f"📍 Platform: GitHub Actions")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📦 Discord.py: {discord.__version__}")
    print("="*50)
    
    if KEEP_ALIVE:
        keep_alive()
        print("✅ Keep-alive server started")
    
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found!")
        return
    
    bot = MarvelBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
