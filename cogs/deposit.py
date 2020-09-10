import discord, json, requests
from discord.ext import commands
from utils import parsing, mysql_module

mysql = mysql_module.Mysql()

class Deposit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]  
        self.stakeflake = config["stake_bal"]
        self.treasurer = config["treasurer"]
        self.donate = config["donation"]
        self.game_id = config["game_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        self.explorer = config["explorer_url"]

        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command()
    async def deposit(self, ctx):
        """Show Your Deposit Address on this Tip Bot Service. Use the address to send coins to your account on this Tip Bot."""
        user = ctx.message.author
        snowflake = ctx.message.author.id
        balance = mysql.get_balance(str(snowflake), check_update=True)
        balance_unconfirmed = mysql.get_balance(snowflake, check_unconfirmed = True)
        # Check if user exists in db
        mysql.check_for_user(user.id)
        user_addy = mysql.get_address(user.id)
        embed=discord.Embed(title="You requested your **Deposit Address**", color=self.embed_color)
        embed.set_author(name="{}".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name=":man_farmer: User", value=ctx.message.author.mention, inline=True)
        embed.add_field(name=":moneybag: Balance",value="{:.8f} {}".format(round(float(balance), 8), self.currency_symbol), inline=True)
        embed.add_field(name=":notepad_spiral: Deposit Address", value="`{}`".format(user_addy), inline=False)
        if float(balance_unconfirmed) != 0.0:
            embed.add_field(name=":red_circle: Unconfirmed Deposits", value="{:.8f} {}".format(round(float(balance_unconfirmed), 8),self.currency_symbol))
        embed.add_field(name=":newspaper: Deposit Transactions", value="Type $dlist for a list of your deposits.")
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.author.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

        if ctx.message.guild is not None:
            await ctx.send("{}, I PMed you your **Deposit Address**! Make sure to double check that it is from me!".format(user.mention))

#    @commands.command(pass_context=True)
#    async def mobile(self, ctx):
#        """Show Your Deposit Address on this Tip Bot Service. Use the address to send coins to your account on this Tip Bot.  Formatted for easy copying on Mobile."""
#        user = ctx.message.author
        # Check if user exists in db
        # mysql.check_for_user(user.id)
#        if mysql.check_for_user(snowflake) is None:
#            return
#        user_addy = mysql.get_address(user.id)

#        await self.bot.send_message(ctx.message.author, "Your {} ({}) Deposit Address: \n".format(self.coin_name, self.currency_symbol))
#        await self.bot.send_message(ctx.message.author, "**{}**".format(user_addy))

#        if ctx.message.server is not None:
#            await self.bot.say("{}, I PMed you your **Deposit Address**! Make sure to double check that it is from me!".format(user.mention))

    @commands.command()
    async def dlist(self, ctx):
        """Show a list of your Deposits on this Tip Bot Service. TXID, Amount, and Deposit Status are displayed to easily track deposits."""
        user = ctx.message.author
        txcounter = 0

        # only allow this message to be sent privatly for privacy - send a message to the user in the server.    
        if ctx.message.guild is not None:
            await ctx.send("{}, I PMed you your **Deposit List**! Make sure to double check that it is from me!".format(user.mention))
        # begin sending pm transaction list to user
        await ctx.author.send("{} You requested Your **{} ({}) Deposits**: \n".format(user.mention, self.coin_name, self.currency_symbol))
        # Check if user exists in db
        if mysql.check_for_user(user.id) is None:
            await ctx.send("User is not found in the database")
            return

        embed = discord.Embed(title="{} {} Deposits".format(self.coin_name, self.currency_symbol), color=self.embed_color)

        user_addy = mysql.get_address(user.id)
        embed.add_field(name=":notepad_spiral: Deposit Address", value="`{}`".format(user_addy), inline=True)

        # Get the list of deposit txns by user.id transactions
        conf_txns = mysql.get_deposit_list_byuser(user.id)
        embed.add_field(name=":evergreen_tree: Total number of deposits", value=len(conf_txns), inline=True)

        # List the transactions
        for txns in conf_txns:
            txcounter = txcounter + 1
            dep_amount = mysql.get_deposit_amount(txns)
            embed.add_field(name=":currency_exchange: TXID #{}".format(txcounter), value="<https://{}{}>".format(self.explorer, str(txns)), inline=False)
            embed.add_field(name=":moneybag: Deposit amount", value="{:.8f} {}".format(float(dep_amount), self.currency_symbol), inline=True)

            dep_status = mysql.get_transaction_status_by_txid(txns)
            if dep_status == 'CONFIRMED':
                embed.add_field(name=":white_check_mark: Deposit status", value="{}".format(dep_status), inline=True)
            else:
                embed.add_field(name=":ballot_box_with_check: Deposit status", value="{}".format(dep_status), inline=True)

            # Show a maximum of 5 deposits (limited by Discords 2000 character limitation)
            if txcounter == 5 or len(conf_txns) == txcounter:
                break

            embed.add_field(name="\u200b\n", value="\u200b\n", inline=False)

        await ctx.author.send(embed=embed)


def setup(bot):
    bot.add_cog(Deposit(bot))


