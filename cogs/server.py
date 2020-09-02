import discord, os, itertools
from discord.ext import commands
from utils import parsing, checks, mysql_module

mysql = mysql_module.Mysql()


class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, hidden=True)
    @commands.check(checks.in_server)
    @commands.check(checks.is_owner)
    async def allowsoak(self, ctx, enable: bool):
        """
        Enable and disable the soak feature [ADMIN ONLY]
        """
        mysql.set_soak(ctx.message.server, int(enable))
        if enable:
            await self.bot.say("Ok! Soaking is now enabled! :white_check_mark:")
        else:
            await self.bot.say("Ok! Soaking is now disabled! :no_entry_sign:")

    @commands.command(pass_context=True)
    @commands.check(checks.in_server)
    async def checksoak(self, ctx):
        """
        Checks if soak is available on the server
        """
        result_set = mysql.check_soak(ctx.message.server)
        if result_set:
            await self.bot.say("Soaking is enabled! :white_check_mark:")
        else:
            await self.bot.say("Soaking is disabled! :no_entry_sign:")


def setup(bot):
    bot.add_cog(Server(bot))
