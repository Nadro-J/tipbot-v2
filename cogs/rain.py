import math
import discord, json, requests
from discord.ext import commands
from utils import output, helpers, parsing, mysql_module
import random

mysql = mysql_module.Mysql()

class Rain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rain(self, ctx, amount:float):
        """Rain all active users"""

        config = parsing.parse_json('config.json')   
        CURRENCY_SYMBOL = config["currency_symbol"] 

        rain_config = parsing.parse_json('config.json')['rain']
        RAIN_MINIMUM = rain_config['min_amount']
        RAIN_REQUIRED_USER_ACTIVITY_M = rain_config['user_activity_required_m']   
        USE_MAX_RECIPIENTS = rain_config['use_max_recipients']
        MAX_RECIPIENTS = rain_config['max_recipients']        

        if ctx.message.guild is not None:
            await ctx.message.delete()

        message = ctx.message
        if helpers.is_private_dm(self.bot, message.channel):
            return

        if amount < RAIN_MINIMUM:
            await ctx.send("**:warning: Amount {:.8f} {} for rain is less than minimum {} required! :warning:**".format(float(amount), CURRENCY_SYMBOL, float(RAIN_MINIMUM)))
            return

        snowflake = str(ctx.message.author.id)

        mysql.check_for_user(snowflake)
        balance = mysql.get_balance(snowflake, check_update=True)

        if float(balance) < amount:
            await ctx.send("{} **:warning:You cannot rain more {} than you have!:warning:**".format(ctx.message.author.mention, CURRENCY_SYMBOL))
            return

        # Create tip list
        active_id_users = mysql.get_active_users_id(RAIN_REQUIRED_USER_ACTIVITY_M, True)
        
        if int(ctx.message.author.id) in active_id_users:
            active_id_users.remove(int(ctx.message.author.id))

        #users_list is all members on the server   
        users_list=[]            
        for user in ctx.message.guild.members:
            if mysql.check_for_user(user.id) is not None:
                users_list.append(user)

        server_users = [x for x in users_list]

        if ctx.message.author in server_users:
            server_users.remove(ctx.message.author)

        server_users=[x for x in server_users if x.bot==False]

        active_users = []
        for user in server_users:
            if int(user.id) in active_id_users:
                active_users.append(user)

        if USE_MAX_RECIPIENTS:
            len_receivers = min(len(active_users), MAX_RECIPIENTS)
        else:
            len_receivers = len(active_users)

        if len_receivers == 0:
            await ctx.send("{}, you are all alone if you don't include bots! Trying raining when people are online and active.".format(ctx.message.author.mention))
            return

        amount_split = math.floor(float(amount) * 1e8 / len_receivers) / 1e8
        if amount_split == 0:
            await ctx.send("{} **:warning:{:.8f} {} is not enough to split between {} users:warning:**".format(ctx.message.author.mention, float(amount), CURRENCY_SYMBOL, len_receivers))
            return    
        
        receivers = []        
        for active_user in active_users:
            receivers.append(active_user.mention)
            mysql.check_for_user(active_user.id)
            mysql.add_tip(snowflake, active_user.id, amount_split)

        if len(receivers) == 0:
            await ctx.send("{}, you are all alone if you don't include bots! Trying raining when people are online and active.".format(ctx.message.author.mention))
            return

        await ctx.send(":cloud_rain: {} **Rained {:.8f} {} on {} users** (Total {:.8f} {}) :cloud_rain:".format(ctx.message.author.mention, float(amount_split), CURRENCY_SYMBOL, len_receivers, float(amount), CURRENCY_SYMBOL))
        users_soaked_msg = []
        idx = 0
        for users in receivers:
            users_soaked_msg.append(users)
            idx += 1
            if (len(users_soaked_msg) >= 25) or (idx == int(len_receivers)):
                await ctx.send("{}".format(' '.join(users_soaked_msg)))
                del users_soaked_msg[:]
                users_soaked_msg = []

def setup(bot):
    bot.add_cog(Rain(bot))