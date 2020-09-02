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
    async def guess(self, ctx, amount:float, *args: discord.Member):
        """User: Guess a user from the registered users list
        Bot: chooses a random user and compare to the users guess
        if the user guess equals the bots choice then the user receives 10X coins they bet
        """
        #snowflake is a str that eqals the discord call for the authors id number
        snowflake = ctx.message.author.id
        #make sure the list of args contains on one user
        users=list(set(args))
        if len(users) == 0:
            await self.bot.say("{} **:warning:You must guess One user!:warning:**".format(ctx.message.author.mention))
            return

        if len(users) != 1:
            await self.bot.say("{} **:warning:You cannot guess more than One user!:warning:**".format(ctx.message.author.mention))
            return
  
        for user in users:
            #guess_user is the str of the id of the user guess passed from args
            guess_user = str(user.id)
            #check that the guess_user is in the database
            if mysql.get_user(guess_user) is None:
                await self.bot.say("{} **:warning:You cannot guess a User that is Not registered!:warning:**".format(ctx.message.author.mention))
                return   
            #check if sender is trying to guess to themselves and return error to user in chat
            if snowflake == guess_user:
                await self.bot.say("{} **:warning:You cannot guess yourself!:warning:**".format(ctx.message.author.mention))
                return
            #check if amount is negative and return error to user in chat
            if amount <= 0.0:
                await self.bot.say("{} **:warning:You cannot bet <= 0!:warning:**".format(ctx.message.author.mention))
                return

            #if all the checks above pass get the snowflakes balance(user that sent message)
            balance = mysql.get_balance(snowflake, check_update=True)
            #check the senders balance for overdraft and return error to user in chat
            if float(balance) < amount:
                await self.bot.say("{} **:warning:You cannot bet more money than you have!:warning:**".format(ctx.message.author.mention))
            #run the game
            else:
                #choose a random user from the users list
                bot_guess = int(random.choice(mysql.get_reg_users_id()))
                guess_user_id = int(user.id)
                #await self.bot.say("{} **Sorry! You guessed {}. Betting {} {}! I was thinking {}.  You Lost {} {}**".format(ctx.message.author.mention, guess_user_id, str(amount), self.currency_symbol, bot_guess, str(amount), self.currency_symbol))
                
                #if the random id is equal to any hardcoded ids pick a new random user
                if bot_guess == int(self.game_id):
                    bot_guess = int(random.choice(mysql.get_reg_users_id()))
                if bot_guess == int(self.donation_id):
                    bot_guess = int(random.choice(mysql.get_reg_users_id()))
                if bot_guess == int(self.stake_id):
                    bot_guess = int(random.choice(mysql.get_reg_users_id()))
                if bot_guess == int(self.treasury_id):
                    bot_guess = int(random.choice(mysql.get_reg_users_id()))

                #compare that user to guess user if the user losses than tip the game_bal
                servermembers = [x for x in ctx.message.server.members]
                for member in servermembers:
                    if int(member.id) == int(bot_guess):
                        bot_user_guess = str(member.mention)
                        break
                if bot_guess != guess_user_id:
                    mysql.add_tip(snowflake, self.game_id, amount)
                    await self.bot.say("{} **SORRY! You guessed {} - Betting {} {}! I was thinking {}.  You Lost {} {}**".format(ctx.message.author.mention, user.mention, str(amount), self.currency_symbol, bot_user_guess, str(amount), self.currency_symbol))
                    #if the user looses they have a 1-6 chance of getting a free bet roll
                    if random.randint(1,6) == 3:
                        await self.bot.say("{} **You Get a Free Bet for {} {}!**".format(ctx.message.author.mention, str(amount), self.currency_symbol))       
                        #begin the betting - choose a random int between 0-999999999 if even win, if odd lose
                        secret_number = random.randint(1,9999999) 
                        if secret_number % 2 == 0 and secret_number != 0:
                            bet_admin_bal = mysql.get_balance(self.game_id, check_update=True)
                            if float(bet_admin_bal) >= amount:
                                mysql.add_tip(self.game_id, snowflake, amount)
                                await self.bot.say("{} **EVEN NUMBER! {} You WIN the Free Roll for {} {}! :tada:**".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                            else:
                                await self.bot.say("{} **EVEN NUMBER! {} You WIN the Free Roll for {} {}!** BUT THE BOT DOES NOT HAVE ENOUGH FUNDS TO PAY YOU".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                        else:
                            await self.bot.say("{} **ODD NUMBER! {} You LOSE the Free Roll for {} {}!** You should try again.".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                else:
                    win_amount = amount * 10.0
                    bet_user = str(self.game_id)
                    bet_user_bal = mysql.get_balance(self.game_id, check_update=True)
                    if float(bet_user_bal) >= win_amount:
                        mysql.add_tip(self.game_id, snowflake, win_amount)
                        await self.bot.say("{} **YOU WIN! You guessed {}. Betting {} {}!  I was thinking {}.  You WON {} {}!!!:tada:**".format(ctx.message.author.mention, user.mention, str(amount), self.currency_symbol, bot_user_guess, str(win_amount), self.currency_symbol))
                    else:
                        await self.bot.say("{} **YOU WIN! You guessed {}. Betting {} {}!  I was thinking {}.  You WON {} {} BUT UNFORTUNATLY I DO NOT HAVE ENOUGH COINS TO PAY YOU.".format(ctx.message.author.mention, user.mention, str(amount), self.currency_symbol, bot_user_guess, str(win_amount), self.currency_symbol))



    @commands.command(pass_context=True)
    async def bet(self, ctx, amount:float):
        """Donate to a donation account"""
        snowflake = ctx.message.author.id
        #the betting user is the house
        bet_user = str(self.game_id)
        #check if amount is negative and return error to user in chat
        if amount <= 0.0:
            await self.bot.say("{} **:warning:You cannot bet <= 0!:warning:**".format(ctx.message.author.mention))
            return
        #check if receiver is in database

        balance = mysql.get_balance(snowflake, check_update=True)
        #check the senders balance for overdraft and return error to user in chat
        if float(balance) < amount:
            await self.bot.say("{} **:warning:You cannot bet more {} than you have!:warning:**".format(ctx.message.author.mention, self.currency_symbol))
        else:
            #begin the betting - choose a random int between 0-999999999 if even win, if odd lose
            secret_number = random.randint(1,9999999) 
            if secret_number % 2 == 0 and secret_number != 0:
                secret_number = random.randint(1,9999999)
                if secret_number % 2 == 0 and secret_number != 0:
                    bet_user_bal = mysql.get_balance(self.game_id, check_update=True)
                    if float(bet_user_bal) >= amount:
                        mysql.add_tip(bet_user, snowflake, amount)
                        await self.bot.say("{} **EVEN NUMBER! {} You WIN {} {}! :tada:**".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                    else:
                        await self.bot.say("{} **EVEN NUMBER! {} You WIN {} {}!** BUT THE BOT DOES NOT HAVE ENOUGH FUNDS TO PAY YOU".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
                else:
                    mysql.add_tip(snowflake, bet_user, amount)
                    await self.bot.say("{} **ODD NUMBER! {} You LOSE {} {}!** You should try again.".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))
            else:
                mysql.add_tip(snowflake, bet_user, amount)
                await self.bot.say("{} **ODD NUMBER! {} You LOSE {} {}!** You should try again.".format(ctx.message.author.mention, secret_number, str(amount), self.currency_symbol))

def setup(bot):
    bot.add_cog(Game(bot))
