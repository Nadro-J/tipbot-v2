import discord
from discord.ext import commands
from utils import output, parsing, checks, mysql_module, helpers
import os
from setup import database

config = parsing.parse_json('config.json')
skip_cogs=config['skip_cogs']

Mysql = mysql_module.Mysql()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['prefix'], description=config["description"], intents=intents)

try:
    os.remove("logs/log.txt")
except FileNotFoundError:
    pass

startup_extensions = os.listdir("./cogs")
if "__pycache__" in startup_extensions:
    startup_extensions.remove("__pycache__")
startup_extensions = [ext.replace('.py', '') for ext in startup_extensions]
loaded_extensions = []

startup_extensions=[x for x in startup_extensions if x not in skip_cogs]

@bot.event
async def on_ready():
    output.info("Loading {} extension(s)...".format(len(startup_extensions)))
    for extension in startup_extensions:
        try:
            bot.load_extension("cogs.{}".format(extension.replace(".py", "")))
            loaded_extensions.append(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            output.error('Failed to load extension {}\n\t->{}'.format(extension, exc))
    output.success('Successfully loaded the following extension(s): {}'.format(', '.join(loaded_extensions)))
    output.info('You can now invite the bot to a server using the following link: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(bot.user.id))

@bot.event
async def on_message(message):
    # disregard messages sent by our own bot
    if message.author.id == bot.user.id:
        return

    # check if the owner is registered
    # must be done to add an entry to the db and initialize the db
    owner = config["owners"]
    for ids in owner:
        if Mysql.get_user(ids) is None:
            if message.author.id == ids:
                Mysql.register_user(ids)

    # check if the message is from a banned server
    if message.guild is not None:
        if Mysql.check_for_server_status(message.guild.id) == 2:
            return

    # check if staking account is set up
    airdrop_account = config["airdrop"]
    if Mysql.get_staking_user(airdrop_account) is None:
        Mysql.register_user(airdrop_account)

    staking_account = config["stake_bal"]
    if Mysql.get_staking_user(staking_account) is None:
        Mysql.register_user(staking_account)

    # check if treasury account is set up
    treasury_account = config["treasurer"]
    if Mysql.get_staking_user(treasury_account) is None:
        Mysql.register_user(treasury_account)

    # check if donation account is set up
    donate_account = config["donation"]
    if Mysql.get_staking_user(donate_account) is None:
        Mysql.register_user(donate_account)

    # check if game account is set up
    game_account = config["game_bal"]
    if Mysql.get_staking_user(game_account) is None:
        Mysql.register_user(game_account)

    # users that are not registered will be caught below
    # continue if the message is not from the bot
    if not message.author.bot:
        #config register keyword
        rkeyword = str(config["register_keyword"])
        prefix = str(config["prefix"])
        #rkeywordcall is the register command for users not registered
        rkeywordcall = prefix + rkeyword
        coin_name = str(config["currency_symbol"])
        #authid is the unique discord id number for the user that send the message to the server
        authid = message.author.id
        #check if the message author is in the database (meaning they are registered)
        if Mysql.get_user(authid) is None:
            #if they they are not it the database but send the
            if str(message.content).startswith(rkeywordcall) is True:
                if message.guild is not None:
                    await message.delete()

                Mysql.register_user(authid)
                await message.channel.send('{} You are now registered! :tada:'.format(message.author.mention))
                await message.channel.send('Use {}deposit to view your {} address'.format(prefix, coin_name))
                return
            elif str(message.content).startswith(prefix) is True:

                await message.channel.send('{} You are NOT registered. Type **{}** to begin.'.format(message.author.mention, rkeywordcall))
                return
        else:
            if Mysql.user_last_msg_check(message.author.id, message.content, helpers.is_private_dm(bot, message.channel)) == False:
                return 
            await bot.process_commands(message)

@bot.command(pass_context=True, hidden=True)
@commands.check(checks.is_owner)
async def shutdown(ctx):
    """Shut down the bot [ADMIN ONLY]"""
    author = str(ctx.message.author)

    try:
        await bot.say("Shutting down...")
        await bot.logout()
        bot.loop.stop()
        output.info('{} has shut down the bot...'.format(author))

    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        output.error('{} has attempted to shut down the bot, but the following '
                     'exception occurred;\n\t->{}'.format(author, exc))

@bot.command(pass_context=True, hidden=True)
@commands.check(checks.is_owner)
async def restart(ctx):
    """Restart the bot"""
    author = str(ctx.message.author)

    try:
        await ctx.send("Restarting...")
        await bot.logout()
        bot.loop.stop()
        output.info('{} has restarted the bot...'.format(author))
        os.system('sh restart.sh')

    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        output.error('{} has attempted to restart the bot, but the following '
                     'exception occurred;\n\t->{}'.format(author, exc))

@bot.command(pass_context=True, hidden=True)
@commands.check(checks.is_owner)
async def load(ctx, module: str):
    """Load a cog located in /cogs [ADMIN ONLY]"""
    author = str(ctx.message.author)
    module = module.strip()

    try:
        bot.load_extension("cogs.{}".format(module))
        output.info('{} loaded module: {}'.format(author, module))
        startup_extensions.append(module)
        await bot.say("Successfully loaded {}.py".format(module))

    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        output.error('{} attempted to load module \'{}\' but the following '
                     'exception occured;\n\t->{}'.format(author, module, exc))
        await bot.say('Failed to load extension {}\n\t->{}'.format(module, exc))

@bot.command(pass_context=True, hidden=True)
@commands.check(checks.is_owner)
async def unload(ctx, module: str):
    """Unload any loaded cog [ADMIN ONLY]"""
    author = str(ctx.message.author)
    module = module.strip()

    try:
        bot.unload_extension("cogs.{}".format(module))
        output.info('{} unloaded module: {}'.format(author, module))
        startup_extensions.remove(module)
        await bot.say("Successfully unloaded {}.py".format(module))

    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        await bot.say('Failed to load extension {}\n\t->{}'.format(module, exc))

@bot.command(hidden=True)
@commands.check(checks.is_owner)
async def loaded():
    """List loaded cogs [ADMIN ONLY]"""
    string = ""
    for cog in loaded_extensions:
        string += str(cog) + "\n"

    await bot.say('Currently loaded extensions:\n```{}```'.format(string))

@bot.event
async def on_server_join(server):
    output.info("Added to {0}".format(server.name))
    Mysql.add_server(server)
    for channel in server.channels:
        Mysql.add_channel(channel)

@bot.event
async def on_server_leave(server):
    Mysql.remove_server(server)
    output.info("Removed from {0}".format(server.name))

@bot.event
async def on_channel_create(channel):
    if isinstance(channel, discord.PrivateChannel):
        return
    Mysql.add_channel(channel)
    output.info("Channel {0} added to {1}".format(channel.name, channel.guild.name))

@bot.event
async def on_channel_delete(channel):
    Mysql.remove_channel(channel)
    output.info("Channel {0} deleted from {1}".format(channel.name, channel.guild.name))

# to be revised
async def send_cmd_help(ctx, arg_type, error):
    command = ctx.message.content.split()[0][1:]

    try:
        help = config['handler_msg'][command]
    except KeyError:
        help = 'Command not found'

    if 'BadArgument' in str(arg_type):
        descriptor = 'Bad Argument'

    if 'MissingRequiredArgument' in str(arg_type):
        descriptor = 'Missing Argument'

    if help != 'Command not found':
        em = discord.Embed(title=":exclamation: An error has occurred",
                           description="``{}``".format(arg_type),
                           color=discord.Color.red())
        em.add_field(name="Details", value="{}".format(descriptor), inline=True)
        em.add_field(name="Help", value="{}".format(help), inline=True)
        await ctx.author.send(embed=em)
    else:
        em = discord.Embed(title=":exclamation: An error has occurred",
                           description="``Command key not found``",
                           color=discord.Color.red())
        await ctx.author.send(embed=em)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        if ctx.message.guild is not None:
            await ctx.message.delete()
        await send_cmd_help(ctx, commands.MissingRequiredArgument, error)

    elif isinstance(error, commands.BadArgument):
        if ctx.message.guild is not None:
            await ctx.message.delete()
        await send_cmd_help(ctx, commands.BadArgument, error)

    elif isinstance(error, commands.CommandInvokeError):
        output.error("Exception in command '{}', {}".format(ctx.command.qualified_name, error.original))
        oneliner = "Error in command '{}' - {}: {}\nIf this issue persists, Please report it in the support server.".format(
            ctx.command.qualified_name, type(error.original).__name__, str(error.original))
        await ctx.send(oneliner)

    elif isinstance(error, commands.CommandOnCooldown):
        if ctx.message.guild is not None:
            await ctx.message.delete()
        await ctx.author.send(f'This command is on cooldown. Please wait {error.retry_after:.2f}s :alarm_clock: ')

database.run()
bot.run(config["discord"]["token"])
bot.loop.close()
