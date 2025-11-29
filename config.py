import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))

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

MARVEL_RANKS = []
for ranks in RANK_CATEGORIES.values():
    MARVEL_RANKS.extend(ranks)

COLORS = {
    "success": 0x00FF00,
    "error": 0xFF0000,
    "info": 0x00BFFF,
    "warning": 0xFFFF00,
    "purple": 0x9B59B6
}

RANK_EMOJIS = {
    "Bronze": "🟫",
    "Silver": "⚪",
    "Gold": "🟨",
    "Platinum": "⬜",
    "Diamond": "💎",
    "Vibranium": "🟣",
    "Grandmaster": "🔴",
    "Celestial": "⭐",
    "One Above All": "👑",
    "Eternity": "♾️"
}
