import math
import discord
from discord.ext import commands
from utils import rpc_module, mysql_module, checks, parsing
import random

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Soak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        soak_config = parsing.parse_json('config.json')['soak']
        config = parsing.parse_json('config.json')         
        '''
        soak_max_recipients sets the max recipients for a soak. chosen randomly.
        soak_min_received sets the minimum possible soak received for a user.
        The number of soak recipients will be adjusted to fit these constraints
        if enabled via use_max_recipients and use_min_received
        '''
        self.soak_max_recipients = soak_config["soak_max_recipients"]
        self.use_max_recipients = soak_config["use_max_recipients"]
        self.soak_min_received = soak_config["soak_min_received"]
        self.use_min_received = soak_config["use_min_received"]
        self.soak_minimum = soak_config['min_amount']        
        self.currency_symbol = config["currency_symbol"] 
        self.prefix = config["prefix"]           

    @commands.command(pass_context=True)
    @commands.check(checks.allow_soak)
    async def soak(self, ctx, amount: float, role_id=""):
        """Tip all online users"""
        if ctx.message.guild is not None:
            await ctx.message.delete()

        if self.use_max_recipients and self.soak_max_recipients == 0:
            await ctx.send("**:warning: max users for soak is set to 0! Talk to the config owner. :warning:**")
            return

        if amount < self.soak_minimum:
            await ctx.send("**:warning: Amount {:.8f} {} for soak is less than minimum {:.8f} {} required! :warning:**".format(float(amount), self.currency_symbol, float(self.soak_minimum), self.currency_symbol))
            return

        snowflake = ctx.message.author.id

        mysql.check_for_user(str(snowflake))
        balance = mysql.get_balance(str(snowflake), check_update=True)

        if float(balance) < amount:
            await ctx.send("{} **:warning:You cannot soak more {} than you have!:warning:**".format(ctx.message.author.mention, self.currency_symbol))
            return

        users_list=[]
        if role_id=="" or role_id=="@verified" or role_id=="@here" or role_id=="all":
            for user in ctx.message.guild.members:
                if mysql.check_for_user(user.id) is not None:
                    users_list.append(user)
        else:
            server_roles = ctx.message.guild.roles
            role=[x for x in server_roles if x.mention==role_id]
            if len(role)==0:
                await ctx.send("{}, This role does not exist! To tip a single user, use {}tip command instead.".format(ctx.message.author.mention,self.prefix))
                return
            else:
                for user in ctx.message.guild.members:
                    if role[0] in user.roles:
                        if mysql.check_for_user(user.id) is not None:
                            users_list.append(user)    

        if role_id!="":
            online_users = [x for x in users_list]
        else:
            online_users = [x for x in users_list]

        if ctx.message.author in online_users:
            online_users.remove(ctx.message.author)

        online_users=[x for x in online_users if x.bot==False]

        if self.use_max_recipients:
            len_receivers = min(len(online_users), self.soak_max_recipients)
        else:
            len_receivers = len(online_users)

        if self.use_min_received:
            len_receivers = min(len_receivers, amount / self.soak_min_received)

        if len_receivers == 0:
            await ctx.send("{}, you are all alone if you don't include bots! Trying soaking when people are online.".format(ctx.message.author.mention))
            return

        amount_split = math.floor(float(amount) * 1e8 / len_receivers) / 1e8
        if amount_split == 0:
            await ctx.send("{} **:warning:{:.8f} {} is not enough to split between {} users:warning:**".format(ctx.message.author.mention, float(amount), self.currency_symbol, len_receivers))
            return

        if role_id=="all" or role_id=="@everyone" or role_id=="@here":
            await ctx.send("{} **Sorry, Soaking the {} role is not permitted.**".format(ctx.message.author.mention, role_id))
        else:
            receivers = []
            if role_id == "":
                for i in range(len_receivers):
                    user = random.choice(online_users)
                    receivers.append(user)
                    online_users.remove(user)
                    mysql.check_for_user(user.id)
                    mysql.add_tip(snowflake, user.id, amount_split)

                await ctx.send(":cloud_rain: {} **Soaked {:.8f} {} on {} users** (Total {:.8f} {}) :cloud_rain:".format(ctx.message.author.mention, float(amount_split), self.currency_symbol, len_receivers, float(amount), self.currency_symbol))
                users_soaked_msg = []
                idx = 0
                for users in receivers:
                    users_soaked_msg.append(users.mention)
                    idx += 1
                    if (len(users_soaked_msg) >= 25) or (idx == int(len_receivers)):
                        await ctx.send("{}".format(' '.join(users_soaked_msg)))
                        del users_soaked_msg[:]
                        users_soaked_msg = []
            else:
                for i in range(len_receivers):
                    user = random.choice(online_users)
                    receivers.append(user)
                    online_users.remove(user)
                    mysql.check_for_user(user.id)
                    mysql.add_tip(snowflake, user.id, amount_split)

                long_soak_msg = ":cloud_rain: {} **Soaked {:.8f} {} on {} {} users** (Total {:.8f} {}) :cloud_rain:".format(ctx.message.author.mention, float(amount_split), self.currency_symbol, len_receivers, role_id, float(amount), self.currency_symbol)

                #bot response:
                await ctx.send(long_soak_msg)

                #parse into 25 username sized message chunks
                users_soaked_msg = []
                idx = 0
                for users in receivers:
                    users_soaked_msg.append(users.mention)
                    idx += 1
                    if (len(users_soaked_msg) >= 25) or (idx == int(len_receivers)):
                        await ctx.send("{}".format(' '.join(users_soaked_msg)))
                        del users_soaked_msg[:]
                        users_soaked_msg = []


    @commands.command()
    async def soak_info(self, ctx):
        """Display min soak amount and maximum soak recipients"""
        if ctx.message.guild is not None:
            await ctx.message.delete()

        if self.use_max_recipients:
            st_max_users = str(self.soak_max_recipients)
        else:
            st_max_users = "<disabled>"

        if self.use_min_received:
            st_min_received = str(self.soak_min_received)
        else:
            st_min_received = "<disabled>"
            
        await ctx.send(":information_source: Soak info: max recipients {}, min amount receivable {} :information_source:".format(st_max_users, st_min_received))

def setup(bot):
    bot.add_cog(Soak(bot))