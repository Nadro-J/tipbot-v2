import discord, json, requests
from discord.ext import commands
from utils import output, checks, helpers, parsing, mysql_module, rpc_module as rpc
import os
import traceback
import database
import re

mysql = mysql_module.Mysql()
#define bot to use his avatarurl
config = parsing.parse_json('config.json')
bot = commands.Bot(command_prefix=config['prefix'], description=config["description"])

class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rpc = rpc.Rpc()
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stake_id = config["stake_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def wallet(self):
        """Show wallet info [ADMIN ONLY]"""
        #rpc commands for getinfo
        info = self.rpc.getinfo()
        wallet_balance = str(float(info["balance"]))
        block_height = info["blocks"]
        connection_count = self.rpc.getconnectioncount()
        staking_balance = str(float(info["stake"]))
        #staking rpc commands
        stake_info = self.rpc.getstakinginfo()
        staking_state = stake_info["enabled"]
        staking_status = stake_info["staking"]
        stake_weight = float(stake_info["weight"]) * 0.00000001
        net_weight = float(stake_info["netstakeweight"]) * 0.00000001
        #number of registered users in database
        num_uses = len(mysql.get_reg_users_id())
        #below used for active user calculation
        rain_config = parsing.parse_json('config.json')['rain']
        RAIN_MINIMUM = rain_config['min_amount']
        RAIN_REQUIRED_USER_ACTIVITY_M = rain_config['user_activity_required_m']   
        USE_MAX_RECIPIENTS = rain_config['use_max_recipients']
        MAX_RECIPIENTS = rain_config['max_recipients']  
        active_id_users = mysql.get_active_users_id(RAIN_REQUIRED_USER_ACTIVITY_M, True)
        #embed starts here
        embed=discord.Embed(title="You requested the **Wallet**", color=self.embed_color, inline=False)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="Balance", value="{:.8f} BOXY".format(float(wallet_balance)))
        embed.add_field(name="Connections", value=connection_count)
        embed.add_field(name="Block Height", value=block_height)
        #user information below
        #embed.add_field(name="User Info", value="General Wallet Info", inline=False)
        embed.add_field(name="Number of Registered Users", value=num_uses, inline=False)
        embed.add_field(name="Number of Active Users", value=len(active_id_users))
        #Staking Print out below
        #embed.add_field(name="Staking Info", value="Wallet Staking Info", inline=False)
        embed.add_field(name="Staking State", value=staking_state)
        embed.add_field(name="Staking Status", value=staking_status)
        embed.add_field(name="Balance Currently Staking", value="{:.8f} {}".format(float(staking_balance), self.currency_symbol))
        embed.add_field(name="Staking Weight", value="{:.8f} {}".format(stake_weight, self.currency_symbol))
        embed.add_field(name="Net Staking Weight", value="{:.8f} {}".format(net_weight, self.currency_symbol))
        #embed footer
        embed.set_footer(text=self.footer_text)
        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission to send this")

    # ban a server 
    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def banserver(self, server: int):
        """Ban a server from using the bot [ADMIN ONLY]"""
        soak_status = mysql.check_for_server_status(server)
        if soak_status is None:
            await self.bot.say("Server ID: {} is not registered with this bot. The server will now be registered and marked as banned".format(server))
            mysql.check_server(server)
            mysql.ban_server(server, 2)
            await self.bot.say("Server ID: {} is now registered with this bot and BANNED.".format(server))
        elif soak_status == 2:
            await self.bot.say("Server ID: {} is already BANNED.".format(server))
        else:
            mysql.ban_server(server, 2)
            await self.bot.say("Server ID: {} is now marked as BANNED.".format(server))

    # unban a server 
    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def unbanserver(self, server: int):
        soak_status = mysql.check_for_server_status(server)
        """Un-Ban a server that is currently marked as BANNED [ADMIN ONLY]"""
        if soak_status is None:
            await self.bot.say("Server ID: {} is not registered with this bot. This server cannot be UNBANNED.".format(server))
        elif soak_status == 1:
            await self.bot.say("Server ID: {} is already UNBANNED.".format(server))
        else:
            mysql.ban_server(server, 1)
            await self.bot.say("Server ID: {} is now marked as UNBANNED.".format(server))

    



def setup(bot):
    bot.add_cog(Wallet(bot))

