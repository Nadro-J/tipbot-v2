import discord
from discord.ext import commands
from utils import rpc_module, mysql_module, parsing, checks

#result_set = database response with parameters from query
#db_bal = nomenclature for result_set["balance"]
#snowflake = snowflake from message context, identical to user in database
#wallet_bal = nomenclature for wallet reponse

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Balance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stake_id = config["stake_bal"]
        self.donate = config["donation"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(pass_context=True)
    async def balance(self, ctx):
        """Display your balance"""
        # Set important variables
        snowflake = ctx.message.author.id

        # Check if user exists in db
        mysql.check_for_user(str(snowflake))

        balance = mysql.get_balance(str(snowflake), check_update=True)
        balance_unconfirmed = mysql.get_balance(str(snowflake), check_unconfirmed = True)

        # get the users staking rewards
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, str(snowflake))

        # get the users donated amount
        donations = mysql.get_tip_amounts_from_id(str(snowflake), self.donate)
        # Execute and return SQL Query

        # Simple embed function for displaying username and balance
        embed=discord.Embed(title="You requested your **Balance**", color=self.embed_color)
        embed.set_author(name=self.bot_name)
        embed.add_field(name="User", value=ctx.message.author.mention, inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(balance), 8),self.currency_symbol))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        if float(balance_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Deposits", value="{:.8f} {}".format(round(float(balance_unconfirmed), 8),self.currency_symbol))
        if float(sum(stakes)) != 0.0:
            embed.add_field(name="Your Total Staking Rewards", value="{:.8f} {}".format(round(float(stakes), 8),self.currency_symbol))
        if float(sum(donations)) != 0.0:
            embed.add_field(name="Your Total Donations", value="{:.8f} {}".format(round(float(donations), 8),self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.author.send(embed=embed)
            if ctx.message.guild is not None:
                await ctx.send("{}, I PMed you your **Balance**! Make sure to double check that it is from me!".format(ctx.message.author.mention))
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

def setup(bot):
    bot.add_cog(Balance(bot))
