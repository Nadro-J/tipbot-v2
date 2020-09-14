import discord, json, requests, pymysql.cursors
from discord.ext import commands
from utils import rpc_module, mysql_module, parsing, checks

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Tip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')         
        self.currency_symbol = config["currency_symbol"]
        self.donation_id = config["donation"] 

        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(pass_context=True)
    @commands.check(checks.in_server)
    async def tip(self, ctx, amount:float, *args: discord.Member):
        """Tip users coins. You can tip multiple users"""
        snowflake = ctx.message.author.id
        users=list(set(args))

        if ctx.message.guild is not None:
            await ctx.message.delete()

        for user in users:

            tip_user = user.id
            #check if sender is trying to send to themselves and return error to user in chat
            if snowflake == tip_user:
                await ctx.send("{} **:warning:You cannot tip yourself!:warning:**".format(ctx.message.author.mention))
                return
            #check if amount is negative and return error to user in chat
            if amount <= 0.0:
                await ctx.send("{} **:warning:You cannot tip <= 0!:warning:**".format(ctx.message.author.mention))
                return
            #check if the sender is in database (should always return true) we will not check this using depreciated check_for_user()
            mysql.check_for_user(str(snowflake))
            #check if receiver is in database
            if mysql.check_for_user(tip_user) is not None:
                balance = mysql.get_balance(str(snowflake), check_update=True)
                #check the senders balance for overdraft and return error to user in chat
                if float(balance) < amount:
                    await ctx.send("{} **:warning:You cannot tip more money than you have!:warning:**".format(ctx.message.author.mention))
                else:
                    mysql.add_tip(str(snowflake), tip_user, amount)
                    await ctx.send("{} **Tipped {} {} {}! :moneybag:**".format(ctx.message.author.mention, user.mention, str(amount), self.currency_symbol))
            #if receiver not in database return error to user in chat
            else:
                await ctx.send("{} **:warning:You cannot tip {}. That user is not Registered:warning:**".format(ctx.message.author.mention, user.mention))

    @commands.command(pass_context=True)
    async def donate(self, ctx, amount:float):
        """Donate to a donation account"""
        snowflake = ctx.message.author.id
        tip_user = str(self.donation_id)

        if ctx.message.guild is not None:
            await ctx.message.delete()

        #check if sender is trying to send to themselves and return error to user in chat
        if snowflake == tip_user:
            await ctx.send("{} **:warning:You cannot donate to yourself!:warning:**".format(ctx.message.author.mention))
            return
        #check if amount is negative and return error to user in chat
        if amount <= 0.0:
            await ctx.send("{} **:warning:You cannot donate <= 0!:warning:**".format(ctx.message.author.mention))
            return
        #check if the sender is in database (should always return true) we will not check this using depreciated check_for_user()
        mysql.check_for_user(str(snowflake))
        #check if receiver is in database
        if mysql.check_for_user(tip_user) is not None:
            balance = mysql.get_balance(str(snowflake), check_update=True)
            #check the senders balance for overdraft and return error to user in chat
            if float(balance) < amount:
                await ctx.send("{} **:warning:You cannot donate more money than you have!:warning:**".format(ctx.message.author.mention))
            else:
                mysql.add_tip(str(snowflake), tip_user, amount)
                await ctx.send("{} **Donated {} {}! Thank You :tada:**".format(ctx.message.author.mention, str(amount), self.currency_symbol))
        #if receiver not in database return error to user in chat
        else:
            await ctx.send("{} **:warning:You cannot tip {}. That user is not Registered:warning:**".format(ctx.message.author.mention, tip_user))

def setup(bot):
    bot.add_cog(Tip(bot))
