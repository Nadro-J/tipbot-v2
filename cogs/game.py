import discord, json, requests, pymysql.cursors
from discord.ext import commands
from utils import rpc_module, mysql_module, parsing, checks
import random
import math

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')         
        self.currency_symbol = config["currency_symbol"]
        self.donation_id = config["donation"]
        self.game_id = config["game_bal"]
        self.stake_id = config["stake_bal"]
        self.treasury_id = config["treasurer"]

    @commands.command(pass_context=True)
    @commands.cooldown(10, 30)
    async def bet(self, ctx, amount:float):
        """Place a bet on whether o not the number will be EVEN. Between 1, 9999999"""
        snowflake = ctx.message.author.id
        #the betting user is the house
        bet_user = str(self.game_id)

        if ctx.message.guild is not None:
            await ctx.message.delete()

        #check if amount is negative and return error to user in chat
        if amount <= 0.0 or float('{:.8f}'.format(amount)) == 0.00000000:
            await ctx.send("{} **:warning:You cannot bet <= 0 or with a decimal value that has more than 8 leading zeros!:warning:**".format(ctx.message.author.mention))
            return

        #check if receiver is in database

        balance = mysql.get_balance(str(snowflake), check_update=True)
        #check the senders balance for overdraft and return error to user in chat
        if float(balance) < amount:
            await ctx.send("{} **:warning:You cannot bet more {} than you have!:warning:**".format(ctx.message.author.mention, self.currency_symbol))
        else:
            #begin the betting - choose a random int between 0-999999999 if even win, if odd lose
            secret_number = random.randint(1,9999999) 
            if secret_number % 2 == 0 and secret_number != 0:
                secret_number = random.randint(1,9999999)
                if secret_number % 2 == 0 and secret_number != 0:
                    bet_user_bal = mysql.get_balance(self.game_id, check_update=True)

                    if float(bet_user_bal) >= amount:
                        mysql.add_tip(bet_user, str(snowflake), amount)
                        await ctx.send("{0} **EVEN NUMBER! {1} You WIN {2:.8f} {3}! :tada:**".format(ctx.message.author.mention, secret_number, amount, self.currency_symbol))

                    else:
                        await ctx.send("{0} **EVEN NUMBER! {1} You WIN {2:.8f} {3}!** BUT THE BOT DOES NOT HAVE ENOUGH FUNDS TO PAY YOU".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                else:
                    mysql.add_tip(str(snowflake), bet_user, amount)
                    await ctx.send("{0} **ODD NUMBER! {1} You LOSE {2:.8f} {3}!** You should try again.".format(ctx.message.author.mention, secret_number, amount, self.currency_symbol))
            else:
                mysql.add_tip(str(snowflake), bet_user, amount)
                await ctx.send("{0} **ODD NUMBER! {1} You LOSE {2:.8f} {3}!** You should try again.".format(ctx.message.author.mention, secret_number, amount, self.currency_symbol))

def setup(bot):
    bot.add_cog(Game(bot))
