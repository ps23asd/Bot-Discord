@app_commands.command(name="bot_info", description="معلومات عن البوت والسيرفر")
async def bot_info(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 معلومات البوت",
        color=COLORS['info']
    )
    
    # Bot info
    embed.add_field(
        name="🤖 البوت",
        value=f"```\n"
              f"الاسم: {self.bot.user.name}\n"
              f"ID: {self.bot.user.id}\n"
              f"المنصة: GitHub Actions\n"
              f"```",
        inline=False
    )
    
    # Server info
    guild = interaction.guild
    embed.add_field(
        name="🏰 السيرفر",
        value=f"```\n"
              f"الأعضاء: {guild.member_count}\n"
              f"القنوات: {len(guild.channels)}\n"
              f"الأدوار: {len(guild.roles)}\n"
              f"```",
        inline=True
    )
    
    # Data info
    from database import db
    accounts = await db.get_all_accounts()
    stats = await db.get_stats()
    
    embed.add_field(
        name="💾 البيانات",
        value=f"```\n"
              f"الحسابات: {len(accounts)}\n"
              f"المبيعات: {stats.get('total_sales', 0)}\n"
              f"الأرباح: {stats.get('total_revenue', 0)} ج\n"
              f"```",
        inline=True
    )
    
    # Uptime (من آخر restart)
    import discord.utils
    embed.add_field(
        name="⏰ معلومات التشغيل",
        value=f"```\n"
              f"البوت يعمل على GitHub Actions\n"
              f"يُعاد التشغيل كل 5 ساعات 45 دقيقة\n"
              f"البيانات محفوظة تلقائياً\n"
              f"```",
        inline=False
    )
    
    embed.set_footer(text="Marvel Bot - Running on GitHub Actions")
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)
