import discord, json, requests, pymysql.cursors
from discord.ext import commands
from utils import rpc_module, mysql_module, parsing
import math

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Withdraw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')         
        self.is_treasurer = config["treasurer"]
        self.explorer = config["explorer_url"]
        self.currency_symbol = config["currency_symbol"]
        self.coin_name = config["currency_name"]
        self.withdrawfee = config["withdraw_fee"]
        self.withdrawmax = config["withdraw_max"]
        self.minwithdraw = config["min_withdrawal"]
        self.bot_name = config["description"]

        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(pass_context=True)
    async def withdraw(self, ctx, address: str, amount: float):
        """Withdraw coins from your account to any address, You agree to pay a withdrawal fee to support the costs of this service"""
        snowflake = ctx.message.author.id
        if amount <= float(self.minwithdraw):
            await ctx.author.send("{} **:warning: Minimum withdrawal amount is {:.8f} {} :warning:**".format(ctx.message.author.mention, float(self.minwithdraw), self.currency_symbol))
            return

        # await self.bot.say("checkingbotfee")
        # calculate bot fee and pay to owner in form of a tip
        botfee = amount * float(self.withdrawfee)
        if botfee >= float(self.withdrawmax):
            botfee = float(self.withdrawmax)
            amount = amount - botfee
        else:
            amount = amount - botfee

        # await self.bot.say("checking amount")
        abs_amount = abs(amount)
        if math.log10(abs_amount) > 8:
            await ctx.author.send(":warning: **Invalid amount!** :warning:")
            return
        # await self.bot.say("checking for user")
        mysql.check_for_user(str(snowflake))
        # await self.bot.say("rpc call to check address")
        conf = rpc.validateaddress(address)
        if not conf["isvalid"]:
            await ctx.send("{} **:warning: Invalid address! :warning:**".format(ctx.message.author.mention))
            return

        # await self.bot.say("check if owned by bot")
        ownedByBot = False
        for address_info in rpc.listreceivedbyaddess(0, True):
            if address_info["address"] == address:
                ownedByBot = True
                break
        if ownedByBot:
            await self.bot.say("{} **:warning: You cannot withdraw to an address owned by this bot! :warning:** Please use tip instead!".format(ctx.message.author.mention))
            return
        # await self.bot.say("get the withdrawers balance")
        balance = mysql.get_balance(str(snowflake), check_update=True)
        if float(balance) < amount:
            await ctx.author.send("{} **:warning: You cannot withdraw more {} than you have! :warning:**".format(ctx.message.author.mention, self.currency_symbol))
            return

        txid = mysql.create_withdrawal(str(snowflake), address, amount)
        if txid is None:
            await ctx.author.send("{} your withdraw failed despite having the necessary balance! Please contact the bot owner".format(ctx.message.author.mention))
        else:
            botowner = self.is_treasurer
            # do a tip to transfer the bot fee after the transaction is done
            mysql.add_tip(str(snowflake), botowner, botfee)
            usermention = ctx.message.author.mention
            updbalance = mysql.get_balance(str(snowflake), check_update=True)
            # send an embed receipt to the user
            embed=discord.Embed(title="You made a **Withdrawal**", color=self.embed_color)
            embed.set_author(name="{}".format(self.bot_name))
            embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
            embed.add_field(name=":man_farmer: User", value="{}".format(usermention), inline=True)
            embed.add_field(name=":moneybag: Balance", value="{:.8f} {}".format(round(float(updbalance), 8),self.currency_symbol), inline=True)
            embed.add_field(name=":currency_exchange: TXID", value="http://{}{}".format(self.explorer, str(txid)), inline=False)
            embed.add_field(name=":notepad_spiral: Withdrawal Address", value="{}".format(address), inline=False)
            embed.add_field(name=":dollar: Withdraw Amount", value="{:.8f} {}".format(float(amount), self.currency_symbol), inline=True)
            embed.add_field(name=":paperclip: Fee", value="{:.8f} {}".format(float(botfee), self.currency_symbol), inline=False)
            embed.add_field(name="Withdrawal Transactions", value="Type $wlist for a list of your deposits.")
            embed.set_footer(text=self.footer_text)
            try:
                await ctx.author.send(embed=embed)
            except discord.HTTPException:
                await ctx.send("I need the `Embed links` permission to send this")

            if ctx.message.guild is not None:
                await ctx.send("{}, I PMed you your **Withdrawal Confirmation**! Make sure to double check that it is from me!".format(usermention))
                await ctx.send(":warning: {}, To Protect Your Privacy, please make Withdrawals by messaging me directly next time. :warning:".format(usermention))

    @commands.command(pass_context=True)
    async def wlist(self, ctx):
        """Show a list of your Withdrawals on this Tip Bot Service. TXID, and Amount are displayed to easily track withdrawals."""
        user = ctx.message.author
        # only allow this message to be sent privatly for privacy - send a message to the user in the server.    
        if ctx.message.guild is not None:
            await ctx.send("{}, I PMed you your **Withdrawal List**! Make sure to double check that it is from me!".format(user.mention))
        # begin sending pm transaction list to user
        await ctx.author.send("{} You requested Your **{} ({}) Withdrawals**: \n".format(user.mention, self.coin_name, self.currency_symbol))
        # Check if user exists in db
        if mysql.check_for_user(user.id) is None:
            await ctx.author.send("User is not found in the database")
            return
        # Get the list of deposit txns by user.id transactions
        conf_txns = mysql.get_withdrawal_list_byuser(user.id)
        await ctx.author.send("Number of Withdrawals: **{}**".format(len(conf_txns)))
        # List the transactions
        for txns in conf_txns:
            wit_amount = mysql.get_withdrawal_amount(txns)
            await ctx.author.send("TXID: <http://{}{}>".format(self.explorer, str(txns)))
            await ctx.author.send("Withdrawal amount {:.8f} {}".format(float(wit_amount), self.currency_symbol))

def setup(bot):
    bot.add_cog(Withdraw(bot))
