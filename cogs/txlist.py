import discord
from discord.ext import commands
from utils import rpc_module, mysql_module, parsing, checks

#result_set = database response with parameters from query
#db_bal = nomenclature for result_set["balance"]
#snowflake = snowflake from message context, identical to user in database
#wallet_bal = nomenclature for wallet reponse

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()

class Txlist(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        #parse the config file
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]   
        self.stakeflake = config["stake_bal"]
        self.treasurer = config["treasurer"]
        self.donate = config["donation"]
        self.game_id = config["game_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]

        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    async def do_stake_embed(self, ctx, name, db_bal, db_bal_unconfirmed, stake_total_amt, stake_total_received, reg_users_eligible):
        # Simple embed function for displaying username and balance
        embed=discord.Embed(title="You requested the **Staking Balance**", color=self.embed_color)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.add_field(name="User", value=name, inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(db_bal), 8),self.currency_symbol))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        if float(db_bal_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Staking Deposits", value="{:.8f} {}".format(round(float(db_bal_unconfirmed), 8),self.currency_symbol))
        embed.add_field(name="Total Stakes", value="{}".format(int(stake_total_amt)))
        embed.add_field(name="Total Received From Staking", value="{:.8f} {}".format(round(float(stake_total_received), 8),self.currency_symbol))
        embed.add_field(name="Users Eleigible for Staking Payout", value="{}".format(int(reg_users_eligible)))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    async def do_fee_embed(self, ctx, name, db_bal, db_bal_unconfirmed, stake_total):
        # Simple embed function for displaying username and balance
        embed=discord.Embed(title="You requested the **Fee Balance**", color=self.embed_color)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.add_field(name="User", value=name, inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(db_bal), 8),self.currency_symbol))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        if float(db_bal_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Fee Deposits", value="{:.8f} {}".format(round(float(db_bal_unconfirmed), 8),self.currency_symbol))
        if float(stake_total) != 0.0:
            embed.add_field(name="Your Total Staking Rewards", value="{:.8f} {}".format(round(float(stake_total), 8),self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    async def do_donate_embed(self, ctx, name, db_bal, db_bal_unconfirmed, stake_total):
        # Simple embed function for displaying username and balance
        embed=discord.Embed(title="You requested the **Donate Balance**", color=self.embed_color)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.add_field(name=":man_farmer: User", value=name, inline=False)
        embed.add_field(name=":moneybag: Balance", value="{:.8f} {}".format(round(float(db_bal), 8),self.currency_symbol))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        if float(db_bal_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Deposits", value="{:.8f} {}".format(round(float(db_bal_unconfirmed), 8),self.currency_symbol))
        if float(stake_total) != 0.0:
            embed.add_field(name="Your Total Staking Rewards", value="{:.8f} {}".format(round(float(stake_total), 8),self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    async def do_all_embed(self, ctx, name, address, request, db_bal, db_bal_unconfirmed, stake_total):
        # Simple embed function for displaying username and balance
        embed=discord.Embed(title="You requested the **{}**".format(request), color=self.embed_color)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.add_field(name="User", value="{} {}".format(self.coin_name, name), inline=False)
        embed.add_field(name="Address", value=str(address), inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(db_bal), 8),self.currency_symbol))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        if float(db_bal_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Deposits", value="{:.8f} {}".format(round(float(db_bal_unconfirmed), 8),self.currency_symbol))
        if float(stake_total) != 0.0:
            embed.add_field(name="Your Total Staking Rewards", value="{:.8f} {}".format(round(float(stake_total), 8),self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission to send this")

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def fees(self, ctx):
        """Display your balance"""
        if ctx.message.guild is not None:
            await ctx.message.delete()

        # Set important variables
        snowflake = str(self.treasurer)
        #await self.bot.say("Staking account snowflake: {}".format(snowflake))
        name = str("Treasury Account - Withdrawl and Staking Fees")

        # Check if user exists in db
        #await self.bot.say("Checking for updated mining balance")
        mysql.check_for_updated_mining_balance()
        #await self.bot.say("Checking if staking user exists")
        mysql.get_staking_user(snowflake)

        #if you call get_balance with the snowflake equal to the tresury account
        #await self.bot.say("Checking balance")
        balance = mysql.get_balance(snowflake, check_update=True)

        #await self.bot.say("Checking unconfirmed staking balance")
        balance_unconfirmed = mysql.get_balance(snowflake, check_unconfirmed = True)

        # get the users staking rewards
        stakes =  mysql.get_tip_amounts_from_id(self.stakeflake, snowflake)

        # Execute and return SQL Query
        await self.do_fee_embed(ctx, name, balance, balance_unconfirmed, sum(stakes))

    @commands.command(pass_context=True, hidden=True)
    @commands.check(checks.is_owner)
    async def stake(self, ctx):
        if ctx.message.guild is not None:
            await ctx.message.delete()

        # Set important variables
        snowflake = str(self.stakeflake)
        # await self.bot.say("Staking account snowflake: {}".format(snowflake))
        name = str("Staking Account")

        # Check if user exists in db
        # await self.bot.say("Checking for updated mining balance")
        # mysql.check_for_updated_mining_balance()
        # await self.bot.say("Checking if staking user exists")
        mysql.get_staking_user(snowflake)

        # if you call get_balance with the snowflake equal to the staking account it will initialize the check for mined transactions
        # the mined transactions are added to the staking account
        # await self.bot.say("Checking balance")
        balance = mysql.get_balance(snowflake, check_update=True)

        # await self.bot.say("Checking unconfirmed staking balance")
        balance_unconfirmed = mysql.get_balance(snowflake, check_unconfirmed = True)

        # get the total number of stakes returned in a list of txids
        stake_tips = mysql.get_deposit_list("CONFIRMED-STAKE")
        stake_total_amt = len(stake_tips)
        # await self.bot.say("number of stakes received {}".format(stake_total_amt))

        # get the total balance received from stakes
        stake_total_received = []
        for x in stake_tips:
            stake_total_received.append(mysql.get_deposit_amount(x))

        # await self.bot.say("total amount received from staking {}".format(sum(stake_total_received)))

        # find the total balance that was staked
        # the balance is fetched directly from the wallet using rpc
        # balance is ussually found in using the getinfo command you need to add the balance that is staking in case the wallet is currently staking
        balance_staked = rpc.getbalance() - float(balance)
        # await self.bot.say("wallet ballance is {} and balance staked is {}".format(wallet_balance, balance_staked))

        # get the number of users that will receive this stake
        # first get all the reg_users_id
        all_regusr = mysql.get_reg_users_id()
        # await self.bot.say("registered users were imported")
        # check if the balance is below 0.00001000 and remove user from the list
        reg_users_eligible = []
        for users in all_regusr:
            reg_str = str(users)
            #remove the staking account from the eligible users list
            if reg_str == self.stakeflake:
                continue
            user_bal = mysql.get_balance(reg_str, check_update=True)

            if (float(user_bal) >= 0.00001001):
                # now the reg user list contains those eligible for the stake lets get the length of the list to pass
                reg_users_eligible.append(reg_str)
        #await self.bot.say("Reg_users_eligible was appended")

        # print into the embed object
        await self.do_stake_embed(ctx, name, balance, balance_unconfirmed, stake_total_amt, sum(stake_total_received), len(reg_users_eligible))

        # if the balance is > 0 continue to pay out
        if balance <= 0:
            return
        # actually do the payout
        # for each user divide the users balance by the total
        for eligibleusrs in reg_users_eligible:
            usrbal = mysql.get_balance(eligibleusrs)
            userpercent = float(usrbal) / balance_staked
            stake_payout_pre = userpercent * float(balance)
            stake_payout = stake_payout_pre - 0.00000001
            # await self.bot.say("stake payout is {:.8f}".format(float(stake_payout)))
            if mysql.check_for_user(eligibleusrs) is not None:
                balance_stakeacct = mysql.get_staking_user(snowflake)
                balance_stake = balance_stakeacct["balance"]
                # check the senders balance for overdraft and return error to user in chat, do not check for update again
                if float(balance_stake) < stake_payout:
                    # await self.bot.say("Stake Account Manager **:warning:You cannot tip more money than you have!:warning:**")
                    continue
                elif float(stake_payout) < 0:
                    # await self.bot.say("Stake Account Manager **:warning: Stake Payout was Negative, skipping**")
                    continue
                else:
                    mysql.add_tip(snowflake, eligibleusrs, stake_payout)
                    # servermembers = ctx.message.server.members
                    # for member in servermembers:
                    #     if int(member.id) == int(eligibleusrs):
                    #         stake_recv_mention = str(member.mention)
                    #         await self.bot.say("Staking Payouts **Tipped {} {:.8f} {}! :moneybag:**".format(stake_recv_mention, stake_payout, self.currency_symbol))
        # take the extra and transfer to the fees account
        balance_stakeacct = mysql.get_staking_user(snowflake)
        balance_stake = balance_stakeacct["balance"]
        if balance_stake > 0.0:
            mysql.add_tip(snowflake, self.treasurer, balance_stake)
            # await self.bot.say("Staking Payouts **Sent {:.8f} {} to Fees! :moneybag:**".format(balance_stake, self.currency_symbol))

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def donations(self, ctx):
        if ctx.message.guild is not None:
            await ctx.message.delete()
        # Set important variables
        snowflake = str(self.donate)
        #await self.bot.say("Staking account snowflake: {}".format(snowflake))
        name = str("Donation Account")

        # Check if user exists in db
        #await self.bot.say("Checking for updated mining balance")
        #mysql.check_for_updated_mining_balance()
        #await self.bot.say("Checking if staking user exists")
        mysql.get_staking_user(snowflake)

        #if you call get_balance with the snowflake equal to the staking account it will initialize the check for mined transactions
        #the mined transactions are added to the staking account
        #await self.bot.say("Checking balance")
        balance = mysql.get_balance(snowflake, check_update=True)

        #await self.bot.say("Checking unconfirmed staking balance")
        balance_unconfirmed = mysql.get_balance(snowflake, check_unconfirmed = True)

        stakes =  mysql.get_tip_amounts_from_id(self.stakeflake, snowflake)

        # Execute and return SQL Query
        await self.do_donate_embed(ctx, name, balance, balance_unconfirmed, sum(stakes))

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def gamebal(self, ctx):
        if ctx.message.guild is not None:
            await ctx.message.delete()

        # Set important variables
        snowflake = str(self.game_id)
        #await self.bot.say("Staking account snowflake: {}".format(snowflake))
        name = str("Game Account")
        request = str("Game Balance")

        # Check if user exists in db
        #await self.bot.say("Checking for updated mining balance")
        #mysql.check_for_updated_mining_balance()
        #await self.bot.say("Checking if staking user exists")
        mysql.get_staking_user(snowflake)

        #get user addres
        address = mysql.get_address(snowflake)

        #if you call get_balance with the snowflake equal to the staking account it will initialize the check for mined transactions
        #the mined transactions are added to the staking account
        #await self.bot.say("Checking balance")
        balance = mysql.get_balance(snowflake, check_update=True)

        #await self.bot.say("Checking unconfirmed staking balance")
        balance_unconfirmed = mysql.get_balance(snowflake, check_unconfirmed = True)

        stakes =  mysql.get_tip_amounts_from_id(self.stakeflake, snowflake)

        # Execute and return SQL Query
        await self.do_all_embed(ctx, name, address, request, balance, balance_unconfirmed, sum(stakes))

def setup(bot):
    bot.add_cog(Txlist(bot))
